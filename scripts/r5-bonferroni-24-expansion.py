"""R5 — Bonferroni-24 expansion: extend Phase 0+1 12-cell ledger to 24 cells.

Defines 12 additional cells in the same 3-axis structure
(angle x cohort/form x forward window):

  Angle 1 (event-CAR via CRSP delret):
    1-5  NT 10-K  30d drift
    1-6  NT 10-Q  30d drift
    1-7  NT 10-K  90d drift
    1-8  NT 10-Q  90d drift

  Angle 2 (Strategy D LLM forward):
    2-5  rate-diff 14d (already computed)
    2-6  rate-diff 180d (already computed)
    2-7  NT 10-K cohort rate-diff 90d
    2-8  NT 10-Q cohort rate-diff 90d

  Angle 4 (recurring NT-filer XS):
    4-5  Recurring pooled 30d
    4-6  Recurring pooled 180d
    4-7  Recurring NT 10-K 252d
    4-8  Recurring NT 10-Q 252d

This extends the launch-SPEC Bonferroni-12 ledger to a full 24-cell grid.
V5-11(b) Bonferroni-24 threshold (proportional): >= 6/24 PASS = PASS;
4-5/24 BORDERLINE; <= 3/24 KILL.

Cell IDs 1-1..1-4, 2-1..2-4, 4-1..4-4 read from existing JSON files.
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from statistics import mean, pstdev

REPO_ROOT = Path(__file__).resolve().parents[1]
LEDGER_12_PATH = REPO_ROOT / "reports" / "bonferroni-12-ledger.json"
LEDGER_24_OUT = REPO_ROOT / "reports" / "r5-bonferroni-24-ledger.json"


def winsorize(vals: list[float], lo_pct: float = 1.0, hi_pct: float = 1.0) -> dict:
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


def two_prop_z(p1: float, n1: int, p2: float, n2: int) -> float:
    p_pool = (p1 * n1 + p2 * n2) / (n1 + n2) if (n1 + n2) > 0 else 0
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2)) if 0 < p_pool < 1 else 0
    return (p1 - p2) / se if se > 0 else 0


def car(firm_rets: list[tuple[str, float]], market: dict[str, float],
        filing_date: str, start: int, end: int) -> float | None:
    t0 = next((i for i, (d, _) in enumerate(firm_rets) if d >= filing_date), None)
    if t0 is None:
        return None
    s, e = t0 + start, t0 + end
    if s < 0 or e >= len(firm_rets):
        return None
    tot = 0.0
    n = 0
    for i in range(s, e + 1):
        d, fr = firm_rets[i]
        mr = market.get(d)
        if mr is None:
            continue
        tot += (fr - mr)
        n += 1
    return tot if n > 0 else None


def main() -> int:
    # Load existing 12-cell ledger
    ledger_12 = json.loads(LEDGER_12_PATH.read_text(encoding="utf-8"))
    cells_24 = list(ledger_12["cells"])  # 12 cells

    # ============== Angle 1 extensions (1-5..1-8) via CRSP ==============
    print("Loading CRSP returns for Angle 1 ext...", flush=True)
    import duckdb
    db = duckdb.connect(":memory:")
    crsp_path = REPO_ROOT / "data" / "crsp_returns.parquet"
    df = db.execute(
        f"SELECT ticker, dlycaldt, dlyret FROM read_parquet('{crsp_path}') "
        f"WHERE dlyret IS NOT NULL ORDER BY ticker, dlycaldt"
    ).fetchdf()
    by_ticker: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for tk, dt, ret in zip(df["ticker"], df["dlycaldt"], df["dlyret"]):
        d_str = dt.strftime("%Y-%m-%d") if hasattr(dt, "strftime") else str(dt)[:10]
        by_ticker[tk].append((d_str, float(ret)))
    for tk in by_ticker:
        by_ticker[tk].sort(key=lambda r: r[0])
    print(f"  tickers: {len(by_ticker)}", flush=True)

    # SPY market returns
    spy_p = REPO_ROOT / "data" / "yfinance_cache" / "SPY.jsonl"
    spy_rows = [json.loads(l) for l in spy_p.open(encoding="utf-8")]
    spy_rows.sort(key=lambda r: r["date"])
    market: dict[str, float] = {}
    prev = None
    for r in spy_rows:
        c = r["close"]
        if prev is not None and prev > 0:
            market[r["date"]] = c / prev - 1.0
        prev = c

    matched = [json.loads(l) for l in (REPO_ROOT / "data" / "form_nt_matched.jsonl").open(encoding="utf-8")]
    matched = [r for r in matched if r.get("exchange") in ("NYSE", "Nasdaq") and r.get("ticker") in by_ticker]

    print(f"  filings with CRSP: {len(matched)}", flush=True)

    # Compute 30d and 90d drift for NT 10-K + NT 10-Q
    drift30: dict[str, list[float]] = defaultdict(list)
    drift90: dict[str, list[float]] = defaultdict(list)
    for r in matched:
        ft = r["form_type"]
        if ft not in ("NT 10-K", "NT 10-Q"):
            continue
        firm = by_ticker[r["ticker"]]
        c30 = car(firm, market, r["date_filed"], +1, +30)
        c90 = car(firm, market, r["date_filed"], +1, +90)
        if c30 is not None:
            drift30[ft].append(c30)
        if c90 is not None:
            drift90[ft].append(c90)

    # Add cells 1-5..1-8
    angle1_ext = []
    for cell_id, ft, win, vals in [
        ("1-5", "NT 10-K", "30d drift", drift30["NT 10-K"]),
        ("1-6", "NT 10-Q", "30d drift", drift30["NT 10-Q"]),
        ("1-7", "NT 10-K", "90d drift", drift90["NT 10-K"]),
        ("1-8", "NT 10-Q", "90d drift", drift90["NT 10-Q"]),
    ]:
        w = winsorize(vals)
        t = w["t_stat"] or 0
        m = w["mean_pct"] or 0
        cell = {
            "id": cell_id,
            "angle": 1,
            "label": f"{ft} event-CAR {win}",
            "n": w["n"],
            "mean_pct": w["mean_pct"],
            "t_stat": t,
            "direction_v5_thesis": "negative",
            "bonferroni12_PASS": abs(t) > 2.78,
            "v5_direction_PASS": abs(t) > 2.78 and m < 0,
        }
        cells_24.append(cell)
        angle1_ext.append(cell)
        print(f"  {cell_id} {ft} {win}: n={w['n']} mean={m}% t={t}", flush=True)

    # ============== Angle 2 extensions (2-5..2-8) ==============
    print("\nAngle 2 ext...", flush=True)
    rows2 = [json.loads(l) for l in (REPO_ROOT / "data" / "angle_2_forward.jsonl").open(encoding="utf-8")]
    rows2 = [r for r in rows2 if r["label"] in ("accounting_issue", "other")]

    # 2-5 rate-diff 14d (re-read from existing summary if needed)
    ai = [r for r in rows2 if r["label"] == "accounting_issue"]
    ot = [r for r in rows2 if r["label"] == "other"]
    for cell_id, label, win_key in [
        ("2-5", "Strategy D rate-diff 14d", "restated_within_14d"),
        ("2-6", "Strategy D rate-diff 180d", "restated_within_180d"),
    ]:
        n1, n2 = len(ai), len(ot)
        p1 = sum(1 for r in ai if r.get(win_key)) / n1
        p2 = sum(1 for r in ot if r.get(win_key)) / n2
        z = two_prop_z(p1, n1, p2, n2)
        cell = {
            "id": cell_id, "angle": 2, "label": label,
            "p_ai_pct": round(100 * p1, 4), "p_other_pct": round(100 * p2, 4),
            "diff_pp": round(100 * (p1 - p2), 4),
            "z_stat": round(z, 4),
            "bonferroni12_PASS": abs(z) > 2.78,
            "v5_direction_PASS": abs(z) > 2.78 and (p1 - p2) > 0,
        }
        cells_24.append(cell)
        print(f"  {cell_id}: AI={cell['p_ai_pct']}% OT={cell['p_other_pct']}% diff={cell['diff_pp']}pp z={z:.4f}", flush=True)

    # 2-7 rate-diff 90d for NT 10-K cohort only
    # 2-8 rate-diff 90d for NT 10-Q cohort only
    for cell_id, ft, label in [
        ("2-7", "NT 10-K", "Strategy D rate-diff 90d cohort=NT 10-K"),
        ("2-8", "NT 10-Q", "Strategy D rate-diff 90d cohort=NT 10-Q"),
    ]:
        ai_s = [r for r in ai if r["form_type"] == ft]
        ot_s = [r for r in ot if r["form_type"] == ft]
        if not ai_s or not ot_s:
            continue
        n1, n2 = len(ai_s), len(ot_s)
        p1 = sum(1 for r in ai_s if r.get("restated_within_90d")) / n1
        p2 = sum(1 for r in ot_s if r.get("restated_within_90d")) / n2
        z = two_prop_z(p1, n1, p2, n2)
        cell = {
            "id": cell_id, "angle": 2, "label": label,
            "p_ai_pct": round(100 * p1, 4), "p_other_pct": round(100 * p2, 4),
            "diff_pp": round(100 * (p1 - p2), 4),
            "n_ai": n1, "n_other": n2,
            "z_stat": round(z, 4),
            "bonferroni12_PASS": abs(z) > 2.78,
            "v5_direction_PASS": abs(z) > 2.78 and (p1 - p2) > 0,
        }
        cells_24.append(cell)
        print(f"  {cell_id} ({ft}): AI={cell['p_ai_pct']}% OT={cell['p_other_pct']}% diff={cell['diff_pp']}pp z={z:.4f}", flush=True)

    # ============== Angle 4 extensions (4-5..4-8) ==============
    print("\nAngle 4 ext...", flush=True)
    # Need 30d and 180d drift (compute now), and recurring x form-type x 252d
    drift30_pooled: list[tuple[bool, float]] = []
    drift180_pooled: list[tuple[bool, float]] = []
    drift252_byft: dict[str, list[tuple[bool, float]]] = defaultdict(list)
    cy_count: Counter = Counter()
    for r in matched:
        cy_count[(r["cik"], r["year"])] += 1
    for r in matched:
        ft = r["form_type"]
        if ft not in ("NT 10-K", "NT 10-Q"):
            continue
        recurring = cy_count[(r["cik"], r["year"])] >= 2
        firm = by_ticker[r["ticker"]]
        c30 = car(firm, market, r["date_filed"], +1, +30)
        c180 = car(firm, market, r["date_filed"], +1, +180)
        c252 = car(firm, market, r["date_filed"], +1, +252)
        if c30 is not None:
            drift30_pooled.append((recurring, c30))
        if c180 is not None:
            drift180_pooled.append((recurring, c180))
        if c252 is not None:
            drift252_byft[ft].append((recurring, c252))

    def _ang4_cell(cell_id: str, label: str, data: list[tuple[bool, float]]) -> dict:
        rec = [v for r, v in data if r]
        non = [v for r, v in data if not r]
        w_rec = winsorize(rec)
        w_non = winsorize(non)
        t_rec = w_rec["t_stat"] or 0
        m_rec = w_rec["mean_pct"] or 0
        return {
            "id": cell_id, "angle": 4, "label": label,
            "recurring_n": w_rec["n"],
            "recurring_mean_pct": w_rec["mean_pct"],
            "recurring_t_stat": t_rec,
            "non_recurring_n": w_non["n"],
            "non_recurring_mean_pct": w_non["mean_pct"],
            "direction_v5_thesis": "negative (recurring underperform)",
            "bonferroni12_PASS": abs(t_rec) > 2.78,
            "v5_direction_PASS": abs(t_rec) > 2.78 and m_rec < 0,
        }

    cell = _ang4_cell("4-5", "Recurring pooled 30d", drift30_pooled)
    cells_24.append(cell)
    print(f"  4-5: rec n={cell['recurring_n']} mean={cell['recurring_mean_pct']}% t={cell['recurring_t_stat']}", flush=True)

    cell = _ang4_cell("4-6", "Recurring pooled 180d", drift180_pooled)
    cells_24.append(cell)
    print(f"  4-6: rec n={cell['recurring_n']} mean={cell['recurring_mean_pct']}% t={cell['recurring_t_stat']}", flush=True)

    cell = _ang4_cell("4-7", "Recurring NT 10-K 252d", drift252_byft["NT 10-K"])
    cells_24.append(cell)
    print(f"  4-7: rec n={cell['recurring_n']} mean={cell['recurring_mean_pct']}% t={cell['recurring_t_stat']}", flush=True)

    cell = _ang4_cell("4-8", "Recurring NT 10-Q 252d", drift252_byft["NT 10-Q"])
    cells_24.append(cell)
    print(f"  4-8: rec n={cell['recurring_n']} mean={cell['recurring_mean_pct']}% t={cell['recurring_t_stat']}", flush=True)

    # ============== Final summary ==============
    n_mech = sum(1 for c in cells_24 if c.get("bonferroni12_PASS"))
    n_dir = sum(1 for c in cells_24 if c.get("v5_direction_PASS"))
    per_angle_mech = Counter(c["angle"] for c in cells_24 if c.get("bonferroni12_PASS"))
    per_angle_dir = Counter(c["angle"] for c in cells_24 if c.get("v5_direction_PASS"))

    floor = 6  # 24 cells * 0.25 = 6
    border = 4
    if n_mech >= floor:
        verdict_mech = "PASS"
    elif n_mech >= border:
        verdict_mech = "BORDERLINE"
    else:
        verdict_mech = "KILL"

    out = {
        "cells": cells_24,
        "n_cells": 24,
        "n_pass_mechanical": n_mech,
        "n_pass_v5_direction_conditioned": n_dir,
        "per_angle_mechanical": dict(per_angle_mech),
        "per_angle_v5_direction_conditioned": dict(per_angle_dir),
        "v5_11b_24_verdict_mechanical": verdict_mech,
        "v5_11b_24_threshold": ">= 6/24 PASS = PASS; 4-5/24 BORDERLINE; <= 3/24 KILL",
        "lock_c_3_angle_OK_mechanical": (
            per_angle_mech.get(1, 0) >= 1 and per_angle_mech.get(2, 0) >= 1 and per_angle_mech.get(4, 0) >= 1
        ),
        "lock_c_3_angle_OK_direction": (
            per_angle_dir.get(1, 0) >= 1 and per_angle_dir.get(2, 0) >= 1 and per_angle_dir.get(4, 0) >= 1
        ),
        "notes": [
            "Cells 1-1..4-4 inherited from Phase 0+1 Bonferroni-12 ledger (CRSP-based).",
            "Cells 1-5..4-8 newly computed for R5 Bonferroni-24 expansion.",
            "Threshold scaled proportionally (12→24 cells: 3→6 PASS floor).",
        ],
    }

    LEDGER_24_OUT.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_24_OUT.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print()
    print("=" * 60)
    print(f"Bonferroni-24 ledger:")
    print(f"  mechanical PASS: {n_mech}/24 -> {verdict_mech}")
    print(f"  direction PASS:  {n_dir}/24")
    print(f"  per-angle mech:  {dict(per_angle_mech)}")
    print(f"  per-angle dir:   {dict(per_angle_dir)}")
    print(f"  Lock C 3-angle OK (mech): {out['lock_c_3_angle_OK_mechanical']}")
    print(f"  Lock C 3-angle OK (dir):  {out['lock_c_3_angle_OK_direction']}")
    print(f"\nLedger written to: {LEDGER_24_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
