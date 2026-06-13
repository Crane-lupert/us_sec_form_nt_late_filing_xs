# V5 Sanity-Check Battery — Honest Revision of Headline Claims

**Date**: 2026-06-13
**Repo**: us_sec_form_nt_late_filing_xs
**Scope**: User-flagged "too good to be true" sanity audit on the
+31.5%/yr alpha, +540 pp cumulative, Sharpe 0.59 paper headline.
Eight checks run in parallel; two return CRITICAL flags requiring
headline-language adjustment in the next draft.

## §1 Eight checks

The eight checks were chosen to cover the dimensions that a JF/JFE referee
is most likely to probe for a paper reporting double-digit annualized
alpha at $T = 58$ months.

| # | Check | Method | Result |
|---|---|---|---|
| 1 | Effective leverage from overlapping positions | Monthly entry + 90-day hold ⇒ ~4.3 simultaneous positions per dollar of capital. Re-scale Sharpe under independence approximation | per-position SR 0.59 → **per-capital SR 0.29** |
| 2 | Capacity-aware sizing | Re-build basket with (a) equal-weight, (b) inverse-price, (c) price-floor filters, (d) price-weighted | Within-month 1/99 winsor + equal-weight → SR **0.23**; price-floor ≥ \$5 → SR 0.46; price-floor ≥ \$10 → SR 0.78 ($n = 13$ months only) |
| 4 | Survivorship at extraction layer | Compare label distribution between filings that survive to the final basket and filings dropped at the "no 90d CAR available" stage | **Dropped subset AI share 61.3% vs in-basket 52.3%; differential −8.9 pp** |
| 5 | Winsorization sensitivity | Re-run Sharpe at 0.5/99.5, 1/99 (paper), 2/98, hard truncation at ±100 pp and ±50 pp, no winsorization | Variants in the 1-2/99-98 band cluster around 0.55-0.59. **Truncation at ±100 pp → SR -0.33; truncation at ±50 pp → SR -0.04** |
| 7 | Deflated Sharpe Ratio at varying $n_{\text{trials}}$ | Re-deflate per Bailey–López de Prado at $n_{\text{trials}} \in \{8, 16, 32, 64, 128\}$ | $n_{\text{trials}} = 8$: DSR 0.99; $n_{\text{trials}} = 128$: DSR 0.90. Survives even aggressive trial inflation |
| 8 | Contamination audit | Redact firm name / ticker / CIK / dates / contacts from $n = 20$ narratives, re-classify, compare to original | **20/20 agreement after redaction** at \$0.0046 spend. Classifier does not rely on firm-specific retrieval |
| 9 | Annualization convention sensitivity | Re-annualize per-position alpha at $252 / 90 \approx 2.8$, monthly-compounding $12$, quarterly $4$ | $\alpha = +31.5\%$/yr (paper), $+134.9\%$/yr (monthly), $+45.0\%$/yr (quarterly) |
| 10 | Spanning regression: body-narrative L/S on recurring L/S | OLS with Newey-West HAC lag 6 | $\alpha_{\text{residual}} = 7.71\%$/mo, NW-SE 5.51, $t = 1.40$. $\beta_{\text{recurring}} = -0.06$ ($t = -0.63$, n.s.). $R^2 = 0.4\%$. **Recurring L/S has negligible explanatory power; body-narrative L/S marginal $\alpha$ is weak at conventional thresholds** |

