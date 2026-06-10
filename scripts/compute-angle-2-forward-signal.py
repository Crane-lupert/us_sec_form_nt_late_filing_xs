"""Phase 0 step 6c - Angle 2 forward signal (NT body LLM -> restatement).

Joins NT classifications (Strategy D label per filing) to restatement
events (from same CIK after NT filing), then tests:

  (A) Predictive rate test: P(restatement within window | NT body says
      accounting_issue) > P(restatement within window | NT body says
      other), measured via two-proportion z-test. Windows = {4-14d,
      30d, 90d}.
  (B) Forward CAR conditional on label: compute fwd-30d / fwd-90d CAR
      stratified by Strategy D label and t-test the
      accounting_issue minus other difference, using cached yfinance
      prices.

Bonferroni-12 cell allocation (4 of 12 for Angle 2):
    2-1 rate-diff × 30d window
    2-2 rate-diff × 90d window
    2-3 CAR-diff × 30d window (accounting_issue minus other)
    2-4 CAR-diff × 90d window

Lock F sort-stable on (cik, date_filed, accession_number).

Usage:
    python scripts/compute-angle-2-forward-signal.py
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import mean, pstdev

REPO_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = REPO_ROOT / "data" / "yfinance_cache"


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _winsorize_t(vals: list[float], lo_pct: float = 1.0, hi_pct: float = 1.0) -> dict:
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
    return {"n": len(w), "mean_pct": round(100 * m, 4), "stdev_pct": round(100 * s, 4),
            "t_stat": round(t, 3)}


def _two_prop_z(k1: int, n1: int, k2: int, n2: int) -> dict:
    """Two-proportion z-test for p1=k1/n1 vs p2=k2/n2."""
    if n1 == 0 or n2 == 0:
        return {"p1": None, "p2": None, "diff": None, "z": None, "n1": n1, "n2": n2}
    p1 = k1 / n1
    p2 = k2 / n2
    p_pool = (k1 + k2) / (n1 + n2)
    import math
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    z = (p1 - p2) / se if se > 0 else 0.0
    return {"p1_pct": round(100 * p1, 4), "p2_pct": round(100 * p2, 4),
            "diff_pct": round(100 * (p1 - p2), 4),
            "z_stat": round(z, 3), "n1": n1, "n2": n2}


def _read_price_cache(ticker: str) -> list[dict]:
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


def _forward_car(firm_ret: list[tuple[str, float]], mkt: dict[str, float],
                 filing_date: str, end_days: int) -> float | None:
    t0_idx = None
    for i, (d, _) in enumerate(firm_ret):
        if d >= filing_date:
            t0_idx = i
            break
    if t0_idx is None:
        return None
    end_idx = t0_idx + end_days
    if end_idx >= len(firm_ret):
        return None
    car = 0.0
    n_days = 0
    for i in range(t0_idx + 1, end_idx + 1):
        d, fr = firm_ret[i]
        mr = mkt.get(d)
        if mr is None:
            continue
        car += fr - mr
        n_days += 1
    return car if n_days > 0 else None


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--classifications", default=str(REPO_ROOT / "data" / "nt_classifications.jsonl"))
    p.add_argument("--restatements", default=str(REPO_ROOT / "data" / "restatement_events.jsonl"))
    p.add_argument("--output", default=str(REPO_ROOT / "data" / "angle_2_forward.jsonl"))
    p.add_argument("--report", default=str(REPO_ROOT / "reports" / "angle-2-summary.json"))
    p.add_argument("--windows", default="14,30,90,180")
    args = p.parse_args()

    cls_path = Path(args.classifications)
    rst_path = Path(args.restatements)
    if not cls_path.exists():
        print(f"ERROR: classifications {cls_path} not found", file=sys.stderr)
        return 1
    if not rst_path.exists():
        print(f"ERROR: restatements {rst_path} not found", file=sys.stderr)
        return 1

    cls_rows = [json.loads(l) for l in cls_path.open(encoding="utf-8") if l.strip()]
    cls_rows = [r for r in cls_rows if r.get("label") in ("accounting_issue", "unresolved_sec_comment", "other")]
    print(f"Classified rows: {len(cls_rows)}", flush=True)

    rst_rows = [json.loads(l) for l in rst_path.open(encoding="utf-8") if l.strip()]
    print(f"Restatement-event rows: {len(rst_rows)}", flush=True)

    # Index restatements by CIK
    rst_by_cik: dict[str, list[date]] = defaultdict(list)
    for r in rst_rows:
        if not r.get("filing_date"):
            continue
        try:
            rst_by_cik[r["cik"].lstrip("0") or "0"].append(_parse_date(r["filing_date"]))
        except ValueError:
            continue
    for k in rst_by_cik:
        rst_by_cik[k].sort()

    windows_days = [int(w) for w in args.windows.split(",")]

    # SPY market returns
    spy = _read_price_cache("SPY")
    spy_ret = dict(_return_series(spy)) if spy else {}

    joined: list[dict] = []
    by_ticker_cls: dict[str, list[dict]] = defaultdict(list)
    for r in cls_rows:
        by_ticker_cls[r["ticker"]].append(r)
    for ticker, tfilings in by_ticker_cls.items():
        prices = _read_price_cache(ticker)
        firm_ret = _return_series(prices) if prices else []
        for r in tfilings:
            nt_d = _parse_date(r["date_filed"])
            cik_norm = r["cik"].lstrip("0") or "0"
            rst_dates = rst_by_cik.get(cik_norm, [])
            # Find first restatement event STRICTLY AFTER NT filing
            future = [d for d in rst_dates if d > nt_d]
            first_rst = future[0] if future else None
            row_out = {
                "accession_number": r["accession_number"],
                "cik": r["cik"],
                "ticker": ticker,
                "form_type": r["form_type"],
                "date_filed": r["date_filed"],
                "label": r["label"],
                "first_restatement_after": first_rst.isoformat() if first_rst else None,
                "days_to_first_restatement": (first_rst - nt_d).days if first_rst else None,
            }
            for w in windows_days:
                row_out[f"restated_within_{w}d"] = bool(first_rst and (first_rst - nt_d).days <= w)
            if firm_ret and spy_ret:
                for w in (30, 90):
                    row_out[f"car_fwd_{w}d"] = _forward_car(firm_ret, spy_ret, r["date_filed"], w)
            else:
                for w in (30, 90):
                    row_out[f"car_fwd_{w}d"] = None
            joined.append(row_out)

    joined.sort(key=lambda r: (r["cik"], r["date_filed"], r["accession_number"]))

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for r in joined:
            f.write(json.dumps(r) + "\n")

    # Compute Bonferroni-12 cells for Angle 2
    out: dict = {"n_classified": len(cls_rows), "n_joined": len(joined),
                 "windows_days": windows_days}

    # Rate-diff cells (accounting_issue vs other)
    rate_cells: dict[str, dict] = {}
    by_label = defaultdict(list)
    for r in joined:
        by_label[r["label"]].append(r)
    ai = by_label["accounting_issue"]
    ot = by_label["other"]
    for w in windows_days:
        n1 = len(ai); k1 = sum(1 for r in ai if r[f"restated_within_{w}d"])
        n2 = len(ot); k2 = sum(1 for r in ot if r[f"restated_within_{w}d"])
        z = _two_prop_z(k1, n1, k2, n2)
        rate_cells[f"rate_{w}d"] = {
            **z,
            "bonferroni12_critical_z": 2.78,
            "bonferroni12_PASS": bool(z["z_stat"] is not None and abs(z["z_stat"]) > 2.78),
            "v5_dir_PASS": bool(z["diff_pct"] is not None and z["diff_pct"] > 0
                                and abs(z["z_stat"] or 0) > 2.78),
        }
    out["rate_diff_cells"] = rate_cells

    # CAR-diff cells
    car_cells: dict[str, dict] = {}
    for w in (30, 90):
        ai_v = [r[f"car_fwd_{w}d"] for r in ai if r[f"car_fwd_{w}d"] is not None]
        ot_v = [r[f"car_fwd_{w}d"] for r in ot if r[f"car_fwd_{w}d"] is not None]
        s_ai = _winsorize_t(ai_v)
        s_ot = _winsorize_t(ot_v)
        diff = None
        if s_ai["mean_pct"] is not None and s_ot["mean_pct"] is not None:
            diff = round(s_ai["mean_pct"] - s_ot["mean_pct"], 4)
        car_cells[f"car_diff_{w}d"] = {
            "accounting_issue": s_ai,
            "other": s_ot,
            "diff_pct_ai_minus_other": diff,
            "bonferroni12_critical": 2.78,
            "bonferroni12_PASS_ai": bool(s_ai["t_stat"] is not None and abs(s_ai["t_stat"]) > 2.78),
        }
    out["car_diff_cells"] = car_cells

    # Label distribution snapshot
    label_dist = {lab: len(by_label[lab]) for lab in ("accounting_issue", "unresolved_sec_comment", "other")}
    out["label_distribution"] = label_dist

    rep_path = Path(args.report)
    rep_path.parent.mkdir(parents=True, exist_ok=True)
    with rep_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print()
    print("Label distribution:", label_dist)
    print("\nRate-diff cells:")
    for k, v in rate_cells.items():
        print(f"  {k}: AI={v['p1_pct']}% (n={v['n1']}), OTHER={v['p2_pct']}% (n={v['n2']}), diff={v['diff_pct']}pp z={v['z_stat']} pass_mech={v['bonferroni12_PASS']} dir_pass={v['v5_dir_PASS']}")
    print("\nCAR-diff cells:")
    for k, v in car_cells.items():
        print(f"  {k}: AI mean={v['accounting_issue']['mean_pct']}% n={v['accounting_issue']['n']} t={v['accounting_issue']['t_stat']} | other={v['other']['mean_pct']}% n={v['other']['n']} | diff={v['diff_pct_ai_minus_other']}pp")
    print()
    print(f"Output: {out_path}")
    print(f"Report: {rep_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
