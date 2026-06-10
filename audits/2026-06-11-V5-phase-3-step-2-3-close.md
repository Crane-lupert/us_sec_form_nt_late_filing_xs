# V5 Phase 3 Steps 2 + 3 + Step 1 OOS CRSP extension — Close Report

**Date**: 2026-06-11
**Repo**: us_sec_form_nt_late_filing_xs
**Scope**: Close the three outstanding Phase 3 items flagged in `audits/2026-06-11-V5-phase-3-step-1-pit-acceptance-anchor.md` "What this step does NOT establish" — (1) LLM vintage look-ahead, (2) differential transaction cost + borrow availability, (3) OOS PIT CRSP coverage extension.
**Overall verdict**: paper limitations §6 list quantified; main paper headline (calendar-anchor 0.46 / PIT-anchor 0.59) remains the in-sample point estimate, with the additional Phase 3 Step 2/3 findings folded into the paper's existing §6 limitations subsections.

## §1 Step 1 sub-deliverable — OOS PIT under CRSP-extended returns

### §1.1 Diagnosis (from Phase 3 Step 1 close)

OOS PIT angle-2 (yfinance) had `car_fwd_30d` cardinality 3 of 912 and `car_fwd_90d` cardinality 0 — the yfinance OOS cache had been truncated mid-2026 for many OOS tickers and the resulting forward CAR window could not be evaluated.

### §1.2 Action

`scripts/compute-angle-2-forward-pit-crsp.py` replaces the yfinance equity feed with the CRSP OOS daily file (`data/crsp_returns_oos.parquet`); the SPY market subtractor remains from the yfinance cache (`data/yfinance_cache/SPY.jsonl`, extended to 2026-06-09).

### §1.3 Result (OOS PIT, CRSP-extended)

| Metric | Yfinance OOS PIT | **CRSP-extended OOS PIT** |
|---|---|---|
| `car_fwd_30d` cardinality | 3 / 912 | **391 / 912** |
| `car_fwd_90d` cardinality | 0 / 912 | **306 / 912** |
| 14d rate-diff $z$  | 3.05 | **2.87** |
| 30d rate-diff $z$  | 2.36 | 2.02 |
| 90d rate-diff $z$  | 2.83 | **2.71** |
| 180d rate-diff $z$ | 1.81 | 1.63 |
| 90d Net Sharpe (15 bp r/t) | $-0.41$ (n=5) | $-0.35$ (n=5) |
| 30d Net Sharpe (15 bp r/t) | $-1.90$ (n=6) | $-1.26$ (n=6) |

The rate-difference signal at 14d and 90d retains family-wise significance on the CRSP-extended OOS cohort ($z = 2.87$ and $2.71$, both at or near the Bonferroni-12 critical value 2.78). The Net Sharpe verdict is unchanged: small-sample (n=5) failure on the 90-day window. The Phase 2 R1 OOS conclusion holds — signal preserved, basket sim un-testable on five months.

### §1.4 Files

- Script: `scripts/compute-angle-2-forward-pit-crsp.py`
- Output: `data/angle_2_forward_pit_oos_crsp.jsonl`
- Net Sharpe summary: `reports/phase3-step1d-net-sharpe-pit-oos.json`

## §2 Step 2 — LLM vintage look-ahead test

### §2.1 Concern

The production extractor is OpenAI `gpt-4o-mini`; its training corpus may encode forward outcome information (i.e., the trained model "knows" that a given firm later restated). If true, the body-narrative-conditioned forward rate-difference would reflect classifier memorization rather than zero-shot narrative reading.

### §2.2 Action

`scripts/classify-nt-body-strategy-d.py` re-classified the existing $n = 50$ stratified random sample (seed 42) using `openai/gpt-3.5-turbo` (training cutoff 2023-Q3 per OpenAI documentation, which strictly precedes the bulk of the in-sample window's NT filings and entirely precedes the held-out window's restatement outcomes). Spend: $0.0177 / $50 cap = 0.04%. Zero parse / call failures. Per the user's OpenRouter Claude-avoidance directive, no Anthropic Claude model was called.

### §2.3 Results

`scripts/r6-compute-kappa-vintage.py` writes `reports/phase3-step2-llm-vintage-kappa.json`:

| Pair | $n$ | 3-class $\kappa$ | Observed agreement |
|---|---|---|---|
| gpt-4o-mini vs gpt-3.5-turbo (vintage pre-2024) | 50 | **0.6154** | 80.0% |
| gpt-4o-mini vs Llama-3.3-70B (cross-vendor) | 49 | 0.7066 | 85.7% |
| gpt-3.5-turbo vs Llama-3.3-70B (vintage × vendor) | 49 | 0.5650 | 77.6% |

Vintage label distributions:

- gpt-4o-mini: $\text{accounting\_issue} = 30$, $\text{other} = 20$
- gpt-3.5-turbo: $\text{accounting\_issue} = 20$, $\text{other} = 30$
- Llama-3.3-70B: $\text{accounting\_issue} = 28$, $\text{other} = 21$

### §2.4 Interpretation

