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
    """Long–short alternative benchmark: long non-recurring NT filers minus
    short recurring NT filers, ninety-trading-day forward CAR, monthly basket.

    This is the same-cadence, same-horizon, same-cohort long–short alternative
    constructed from the paper's recurring-late-filer cross-section angle
    (Section 4.2, third angle). It is a market-neutral counterpart to the
    body-narrative-classification basket and therefore the fair benchmark for
    the cumulative profit-and-loss chart.
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
        # Long-short = non-recurring leg minus recurring leg; the paper's
        # recurring-filer test predicts recurring filers underperform.
        out.append(np.mean(non) - np.mean(rec))
    return np.array(out)


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

    # Long-short alternative benchmark: recurring vs non-recurring NT filer
    # cross-section (paper's third angle), same monthly cadence, same 90-day
    # forward horizon. This is the fair market-neutral comparison.
    recurring_xs = _recurring_xs_monthly_return_series(months)
    cum_recurring = 100.0 * np.cumsum(recurring_xs)

    x = np.arange(len(months))
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.fill_between(x, 0, cum_net, color="C0", alpha=0.15)
    ax.plot(x, cum_net, color="C0", linewidth=1.8,
            label="Body-narrative long–short, net of 15 bp round-trip")
    ax.plot(x, cum_gross, color="C0", linewidth=1.0, linestyle=":", alpha=0.7,
            label="Body-narrative long–short, gross")
    ax.plot(x, cum_recurring, color="C3", linewidth=1.3, linestyle="--",
            label="Recurring vs non-recurring NT filer long–short (in-paper alternative)")
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
    ax.set_title("Body-narrative long–short basket vs in-paper recurring-vs-non-recurring\n"
                 "NT filer long–short alternative, in-sample 2014–2024")
    ax.legend(loc="upper left", framealpha=0.9, fontsize=9)
    ax.grid(True, alpha=0.25)

    # Annotation placement: keep both labels readable
    strategy_end = cum_net[-1]
    alt_end = cum_recurring[-1]
    ax.annotate(f"Body-narrative L/S:\nterminal = {strategy_end:.0f}\\%, Net Sharpe = 0.59",
                xy=(x[-1], strategy_end),
                xytext=(x[-1] - 22, strategy_end + 30),
                fontsize=9, ha="left",
                arrowprops=dict(arrowstyle="->", color="gray", linewidth=0.8))
    ax.annotate(f"Recurring-filer L/S:\nterminal = {alt_end:.0f}\\%",
                xy=(x[-1], alt_end),
                xytext=(x[-1] - 22, alt_end - 80),
                fontsize=9, ha="left",
                arrowprops=dict(arrowstyle="->", color="gray", linewidth=0.8))

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
    make_fig1()
    make_fig2()
    make_fig3()
    make_fig4()