Reports: `reports/sanity-check.json` (#1, #5, #7, #9, #10), `reports/capacity-sizing-check.json` (#2), `reports/survivorship-check.json` (#4), `reports/contamination-audit.json` (#8).

## §2 Critical flags

### §2.1 Effective leverage from overlapping positions (#1)

The paper's headline Sharpe ratio of $0.59$ is annualized using $252 / 90 \approx 2.8$ entry periods per year, which is appropriate *per position*: each monthly entry holds for ninety trading days and earns a per-position return whose realized series has annualized standard error $\sigma_{\text{position}} \cdot \sqrt{252 / 90}$. But a *deployed* basket on this strategy holds, on average, $90 / 21 \approx 4.29$ simultaneous positions per dollar of capital, because each new monthly entry overlaps with the prior three months of un-closed positions. Under an independence approximation the per-capital Sharpe is

$$
\text{SR}_{\text{capital}} \;\approx\; \frac{\text{SR}_{\text{position}}}{\sqrt{90 / 21}} \;=\; \frac{0.59}{\sqrt{4.29}} \;\approx\; 0.29.
$$

The exact per-capital Sharpe depends on the cross-position covariance, which the paper does not estimate. Under common factor exposure (Section 7 limit-to-arbitrage cohort, Section 5.7 SMB exposure with $\beta = 1.77$) the per-capital figure is bounded above by the per-position figure and below by the independence approximation. The right honest range is $0.29 \leq \text{SR}_{\text{capital}} \leq 0.59$, with the deployment-realistic mid-point near $0.35-0.40$.

**Action**: the paper's abstract and Section 5.2 numbers ($0.46$ calendar, $0.59$ acceptance-tradable) should be labeled "per-position Sharpe" with a one-sentence companion clarifying the per-capital range. The annualized alpha of $+31.5\%$/yr should likewise be labeled "per-position alpha"; per capital it is approximately $+15\%$/yr.

### §2.2 Winsorization-and-truncation sensitivity (#5)

The paper's winsorization rule is 1%/99% percentile capping applied globally on the pooled per-filing forward CAR. Variants in the 0.5--2% / 99.5--98% band cluster tightly:

| Variant | Sharpe (90d, per-position) |
|---|---:|
| 0.5/99.5 percentile cap | $0.54$ |
| 1/99 percentile cap (paper baseline) | $0.59$ |
| 2/98 percentile cap | $0.57$ |

This narrow band is reassuring under the standard winsorization framing. But under *hard truncation* — drop any observation whose absolute forward CAR exceeds the threshold — the Sharpe collapses:

| Variant | $n_{\text{months}}$ | Sharpe |
|---|---:|---:|
| Truncate \|CAR\| > 100 pp | $55$ | $-0.33$ |
| Truncate \|CAR\| > 50 pp | $54$ | $-0.04$ |
| No winsorization | $58$ | $0.23$ |

The reading is unambiguous: the strategy's Sharpe is driven by the upper tail of the forward CAR distribution. A small number of observations whose absolute forward CAR exceeds 100 percentage points (delisting-recovery winners, post-restatement bounce-backs) carry the realized profit. The 1/99 winsorization rule does not *remove* those observations — it caps their magnitude at the 99th-percentile value. Under hard truncation those observations are excluded entirely, and the Sharpe goes negative.

A reasonable JF/JFE referee will ask whether a strategy whose realized Sharpe disappears under tail-exclusion is a strategy at all. The honest answer is that the strategy's economic motivation — a body-narrative class that predicts subsequent restatement disclosure — is fundamentally a tail bet: the rare firms whose restatement materializes carry a large negative forward return that drives the L/S basket profit. The 1/99 winsorization keeps that tail at full-cap weight; hard truncation discards it.

**Action**: Section 6 Robustness should report the truncation sweep alongside the 0.5--2% / 99.5--98% winsorization sweep, and acknowledge that the strategy's Sharpe is tail-dependent in the precise sense that excluding the extreme observations destroys it. The economic reading is that this *is* the mechanism — late-filed accounting-issue firms eventually deliver a large negative return — not a defect to be hidden, but it should be reported transparently.

### §2.3 Selection bias at the extraction layer (#4)

The paper's in-sample basket excludes filings for which the 90-day forward CAR is unavailable. The drop-out tabulation:

| Stage | Count |
|---|---:|
| NYSE/Nasdaq-matched | 3,970 |
| Body extracted | 3,970 |
| Three-class label assigned | 3,959 (11 fail) |
| Reaches in-sample basket (90d CAR available) | 2,559 |

The 1,252 filings dropped at the "no 90d CAR" stage have an AI label share of $61.3\%$, against $52.3\%$ for the 2,559 filings that reach the basket. The differential of $-8.9$ percentage points is one-sided in the direction that biases the basket toward the *less-distressed* accounting-issue cohort, because the dropped subset is dominated by (i) the most recent in-sample filings whose 90-day forward window has not yet closed and (ii) firms whose CRSP ticker mapping fails to resolve at the analysis date. The latter class is in principle the most distressed: tickers fail to resolve when the firm has been deregistered or undergone a corporate action that severs the ticker–CIK link, which is exactly the outcome the body-narrative classification is supposed to predict.

**Action**: Section 8 Limitations should disclose this differential and acknowledge that the in-basket cohort is selected on the dependent variable in a non-trivial way. A natural follow-on is to back-fill the CRSP join via a manual CRSP–Compustat link upgrade and to re-extract the held-out 90-day window for filings within twelve months of the analysis date as additional months accumulate.

## §3 Clean checks

### §3.1 Deflated Sharpe Ratio (#7)

At $n_{\text{trials}} = 8$ (the paper's pre-specified family) DSR is $0.99$. Even at $n_{\text{trials}} = 128$ — a deliberately punitive inflation that bounds implicit trials from anchor changes, cohort splits, window changes, and weighting variants — DSR remains at $0.90$. The Sharpe-magnitude is not a multiple-testing artifact.

### §3.2 Contamination audit (#8)

Twenty stratified narratives (ten AI, ten other) are passed through the production extractor twice — once with the original narrative and once with firm name, ticker, CIK, all dates, all phone numbers, and all email addresses replaced with `[REDACT_*]` tokens. **All twenty agree after redaction**. The classifier does not retrieve firm-specific knowledge from its pre-training corpus; it reads the substantive accounting language of the narrative. This matches the Project X (sec-comment-letter-alpha) contamination audit at $\kappa = 1.000$ on $n = 50$ and is the cleanest possible result on this dimension.

The implication is that the vintage cross-rater $\kappa = 0.62$ on gpt-3.5-turbo (Section 6 vintage check) reflects classifier-quality variation between model generations rather than a vintage-leakage channel. The contemporary model is a better zero-shot reader of accounting language; it is not retrieving forward outcomes.

### §3.3 Annualization sensitivity (#9)

The paper's $252 / 90 \approx 2.8$ entry periods per year is the convention appropriate to a position-level Sharpe annualization. A naïve $12$-period annualization would inflate alpha to $+134.9\%$/yr; a quarterly $4$-period annualization gives $+45.0\%$/yr. The paper's convention is the correct one; alternative-convention citations should not be allowed to pass without clarifying which annualization the speaker has in mind.

### §3.4 Spanning regression (#10)

Body-narrative L/S regressed on recurring L/S yields $\alpha = 7.71\%$/mo with NW-SE $5.51$ and $t = 1.40$. The recurring L/S itself does not explain the body-narrative L/S ($\beta = -0.06$, $R^2 = 0.4\%$), but the body-narrative L/S's marginal alpha after orthogonalization against the recurring L/S falls below the conventional $t = 2$ threshold. The body-narrative classification adds essentially uncorrelated information, but the realized portfolio profit from that information is statistically borderline once the cohort split is removed.

**Action**: Section 7 Discussion should soften the strict "to my knowledge, the Form NT 10-Q cohort dominance ... has not been documented before" claim by noting that the recurring-vs-non-recurring split alone produces a long-short basket with a comparable cumulative profile, and that the body-narrative classification's marginal contribution is independent but not strongly significant in head-to-head spanning at the realized $T = 58$ sample size.

## §4 Required paper revisions

| Paper element | Current | Revised |
|---|---|---|
| Abstract Sharpe | "net Sharpe ratio of $0.59$" | "per-position net Sharpe ratio of $0.59$ ($\approx 0.29$ per dollar of capital under the four-overlapping-positions approximation)" |
| Abstract alpha | "$+31.5$ percentage points ($t = 2.14$)" | "$+31.5$ percentage points per-position ($t = 2.14$); per dollar of capital approximately $+15$ percentage points" |
| Section 5.2 Sharpe | "$0.46$ ... $0.59$" | Same numbers, label as "per-position" and add per-capital companion |
| Section 5.7 alpha | "$+31.5\%$/yr ($t = 2.14$)" | Same number, label as "per-position" and add per-capital companion |
| Section 6 Robustness | TC sensitivity, schema, body-length, sub-sample | Add winsorization-and-truncation sweep with the $\pm 100$ pp truncation result |
| Section 7 Discussion | "to my knowledge ... cohort dominance ... has not been documented before" | Soften to "the body-narrative classification's marginal alpha after orthogonalization against the recurring-vs-non-recurring split is at $t = 1.40$, statistically borderline" |
| Section 8 Limitations | Coverage gap, LLM vintage, CAR-diff null, NT 10-Q dominant, recurring borrow | Add explicit selection-bias paragraph on the $1{,}252$-filing drop with $-8.9$ pp AI-share differential |
| Section 8 Limitations | (not currently present) | Add explicit tail-dependence acknowledgement: the strategy's Sharpe disappears under hard truncation at $\pm 100$ pp |

## §5 What the audit does *not* change

The four findings in the paper's Introduction stand under the audit:

1. Body-narrative forward signal at $z = 5.61$ in-sample and $z = 2.83$ held-out — unaffected by leverage, capacity, winsorization, or selection-bias concerns. The signal is a contingency-table statistic on the rate of subsequent restatement disclosure, not a portfolio Sharpe.
2. Form NT 10-Q cohort dominance at $z = 6.77$ vs $z = 0.50$ on Form NT 10-K — unaffected.
3. Institutional fact that $63.5\%$ of in-sample filings clear the SEC's intake queue after the market close — unaffected.
4. Free-tier delisting-return artifact — unaffected.

What the audit *does* change is the portfolio-construction claims attached to Finding 3. The Sharpe lift from $0.46$ to $0.59$ under acceptance-tradable anchoring remains the in-paper measurement, but the deployment-relevant *per-capital* Sharpe is materially lower, the strategy is tail-dependent in the precise winsorization-vs-truncation sense, and the in-basket cohort is selected on the dependent variable through the 32% drop at the 90-day-CAR-availability stage.

## §6 Cross-reference

- Paper draft: `analysis/paper_v2_en.md` (current commit chain `ab5d409`).
- Paper-writing-lessons portable checklist: `D:/vscode/meta-harness/audits/2026-06-02-X-paper-writing-lessons-portable-checklist.md` — this audit is a candidate addendum (a "sanity check" sub-section in §14 V5 addenda) once the revisions are in.
- The contamination audit pattern is the same as Project X's `data/contamination_audit_summary.json` reference.
- The per-capital-vs-per-position Sharpe convention is the right convention for any overlapping-position strategy and is a candidate addition to §14 V5 addenda.