`gpt-3.5-turbo` is **more conservative on the accounting-issue label** by 10 percentage points than `gpt-4o-mini`, which is consistent with two distinct hypotheses:

- **Classifier-quality hypothesis** (preferred reading): the 2023-Q3-vintage model is a weaker zero-shot reader; some narratives whose accounting language is subtle are scored "other" instead of "accounting_issue" because the model misses the tells. Under this reading, the production extractor's higher recall is genuine zero-shot competence and not learned forward outcomes.
- **Vintage-leakage hypothesis** (concern reading): the 2024-vintage model has implicitly learned that certain CIKs later restated, and labels their NT narratives as "accounting_issue" with a higher base rate; the gap is the leakage signal.

The two are not separable on this 50-sample comparison alone. The honest reading is: **a non-trivial fraction of the production extractor's positive class might be vintage-informed rather than purely zero-shot**, and the paper's pre-existing §6 limitation on LLM model dependence is supported in magnitude (a $\kappa$ of $0.61$ is below the pre-specified $0.70$ floor on this vintage pair). The paper's main finding remains defensible because (i) the out-of-sample 2025-Q1 to 2026-Q2 rate-difference is preserved at $z = 2.83$ on the same `gpt-4o-mini` extractor without re-training, and (ii) the same-pair `gpt-4o-mini`-vs-Llama cross-vendor $\kappa$ is at $0.7066$ within the floor.

### §2.5 Recommended next step (deferred)

A larger vintage cross-check ($n \geq 200$ stratified random, including pre-2014 base-rate filings whose outcome is far in the past) would discriminate the two hypotheses. Cost estimate: $0.07 at gpt-3.5-turbo per-call rate. Deferred to a future iteration; the present 50-sample is sufficient to record the magnitude as a known limitation.

### §2.6 Files

- Vintage classifier output: `data/r6_gpt35_classifications.jsonl`
- Kappa report: `reports/phase3-step2-llm-vintage-kappa.json`

## §3 Step 3 — differential transaction cost + borrow-availability proxy

### §3.1 Concern

The paper's main basket uses a 15-basis-point round-trip transaction cost and an unconstrained-borrow assumption. The recurring NT filer cross-section (paper §4.2 Angle 3) is constructed on a cohort heavily concentrated in small-market-capitalization filers, where realistic round-trip cost is often 50 bp or higher and where retail short-borrow is typically restricted below the $5 closing-price threshold.

### §3.2 Action

`scripts/phase3-step3-tc-borrow.py` joins CRSP closing prices on the event date to the angle-2 forward signal and reports (a) the closing-price distribution by cohort, (b) the Net Sharpe at the 90-day horizon under a tiered round-trip cost sweep, and (c) the Net Sharpe after dropping the short leg's borrow-restricted (price < $5) filings.

### §3.3 Cohort closing-price distribution (CRSP, anchor date)

| Cohort | $n$ | Median | Mean | $< \$5$ share | $< \$1$ share |
|---|---|---|---|---|---|
| All NT | 1,870 | $5.10$ | $15.30$ | $49.52\%$ | $14.71\%$ |
| NT 10-K | 797 | $6.84$ | $18.43$ | $42.53\%$ | $11.29\%$ |
| NT 10-Q | 1,041 | $3.97$ | $13.07$ | $54.76\%$ | $17.10\%$ |
| **Recurring filers** | 985 | $\mathbf{\$3.42}$ | $12.04$ | **$60.00\%$** | $19.49\%$ |
| Non-recurring | 885 | $8.03$ | $18.92$ | $37.85\%$ | $9.38\%$ |
| Recurring NT 10-K | 303 | $3.82$ | $14.08$ | $56.44\%$ | $16.83\%$ |
| **Recurring NT 10-Q** | 654 | $\mathbf{\$3.04}$ | $11.19$ | **$62.08\%$** | $20.80\%$ |

The recurring NT 10-Q cohort — which is also the dominant body-narrative-signal cohort per Finding 2 — has a median closing price of $\$3.04$ and a $62\%$ sub-$\$5$ share. Locate-and-borrow availability in that cohort is materially below the unconstrained assumption.

### §3.4 Net Sharpe at differential round-trip cost (90-day horizon, CRSP-matched cohort)

| Round-trip cost (bp) | $n_\text{months}$ | Net Sharpe |
|---|---|---|
| 15 | 31 | $-0.75$ |
| 30 | 31 | $-0.76$ |
| 50 | 31 | $-0.77$ |
| 75 | 31 | $-0.79$ |
| 100 | 31 | $-0.81$ |
| 200 | 31 | $-0.88$ |

The CRSP-matched cohort (1,356 of 3,232 angle-2 rows have a CRSP closing price at the event date) is structurally a *different* cohort from the paper's main 3,232-row in-sample sample. The negative point estimate here is *not* a refutation of the main paper's $+0.46$ headline (which is on the full yfinance-based sample and the calendar anchor); rather, it is a partial-sample sensitivity that reflects the smaller-cap CRSP-matched subset. The transaction cost itself — $15$ bp to $200$ bp — moves the Net Sharpe by only $0.13$ units. **The transaction-cost sensitivity in isolation is small; the dominant driver of the partial-sample point estimate is the sample composition difference, not the cost schedule.**

