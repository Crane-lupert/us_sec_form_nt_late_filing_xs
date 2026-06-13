"""Sanity-check battery for the body-narrative long-short basket.

Five deterministic checks that do not require additional data or LLM calls:

  (1) Effective leverage from overlapping 90-day positions.
       Monthly entry + 90-day hold ⇒ at most 3 simultaneous positions.
       Reports the implied per-dollar-of-capital Sharpe alongside the
       per-position Sharpe.

  (5) Winsorization sensitivity: re-runs the Net Sharpe at 0.5/99.5,
       1/99, 2/98, and a hard truncation rule (+/- 100%).

  (7) Deflated-Sharpe-ratio (Bailey & Lopez de Prado 2014) sensitivity to
       n_trials. Re-deflates the in-sample 0.59 Sharpe at n_trials =
       {8, 16, 32, 64, 128} to bracket implicit data-snooping breadth.

  (9) Annualization sensitivity: reports the alpha annualized under the
       paper's 252/90 = 2.8 convention and under naïve 12-period-per-year
       and 4-quarter-per-year alternatives.

 (10) Spanning regression: body-narrative L/S monthly return on the
       recurring-vs-non-recurring NT filer L/S monthly return.
       If the recurring L/S spans the body-narrative L/S, the
       classification adds nothing beyond the cohort split.

Output: reports/sanity-check.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
REPORTS = REPO / "reports"


def _load_strategy_monthly(tc_bps_rt: float = 15.0) -> dict[str, float]:
    rows = [json.loads(l) for l in (DATA / "net_sharpe_strategy_d_pit.jsonl").open(encoding="utf-8")]
    rows = [r for r in rows if r["window_days"] == 90]
    rows.sort(key=lambda r: r["year_month"])
    return {r["year_month"]: r["long_short_pct"] - tc_bps_rt / 100.0 for r in rows}


def _load_recurring_monthly() -> dict[str, float]:
    rows = [json.loads(l) for l in (DATA / "crsp_angle_4_recurring.jsonl").open(encoding="utf-8")]
    by_rec: dict[str, list[float]] = {}
    by_non: dict[str, list[float]] = {}
    for r in rows:
        ym = r["date_filed"][:7]
        v = r.get("fwd_90d")
        if v is None:
            continue
        (by_rec if r["recurring"] else by_non).setdefault(ym, []).append(v)
    out: dict[str, float] = {}
    for ym in set(by_rec) | set(by_non):
        rec = by_rec.get(ym, [])
        non = by_non.get(ym, [])
        if len(rec) >= 5 and len(non) >= 5:
            # Convert from fraction to percent
            out[ym] = 100.0 * (float(np.mean(non)) - float(np.mean(rec)))
    return out


def _load_angle2_forward() -> list[dict]:
    return [json.loads(l) for l in (DATA / "angle_2_forward_pit.jsonl").open(encoding="utf-8")]


def _winsorize(arr: np.ndarray, lo_pct: float, hi_pct: float) -> np.ndarray:
    if arr.size == 0:
        return arr
    lo, hi = np.percentile(arr, [lo_pct, hi_pct])
    return np.clip(arr, lo, hi)


def _truncate(arr: np.ndarray, threshold: float) -> np.ndarray:
    return arr[(arr >= -threshold) & (arr <= threshold)]


def _monthly_long_short_from_angle2(rows: list[dict], winsorize_pct: tuple[float, float] | None,
                                     truncation: float | None = None,
                                     tc_bps_rt: float = 15.0) -> list[tuple[str, float, int, int]]:
    """Rebuild the monthly L-S series for the 90d horizon with a configurable
    winsorization or truncation rule.

    Returns list of (year_month, monthly_pct, n_ai, n_other).
    """
    rows = [r for r in rows if r.get("label") in ("accounting_issue", "other")]
    # Collect car_fwd_90d (already a fraction). Convert to percent.
    pool = np.array([100.0 * r["car_fwd_90d"] for r in rows if r.get("car_fwd_90d") is not None])
    if winsorize_pct is not None:
        lo_pct, hi_pct = winsorize_pct
        clipped_pool = _winsorize(pool, lo_pct, hi_pct)
        lo = float(np.percentile(pool, lo_pct))
        hi = float(np.percentile(pool, hi_pct))
        # Apply same winsor levels to each filing
        for r in rows:
            v = r.get("car_fwd_90d")
            if v is None:
                continue
            v_pct = 100.0 * v
            r["_car_fwd_90d_adj"] = max(lo, min(hi, v_pct))
    elif truncation is not None:
        for r in rows:
            v = r.get("car_fwd_90d")
            if v is None:
                continue
            v_pct = 100.0 * v
            if v_pct < -truncation or v_pct > truncation:
                r["_car_fwd_90d_adj"] = None
            else:
                r["_car_fwd_90d_adj"] = v_pct
    else:
        for r in rows:
            v = r.get("car_fwd_90d")
            r["_car_fwd_90d_adj"] = 100.0 * v if v is not None else None

    # Group by month
    by_month_ai: dict[str, list[float]] = {}
    by_month_ot: dict[str, list[float]] = {}
    for r in rows:
        ym = r["date_filed"][:7]
        v = r.get("_car_fwd_90d_adj")
        if v is None:
            continue
        if r["label"] == "accounting_issue":
            by_month_ai.setdefault(ym, []).append(v)
        else:
            by_month_ot.setdefault(ym, []).append(v)
    months = sorted(set(by_month_ai) & set(by_month_ot))
    out: list[tuple[str, float, int, int]] = []
    for ym in months:
        ai = by_month_ai[ym]
        ot = by_month_ot[ym]
        if len(ai) < 5 or len(ot) < 5:
            continue
        ls = float(np.mean(ot) - np.mean(ai)) - tc_bps_rt / 100.0
        out.append((ym, ls, len(ai), len(ot)))
    return out


def _sharpe(rets_pct: np.ndarray, periods_per_year: float) -> dict:
    if rets_pct.size < 2:
        return {"n": int(rets_pct.size), "ann_mean_pct": None, "ann_vol_pct": None, "sharpe": None}
    m = float(np.mean(rets_pct))
    s = float(np.std(rets_pct, ddof=0))
    ann_m = m * periods_per_year
    ann_v = s * (periods_per_year ** 0.5)
    return {
        "n": int(rets_pct.size),
        "period_mean_pct": round(m, 4),
        "period_vol_pct": round(s, 4),
        "ann_mean_pct": round(ann_m, 4),
        "ann_vol_pct": round(ann_v, 4),
        "sharpe": round(ann_m / ann_v, 4) if ann_v > 0 else None,
    }


def _deflated_sharpe(sr: float, n_obs: int, n_trials: int,
                     skew: float = 0.0, kurt: float = 3.0) -> dict:
    """Deflated Sharpe Ratio per Bailey & Lopez de Prado 2014.

    DSR = Φ( (SR - E[SR_max]) * sqrt(n - 1) / sqrt(1 - skew*SR + (kurt - 1)/4 * SR^2) )

    where E[SR_max] = sqrt(2 * ln(n_trials)) under N(0, 1) standardized.
    Higher n_trials lowers DSR.
    """
    from math import sqrt, log
    if n_trials < 1 or n_obs < 2:
        return {"dsr": None}
    e_sr_max = sqrt(2.0 * log(n_trials)) / sqrt(n_obs)
    denom = sqrt(max(1e-9, 1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr * sr))
    z = (sr - e_sr_max) * sqrt(n_obs - 1) / denom
    # Standard normal CDF via erf
    from math import erf
    dsr = 0.5 * (1.0 + erf(z / sqrt(2.0)))
    return {"e_sr_max": round(e_sr_max, 4), "z": round(z, 4), "dsr": round(dsr, 4)}


def main() -> int:
    out: dict = {}

    # --------------------------------------------------------------
    # (1) Effective leverage from overlapping positions
    # --------------------------------------------------------------
    strat = _load_strategy_monthly()
    months_sorted = sorted(strat)
    rets_pp = np.array([strat[m] for m in months_sorted])
    base_per_position_sharpe = _sharpe(rets_pp, periods_per_year=252.0 / 90.0)
    # If holding period is 90 trading days and entries are monthly, average
    # number of simultaneous positions is approx 90 / 21 ≈ 4.3 per dollar
    # of capital. The per-capital monthly return is then the mean of three
    # overlapping forward CARs, with vol scaled by sqrt(1 / k) under
    # independence (clearly an approximation under common factor exposure).
    avg_overlap = 90.0 / 21.0   # trading days in a month
    per_capital_mean = float(np.mean(rets_pp))   # same per dollar of capital;
                                                 # each entry is one position
    # But with k overlapping positions, the realized monthly capital used is
    # k × (capital per entry). Reporting both reading conventions.
    per_capital_sharpe_under_independence = (
        base_per_position_sharpe["sharpe"] / math.sqrt(avg_overlap)
        if base_per_position_sharpe["sharpe"] is not None else None
    )
    # 보다 정직: realized cumulative additive sum / years.
    sum_pp = float(np.sum(rets_pp))
    years = (len(rets_pp) / 12.0)
    ann_simple = sum_pp / years
    out["leverage"] = {
        "n_months": len(rets_pp),
        "years_covered": round(years, 2),
        "cumulative_additive_pp": round(sum_pp, 2),
        "annualized_additive_pp_per_year": round(ann_simple, 2),
        "avg_simultaneous_positions_per_dollar_capital": round(avg_overlap, 2),
        "per_position_sharpe_252_over_90": base_per_position_sharpe["sharpe"],
        "per_position_ann_mean_pct": base_per_position_sharpe["ann_mean_pct"],
        "per_position_ann_vol_pct": base_per_position_sharpe["ann_vol_pct"],
        "per_capital_sharpe_under_independence_approx": (
            round(per_capital_sharpe_under_independence, 4)
            if per_capital_sharpe_under_independence is not None else None
        ),
        "note": (
            "The 'per-position' Sharpe annualizes a single 90-day entry at 252/90 ≈ 2.8 "
            "periods/yr. The 'per-capital' approximation under independence is "
            "Sharpe / sqrt(90/21). Under common factor exposure the per-capital "
            "Sharpe is somewhere between the two. The paper's 0.59 is the "
            "per-position figure; a deployment-realistic per-capital number is "
            "smaller by approximately a factor of 2."
        ),
    }
    print(f"[1] Leverage (overlapping positions):")
    print(f"    avg simultaneous positions per $: {avg_overlap:.2f}")
    print(f"    per-position Sharpe (paper's 0.59): {base_per_position_sharpe['sharpe']}")
    print(f"    per-capital Sharpe (independence approx): {per_capital_sharpe_under_independence:.4f}" if per_capital_sharpe_under_independence else "    per-capital Sharpe: n/a")
    print(f"    cumulative additive return: {sum_pp:.1f} pp / {years:.2f} yr = {ann_simple:.2f} pp/yr (simple annualization)")

    # --------------------------------------------------------------
    # (5) Winsorization sensitivity
    # --------------------------------------------------------------
    a2 = _load_angle2_forward()
    print("\n[5] Winsorization sensitivity (per-position Sharpe at 90d):")
    out["winsorization"] = {}
    variants = [
        ("0.5/99.5", (0.5, 99.5), None),
        ("1/99 (paper baseline)", (1.0, 99.0), None),
        ("2/98", (2.0, 98.0), None),
        ("truncate +/-100pp", None, 100.0),
        ("truncate +/-50pp", None, 50.0),
        ("no winsorization", None, None),
    ]
    for name, w, trunc in variants:
        monthly = _monthly_long_short_from_angle2(a2, w, trunc)
        rets = np.array([m[1] for m in monthly])
        s = _sharpe(rets, periods_per_year=252.0 / 90.0)
        out["winsorization"][name] = {
            "n_months": s["n"],
            "ann_mean_pct": s["ann_mean_pct"],
            "ann_vol_pct": s["ann_vol_pct"],
            "sharpe": s["sharpe"],
        }
        print(f"  {name:<28} n_months={s['n']:>3}  ann_mean={s['ann_mean_pct']}%  ann_vol={s['ann_vol_pct']}%  Sharpe={s['sharpe']}")

    # --------------------------------------------------------------
    # (7) Deflated Sharpe Ratio sensitivity to n_trials
    # --------------------------------------------------------------
    print("\n[7] Deflated Sharpe Ratio (per-position, paper SR = 0.59, n = 58):")
    out["deflated_sharpe"] = {}
    for n_trials in [8, 16, 32, 64, 128]:
        d = _deflated_sharpe(0.59, n_obs=58, n_trials=n_trials)
        out["deflated_sharpe"][f"n_trials={n_trials}"] = d
        print(f"  n_trials={n_trials:>3}  E[SR_max]={d['e_sr_max']}  z={d['z']}  DSR={d['dsr']}")

    # --------------------------------------------------------------
    # (9) Annualization sensitivity
    # --------------------------------------------------------------
    print("\n[9] Annualization sensitivity (per-position SR 0.59):")
    out["annualization"] = {}
    for label, ppy in [("paper: 252/90 approx 2.8", 252.0 / 90.0),
                       ("monthly compounding (12)", 12.0),
                       ("quarterly (4)", 4.0)]:
        alpha_mo = 11.24   # from factor regression
        ann_alpha = alpha_mo * ppy
        ann_sharpe = (alpha_mo / float(np.std(rets_pp, ddof=0))) * math.sqrt(ppy)
        out["annualization"][label] = {
            "periods_per_year": round(ppy, 3),
            "ann_alpha_pct": round(ann_alpha, 2),
            "ann_sharpe_implied": round(ann_sharpe, 4),
        }
        print(f"  {label:<26} ppy={ppy:.3f}  ann_alpha={ann_alpha:.2f}%  ann_Sharpe={ann_sharpe:.4f}")

    # --------------------------------------------------------------
    # (10) Spanning regression: body-narrative L-S on recurring L-S
    # --------------------------------------------------------------
    print("\n[10] Spanning regression: body-narrative L-S ~ recurring L-S")
    recurring = _load_recurring_monthly()
    common = sorted(set(strat) & set(recurring))
    y = np.array([strat[m] for m in common])
    X = np.array([[1.0, recurring[m]] for m in common])
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    fitted = X @ beta
    res = y - fitted
    T = X.shape[0]
    # Newey-West SE lag 6
    def nw_se(X, res, lag):
        T, k = X.shape
        XtX_inv = np.linalg.inv(X.T @ X)
        u = (X.T * res).T
        S = u.T @ u
        for h in range(1, lag + 1):
            w = 1.0 - h / (lag + 1.0)
            G = u[h:].T @ u[:-h]
            S += w * (G + G.T)
        return np.sqrt(np.diag(XtX_inv @ S @ XtX_inv))
    se = nw_se(X, res, lag=6)
    tstat = beta / se
    ss_res = float(np.sum(res ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else None
    out["spanning_body_on_recurring"] = {
        "n_obs": int(T),
        "alpha_pct": round(float(beta[0]), 4),
        "alpha_nw_se": round(float(se[0]), 4),
        "alpha_tstat": round(float(tstat[0]), 4),
        "beta_recurring": round(float(beta[1]), 4),
        "beta_nw_se": round(float(se[1]), 4),
        "beta_tstat": round(float(tstat[1]), 4),
        "r_squared": round(r2, 4) if r2 is not None else None,
    }
    print(f"  alpha (residual after recurring): {beta[0]:.4f}%/mo NW-SE {se[0]:.4f} t={tstat[0]:.3f}")
    print(f"  beta on recurring L-S:            {beta[1]:.4f} NW-SE {se[1]:.4f} t={tstat[1]:.3f}")
    print(f"  R^2:                              {r2:.4f}")
    print(f"  Interpretation: if alpha t>2 after recurring beta absorption, body-narrative adds independent information.")

    # --------------------------------------------------------------
    # Write
    # --------------------------------------------------------------
    REPORTS.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS / "sanity-check.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nReport: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
