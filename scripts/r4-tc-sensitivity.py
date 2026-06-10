"""R4 — Transaction cost sensitivity of V5-11(c) Net Sharpe.

Re-runs the long-short basket sim at multiple round-trip TC levels:
  0 / 5 / 10 / 15 / 20 / 30 / 50 / 75 / 100 bps round-trip

Reports gross & net Sharpe @ 30d and 90d windows, plus break-even bps
(the TC at which net Sharpe falls below 0.30 PASS / 0.21 BORDERLINE).

Mirrors compute-net-sharpe-strategy-d.py logic but parametrizes TC.
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev

REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT = REPO_ROOT / "data" / "angle_2_forward.jsonl"
OUTPUT = REPO_ROOT / "reports" / "r4-tc-sensitivity.json"

TC_LEVELS_BPS = [0, 5, 10, 15, 20, 30, 50, 75, 100, 150, 200]


def sim_window(rows: list[dict], window_days: int, tc_bps_rt: float) -> dict:
    car_col = f"car_fwd_{window_days}d"
    vals = sorted(r[car_col] for r in rows if r.get(car_col) is not None)
    if len(vals) < 100:
        return {"verdict": "INSUFFICIENT"}
    lo = vals[int(len(vals) * 0.01)]
    hi = vals[int(len(vals) * 0.99) - 1]

    by_month_ai, by_month_ot = defaultdict(list), defaultdict(list)
    for r in rows:
        v = r.get(car_col)
        if v is None:
            continue
        v = max(lo, min(hi, v))
        ym = r["date_filed"][:7]
        if r["label"] == "accounting_issue":
            by_month_ai[ym].append(v)
        elif r["label"] == "other":
            by_month_ot[ym].append(v)
    months = sorted(set(by_month_ai) | set(by_month_ot))
    ls_rets: list[float] = []
    for m in months:
        if len(by_month_ai.get(m, [])) >= 5 and len(by_month_ot.get(m, [])) >= 5:
            ls_rets.append(mean(by_month_ot[m]) - mean(by_month_ai[m]))
    if len(ls_rets) < 4:
        return {"verdict": "INSUFFICIENT_MONTHS"}
    ppy = 252 / window_days
    m_mu = mean(ls_rets)
    m_sd = pstdev(ls_rets) if len(ls_rets) > 1 else 0
    ann_vol = m_sd * math.sqrt(ppy)
    # Net = gross - TC every entry (period = window). Long+Short both turn over -> already
    # accounted by treating tc as round-trip on the spread.
    net_rets = [r - tc_bps_rt / 10000 for r in ls_rets]
    net_mu = mean(net_rets)
    net_ann_mean = net_mu * ppy
    net_sharpe = (net_ann_mean / ann_vol) if ann_vol > 0 else 0
    verdict = (
        "PASS" if net_sharpe >= 0.30
        else "BORDERLINE" if net_sharpe >= 0.21
        else "KILL"
    )
    return {
        "tc_bps_rt": tc_bps_rt,
        "n_months": len(ls_rets),
        "net_ann_mean_pct": round(100 * net_ann_mean, 4),
        "ann_vol_pct": round(100 * ann_vol, 4),
        "net_sharpe": round(net_sharpe, 4),
        "v5_11c_verdict": verdict,
    }


def break_even_bps(rows: list[dict], window_days: int, target_sharpe: float) -> float | None:
    """Binary search for TC at which net_sharpe falls to target."""
    lo_bps, hi_bps = 0.0, 1000.0
    # check feasibility at lo
    s_lo = sim_window(rows, window_days, lo_bps).get("net_sharpe")
    if s_lo is None or s_lo < target_sharpe:
        return None
    # bisect
    for _ in range(50):
        mid = (lo_bps + hi_bps) / 2
        s = sim_window(rows, window_days, mid).get("net_sharpe")
        if s is None:
            return None
        if s >= target_sharpe:
            lo_bps = mid
        else:
            hi_bps = mid
        if hi_bps - lo_bps < 0.1:
            break
    return round((lo_bps + hi_bps) / 2, 2)


def main() -> int:
    rows = [json.loads(l) for l in INPUT.open(encoding="utf-8")]
    rows = [r for r in rows if r.get("label") in ("accounting_issue", "other")]
    print(f"In-scope rows: {len(rows)}", flush=True)

    out: dict = {"cells": {}, "break_even_bps": {}}

    for H in (30, 90):
        cells = {}
        for tc in TC_LEVELS_BPS:
            cells[f"tc_{tc}bps"] = sim_window(rows, H, tc)
        out["cells"][f"window_{H}d"] = cells

        out["break_even_bps"][f"window_{H}d"] = {
            "pass_floor_0.30": break_even_bps(rows, H, 0.30),
            "borderline_floor_0.21": break_even_bps(rows, H, 0.21),
            "positive_sharpe_0.00": break_even_bps(rows, H, 0.0),
        }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(f"\n{'window':<10} {'TC (bps RT)':>12} {'Sharpe':>8} {'verdict':>10}")
    for H_key, cells in out["cells"].items():
        for k, v in cells.items():
            print(f"{H_key:<10} {v.get('tc_bps_rt'):>12} {v.get('net_sharpe'):>8} {v.get('v5_11c_verdict'):>10}")
        print()
    print("Break-even bps (TC at which net Sharpe drops to floor):")
    for H_key, b in out["break_even_bps"].items():
        print(f"  {H_key}: PASS@0.30 = {b['pass_floor_0.30']}  BORDER@0.21 = {b['borderline_floor_0.21']}  Sharpe>0 = {b['positive_sharpe_0.00']}")
    print(f"\nReport: {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
