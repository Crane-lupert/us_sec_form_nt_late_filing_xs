"""Phase 0 step 7 - Angle 4 recurring NT filer cross-section.

For each (CIK, calendar_year) cell in the NYSE+Nasdaq-matched cohort,
counts NT filings. Recurring = >=2 NT filings in a single calendar year.

For each filing (recurring OR not), computes market-adjusted forward
CAR over windows {30d, 90d, 252d (~12mo)} using cached yfinance prices
from step 5.

Compares the recurring-filer firm-year subset's forward CAR mean to
the non-recurring subset (and to zero). Output: per-filing JSONL +
Bonferroni-12 cell-summary JSON.

Lock F compliance: sort-stable on (cik, date_filed, accession_number).

Usage:
    python scripts/compute-angle-4-recurring-xs.py
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, pstdev

REPO_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = REPO_ROOT / "data" / "yfinance_cache"

FORWARD_WINDOWS = {
    "fwd_30d": (1, 30),
    "fwd_90d": (1, 90),
    "fwd_252d": (1, 252),
}


def _load_filings(path: Path, exch: tuple[str, ...]) -> list[dict]:
    rows = [json.loads(l) for l in path.open(encoding="utf-8")]
    return [r for r in rows if r.get("ticker") and r.get("exchange") in exch]


def _read_cache(ticker: str) -> list[dict]:
    safe = ticker.replace("/", "_")
    p = CACHE_DIR / f"{safe}.jsonl"
    if not p.exists() or p.stat().st_size == 0:
        return []
    return [json.loads(l) for l in p.open(encoding="utf-8")]


def _return_series(prices: list[dict]) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    prev: float | None = None
    for r in prices:
        c = r["close"]
        if prev is not None and prev > 0:
            out.append((r["date"], c / prev - 1.0))
        prev = c
    return out


def _winsorize_stats(vals: list[float], lo_pct: float = 1.0, hi_pct: float = 1.0) -> dict:
    sv = sorted(v for v in vals if v is not None)
    n = len(sv)
    if n == 0:
        return {"n": 0, "mean_pct": None, "t_stat": None}
    a = int(n * lo_pct / 100)
    b = max(int(n * (100 - hi_pct) / 100) - 1, a)
    lo_val = sv[a]
    hi_val = sv[b]
    w = [min(max(v, lo_val), hi_val) for v in sv]
    m = mean(w)
    s = pstdev(w) if len(w) > 1 else 0.0
    t = m / (s / (len(w) ** 0.5)) if s > 0 else 0.0
    return {
        "n": len(w),
        "mean_pct": round(100 * m, 4),
        "stdev_pct": round(100 * s, 4),
        "t_stat": round(t, 3),
    }


def _compute_forward_car(
    firm_ret: list[tuple[str, float]],
    market_ret: dict[str, float],
    filing_date: str,
    start: int,
    end: int,
) -> float | None:
    # Find T=0 = first trading day on or after filing_date
    t0_idx = None
    for i, (d, _) in enumerate(firm_ret):
        if d >= filing_date:
            t0_idx = i
            break
    if t0_idx is None:
        return None
    start_idx = t0_idx + start
    end_idx = t0_idx + end
    if end_idx >= len(firm_ret) or start_idx < 0:
        return None
    car = 0.0
    n_days = 0
    for i in range(start_idx, end_idx + 1):
        d, fr = firm_ret[i]
        mr = market_ret.get(d)
        if mr is None:
            continue
        car += fr - mr
        n_days += 1
    if n_days == 0:
        return None
    return car


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", default=str(REPO_ROOT / "data" / "form_nt_matched.jsonl"))
    p.add_argument("--output", default=str(REPO_ROOT / "data" / "angle_4_recurring.jsonl"))
    p.add_argument("--report", default=str(REPO_ROOT / "reports" / "angle-4-summary.json"))
    p.add_argument("--exchanges", default="NYSE,Nasdaq")
    args = p.parse_args()

    exch = tuple(args.exchanges.split(","))
    rows = _load_filings(Path(args.input), exch)
    print(f"NT filings in scope: {len(rows)}", flush=True)

    # Per (CIK, year) count
    cy_count: Counter = Counter()
    for r in rows:
        cy_count[(r["cik"], r["year"])] += 1

    # Tag each filing with its (cik, year) count and recurring flag
    for r in rows:
        c = cy_count[(r["cik"], r["year"])]
        r["nt_in_year"] = c
        r["recurring"] = c >= 2

    n_recurring_filings = sum(1 for r in rows if r["recurring"])
    n_distinct_recurring_firm_years = sum(1 for k, v in cy_count.items() if v >= 2)
    print(f"Recurring (>=2 NT in same year) filings: {n_recurring_filings}", flush=True)
    print(f"Distinct recurring (CIK, year) cells   : {n_distinct_recurring_firm_years}", flush=True)

    # Build SPY market returns from cache
    spy = _read_cache("SPY")
    if not spy:
        print("ERROR: SPY cache empty - run compute-angle-1-event-car.py first", file=sys.stderr)
        return 1
    spy_ret = dict(_return_series(spy))

    # Group filings by ticker, compute forward CARs
    by_ticker: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_ticker[r["ticker"]].append(r)

    results: list[dict] = []
    n_no_cache = 0
    for tk, tfilings in by_ticker.items():
        prices = _read_cache(tk)
        if not prices:
            n_no_cache += len(tfilings)
            continue
        firm_ret = _return_series(prices)
        for r in tfilings:
            row_out = {
                "cik": r["cik"], "ticker": tk,
                "accession_number": r["accession_number"],
                "form_type": r["form_type"], "date_filed": r["date_filed"],
                "year": r["year"], "nt_in_year": r["nt_in_year"],
                "recurring": r["recurring"],
            }
            for col, (s, e) in FORWARD_WINDOWS.items():
                row_out[col] = _compute_forward_car(firm_ret, spy_ret, r["date_filed"], s, e)
            results.append(row_out)

    results.sort(key=lambda r: (r["cik"], r["date_filed"], r["accession_number"]))
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    # Bonferroni-12 cell allocation for Angle 4 (4 of 12 cells)
    # Cell 4-1: pooled all forms recurring vs non-recurring × 90d
    # Cell 4-2: pooled all forms recurring vs non-recurring × 252d (12mo)
    # Cell 4-3: NT 10-Q only recurring vs non-recurring × 90d
    # Cell 4-4: NT 10-K only recurring vs non-recurring × 90d
    # Plus descriptive 30d (not in Bonferroni-12 cells)

    def stats_for(rows_in: list[dict], col: str) -> dict:
        vals = [r[col] for r in rows_in if r[col] is not None]
        return _winsorize_stats(vals)

    out: dict = {"n_filings_in_universe": len(rows), "n_results_with_cache": len(results),
                 "n_no_cache": n_no_cache,
                 "recurring_definition": ">= 2 NT filings (any form) per CIK per calendar year"}

    cells: dict[str, dict] = {}
    for label, form_filter, window in [
        ("4-1_pooled_90d", None, "fwd_90d"),
        ("4-2_pooled_252d", None, "fwd_252d"),
        ("4-3_NT10Q_90d", "NT 10-Q", "fwd_90d"),
        ("4-4_NT10K_90d", "NT 10-K", "fwd_90d"),
    ]:
        if form_filter:
            sub = [r for r in results if r["form_type"] == form_filter]
        else:
            sub = results
        rec = [r for r in sub if r["recurring"]]
        non = [r for r in sub if not r["recurring"]]
        s_rec = stats_for(rec, window)
        s_non = stats_for(non, window)
        # Difference t-test (Welch on winsorized samples already computed)
        # Approximate diff effect by recurring mean - non-recurring mean
        diff_pct = None
        if s_rec["mean_pct"] is not None and s_non["mean_pct"] is not None:
            diff_pct = round(s_rec["mean_pct"] - s_non["mean_pct"], 4)
        cells[label] = {
            "form_filter": form_filter or "pooled",
            "window": window,
            "recurring": s_rec,
            "non_recurring": s_non,
            "diff_pct_recurring_minus_non": diff_pct,
            "bonferroni12_critical": 2.78,
            "bonferroni12_PASS_recurring_only": bool(s_rec["t_stat"] is not None and abs(s_rec["t_stat"]) > 2.78),
        }
    out["cells"] = cells

    # Descriptive 30d
    desc_rec = stats_for([r for r in results if r["recurring"]], "fwd_30d")
    desc_non = stats_for([r for r in results if not r["recurring"]], "fwd_30d")
    out["descriptive_30d"] = {"recurring": desc_rec, "non_recurring": desc_non}

    rep_path = Path(args.report)
    rep_path.parent.mkdir(parents=True, exist_ok=True)
    with rep_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print()
    print(json.dumps(cells, indent=2))
    print()
    print(f"Output: {out_path}")
    print(f"Report: {rep_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
