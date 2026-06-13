"""Factor-adjusted performance of the body-narrative long-short basket.

Regresses the monthly long-short return (net of 15 bp round-trip cost) on
the Fama-French 5-factor + UMD momentum monthly returns:

    r_t^LS = alpha + b1*MktRF + b2*SMB + b3*HML + b4*RMW + b5*CMA + b6*MOM + e_t

Standard errors are Newey-West heteroskedasticity-and-autocorrelation-consistent
(HAC) with lag truncation 6 (Andrews 1991 data-dependent rule for ~53 obs).

Inputs:
    data/net_sharpe_strategy_d_pit.jsonl  (monthly L-S returns under PIT anchor)
    data/ff5_umd_monthly.jsonl            (FF5 + UMD monthly factors, % units)

Output:
    reports/factor-regression.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
REPORTS = REPO / "reports"

TC_BPS_PER_LEG = 7.5  # 15 bp round-trip


def _load_strategy_monthly() -> dict[str, float]:
    """Monthly net long-short return on the body-narrative basket (PIT anchor)."""
    rows = [json.loads(l) for l in (DATA / "net_sharpe_strategy_d_pit.jsonl").open(encoding="utf-8")]
    rows = [r for r in rows if r["window_days"] == 90]
    rows.sort(key=lambda r: r["year_month"])
    # long_short_pct is in percent units; subtract 15 bp round-trip per entry.
    return {r["year_month"]: r["long_short_pct"] - 2 * TC_BPS_PER_LEG / 100.0 for r in rows}


def _load_factors() -> dict[str, dict[str, float]]:
    rows = [json.loads(l) for l in (DATA / "ff5_umd_monthly.jsonl").open(encoding="utf-8")]
    return {r["year_month"]: r for r in rows}


def _hac_se(X: np.ndarray, residuals: np.ndarray, lag: int) -> np.ndarray:
    """Newey-West HAC standard errors.

    X shape (T, k); residuals shape (T,). Returns SE vector of length k.
    Uses Bartlett kernel with maximum lag `lag`.
    """
    T, k = X.shape
    XtX_inv = np.linalg.inv(X.T @ X)
    # S = sum over lags of Bartlett-weighted X'_t e_t e_{t-h} X_{t-h}
    u = (X.T * residuals).T  # (T, k)
    S = u.T @ u
    for h in range(1, lag + 1):
        w = 1.0 - h / (lag + 1.0)
        Gamma_h = u[h:].T @ u[:-h]
        S += w * (Gamma_h + Gamma_h.T)
    Var_b = XtX_inv @ S @ XtX_inv
    return np.sqrt(np.diag(Var_b))


def main() -> int:
    strat = _load_strategy_monthly()
    factors = _load_factors()
    common = sorted(set(strat) & set(factors))
    print(f"Strategy monthly periods: {len(strat)}")
    print(f"Factor monthly periods:   {len(factors)}")
    print(f"Common (after join):      {len(common)}")

    # Build the regression matrices. All quantities are in percentage points
    # per month (Ken French convention). Subtract RF from the strategy
    # return to get the excess return.
    y = np.array([strat[ym] - factors[ym]["RF"] for ym in common])
    X_cols = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "MOM"]
    X = np.array([[1.0] + [factors[ym][c] for c in X_cols] for ym in common])
    T = X.shape[0]

    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    fitted = X @ beta
    residuals = y - fitted

    # HAC SE (lag = 6 per Andrews 1991 for T ~ 53)
    se = _hac_se(X, residuals, lag=6)
    tstat = beta / se

    # Annualize alpha: monthly alpha * 12 (but alpha is in percent already, so
    # the annualized number is monthly_alpha * 12).
    alpha_monthly_pct = beta[0]
    # However, the strategy holds 90 trading days per entry; the "monthly"
    # period in net_sharpe_strategy_d_pit.jsonl is one entry per calendar
    # month with a 90-day forward window. Treating it as a monthly series in
    # the regression yields a monthly alpha *per entry*. The deflation to
    # an annualized number uses 252/90 ≈ 2.8 periods per year, not 12.
    # We report both conventions for transparency.
    alpha_periods_per_year = 252.0 / 90.0
    alpha_ann_pct = alpha_monthly_pct * alpha_periods_per_year
    alpha_ann_se = se[0] * alpha_periods_per_year
    alpha_ann_t = alpha_ann_pct / alpha_ann_se if alpha_ann_se > 0 else 0.0

    # R-squared
    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum((y - np.mean(y))**2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    # Adjusted R^2
    k = X.shape[1] - 1  # number of regressors excluding intercept
    adj_r2 = 1.0 - (1.0 - r2) * (T - 1) / max(T - k - 1, 1)

    print()
    print(f"{'Coefficient':<14} {'Estimate':>10} {'NW SE':>10} {'t-stat':>10}")
    print("-" * 50)
    labels = ["alpha (mo., pct)"] + [f"beta {c}" for c in X_cols]
    for lbl, b, s, t in zip(labels, beta, se, tstat):
        print(f"{lbl:<22} {b:>10.4f} {s:>10.4f} {t:>10.3f}")
    print()
    print(f"Annualized alpha (pct/yr, 252/90 periods/yr): {alpha_ann_pct:.3f}")
    print(f"  Newey-West HAC SE:                          {alpha_ann_se:.3f}")
    print(f"  t-stat:                                     {alpha_ann_t:.3f}")
    print()
    print(f"R^2 = {r2:.4f}   Adjusted R^2 = {adj_r2:.4f}")
    print(f"T = {T}, k = {k} (regressors excluding intercept)")

    out = {
        "n_obs": int(T),
        "horizon_days": 90,
        "periods_per_year_annualization": alpha_periods_per_year,
        "tc_bps_round_trip": 15,
        "coefficients": {
            "alpha_monthly_pct": float(beta[0]),
            "Mkt-RF": float(beta[1]),
            "SMB": float(beta[2]),
            "HML": float(beta[3]),
            "RMW": float(beta[4]),
            "CMA": float(beta[5]),
            "MOM": float(beta[6]),
        },
        "newey_west_hac_se": {
            "alpha_monthly_pct": float(se[0]),
            "Mkt-RF": float(se[1]),
            "SMB": float(se[2]),
            "HML": float(se[3]),
            "RMW": float(se[4]),
            "CMA": float(se[5]),
            "MOM": float(se[6]),
            "lag_truncation": 6,
        },
        "t_statistics": {
            "alpha_monthly": float(tstat[0]),
            "Mkt-RF": float(tstat[1]),
            "SMB": float(tstat[2]),
            "HML": float(tstat[3]),
            "RMW": float(tstat[4]),
            "CMA": float(tstat[5]),
            "MOM": float(tstat[6]),
        },
        "annualized_alpha_pct": float(alpha_ann_pct),
        "annualized_alpha_hac_se": float(alpha_ann_se),
        "annualized_alpha_tstat": float(alpha_ann_t),
        "r_squared": float(r2),
        "adjusted_r_squared": float(adj_r2),
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS / "factor-regression.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nReport: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