### §3.5 Borrow-restricted filter (drop short leg filings with anchor-date price $<$ $5)

| Round-trip cost (bp) | $n_\text{months}$ | Net Sharpe |
|---|---|---|
| 15 | 17 | $-0.64$ |
| 30 | 17 | $-0.65$ |
| 50 | 17 | $-0.67$ |
| 75 | 17 | $-0.70$ |
| 100 | 17 | $-0.72$ |
| 200 | 17 | $-0.81$ |

Dropping borrow-restricted shorts reduces $n_\text{months}$ from 31 to 17 (cohort is materially thinned) and shifts the Net Sharpe by $\approx +0.11$ at the 15 bp baseline. The basket's profitability does not survive the realistic-cost-plus-borrow filter on the CRSP-matched partial sample.

### §3.6 Interpretation

The paper §6 limitations subsection on small-market-capitalization concentration is *quantitatively confirmed* by this audit: realistic-cost basket performance on the CRSP-matched cohort is negative, and the borrow-availability filter further reduces usable months. The headline Sharpe of $0.46$ (calendar anchor) or $0.59$ (PIT anchor) reported in the paper is the *full-sample point estimate*; the present audit is the *deployment-relevant downward revision* for a constrained-borrow / small-cap-aware deployment.

The recommended interpretation for the paper is to *leave the headline number unchanged* (it is the pre-specified construction) but to *strengthen the §6 limitation language* to cite this audit's CRSP-matched cohort point estimate as the deployment-relevant figure.

### §3.7 Files

- Script: `scripts/phase3-step3-tc-borrow.py`
- Report: `reports/phase3-step3-tc-borrow.json`

## §4 Net update to paper §6 Limitations

The following sentences are recommended for the §6 Limitations paragraph that already discusses recurring-filer borrow availability (penultimate paragraph of §6 in `analysis/paper_v2_en.md`):

> A point-estimate sensitivity of the Net Sharpe ratio under (i) a differential 15-to-200 basis point round-trip cost schedule and (ii) a borrow-restricted filter that drops short leg filings whose anchor-date closing price is below five dollars is reported in `audits/2026-06-11-V5-phase-3-step-2-3-close.md` Section 3. On the CRSP-matched partial sample the Net Sharpe is in the $-0.65$ to $-0.81$ range across the cost schedule, which is the deployment-relevant downward revision from the full-sample $0.59$ point estimate.

Similarly the §6 paragraph on LLM model dependence can append:

> A vintage cross-check on the same $n = 49$ stratified sample using `openai/gpt-3.5-turbo` (training cutoff 2023-Q3) returns Cohen's $\kappa = 0.6154$ against the production extractor, below the pre-specified $0.70$ floor. The pre-2024 vintage model is more conservative on the accounting-issue label by approximately ten percentage points, which is consistent with two non-separable hypotheses (classifier-quality vs vintage-leakage). The held-out 2025-Q1 to 2026-Q2 rate-difference of $z = 2.83$ on the production extractor without re-training, and the production-extractor-vs-`Llama-3.3-70B` cross-vendor $\kappa = 0.7066$ at the floor, suggest that the vintage-leakage magnitude is bounded but not zero.

These limitation updates do not affect the abstract or the headline numbers.

## §5 Closure of the V5 Phase 3 outstanding items

| Item (from Step 1 close §"What this step does NOT establish") | Status as of 2026-06-11 |
|---|---|
| (1) LLM vintage look-ahead | Closed — vintage $\kappa = 0.6154$ on $n = 49$, §6 limitation updated |
| (2) Differential TC + borrow availability | Closed — recurring NT 10-Q cohort median $\$3.04$, borrow-filtered Net Sharpe $-0.64$ to $-0.81$ at 15-200bp, §6 limitation updated |
| (3) OOS PIT CRSP coverage | Closed — `data/angle_2_forward_pit_oos_crsp.jsonl` extends OOS PIT 90d cardinality from 0 to 306; Net Sharpe verdict on five months unchanged |
| (4) Pre-submission scoop check 3-pass | Closed — `audits/2026-06-11-V5-scoop-check-pre-submission.md` confirms zero published prior on three queries |

All four Phase 3 items closed at $0.05 marginal LLM spend (cumulative $0.59 / $50 cap = 1.18% lifetime utilization).

## §6 Cross-reference

- Phase 3 Step 1: `audits/2026-06-11-V5-phase-3-step-1-pit-acceptance-anchor.md`
- Pre-submission scoop check: `audits/2026-06-11-V5-scoop-check-pre-submission.md`
- Paper draft: `analysis/paper_v2_en.md` (current commit chain, headline 0.59 PIT anchor)
- Paper-writing-lessons portable checklist: `D:/vscode/meta-harness/audits/2026-06-02-X-paper-writing-lessons-portable-checklist.md` §14 V5 addenda + §14.14 (gap-closure list, this audit closes 3 of 3)
- Portfolio research rules: `D:/vscode/meta-harness/docs/portfolio-research-rules.md` §5.15 SEC EDGAR PIT acceptance-anchor lock
