"""Phase 1 step 1 - V5-11(c) Net Sharpe simulation on Strategy D signal.

Builds a long-short portfolio from data/angle_2_forward.jsonl:

  - For each calendar month m, group NT filings with filing_date in m.
  - LONG basket : filings labeled 'other' (equal-weight).
  - SHORT basket: filings labeled 'accounting_issue' (equal-weight).
  - Hold each entry for H trading days (H in {30, 90}).
  - Monthly portfolio return = mean(LONG CAR_H) - mean(SHORT CAR_H).
  - Annualize: 12 * monthly mean / (sqrt(12) * monthly stdev)
  - Net Sharpe = gross Sharpe with each round-trip leg charged 15bps
    flat applied to absolute monthly turnover.

V5-11(c) gate:
  PASS       Net Sharpe >= 0.30
  BORDERLINE 0.21 <= Net Sharpe < 0.30
  KILL       Net Sharpe < 0.21

Lock F clean — sort-stable on (filing_year_month, label, accession_number).

Usage:
    python scripts/compute-net-sharpe-strategy-d.py
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, pstdev

REPO_ROOT = Path(__file__).resolve().parents[1]

TC_BPS_ONE_WAY = 7.5  # 15bps round-trip = 7.5bps per leg


def _year_month(date_str: str) -> str:
    return date_str[:7]


def _ann_factor(window_days: int) -> float:
    """Compounding frequency per year if we hold H days each entry.

    Approximating 252 trading days/yr; so periods per year = 252 / H.
    For Sharpe annualization we use sqrt(periods_per_yr).
    """
    return 252.0 / window_days


def _sharpe(rets: list[float], periods_per_yr: float) -> dict:
    if not rets:
        return {"n": 0, "ann_mean_pct": None, "ann_vol_pct": None, "sharpe": None}
    n = len(rets)
    m = mean(rets)
    s = pstdev(rets) if n > 1 else 0.0
    ann_mean = m * periods_per_yr
    ann_vol = s * (periods_per_yr ** 0.5)
    sharpe = (ann_mean / ann_vol) if ann_vol > 0 else 0.0
    return {
        "n_periods": n,
        "ann_mean_pct": round(100 * ann_mean, 4),
        "ann_vol_pct": round(100 * ann_vol, 4),
        "sharpe": round(sharpe, 4),
        "period_mean_pct": round(100 * m, 4),
        "period_vol_pct": round(100 * s, 4),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--input",
        default=str(REPO_ROOT / "data" / "angle_2_forward.jsonl"),
    )
    p.add_argument(
        "--output",
        default=str(REPO_ROOT / "data" / "net_sharpe_strategy_d.jsonl"),
    )
    p.add_argument(
        "--report",
        default=str(REPO_ROOT / "reports" / "net-sharpe-summary.json"),
    )
    p.add_argument("--windows", default="30,90")
    args = p.parse_args()

    rows = [json.loads(l) for l in Path(args.input).open(encoding="utf-8")]
    rows = [r for r in rows if r.get("label") in ("accounting_issue", "other")]
    print(f"Rows in scope (AI + other labels): {len(rows)}", flush=True)

    # 1%/99% winsorize CAR globally per window — required because raw CARs
    # include survivorship-recovery firms (e.g., ABVC 60d +4,165%) that
    # otherwise drown out monthly basket means.
    def winsorize_col(col: str) -> None:
        vals = sorted(r[col] for r in rows if r.get(col) is not None)
        n = len(vals)
        if n < 100:
            return
        lo = vals[int(n * 0.01)]
        hi = vals[int(n * 0.99) - 1]
        clipped = 0
        for r in rows:
            v = r.get(col)
            if v is None:
                continue
            if v < lo:
                r[col] = lo
                clipped += 1
            elif v > hi:
                r[col] = hi
                clipped += 1
        print(f"  winsorize {col}: lo={lo*100:.2f}% hi={hi*100:.2f}% clipped={clipped}", flush=True)

    for col in ("car_fwd_30d", "car_fwd_90d"):
        winsorize_col(col)

    cells: dict = {}
    monthly_pnl_records: list[dict] = []
    windows = [int(w) for w in args.windows.split(",")]

    for H in windows:
        car_col = f"car_fwd_{H}d"
        # Group by filing-month
        by_month_ai: dict[str, list[float]] = defaultdict(list)
        by_month_ot: dict[str, list[float]] = defaultdict(list)
        for r in rows:
            v = r.get(car_col)
            if v is None:
                continue
            ym = _year_month(r["date_filed"])
            if r["label"] == "accounting_issue":
                by_month_ai[ym].append(v)
            elif r["label"] == "other":
                by_month_ot[ym].append(v)

        months = sorted(set(by_month_ai) | set(by_month_ot))
        # Drop months with thin baskets (need at least 5 in each side per month
        # for the long-short mean to be meaningful).
        usable_months = []
        for m in months:
            if len(by_month_ai.get(m, [])) >= 5 and len(by_month_ot.get(m, [])) >= 5:
                usable_months.append(m)

        long_short_rets: list[float] = []
        long_only_rets: list[float] = []
        short_only_rets: list[float] = []  # measured as negative-of-AI mean (the return to the short)
        for m in usable_months:
            ai_mean = mean(by_month_ai[m])
            ot_mean = mean(by_month_ot[m])
            ls = ot_mean - ai_mean       # long other, short AI
            long_only_rets.append(ot_mean)
            short_only_rets.append(-ai_mean)
            long_short_rets.append(ls)
            monthly_pnl_records.append({
                "year_month": m, "window_days": H,
                "n_ai": len(by_month_ai[m]), "n_other": len(by_month_ot[m]),
                "ai_mean_pct": round(100 * ai_mean, 4),
                "other_mean_pct": round(100 * ot_mean, 4),
                "long_short_pct": round(100 * ls, 4),
            })

        # Periods per year if we hold H days
        ppy = _ann_factor(H)

        # Gross sharpe
        gross = _sharpe(long_short_rets, ppy)

        # Net sharpe: subtract 15bps round-trip each entry; turnover ~100% per period.
        net_rets = [r - 2 * TC_BPS_ONE_WAY / 10000 for r in long_short_rets]
        net = _sharpe(net_rets, ppy)

        # V5-11(c) verdict
        s_net = net.get("sharpe")
        v5_11c = (
            "PASS" if s_net is not None and s_net >= 0.30
            else "BORDERLINE" if s_net is not None and s_net >= 0.21
            else "KILL" if s_net is not None
            else "INDETERMINATE"
        )

        cells[f"long_short_{H}d"] = {
            "window_days": H,
            "n_usable_months": len(usable_months),
            "periods_per_year": round(ppy, 3),
            "gross": gross,
            "net_after_15bps_roundtrip": net,
            "long_only_basket": _sharpe(long_only_rets, ppy),
            "short_only_basket": _sharpe(short_only_rets, ppy),
            "v5_11c_verdict": v5_11c,
        }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    monthly_pnl_records.sort(key=lambda r: (r["window_days"], r["year_month"]))
    with out_path.open("w", encoding="utf-8") as f:
        for r in monthly_pnl_records:
            f.write(json.dumps(r) + "\n")

    out = {
        "n_rows_in_scope": len(rows),
        "transaction_cost_bps_roundtrip": 15,
        "cells": cells,
        "v5_11c_threshold": ">= 0.30 PASS; 0.21-0.29 BORDERLINE; < 0.21 KILL",
    }

    rep_path = Path(args.report)
    rep_path.parent.mkdir(parents=True, exist_ok=True)
    with rep_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print()
    for k, v in cells.items():
        print(f"--- {k} (H={v['window_days']}d, n_months={v['n_usable_months']}, ppy={v['periods_per_year']}) ---")
        g = v["gross"]
        n = v["net_after_15bps_roundtrip"]
        print(f"  gross: ann_mean={g['ann_mean_pct']}%  ann_vol={g['ann_vol_pct']}%  sharpe={g['sharpe']}")
        print(f"  net  : ann_mean={n['ann_mean_pct']}%  ann_vol={n['ann_vol_pct']}%  sharpe={n['sharpe']}")
        print(f"  V5-11(c) verdict: {v['v5_11c_verdict']}")
    print()
    print(f"Output : {out_path}")
    print(f"Report : {rep_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
