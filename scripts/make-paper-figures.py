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

def make_fig1():
    """Cumulative excess-return chart. Each month-end we record the realized
    ninety-trading-day excess return of the long–short basket; the chart
    plots the running sum of those monthly excess returns, in percentage
    points. The chart therefore reflects the strategy's monthly excess
    earnings on a per-position-dollar basis, without rebalancing-frequency
    overlap distortions that would arise from compounding monthly entries
    whose holding period extends ninety days. The annualized mean and
    annualized standard deviation in the title are computed at the
    correct 252 / 90 ≈ 2.8 periods-per-year factor.
    """
    rows = [json.loads(l) for l in (DATA / "net_sharpe_strategy_d_pit.jsonl").open(encoding="utf-8")]
    rows_90 = sorted([r for r in rows if r["window_days"] == 90], key=lambda r: r["year_month"])
    months = [r["year_month"] for r in rows_90]
    gross_monthly = np.array([r["long_short_pct"] / 100.0 for r in rows_90])
    tc = 15 / 10000  # 15 bps round-trip per entry
    net_monthly = gross_monthly - tc

    cum_net = 100.0 * np.cumsum(net_monthly)        # cumulative percentage points
    cum_gross = 100.0 * np.cumsum(gross_monthly)

    x = np.arange(len(months))
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.fill_between(x, 0, cum_net, color="C0", alpha=0.15)
    ax.plot(x, cum_net, color="C0", linewidth=1.8,
            label="Long–short basket, net of 15 bp round-trip")
    ax.plot(x, cum_gross, color="C0", linewidth=1.0, linestyle=":", alpha=0.7,
            label="Long–short basket, gross")
    ax.axhline(0.0, color="black", linewidth=0.6, alpha=0.4)

    # X-axis: one tick per calendar year (the first month appearing in that year)
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
    ax.set_ylabel("Cumulative excess return (\\%)")
    ax.set_title("Long–short basket on Form NT body-narrative classification\n"
                 "Acceptance-tradable anchor, 90-day holding horizon, 2014–2024")
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(True, alpha=0.25)

    # Annotation: net Sharpe summary, anchored on the last point
    ax.annotate(f"Net Sharpe = 0.59\nAnn. mean = 25.8\\%",
                xy=(x[-1], cum_net[-1]),
                xytext=(x[-1] - 18, cum_net[-1] + 80),
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
    ledger = json.loads((REPORTS / "r5-bonferroni-24-ledger.json").read_text(encoding="utf-8"))
    cells = ledger["cells"]

    # X-axis: cell ID; Y-axis: |t| or |z|; bar color by angle
    ids = []
    tstats = []
    angles = []
    pass_flags = []
    for c in cells:
        ids.append(c["id"])
        # Different angles use different metrics
        t = c.get("t_stat")
        if t is None:
            t = c.get("z_stat")
        tstats.append(abs(t) if t is not None else 0)
        angles.append(c["angle"])
        pass_flags.append(c.get("bonferroni12_PASS", False) and c.get("v5_direction_PASS", False))

    color_map = {1: "C0", 2: "C2", 4: "C3"}   # angle 4 stays internal here
    colors = [color_map[a] for a in angles]
    hatches = ["" if p else "//" for p in pass_flags]

    x = np.arange(len(ids))
    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    for xi, (cid, t, c, h) in enumerate(zip(ids, tstats, colors, hatches)):
        ax.bar(xi, t, color=c, hatch=h, edgecolor="black", linewidth=0.4)
    ax.axhline(2.78, color="black", linestyle="--", linewidth=0.8,
               label="Family-wise critical value = 2.78")
    ax.set_xticks(x)
    ax.set_xticklabels(ids, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("|t-statistic|  or  |z-statistic|")
    ax.set_title("Cell-level outcome under family-wise correction over 24 specifications\n"
                 "(Light hatch = fails direction or magnitude)")
    # Legend: angle colors + critical line
    from matplotlib.patches import Patch
    handles = [
        Patch(color="C0", label="Event-window CAR (Bartov–Konchitchki replication)"),
        Patch(color="C2", label="LLM body-narrative forward signal"),
        Patch(color="C3", label="Recurring late-filer cross-section"),
    ]
    handles.append(plt.Line2D([0], [0], color="black", linestyle="--", label="Critical value 2.78"))
    ax.legend(handles=handles, loc="upper right", framealpha=0.9, fontsize=8)
    ax.grid(True, alpha=0.25, axis="y")

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
