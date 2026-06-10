"""R1 — OOS 2025+ holdout: forward signal + Net Sharpe via CRSP returns.

Reads:
  data/nt_classifications_oos.jsonl     (gpt-4o-mini OOS 912 filings)
  data/restatement_events_oos.jsonl     (8-K 4.02 + 10-K/A + 10-Q/A per CIK)
  data/crsp_returns_oos.parquet         (CRSP returns 2024-2026 for OOS cohort)
  data/yfinance_cache/SPY.jsonl         (SPY market returns, extend if needed)

Produces:
  data/angle_2_forward_oos.jsonl        per-filing forward signal (rate + CRSP CAR)
  reports/r1-oos-angle-2-summary.json   rate-diff + CAR-diff cells (OOS)
  reports/r1-oos-net-sharpe.json        Net Sharpe @ 30d/90d (OOS)
  reports/r1-oos-verdict.json           V5-11(b)/(c) OOS verdict
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from statistics import mean, pstdev

REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def two_prop_z(k1: int, n1: int, k2: int, n2: int) -> dict:
    if n1 == 0 or n2 == 0:
        return {"p1": None, "p2": None, "diff": None, "z": None, "n1": n1, "n2": n2}
    p1, p2 = k1 / n1, k2 / n2
    p_pool = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2)) if 0 < p_pool < 1 else 0
    z = (p1 - p2) / se if se > 0 else 0
    return {
        "p1_pct": round(100 * p1, 4), "p2_pct": round(100 * p2, 4),
        "diff_pct": round(100 * (p1 - p2), 4),
        "z_stat": round(z, 4), "n1": n1, "n2": n2,
    }


def forward_car(firm_ret: list[tuple[str, float]], mkt: dict[str, float],
                filing_date: str, end_days: int) -> float | None:
    t0 = next((i for i, (d, _) in enumerate(firm_ret) if d >= filing_date), None)
    if t0 is None:
        return None
    end = t0 + end_days
    if end >= len(firm_ret):
        return None
    car = 0.0
    n = 0
    for i in range(t0 + 1, end + 1):
        d, fr = firm_ret[i]
        mr = mkt.get(d)
        if mr is None:
            continue
        car += fr - mr
        n += 1
    return car if n > 0 else None


def main() -> int:
    # ---- Load classifications ----
    cls_rows = [json.loads(l) for l in (REPO_ROOT / "data" / "nt_classifications_oos.jsonl").open(encoding="utf-8")]
    cls_rows = [r for r in cls_rows if r.get("label") in ("accounting_issue", "unresolved_sec_comment", "other")]
    print(f"OOS classifications: {len(cls_rows)}", flush=True)

    # ---- Load restatement events ----
    rst_path = REPO_ROOT / "data" / "restatement_events_oos.jsonl"
    rst_by_cik: dict[str, list[date]] = defaultdict(list)
    if rst_path.exists():
        for line in rst_path.open(encoding="utf-8"):
            r = json.loads(line)
            if r.get("filing_date"):
                try:
                    rst_by_cik[r["cik"].lstrip("0") or "0"].append(parse_date(r["filing_date"]))
                except ValueError:
                    pass
        for k in rst_by_cik:
            rst_by_cik[k].sort()
    print(f"Restatement events from {len(rst_by_cik)} CIKs", flush=True)

    # ---- Load CRSP returns ----
    print("Loading CRSP OOS returns...", flush=True)
    import duckdb
    db = duckdb.connect(":memory:")
    crsp_path = REPO_ROOT / "data" / "crsp_returns_oos.parquet"
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
    print(f"  CRSP tickers: {len(by_ticker)}", flush=True)

    # ---- SPY market ----
    spy_p = REPO_ROOT / "data" / "yfinance_cache" / "SPY.jsonl"
    spy_rows = sorted([json.loads(l) for l in spy_p.open(encoding="utf-8")], key=lambda r: r["date"])
    market: dict[str, float] = {}
    prev = None
    for r in spy_rows:
        c = r["close"]
        if prev is not None and prev > 0:
            market[r["date"]] = c / prev - 1.0
        prev = c
    print(f"  SPY market days: {len(market)}", flush=True)

    # ---- Build forward signal per filing ----
    windows_days = [14, 30, 90, 180]
    joined: list[dict] = []
    for r in cls_rows:
        ticker = r["ticker"]
        firm = by_ticker.get(ticker, [])
        nt_d = parse_date(r["date_filed"])
        cik_norm = r["cik"].lstrip("0") or "0"
        rst_dates = rst_by_cik.get(cik_norm, [])
        future = [d for d in rst_dates if d > nt_d]
        first_rst = future[0] if future else None
        row_out = {
            "accession_number": r["accession_number"], "cik": r["cik"], "ticker": ticker,
            "form_type": r["form_type"], "date_filed": r["date_filed"], "label": r["label"],
            "first_restatement_after": first_rst.isoformat() if first_rst else None,
            "days_to_first_restatement": (first_rst - nt_d).days if first_rst else None,
        }
        for w in windows_days:
            row_out[f"restated_within_{w}d"] = bool(first_rst and (first_rst - nt_d).days <= w)
        if firm and market:
            for w in (30, 90):
                row_out[f"car_fwd_{w}d"] = forward_car(firm, market, r["date_filed"], w)
        else:
            for w in (30, 90):
                row_out[f"car_fwd_{w}d"] = None
        joined.append(row_out)
    joined.sort(key=lambda r: (r["cik"], r["date_filed"], r["accession_number"]))

    out_p = REPO_ROOT / "data" / "angle_2_forward_oos.jsonl"
    with out_p.open("w", encoding="utf-8") as f:
        for r in joined:
            f.write(json.dumps(r) + "\n")
    print(f"\nJoined: {len(joined)} filings -> {out_p}", flush=True)

    # ---- Rate-diff cells ----
    by_label = defaultdict(list)
    for r in joined:
        by_label[r["label"]].append(r)
    ai = by_label["accounting_issue"]
    ot = by_label["other"]
    print(f"  AI={len(ai)} OT={len(ot)} UR={len(by_label['unresolved_sec_comment'])}", flush=True)

    rate_cells = {}
    for w in windows_days:
        k1 = sum(1 for r in ai if r[f"restated_within_{w}d"])
        k2 = sum(1 for r in ot if r[f"restated_within_{w}d"])
        z = two_prop_z(k1, len(ai), k2, len(ot))
        rate_cells[f"rate_{w}d"] = {
            **z,
            "bonferroni12_critical_z": 2.78,
            "bonferroni12_PASS": bool(z["z_stat"] is not None and abs(z["z_stat"]) > 2.78),
        }

    # ---- Net Sharpe sim ----
    rows_carscope = [r for r in joined if r["label"] in ("accounting_issue", "other")]
    cells_sharpe = {}
    for H in (30, 90):
        car_col = f"car_fwd_{H}d"
        vals = sorted(r[car_col] for r in rows_carscope if r.get(car_col) is not None)
        if len(vals) < 100:
            cells_sharpe[f"long_short_{H}d"] = {"verdict": "INSUFFICIENT_DATA",
                                                  "n_with_car": len(vals)}
            continue
        lo = vals[int(len(vals) * 0.01)]
        hi = vals[int(len(vals) * 0.99) - 1]
        by_month_ai, by_month_ot = defaultdict(list), defaultdict(list)
        for r in rows_carscope:
            v = r.get(car_col)
            if v is None:
                continue
            v = max(lo, min(hi, v))
            ym = r["date_filed"][:7]
            if r["label"] == "accounting_issue":
                by_month_ai[ym].append(v)
            else:
                by_month_ot[ym].append(v)
        months = sorted(set(by_month_ai) | set(by_month_ot))
        ls_rets = []
        for m in months:
            if len(by_month_ai.get(m, [])) >= 5 and len(by_month_ot.get(m, [])) >= 5:
                ls_rets.append(mean(by_month_ot[m]) - mean(by_month_ai[m]))
        if len(ls_rets) < 4:
            cells_sharpe[f"long_short_{H}d"] = {"verdict": "INSUFFICIENT_MONTHS",
                                                  "n_months": len(ls_rets)}
            continue
        ppy = 252 / H
        m_mu = mean(ls_rets)
        m_sd = pstdev(ls_rets) if len(ls_rets) > 1 else 0
        ann_mean = m_mu * ppy
        ann_vol = m_sd * math.sqrt(ppy)
        net_rets = [r - 15 / 10000 for r in ls_rets]  # 15bps RT
        net_ann_mean = mean(net_rets) * ppy
        gross_sharpe = (ann_mean / ann_vol) if ann_vol > 0 else 0
        net_sharpe = (net_ann_mean / ann_vol) if ann_vol > 0 else 0
        verdict = "PASS" if net_sharpe >= 0.30 else "BORDERLINE" if net_sharpe >= 0.21 else "KILL"
        cells_sharpe[f"long_short_{H}d"] = {
            "window_days": H,
            "n_months": len(ls_rets),
            "gross_ann_mean_pct": round(100 * ann_mean, 4),
            "ann_vol_pct": round(100 * ann_vol, 4),
            "gross_sharpe": round(gross_sharpe, 4),
            "net_sharpe": round(net_sharpe, 4),
            "v5_11c_verdict": verdict,
        }

    # ---- V5-11 OOS verdict ----
    pass_rate = sum(1 for c in rate_cells.values() if c["bonferroni12_PASS"])
    # 4 rate cells
    v5_11b_oos = (
        "PASS" if pass_rate >= 1 else "KILL"
    )  # OOS has only 4 cells of Angle 2; we mirror in-sample structure (any 1+ = PASS for OOS)
    sharpe_pass = any(c.get("v5_11c_verdict") == "PASS" for c in cells_sharpe.values())
    v5_11c_oos = "PASS" if sharpe_pass else (
        "BORDERLINE" if any(c.get("v5_11c_verdict") == "BORDERLINE" for c in cells_sharpe.values())
        else "KILL"
    )

    # ---- Output ----
    out_summary = {
        "n_oos_filings": len(joined),
        "n_in_scope_ai_ot": len(rows_carscope),
        "label_distribution": {k: len(v) for k, v in by_label.items()},
        "windows_days": windows_days,
        "rate_diff_cells": rate_cells,
        "net_sharpe_cells": cells_sharpe,
        "v5_11_OOS_verdict": {
            "v5_11b_rate_diff": v5_11b_oos,
            "v5_11c_net_sharpe": v5_11c_oos,
            "n_rate_cells_pass": pass_rate,
        },
    }
    (REPO_ROOT / "reports" / "r1-oos-summary.json").write_text(
        json.dumps(out_summary, indent=2), encoding="utf-8"
    )

    print("\n=== Rate-diff cells (OOS 2025+) ===")
    for k, v in rate_cells.items():
        print(f"  {k}: AI={v.get('p1_pct')}% OT={v.get('p2_pct')}% diff={v.get('diff_pct')}pp z={v.get('z_stat')} PASS={v.get('bonferroni12_PASS')}")
    print("\n=== Net Sharpe cells (OOS 2025+) ===")
    for k, v in cells_sharpe.items():
        print(f"  {k}: net Sharpe={v.get('net_sharpe')} (vol={v.get('ann_vol_pct')}%, n_months={v.get('n_months')}) {v.get('v5_11c_verdict')}")
    print(f"\n=== V5-11 OOS verdict ===")
    print(f"  V5-11(b) rate-diff: {v5_11b_oos} ({pass_rate}/4 cells PASS)")
    print(f"  V5-11(c) Net Sharpe: {v5_11c_oos}")
    print(f"\nSummary: reports/r1-oos-summary.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
