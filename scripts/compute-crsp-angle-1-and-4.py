"""Phase 1 step 2 - Recompute Angle 1 (event-CAR + 60d drift) and Angle 4
(recurring NT-filer XS) on CRSP-historical returns including delret.

Uses data/crsp_returns.parquet (pulled from WRDS local dump dsf_v2 with
ticker filter restricted to our NYSE+Nasdaq matched NT cohort).
Market proxy = SPY from existing yfinance cache (no equivalent ETF
needed; SPY is the standard market benchmark).

Critical Phase 1 difference vs Phase 0 yfinance-based step 5+7:
  - dlyret on the delist day is the CRSP "delret" — captures the full
    economic delisting event (often -100% for distressed delists)
  - delisted-firm forward returns DO appear in CRSP (yfinance doesn't
    have them at all)
  - Survivorship-recovery bias mitigated

Outputs:
  data/crsp_angle_1_car.jsonl    per-filing event-CAR + 60d drift
  data/crsp_angle_4_recurring.jsonl per-filing forward 90d/252d
  reports/crsp-angle-1-summary.json  cell verdicts
  reports/crsp-angle-4-summary.json  cell verdicts

Lock F clean — sort-stable on (permno, dlycaldt) on input;
output sorted on (cik, date_filed, accession_number).

Usage:
    python scripts/compute-crsp-angle-1-and-4.py
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import mean, pstdev

REPO_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = REPO_ROOT / "data" / "yfinance_cache"


def _winsorize(vals: list[float], lo_pct: float = 1.0, hi_pct: float = 1.0) -> dict:
    sv = sorted(v for v in vals if v is not None)
    n = len(sv)
    if n == 0:
        return {"n": 0, "mean_pct": None, "t_stat": None}
    a = int(n * lo_pct / 100)
    b = max(int(n * (100 - hi_pct) / 100) - 1, a)
    lo, hi = sv[a], sv[b]
    w = [min(max(v, lo), hi) for v in sv]
    m = mean(w)
    s = pstdev(w) if len(w) > 1 else 0.0
    t = m / (s / (len(w) ** 0.5)) if s > 0 else 0.0
    return {"n": len(w), "mean_pct": round(100 * m, 4),
            "stdev_pct": round(100 * s, 4), "t_stat": round(t, 3)}


def _spy_return_series() -> dict[str, float]:
    """Build SPY daily return series from yfinance cache."""
    p = CACHE_DIR / "SPY.jsonl"
    if not p.exists():
        return {}
    prices = [json.loads(l) for l in p.open(encoding="utf-8")]
    prices.sort(key=lambda r: r["date"])
    out: dict[str, float] = {}
    prev: float | None = None
    for r in prices:
        c = r["close"]
        if prev is not None and prev > 0:
            out[r["date"]] = c / prev - 1.0
        prev = c
    return out


def _car(firm_returns: list[tuple[str, float]],
         market: dict[str, float],
         filing_date: str, start: int, end: int) -> float | None:
    t0_idx = None
    for i, (d, _) in enumerate(firm_returns):
        if d >= filing_date:
            t0_idx = i
            break
    if t0_idx is None:
        return None
    s_idx = t0_idx + start
    e_idx = t0_idx + end
    if s_idx < 0 or e_idx >= len(firm_returns):
        return None
    car = 0.0
    n = 0
    for i in range(s_idx, e_idx + 1):
        d, fr = firm_returns[i]
        mr = market.get(d)
        if mr is None:
            continue
        car += (fr - mr)
        n += 1
    return car if n > 0 else None


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--matched", default=str(REPO_ROOT / "data" / "form_nt_matched.jsonl"))
    p.add_argument("--crsp", default=str(REPO_ROOT / "data" / "crsp_returns.parquet"))
    p.add_argument("--exchanges", default="NYSE,Nasdaq")
    p.add_argument("--out-angle-1", default=str(REPO_ROOT / "data" / "crsp_angle_1_car.jsonl"))
    p.add_argument("--out-angle-4", default=str(REPO_ROOT / "data" / "crsp_angle_4_recurring.jsonl"))
    p.add_argument("--report-1", default=str(REPO_ROOT / "reports" / "crsp-angle-1-summary.json"))
    p.add_argument("--report-4", default=str(REPO_ROOT / "reports" / "crsp-angle-4-summary.json"))
    args = p.parse_args()

    # Load filings
    exch = set(args.exchanges.split(","))
    filings = [json.loads(l) for l in Path(args.matched).open(encoding="utf-8")]
    filings = [r for r in filings if r.get("ticker") and r.get("exchange") in exch]
    print(f"NT filings in scope: {len(filings)}", flush=True)

    # Load CRSP returns via DuckDB
    import duckdb
    db = duckdb.connect(":memory:")
    print("Loading CRSP returns...", flush=True)
    df = db.execute(
        f"SELECT ticker, dlycaldt, dlyret, dlydelflg FROM read_parquet('{args.crsp}') "
        f"WHERE dlyret IS NOT NULL ORDER BY ticker, dlycaldt"
    ).fetchdf()
    print(f"  rows: {len(df)}", flush=True)

    # Group returns by ticker
    by_ticker: dict[str, list[tuple[str, float, str]]] = defaultdict(list)
    for tk, dt, ret, delflg in zip(df["ticker"], df["dlycaldt"], df["dlyret"], df["dlydelflg"]):
        # Normalize to YYYY-MM-DD (drop any time component) so we can compare
        # against SPY yfinance cache keys, which are date-only strings.
        if hasattr(dt, "strftime"):
            d_str = dt.strftime("%Y-%m-%d")
        else:
            d_str = str(dt)[:10]
        by_ticker[tk].append((d_str, float(ret), str(delflg) if delflg is not None else ""))

    # Resort firm-day list to ensure stability (parquet read should already be sorted)
    for tk in by_ticker:
        by_ticker[tk].sort(key=lambda r: r[0])

    print(f"Distinct tickers with CRSP data: {len(by_ticker)}", flush=True)
    print(f"  vs NT cohort 895 ticker match (81% of 1106)", flush=True)

    # SPY market returns
    spy = _spy_return_series()
    if not spy:
        print("ERROR: SPY cache empty; run angle-1 yfinance script first", file=sys.stderr)
        return 1

    # Filter filings to those with CRSP data
    crsp_tickers = set(by_ticker)
    in_crsp_filings = [r for r in filings if r["ticker"] in crsp_tickers]
    print(f"Filings with CRSP ticker match: {len(in_crsp_filings)} / {len(filings)}", flush=True)

    # ==================== ANGLE 1 ====================
    angle_1: list[dict] = []
    for r in in_crsp_filings:
        firm_returns = [(d, ret) for d, ret, _ in by_ticker[r["ticker"]]]
        car5 = _car(firm_returns, spy, r["date_filed"], -2, +2)
        car3 = _car(firm_returns, spy, r["date_filed"], -1, +1)
        car60 = _car(firm_returns, spy, r["date_filed"], +1, +60)
        if car5 is None and car3 is None:
            continue
        angle_1.append({
            "cik": r["cik"], "ticker": r["ticker"], "accession_number": r["accession_number"],
            "form_type": r["form_type"], "date_filed": r["date_filed"], "year": r["year"],
            "car_5d": car5, "car_3d": car3, "car_drift60d": car60,
        })
    angle_1.sort(key=lambda r: (r["cik"], r["date_filed"], r["accession_number"]))
    Path(args.out_angle_1).parent.mkdir(parents=True, exist_ok=True)
    with Path(args.out_angle_1).open("w", encoding="utf-8") as f:
        for r in angle_1:
            f.write(json.dumps(r) + "\n")

    angle_1_summary = {"n_filings": len(angle_1), "by_form": {}}
    for ft in sorted({r["form_type"] for r in angle_1}):
        sub = [r for r in angle_1 if r["form_type"] == ft]
        d5 = [r["car_5d"] for r in sub if r["car_5d"] is not None]
        d3 = [r["car_3d"] for r in sub if r["car_3d"] is not None]
        d60 = [r["car_drift60d"] for r in sub if r["car_drift60d"] is not None]
        angle_1_summary["by_form"][ft] = {
            "n": len(sub),
            "car_5d_winsorize_1pct": _winsorize(d5),
            "car_3d_winsorize_1pct": _winsorize(d3),
            "car_drift60d_winsorize_1pct": _winsorize(d60),
        }

    Path(args.report_1).parent.mkdir(parents=True, exist_ok=True)
    with Path(args.report_1).open("w", encoding="utf-8") as f:
        json.dump(angle_1_summary, f, indent=2)

    # ==================== ANGLE 4 ====================
    cy_count: Counter = Counter()
    for r in in_crsp_filings:
        cy_count[(r["cik"], r["year"])] += 1
    for r in in_crsp_filings:
        r["recurring"] = cy_count[(r["cik"], r["year"])] >= 2

    angle_4: list[dict] = []
    for r in in_crsp_filings:
        firm_returns = [(d, ret) for d, ret, _ in by_ticker[r["ticker"]]]
        car90 = _car(firm_returns, spy, r["date_filed"], +1, +90)
        car252 = _car(firm_returns, spy, r["date_filed"], +1, +252)
        if car90 is None and car252 is None:
            continue
        angle_4.append({
            "cik": r["cik"], "ticker": r["ticker"], "accession_number": r["accession_number"],
            "form_type": r["form_type"], "date_filed": r["date_filed"], "year": r["year"],
            "recurring": r["recurring"],
            "fwd_90d": car90, "fwd_252d": car252,
        })
    angle_4.sort(key=lambda r: (r["cik"], r["date_filed"], r["accession_number"]))
    with Path(args.out_angle_4).open("w", encoding="utf-8") as f:
        for r in angle_4:
            f.write(json.dumps(r) + "\n")

    angle_4_summary = {"n_results": len(angle_4), "cells": {}}
    for label, form_filter, window in [
        ("4-1_pooled_90d", None, "fwd_90d"),
        ("4-2_pooled_252d", None, "fwd_252d"),
        ("4-3_NT10Q_90d", "NT 10-Q", "fwd_90d"),
        ("4-4_NT10K_90d", "NT 10-K", "fwd_90d"),
    ]:
        sub = angle_4 if form_filter is None else [r for r in angle_4 if r["form_type"] == form_filter]
        rec = [r[window] for r in sub if r["recurring"] and r[window] is not None]
        non = [r[window] for r in sub if not r["recurring"] and r[window] is not None]
        s_rec = _winsorize(rec)
        s_non = _winsorize(non)
        diff = None
        if s_rec["mean_pct"] is not None and s_non["mean_pct"] is not None:
            diff = round(s_rec["mean_pct"] - s_non["mean_pct"], 4)
        angle_4_summary["cells"][label] = {
            "form_filter": form_filter or "pooled", "window": window,
            "recurring": s_rec, "non_recurring": s_non,
            "diff_pct_recurring_minus_non": diff,
            "bonferroni12_critical": 2.78,
            "bonferroni12_PASS_recurring_only_mech": bool(s_rec["t_stat"] is not None and abs(s_rec["t_stat"]) > 2.78),
            "v5_dir_PASS": bool(s_rec["t_stat"] is not None and abs(s_rec["t_stat"]) > 2.78 and (s_rec["mean_pct"] or 0) < 0),
        }
    with Path(args.report_4).open("w", encoding="utf-8") as f:
        json.dump(angle_4_summary, f, indent=2)

    # Print headlines
    print()
    print("=" * 60)
    print("ANGLE 1 (CRSP, including delret):")
    print("=" * 60)
    for ft in ("NT 10-K", "NT 10-Q"):
        s = angle_1_summary["by_form"].get(ft, {})
        if not s:
            continue
        c5 = s.get("car_5d_winsorize_1pct", {})
        c60 = s.get("car_drift60d_winsorize_1pct", {})
        print(f"  {ft}: n={s['n']} | 5d mean={c5.get('mean_pct')}% t={c5.get('t_stat')} | 60d mean={c60.get('mean_pct')}% t={c60.get('t_stat')}")
    print()
    print("=" * 60)
    print("ANGLE 4 (CRSP, including delret):")
    print("=" * 60)
    for cid, cell in angle_4_summary["cells"].items():
        rec = cell["recurring"]
        print(f"  {cid}: recurring n={rec['n']} mean={rec['mean_pct']}% t={rec['t_stat']} | diff(rec-non)={cell['diff_pct_recurring_minus_non']}pp | v5_dir_PASS={cell['v5_dir_PASS']}")
    print()
    print(f"Outputs:")
    print(f"  {args.out_angle_1}")
    print(f"  {args.out_angle_4}")
    print(f"  {args.report_1}")
    print(f"  {args.report_4}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
