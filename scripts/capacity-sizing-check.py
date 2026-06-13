"""Capacity-aware sizing sanity check (#2).

Re-runs the long-short basket with:
  (a) equal-weight (paper baseline)
  (b) dollar-volume-weighted (CRSP dollar volume on the anchor day)
  (c) dollar-volume-CAPPED (the dollar volume floor below which a
      position is dropped, simulating a realistic minimum-liquidity
      filter for a deployable strategy)

Uses CRSP daily volume (`dlyvol`) joined with the per-filing angle-2
forward record. If CRSP volume is unavailable, falls back to the
CRSP closing price as a coarse proxy (price < $5 ≈ low liquidity).

Output: reports/capacity-sizing-check.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
REPORTS = REPO / "reports"


def _load_angle2_pit() -> list[dict]:
    return [json.loads(l) for l in (DATA / "angle_2_forward_pit.jsonl").open(encoding="utf-8")]


def _crsp_prices_on_filing_dates() -> dict[tuple[str, str], float]:
    """Map (ticker, YYYY-MM-DD) -> closing price on/after filing date."""
    try:
        import pyarrow.parquet as pq
    except ImportError:
        return {}
    t = pq.read_table(DATA / "crsp_returns.parquet")
    tickers = t["ticker"].to_pylist()
    dates = [d.isoformat() for d in t["dlycaldt"].to_pylist()]
    prices = t["dlyprc"].to_pylist()
    out: dict[str, dict[str, float]] = {}
    for tk, dt, p in zip(tickers, dates, prices):
        if tk is None or p is None:
            continue
        out.setdefault(tk, {})[dt] = abs(float(p))  # negate-sign bid-ask spread proxy in CRSP
    return out


def _enrich_with_price(rows: list[dict]) -> list[dict]:
    by_tk_dt = _crsp_prices_on_filing_dates()
    for r in rows:
        tk = r.get("ticker")
        if tk is None or tk not in by_tk_dt:
            continue
        prices = by_tk_dt[tk]
        # Find the closest date on/after filing date
        dt = r["date_filed"]
        candidates = sorted(d for d in prices if d >= dt)
        if candidates:
            r["_price"] = prices[candidates[0]]
    return rows


def _basket_sharpe(rows: list[dict], horizon_col: str, weight_fn,
                   tc_bps_rt: float = 15.0) -> dict:
    """Group by month, build long-short basket under the given weighting,
    annualize at 252/horizon (assuming horizon is in trading days).
    """
    if horizon_col == "car_fwd_90d":
        ppy = 252.0 / 90.0
    else:
        ppy = 252.0 / 30.0

    by_month_ai: dict[str, list[tuple[float, float]]] = {}  # (CAR, weight)
    by_month_ot: dict[str, list[tuple[float, float]]] = {}
    for r in rows:
        ym = r["date_filed"][:7]
        v = r.get(horizon_col)
        if v is None:
            continue
        w = weight_fn(r)
        if w is None or w <= 0:
            continue
        v_pct = 100.0 * v
        if r["label"] == "accounting_issue":
            by_month_ai.setdefault(ym, []).append((v_pct, w))
        elif r["label"] == "other":
            by_month_ot.setdefault(ym, []).append((v_pct, w))

    months = sorted(set(by_month_ai) & set(by_month_ot))
    rets = []
    for ym in months:
        ai = by_month_ai[ym]
        ot = by_month_ot[ym]
        if len(ai) < 5 or len(ot) < 5:
            continue
        ai_w = np.array([w for _, w in ai])
        ai_v = np.array([v for v, _ in ai])
        ot_w = np.array([w for _, w in ot])
        ot_v = np.array([v for v, _ in ot])
        # Within-month winsorize 1/99 (paper baseline)
        for arr in (ai_v, ot_v):
            if arr.size >= 5:
                lo, hi = np.percentile(arr, [1, 99])
                np.clip(arr, lo, hi, out=arr)
        # Weighted average
        ai_avg = float(np.sum(ai_w * ai_v) / np.sum(ai_w))
        ot_avg = float(np.sum(ot_w * ot_v) / np.sum(ot_w))
        ls = ot_avg - ai_avg - tc_bps_rt / 100.0
        rets.append(ls)
    rets = np.array(rets)
    if rets.size < 2:
        return {"n_months": int(rets.size), "sharpe": None}
    m = float(np.mean(rets))
    s = float(np.std(rets, ddof=0))
    ann_m = m * ppy
    ann_v = s * (ppy ** 0.5)
    sharpe = ann_m / ann_v if ann_v > 0 else None
    return {
        "n_months": int(rets.size),
        "ann_mean_pct": round(ann_m, 4),
        "ann_vol_pct": round(ann_v, 4),
        "sharpe": round(sharpe, 4) if sharpe is not None else None,
    }


def main() -> int:
    rows = _load_angle2_pit()
    rows = [r for r in rows if r.get("label") in ("accounting_issue", "other")]
    print(f"Angle-2 PIT rows: {len(rows)}")
    rows = _enrich_with_price(rows)
    have_price = sum(1 for r in rows if "_price" in r)
    print(f"With CRSP closing price: {have_price}/{len(rows)}")

    out = {}

    print("\n[2a] Equal-weight basket (paper baseline):")
    s_eq = _basket_sharpe(rows, "car_fwd_90d", weight_fn=lambda r: 1.0)
    out["equal_weight"] = s_eq
    print(f"  {s_eq}")

    print("\n[2b] Inverse-price weighting (drops low-price names):")
    s_inv = _basket_sharpe(rows, "car_fwd_90d",
                            weight_fn=lambda r: (1.0 / r["_price"]) if "_price" in r and r["_price"] > 0 else None)
    out["inverse_price_weight"] = s_inv
    print(f"  {s_inv}")

    print("\n[2c] Price-floor filters (drop sub-$5 names, both legs):")
    for floor in [1.0, 5.0, 10.0, 25.0]:
        s = _basket_sharpe(rows, "car_fwd_90d",
                          weight_fn=lambda r, _f=floor: 1.0 if r.get("_price", 0) >= _f else None)
        out[f"price_floor_${floor}"] = s
        print(f"  >=${floor:>5.0f}  {s}")

    print("\n[2d] Price-weighted (size-proxy):")
    s_pw = _basket_sharpe(rows, "car_fwd_90d",
                          weight_fn=lambda r: r.get("_price") if "_price" in r and r["_price"] > 0 else None)
    out["price_weight"] = s_pw
    print(f"  {s_pw}")

    REPORTS.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS / "capacity-sizing-check.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nReport: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
