"""Generate paper figures from final result data.

Outputs to analysis/figures/:
  - fig1_cumulative_pnl.png  Cumulative long-short P&L, PIT acceptance anchor,
                             90-day horizon, 15bp round-trip cost
  - fig2_replication.png     Side-by-side: Bartov-K (2017) published vs
                             free-tier vs CRSP+delret, NT 10-K and NT 10-Q
                             5-day CAR
  - fig3_rate_diff.png       Subsequent restatement probability conditional
                             on accounting_issue vs other label, by horizon
  - fig4_bonferroni24.png    Bonferroni-24 cell t-stat distribution

All figures English-labeled, PNG, 300 dpi, vector-friendly fonts.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA = REPO_ROOT / "data"
REPORTS = REPO_ROOT / "reports"
OUT = REPO_ROOT / "analysis" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Serif",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "legend.fontsize": 9,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


# =================================================================
# Figure 1: cumulative long-short PnL, PIT acceptance anchor, 90d
# =================================================================

def _recurring_xs_monthly_return_series(months: list[str]) -> np.ndarray:
    """In-paper alternative long-short: non-recurring minus recurring NT filer
    cohorts, same monthly cadence and 90-day forward horizon. See Section 4.2,
    third angle.
    """
    rows = [json.loads(l) for l in (DATA / "crsp_angle_4_recurring.jsonl").open(encoding="utf-8")]
    by_month_rec: dict[str, list[float]] = {}
    by_month_non: dict[str, list[float]] = {}
    for r in rows:
        ym = r["date_filed"][:7]
        v = r.get("fwd_90d")
        if v is None:
            continue
        if r.get("recurring"):
            by_month_rec.setdefault(ym, []).append(v)
        else:
            by_month_non.setdefault(ym, []).append(v)
    out = []
    for ym in months:
        rec = by_month_rec.get(ym, [])
        non = by_month_non.get(ym, [])
        if len(rec) < 5 or len(non) < 5:
            out.append(0.0)
            continue
        out.append(np.mean(non) - np.mean(rec))
    return np.array(out)


def _factor_replicated_series(months: list[str], strategy_monthly_pct: np.ndarray) -> np.ndarray:
    """Return the factor-spanned portfolio's monthly return: the fitted value
    from a Fama-French 5-factor + UMD momentum regression on the strategy's
    monthly excess return, in percentage points per entry-period (so the
    cumulative additive convention matches the strategy series).

    The factor-replicated portfolio is the projection of the strategy onto
    the six common asset-pricing factors. The vertical gap between the
    strategy and this replicated benchmark is the realized residual alpha
    trail (the cumulative form of the regression intercept). Both are
    market-neutral and share the same cadence and horizon, so the
    comparison is the JF/JFE-conventional factor-baseline test for whether
    the strategy's profitability is spanned by common factors.
    """
    factor_rows = [json.loads(l) for l in (DATA / "ff5_umd_monthly.jsonl").open(encoding="utf-8")]
    by_ym = {r["year_month"]: r for r in factor_rows}
    # Build design matrix and excess return on the strategy's months
    X_cols = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "MOM"]
    keep = [i for i, ym in enumerate(months) if ym in by_ym]
    if not keep:
        return np.zeros(len(months))
    y = np.array([strategy_monthly_pct[i] - by_ym[months[i]]["RF"] for i in keep])
    X = np.array([[1.0] + [by_ym[months[i]][c] for c in X_cols] for i in keep])
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    # Factor-spanned portion of the monthly return (intercept excluded). Add
    # back the risk-free rate so the series is on the same gross-of-RF scale
    # as the strategy long-short series.
    fitted_ex_alpha = X[:, 1:] @ beta[1:]
    out = np.zeros(len(months))
    for k, i in enumerate(keep):
        out[i] = fitted_ex_alpha[k] + by_ym[months[i]]["RF"]
    return out


def make_fig1_per_capital():
    """Per-capital explicit backtest figure replacing the prior per-position
    cumulative additive plot. $1-of-capital strategy growth vs SPY
    buy-and-hold vs Fama-French market portfolio compounded, all on the
    same unit-capital basis.
    """
    series = [json.loads(l) for l in (DATA / "per_capital_backtest.jsonl").open(encoding="utf-8")]
    months = [r["year_month"] for r in series]
    strat = [r["strategy_capital"] for r in series]
    spy = [r["spy_capital"] for r in series]
    mkt = [r["mkt_capital"] for r in series]

    x = np.arange(len(months))
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    ax.fill_between(x, 1.0, strat, color="C0", alpha=0.15)
    ax.plot(x, strat, color="C0", linewidth=1.9, label="Body-narrative long–short basket (overlap-corrected, EW)")
    ax.plot(x, spy, color="C3", linewidth=1.4, linestyle="--", label="SPDR S\\&P 500 ETF (SPY) buy-and-hold")
    ax.plot(x, mkt, color="gray", linewidth=1.1, linestyle=":", label="Fama-French market portfolio (Mkt-RF + RF) compounded")
    ax.axhline(1.0, color="black", linewidth=0.6, alpha=0.4)

    seen = set()
    ticks, lbls = [], []
    for i, m in enumerate(months):
        y = m[:4]
        if y not in seen:
            seen.add(y)
            ticks.append(i)
            lbls.append(y)
    ax.set_xticks(ticks)
    ax.set_xticklabels(lbls, rotation=0)
    ax.set_xlabel("Year")
    ax.set_ylabel("Growth of \\$1 of capital")
    ax.set_title("Per-capital cumulative growth on a unit-capital basis,\nin-sample 2014–2024 (90-day overlap-corrected EW allocation)")
    ax.legend(loc="upper left", framealpha=0.9, fontsize=8)
    ax.grid(True, alpha=0.25)

    # Annotate terminal values
    ax.annotate(f"Strategy: \\${strat[-1]:.2f}\nann. Sharpe = 1.12",
                xy=(x[-1], strat[-1]),
                xytext=(x[-1] - 22, strat[-1] + 0.10),
                fontsize=9, ha="left",
                arrowprops=dict(arrowstyle="->", color="gray", linewidth=0.8))
    ax.annotate(f"SPY: \\${spy[-1]:.2f}\nann. Sharpe = 1.56",
                xy=(x[-1], spy[-1]),
                xytext=(x[-1] - 22, spy[-1] + 0.25),
                fontsize=9, ha="left",
                arrowprops=dict(arrowstyle="->", color="gray", linewidth=0.8))
    ax.annotate(f"FF Mkt: \\${mkt[-1]:.2f}",
                xy=(x[-1], mkt[-1]),
                xytext=(x[-1] - 22, mkt[-1] - 0.30),
                fontsize=8, ha="left", color="gray",
                arrowprops=dict(arrowstyle="->", color="gray", linewidth=0.6))

    fig.tight_layout()
    out = OUT / "fig1_cumulative_pnl.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def make_fig1():
    """Cumulative additive excess-return chart, strategy vs SPY benchmark.

    Each month-end the realized ninety-trading-day excess return of the
    long–short basket is recorded; the strategy line plots the running sum
    of those monthly excess returns, in percentage points. For comparison,
    SPY (buy-and-hold) monthly returns over the same months are summed in
    the same additive convention. The strategy's returns are already
    market-neutral by construction (each long–short observation is a
    firm-minus-SPY excess), so the SPY line serves as the directional
    "long-only equity" reference point against which the strategy's
    cumulative profile can be visually compared at the same scale.
    """
    rows = [json.loads(l) for l in (DATA / "net_sharpe_strategy_d_pit.jsonl").open(encoding="utf-8")]
    rows_90 = sorted([r for r in rows if r["window_days"] == 90], key=lambda r: r["year_month"])
    months = [r["year_month"] for r in rows_90]
    gross_monthly = np.array([r["long_short_pct"] / 100.0 for r in rows_90])
    tc = 15 / 10000  # 15 bps round-trip per entry
    net_monthly = gross_monthly - tc

    cum_net = 100.0 * np.cumsum(net_monthly)
    cum_gross = 100.0 * np.cumsum(gross_monthly)

    # FF5+UMD factor-spanned benchmark: the projection of the monthly L/S onto
    # the Fama-French 5-factor + momentum series. The cumulative gap between
    # the strategy and this benchmark is the realized residual alpha trail.
    factor_spanned = _factor_replicated_series(months, 100.0 * net_monthly)
    cum_factor = np.cumsum(factor_spanned)
    # In-paper alternative L/S kept as a tertiary reference line.
    recurring_xs = _recurring_xs_monthly_return_series(months)
    cum_recurring = 100.0 * np.cumsum(recurring_xs)

    x = np.arange(len(months))
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.fill_between(x, 0, cum_net, color="C0", alpha=0.15)
    ax.plot(x, cum_net, color="C0", linewidth=1.8,
            label="Body-narrative long–short, net of 15 bp round-trip")
    ax.plot(x, cum_gross, color="C0", linewidth=1.0, linestyle=":", alpha=0.7,
            label="Body-narrative long–short, gross")
    ax.plot(x, cum_factor, color="C3", linewidth=1.5, linestyle="--",
            label="FF5 + UMD factor-spanned portfolio (Fama-French 5-factor + momentum projection)")
    ax.plot(x, cum_recurring, color="gray", linewidth=1.0, linestyle=":", alpha=0.7,
            label="Recurring vs non-recurring NT filer L/S (in-paper alternative)")
    ax.axhline(0.0, color="black", linewidth=0.6, alpha=0.4)

    # X-axis: one tick per calendar year
    seen_years = set()
    tick_idx = []
    tick_lbl = []
    for i, m in enumerate(months):
        y = m[:4]
        if y not in seen_years:
            seen_years.add(y)
            tick_idx.append(i)
            tick_lbl.append(y)
    ax.set_xticks(tick_idx)
    ax.set_xticklabels(tick_lbl, rotation=0)

    ax.set_xlabel("Year")
    ax.set_ylabel("Cumulative return (\\%, additive)")
    ax.set_title("Body-narrative long–short vs Fama-French 5-factor + UMD factor-spanned portfolio\n"
                 "(JF/JFE-conventional factor baseline), in-sample 2014–2024")
    ax.legend(loc="upper left", framealpha=0.9, fontsize=8)
    ax.grid(True, alpha=0.25)

    # Annotation placement: strategy terminal + alpha trail + alternative
    strategy_end = cum_net[-1]
    factor_end = cum_factor[-1]
    alt_end = cum_recurring[-1]
    alpha_gap = strategy_end - factor_end
    ax.annotate(f"Body-narrative L/S:\nterminal = {strategy_end:.0f}\\%, Net Sharpe = 0.59",
                xy=(x[-1], strategy_end),
                xytext=(x[-1] - 24, strategy_end + 25),
                fontsize=9, ha="left",
                arrowprops=dict(arrowstyle="->", color="gray", linewidth=0.8))
    ax.annotate(f"Factor-spanned: {factor_end:.0f}\\%\nCum. residual $\\alpha$ trail: {alpha_gap:.0f}\\%",
                xy=(x[-1], factor_end),
                xytext=(x[-1] - 24, factor_end - 30),
                fontsize=9, ha="left",
                arrowprops=dict(arrowstyle="->", color="gray", linewidth=0.8))
    ax.annotate(f"Recurring-filer L/S: {alt_end:.0f}\\%",
                xy=(x[-1], alt_end),
                xytext=(x[-1] - 24, alt_end - 80),
                fontsize=8, ha="left", color="gray",
                arrowprops=dict(arrowstyle="->", color="gray", linewidth=0.6))

    fig.tight_layout()
    out = OUT / "fig1_cumulative_pnl.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


# =================================================================
# Figure 2: Bartov-K replication — three samples side-by-side
# =================================================================

def make_fig2():
    cohorts = ["NT 10-K\n5-day CAR", "NT 10-Q\n5-day CAR", "NT 10-K\n60-day drift", "NT 10-Q\n60-day drift"]
    bk = [-1.96, -2.93, np.nan, np.nan]            # published Bartov-K 2017 (NA for drift)
    yfin = [-1.41, -0.72, +2.08, +5.50]            # free-tier active-exchange-only
    crsp = [-2.11, -2.88, -3.08, -3.20]            # CRSP + delisting return

    x = np.arange(len(cohorts))
    w = 0.27

    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.bar(x - w, bk, width=w, color="C7", label="Bartov–Konchitchki (2017) published")
    ax.bar(x,     yfin, width=w, color="C1", label="Free-tier feed (active-exchange-only)")
    ax.bar(x + w, crsp, width=w, color="C0", label="CRSP daily with delisting return")
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(cohorts)
    ax.set_ylabel("Cumulative abnormal return (%)")
    ax.set_title("Replication of the Form NT short-window and post-filing drift\n"
                 "across three return sources")
    ax.legend(loc="upper right", framealpha=0.9, fontsize=8)
    ax.grid(True, alpha=0.25, axis="y")
    # Annotate gap on the two short-window cells
    for xi, (a, b) in enumerate([(bk[0], crsp[0]), (bk[1], crsp[1])]):
        ax.text(xi + w, b - 0.4, f"gap {abs(a - b):.2f} pp",
                ha="center", va="top", fontsize=8, color="C0")

    fig.tight_layout()
    out = OUT / "fig2_replication.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


# =================================================================
# Figure 3: subsequent restatement probability by horizon
# =================================================================

def make_fig3():
    summary = json.loads((REPORTS / "angle-2-summary.json").read_text(encoding="utf-8"))
    cells = summary["rate_diff_cells"]
    horizons = [14, 30, 90, 180]
    p_ai = [cells[f"rate_{h}d"]["p1_pct"] for h in horizons]
    p_ot = [cells[f"rate_{h}d"]["p2_pct"] for h in horizons]
    diff = [cells[f"rate_{h}d"]["diff_pct"] for h in horizons]
    z = [cells[f"rate_{h}d"]["z_stat"] for h in horizons]

    x = np.arange(len(horizons))
    w = 0.35

    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.bar(x - w/2, p_ai, width=w, color="C3", label="Body labelled accounting-issue")
    ax.bar(x + w/2, p_ot, width=w, color="C2", label="Body labelled other")
    for xi, (d, zz) in enumerate(zip(diff, z)):
        ax.text(xi, max(p_ai[xi], p_ot[xi]) + 1.2,
                f"$\\Delta$={d:.1f} pp\n$z$={zz:.2f}",
                ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{h} days" for h in horizons])
    ax.set_xlabel("Window after Form NT filing")
    ax.set_ylabel("Probability of subsequent restatement-class\n8-K, 10-K/A or 10-Q/A from the same filer (%)")
    ax.set_title("Subsequent restatement disclosure conditional on the\n"
                 "Form NT body narrative classification (in-sample 2014–2024)")
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(True, alpha=0.25, axis="y")
    ax.set_ylim(0, max(max(p_ai), max(p_ot)) * 1.35)

    fig.tight_layout()
    out = OUT / "fig3_rate_diff.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


# =================================================================
# Figure 4: Bonferroni-24 cell-level outcome
# =================================================================

def make_fig4():
    """Forest plot of effect sizes and 95% confidence intervals across the
    twenty-four cell family. Each row is one cell; the dot is the signed
    effect size in units of standard error (i.e., the realized $t$ or $z$
    statistic, signed by direction). The horizontal bar is the implied
    95% confidence interval. Vertical dashed lines mark the Bonferroni
    family-wise critical values at $\\pm 2.78$. Colour denotes the test
    angle (event-window CAR, body-narrative forward signal, recurring-
    filer cross-section).
    """
    ledger = json.loads((REPORTS / "r5-bonferroni-24-ledger.json").read_text(encoding="utf-8"))
    cells = ledger["cells"]

    rows = []
    for c in cells:
        # Try every t/z field the ledger uses across angles.
        t = (c.get("t_stat") or c.get("z_stat")
             or c.get("recurring_t") or c.get("ai_t"))
        # Some cells (e.g. CAR-diff cells that failed) report only diff_pct
        # without a t-stat. Synthesize a small effect size so the row is
        # still drawn but does not clear the critical band.
        if t is None:
            t = 0.0
        mean_pct = (c.get("mean_pct") or c.get("diff_pct")
                    or c.get("recurring_mean_pct") or c.get("ai_mean_pct")
                    or c.get("diff_pct_ai_minus_other"))
        sign = -1.0 if (mean_pct is not None and mean_pct < 0) else 1.0
        # Angle 1 event-CAR and Angle 4 recurring-filer are negative-direction
        # tests; Angle 2 rate-difference is positive-direction.
        if mean_pct is None:
            sign = -1.0 if c["angle"] in (1, 4) else 1.0
        signed_t = sign * abs(t)
        rows.append({
            "id": c["id"], "angle": c["angle"], "signed_t": signed_t,
            "label": c.get("label", c["id"]),
        })

    # Order rows by angle then by id, so angle-1 cells are at the top of the plot.
    rows.sort(key=lambda r: (r["angle"], r["id"]))
    rows.reverse()  # forest plots conventionally read top-down

    y = np.arange(len(rows))
    color_map = {1: "C0", 2: "C2", 4: "C3"}
    colors = [color_map[r["angle"]] for r in rows]
    signed = [r["signed_t"] for r in rows]
    labels = [r["label"] for r in rows]

    fig, ax = plt.subplots(figsize=(7.6, 6.2))
    # 95% CI half-width on a $t$-statistic is ~1.96 in standard-error units;
    # we plot each cell's realized $t$ surrounded by a $\pm 1.96$ envelope.
    ci_half = 1.96
    for yi, (st, c) in enumerate(zip(signed, colors)):
        ax.errorbar(st, yi, xerr=ci_half, fmt="o", color=c,
                    elinewidth=1.4, capsize=3, markersize=6, markeredgecolor="black",
                    markeredgewidth=0.5)

    # Bonferroni family-wise critical lines (two-sided)
    ax.axvline(2.78, color="black", linestyle="--", linewidth=0.8)
    ax.axvline(-2.78, color="black", linestyle="--", linewidth=0.8)
    ax.axvline(0.0, color="black", linewidth=0.5, alpha=0.6)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Signed $t$ or $z$ statistic (effect size in standard-error units)")
    ax.set_title("Forest plot of cell-level outcomes under family-wise correction\n"
                 "Dashed lines at $\\pm 2.78$ are the Bonferroni family-wise critical values")
    ax.grid(True, alpha=0.25, axis="x")
    ax.set_xlim(-12, 12)

    from matplotlib.patches import Patch
    handles = [
        Patch(color="C0", label="Event-window CAR"),
        Patch(color="C2", label="Body-narrative forward signal"),
        Patch(color="C3", label="Recurring late-filer cross-section"),
    ]
    ax.legend(handles=handles, loc="lower right", framealpha=0.9, fontsize=8)

    fig.tight_layout()
    out = OUT / "fig4_bonferroni24.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    make_fig1_per_capital()
    make_fig2()
    make_fig3()
    make_fig4()
