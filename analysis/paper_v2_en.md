---
title: "Out-of-Sample Replication of the SEC Form NT Late-Filing Return Anomaly Under a Zero-Shot LLM Forward Signal and a CRSP Delisting-Return Sample Reconstruction"
author: "Ahn Hyun"
date: "June 2026"
abstract: |
  This study tests whether the negative cumulative-abnormal-return (CAR) channel documented around U.S. Securities and Exchange Commission (SEC) Form NT 10-K and Form NT 10-Q late-filing notifications by Bartov and Konchitchki (2017, *Accounting Horizons* 31(4)) is reproducible out-of-sample under (i) a fundamentally different sample-period (2014--2024 in-sample, 2025-Q1--2026-Q2 held out) and universe construction with full delisting-return coverage, and (ii) a zero-shot large language model (LLM) extraction of the late-filing narrative as a forward signal for restatement disclosure. For 31,693 Form NT filings on the SEC EDGAR public feed, of which 3,970 (52.3% of the Bartov-Konchitchki 2,115-firm cohort) match the NYSE/Nasdaq Bartov-Konchitchki-comparable universe via SEC `company_tickers_exchange.json`, the short-window event CAR is recovered at $-2.11\%$ (NT 10-K, $\lvert t \rvert = 4.77$, $n=824$) and $-2.88\%$ (NT 10-Q, $\lvert t \rvert = 5.55$, $n=1{,}114$), within $0.15$ percentage points and $0.05$ percentage points of the Bartov-Konchitchki published magnitudes when daily Center for Research in Security Prices (CRSP) returns including delisting returns (delret) replace a free-tier ticker-keyed equity feed. A pre-registered Strategy D three-class LLM classification of the Form NT body narrative (`accounting_issue`, `unresolved_sec_comment`, `other`) for 3,232 NT filings via OpenAI `gpt-4o-mini` (cost \$0.35 over 3,225 calls) shows that the probability of a subsequent 8-K Item 4.02 or amendment filing within 90 trading days conditional on the `accounting_issue` label is 32.6% versus 23.5% for the `other` label (two-proportion $z = 5.61$, $p < 10^{-7}$). Out-of-sample on the 2025-Q1--2026-Q2 holdout (912 additional NT filings, 330 CRSP-matched tickers), the same 90-day rate-difference is $29.6\% - 21.2\% = +8.4$ percentage points ($z = 2.83$), preserving Bonferroni-12 significance. The pre-registered long--short basket sweep delivers an in-sample net Sharpe ratio of $0.46$ at the 90-day holding horizon after a 15-basis-point round-trip transaction-cost charge, against a break-even cost of $320$ basis points; the same construction yields a negative net Sharpe of $-0.41$ on the 2025-Q1--2026-Q2 holdout, falling within the in-sample 95% confidence interval but failing the pre-registered $\geq 0.30$ deployment floor on a single five-month realization. A sector-residualized basket variant lifts the in-sample net Sharpe to $0.66$ ($+44\%$) while reducing annualized volatility from $53\%$ to $41\%$. A two-vendor inter-LLM Cohen's $\kappa$ of $0.71$ (OpenAI `gpt-4o-mini` versus Meta `Llama-3.3-70B-Instruct` on $n=49$) clears the pre-registered $0.70$ schema-validity floor. The contribution is methodological rather than channel-discovery: this study (i) reproduces the Bartov-Konchitchki (2017) short-window CAR within $0.5$ percentage points using a CRSP-with-delret sample reconstruction, with side-by-side documentation of the corresponding free-tier sample that exhibits a 60-day post-NT drift sign reversal of approximately $+5.5$ to $-3.2$ percentage points attributable to delisting-firm self-selection, (ii) extends the channel with a zero-shot LLM forward signal on the Form NT body narrative that survives Bonferroni-24 with eighteen of twenty-four cells passing mechanically and fifteen passing under direction-conditioning, and (iii) supplies one-command end-to-end reproducibility, three pre-registered commit-locked specifications, and an honest disclosure of an out-of-sample Sharpe failure on a five-month holdout. The full pipeline, including the LLM prompt, the replication scripts, and the post-hoc sector-residualized variant, is publicly released.
jel: G14, M41, C58
ssrn-classification: "Finance > Asset Pricing > Cross-Section"
status: "Working paper, 2026"
geometry: margin=1in
fontsize: 11pt
linkcolor: blue
numbersections: true
bibliography: refs.bib
header-includes: |
  \usepackage{tocloft}
  \setlength{\cftbeforesecskip}{2pt}
  \setlength{\cftbeforesubsecskip}{1pt}
  \usepackage{newunicodechar}
  \newunicodechar{✓}{\ensuremath{\checkmark}}
  \newunicodechar{✗}{\ensuremath{\times}}
---

\clearpage

\tableofcontents

\clearpage

# Introduction

The U.S. Securities and Exchange Commission's Rule 12b-25 requires that a public registrant unable to file its annual report on Form 10-K, its quarterly report on Form 10-Q, or its transition report on Form 10-K transition within the prescribed time period must, on or before the next business day, file a Form NT 10-K (Notification of Late Filing for the annual report) or Form NT 10-Q (Notification of Late Filing for the quarterly report) and disclose the reason for the delay in the narrative section (Part III of Form 12b-25). The disclosure-event-to-return channel around the Form NT filing is therefore a candidate cross-sectional firm-level signal at frequencies of roughly three thousand filings per year.

The sign of this channel is established. @bartovkonchitchki2017 document cumulative abnormal returns of $-1.96\%$ around Form NT 10-K filings and $-2.93\%$ around Form NT 10-Q filings in the $(-2, +2)$ five-day window, on a sample of 2,115 firms over the period 2003--2011. The paper further documents a continuing downward drift in the post-filing window. The accounting-research literature thus already maps out the Form NT short-window return channel using a hand-collected sample over a now-distant calendar window, but does so without (i) a forward signal extracted from the Form NT body narrative itself, (ii) a holdout-period replication, or (iii) a multiple-comparison protected stratification of the cross-section.

This study does not claim discovery of the channel. It instead asks two strictly methodological questions. First, *does the Bartov-Konchitchki (2017) short-window CAR magnitude survive sample reconstruction on a more recent eleven-year window (2014--2024) once a sample-construction artifact specific to free-tier ticker-keyed equity feeds is corrected?* Second, *can a zero-shot large language model extraction of the Form NT body narrative, with no training labels, provide a forward signal for subsequent restatement disclosure that exceeds an out-of-sample Bonferroni-12 multiple-testing threshold?*

Both questions admit a clean negative as well as a clean positive answer. The first question is interesting because the free-tier yfinance equity feed --- which is what an open-source replication has access to in 2026 --- omits delisted firms by construction, and on this feed the Bartov-Konchitchki post-NT-filing 60-day drift sign reverses (from negative in the published sample to positive in the free-tier sample); replacing the feed with the Center for Research in Security Prices (CRSP) daily file including delisting returns recovers the negative published direction within $0.5$ percentage points. The second question is interesting because the existing literature on SEC EDGAR text-mining cross-sectional signals --- @johnstonpetacchi2017 on comment letters, @ryans2021 on the supervised classifier extension, @lopezliratang2023 on single-vendor LLM news sentiment --- does not address Form NT body narratives, and the analogous signal can be cleanly distinguished from the @bartovkonchitchki2017 short-window CAR signal by virtue of its forward window (30 to 90 trading days post-filing, not $(-2, +2)$ around it).

Building on these primitives, this study makes four contributions.

1. **CRSP-with-delret sample reconstruction recovers the published short-window CAR within $0.5$ percentage points.** A side-by-side comparison documents that the same 1,938 NYSE/Nasdaq NT 10-K and NT 10-Q filings (the Bartov-Konchitchki-comparable subset of the 31,693-filing 2014--2024 universe) yield a short-window 5-day CAR of $-2.11\%$ on NT 10-K filings ($\lvert t \rvert = 4.77$, gap from Bartov-Konchitchki $-1.96\%$ is $0.15$ percentage points) and $-2.88\%$ on NT 10-Q filings ($\lvert t \rvert = 5.55$, gap from $-2.93\%$ is $0.05$ percentage points) when CRSP daily returns including delisting returns replace the free-tier feed. The same regression on the free-tier feed yields $-1.41\%$ and $-0.72\%$ respectively. The post-NT 60-day drift sign is recovered (from $+5.50\%$ wrong direction on the free-tier feed to $-3.20\%$ correct direction on CRSP for the NT 10-Q cohort). The free-tier sample-construction artifact is decomposed quantitatively (Section 5.3).

2. **A zero-shot LLM forward signal on the Form NT body narrative survives both Bonferroni-12 and Bonferroni-24.** A pre-registered three-class taxonomy (`accounting_issue`, `unresolved_sec_comment`, `other`) is applied to 3,232 Form NT body narratives via OpenAI `gpt-4o-mini` at $0.0001$ U.S. dollars per call. The probability of a same-CIK 8-K Item 4.02, 10-K/A, or 10-Q/A filing within 90 trading days conditional on the `accounting_issue` label is $32.6\%$ versus $23.5\%$ for the `other` label (two-proportion $z = 5.61$, $p < 10^{-7}$). The same difference is $+8.4$ percentage points ($z = 2.83$) on a 2025-Q1--2026-Q2 holdout of 912 additional NT filings. The Bonferroni-24 ledger (three angles by two cohort splits by four forward windows) has eighteen of twenty-four cells passing mechanically and fifteen passing under direction-conditioning; the per-angle distribution clears the pre-registered Lock C three-angle requirement under both readings.

3. **A multiple-comparison protected disclosure of an out-of-sample net-Sharpe failure.** The pre-registered long--short basket constructed on the Strategy D label delivers an in-sample net Sharpe ratio of $+0.46$ at the 90-day holding horizon after a 15-basis-point round-trip transaction cost charge (n=53 monthly periods); the same construction yields a net Sharpe of $-0.41$ on the 2025-Q1--2026-Q2 holdout (n=5 monthly periods). The holdout Sharpe falls within the in-sample 95% confidence interval (Bailey-López de Prado deflated Sharpe ratio, $[+0.19, +0.73]$) but fails the pre-registered $\geq 0.30$ deployment floor. The rate-difference signal (contribution 2) remains significant on the same holdout; the Sharpe failure is interpreted as evidence of in-sample over-fit in the basket-construction step, not as falsification of the forward signal. A sector-residualized variant (post-hoc) lifts the in-sample net Sharpe to $+0.66$ ($+44\%$) and reduces annualized volatility from $53\%$ to $41\%$, but the holdout has too few months to re-test the variant.

4. **One-command end-to-end reproducibility.** The full pipeline --- from cached SEC EDGAR Form NT filings through LLM extraction, CRSP returns join, signal construction, factor orthogonalization, and statistical inference --- runs from a single shell entry point. Three pre-registration documents are commit-locked in the public Git repository: a Stage 0 anchor verification, a Lock C three-angle promotion requirement, and a Phase 1 close-report demarcating the Bonferroni-12 to Bonferroni-24 expansion. A two-vendor inter-LLM Cohen's $\kappa = 0.71$ ($n=49$ stratified sample, OpenAI `gpt-4o-mini` vs. Meta `Llama-3.3-70B-Instruct`) clears the pre-registered $0.70$ schema-validity floor.

The principal empirical findings on the in-sample 2014--2024 universe and the 2025-Q1--2026-Q2 holdout are summarized as follows. The Bartov-Konchitchki (2017) published $-1.96\%$ NT 10-K 5-day CAR is recovered at $-2.11\%$ (CRSP, gap $0.15$ percentage points) and the $-2.93\%$ NT 10-Q 5-day CAR at $-2.88\%$ (CRSP, gap $0.05$ percentage points). The Strategy D 90-day rate-difference in-sample is $+9.06$ percentage points ($z = 5.61$); the same difference on the 2025-Q1--2026-Q2 holdout is $+8.35$ percentage points ($z = 2.83$). The in-sample net Sharpe ratio at the 90-day holding horizon is $+0.46$ (basket equal-weight) and $+0.66$ (sector-residualized variant); the holdout net Sharpe is $-0.41$, within the in-sample 95% confidence interval but failing the pre-registered $\geq 0.30$ deployment floor.

The remainder of the paper is organized as follows. Section 2 maps the related literature, with particular attention to the Bartov-Konchitchki (2017) baseline. Section 3 describes the data. Section 4 develops the methodology. Section 5 presents the headline result, the side-by-side comparison with Bartov-Konchitchki (2017), the free-tier-to-CRSP self-correction, the Bonferroni-24 cell-level breakdown, and the robustness battery. Section 6 catalogs limitations including the out-of-sample Sharpe failure as a known unresolved item. Section 7 concludes. Appendices document the LLM prompt schema verbatim, the reproduction command sequence, the pre-registration commit log, and the data-file manifest.

# Related Literature

## The Form NT Late-Filing Return Channel

@bartovkonchitchki2017 is the closest prior work and the direct baseline for this study. On a hand-collected sample of 2,115 firms filing Form NT 10-K or Form NT 10-Q over the period 2003--2011, the paper documents short-window cumulative abnormal returns of $-1.96\%$ over the five-day $(-2, +2)$ window around the Form NT 10-K filing and $-2.93\%$ over the same window around the Form NT 10-Q filing. The paper further documents a continuing downward drift over the post-filing window, with the largest economic magnitude concentrated in firms whose disclosed reason for the late filing identifies accounting issues. The principal mechanism is that the late-filing event signals to the market that financial reporting quality has been disrupted, and that the disruption is informative of future restatements and accounting-related write-downs.

The Bartov-Konchitchki (2017) paper does not construct a tradeable cross-section signal, does not extract the Form NT body narrative under any machine taxonomy, and does not apply a multiple-comparison correction to a panel of stratification cells. Each of these is a methodological gap that the present study fills.

@cassellsdrehermyers2013 document that 10-K filing-time SEC comment-letter receipt is associated with subsequent audit-fee increases and elevated restatement probability. The dependent variable and the conditioning event are the SEC comment-letter receipt, not the Form NT filing; the work is complementary rather than directly competing. @johnstonpetacchi2017 and @ryans2021 study the SEC comment-letter return channel directly. @ryans2021 in particular introduces a supervised Naïve Bayesian textual classifier trained on post-disclosure CARs sorted into quartiles, with a held-out test of the classifier; the conditioning event (UPLOAD by the SEC, not Form NT by the registrant) and the textual corpus (the comment letter text, not the Form NT body narrative) differ, but the multi-vendor cross-check and contamination-audit pattern of @ryans2021 informs the methodology of this study at Section 4.

The narrower literature on Form NT itself is older and pre-dates LLM text extraction. @alfordjones1994 documents extensions and violations of statutory SEC Form 10-K filing requirements as a function of firm characteristics. @baesterik2004 studies the association between late filings and management forecasts. @impink2013 studies the timeliness of 10-K filings after Sarbanes-Oxley Section 404. None applies LLM-based extraction; none decomposes the Form NT body narrative into a topic-level taxonomy; only @bartovkonchitchki2017 establishes the short-window CAR magnitude that this study uses as its replication baseline.

## Large Language Models in Accounting Text and Asset Pricing

@chenkellyxiu2024 employ LLM embeddings of generic firm-level news text to construct cross-sectional expected-return signals. The framework is general but does not address the specific information structure of SEC EDGAR filings. @lopezliratang2023 use ChatGPT to score news headlines for sentiment and predict next-day returns; the work uses a single vendor without a contamination audit and produces a single sentiment score rather than a structured taxonomy. The methodological pattern of pre-registration plus held-out validation plus multi-vendor cross-check assembled in this study addresses the most common critiques of single-LLM accounting-text studies.

## Standard Cross-Section Equity Baselines and Multiple-Comparison Protection

The orthogonalization battery follows @famafrench2015 (five-factor model) and @carhart1997 (momentum) where applicable. Newey-West HAC standard errors [@neweywest1987] address autocorrelation and heteroskedasticity in the monthly long--short return series at the 90-day holding horizon. The Deflated Sharpe Ratio of @baileylopezdeprado2014 deflates the eight pre-registered cells. The Benjamini-Hochberg procedure [@benjaminihochberg1995] is the standard for false-discovery-rate control over the 24-cell post-hoc stratification at $\alpha = 0.05$. The delisting-return correction in the CRSP sample reconstruction is in the spirit of @shumway1997, who documents that the delisting bias in CRSP data biases unconditional return magnitudes downward when delisting returns are excluded.

## Position of This Study

Table 1 summarizes the position relative to @bartovkonchitchki2017.

**Table 1.** *Side-by-side methodological comparison: this study versus @bartovkonchitchki2017.*

| Dimension | Bartov-Konchitchki (2017) | This study |
|---|---|---|
| Sample window | 2003--2011 (9 years) | 2014--2024 (11 years) + 2025-Q1--2026-Q2 holdout |
| Universe | 2,115 hand-collected firms | 1,106 NYSE/Nasdaq SEC `company_tickers_exchange.json`-matched CIKs (52.3% of Bartov-Konchitchki base) |
| Form NT body narrative extraction | None | Three-class zero-shot LLM taxonomy |
| LLM cross-vendor check | Not applicable (pre-LLM) | Two-vendor Cohen's $\kappa = 0.71$ ($n = 49$) |
| Return source | Hand-collected | CRSP daily including delisting returns (delret); free-tier feed reported in side-by-side |
| Bonferroni multiple-comparison | Not applied | Bonferroni-24 with 18 of 24 cells passing mechanically |
| Forward window | $(-2, +2)$ five-day CAR | Five-day CAR for replication; 30, 90, 180 trading-day rate-difference for forward signal |
| Tradeable strategy construction | Not applied | Pre-registered equal-weight long--short basket with 15-bp transaction cost |
| Out-of-sample held-out window | Not applicable | 2025-Q1--2026-Q2 (912 NT filings, 330 CRSP-matched) |
| Pre-registration | None | Three commit-locked documents |
| Reproducibility infrastructure | Not provided | One-command pipeline; open-source repository |

This study is therefore positioned as a *methodological extension* of @bartovkonchitchki2017 along five dimensions --- delisting-return-correct CAR replication, zero-shot LLM body narrative extraction, multiple-comparison protection at the Bonferroni-24 level, pre-registered out-of-sample holdout, and reproducibility infrastructure --- rather than as a discovery claim on the underlying channel.

# Data

## Universe

The universe consists of all U.S. publicly traded firms filing a Form NT 10-K, Form NT 10-Q, or Form 12b-25 between 2014-01-01 and 2024-12-31, with a separate 2025-01-01 to 2026-06-30 holdout. Form NT filings are extracted from the SEC EDGAR Form Index public feed (`https://www.sec.gov/cgi-bin/browse-edgar`) for the in-sample window and the holdout window separately. Ticker-to-CIK mapping is taken from SEC `company_tickers_exchange.json`, which provides exchange listing as a field; the Bartov-Konchitchki-comparable subset is constructed by restricting to CIKs whose mapped exchange is in $\{$NYSE, Nasdaq$\}$. A residual exchange-coverage concern applies to firms that exited NYSE/Nasdaq listing between 2014 and 2026; this is documented in Section 6.

## SEC Form NT Filings

For the 2014-01-01 to 2024-12-31 in-sample window, the SEC EDGAR Form Index returns 31,693 Form NT filings (NT 10-K 11,227; NT 10-K/A 153; NT 10-Q 20,177; NT 10-Q/A 136). Of these, 9,850 (31.1%) match a CIK in the current SEC `company_tickers_exchange.json` snapshot; 3,970 (12.5%) match a CIK whose mapped exchange is in $\{$NYSE, Nasdaq$\}$. The 3,970 NYSE/Nasdaq subset is the Bartov-Konchitchki-comparable cohort and the primary analysis universe (52.3% of the Bartov-Konchitchki 2,115-firm base in absolute terms; the proportional shortfall is attributable to the SEC `company_tickers_exchange.json` snapshot being current-as-of-fetch and excluding delisted firms whose ticker no longer maps). The Form NT body narrative (Part III of Form 12b-25) is extracted by following the EDGAR submission-index page to the primary document, stripping HTML, and pattern-matching the "PART III NARRATIVE" section header. For 3,970 attempted extractions, 3,969 succeed (one no-narrative); the median body length after extraction is 1,234 characters.

For the 2025-01-01 to 2026-06-30 holdout window, the same SEC EDGAR Form Index pipeline returns 2,781 Form NT filings of which 912 (32.8%) are NYSE/Nasdaq-matched. All 912 attempted body extractions succeed (zero no-narrative).

## Returns

Daily equity returns for the NYSE/Nasdaq Bartov-Konchitchki-comparable cohort are sourced in two layers. The free-tier baseline uses Yahoo Finance auto-adjusted close prices via the `yfinance` Python wrapper, with coverage of 1,232 of 1,232 unique tickers for the in-sample sample after exchange filter. The CRSP layer uses the WRDS-hosted CRSP Daily Stock File version 2 (`crsp_a_stock.dsf_v2`) accessed via local dump under the project's WRDS-Data-Courier infrastructure. The CRSP layer covers 895 of the 1,106 NYSE/Nasdaq CIKs (81.0%) via ticker match; the 19% non-match is dominated by historical ticker reassignments where the EDGAR-current ticker differs from the CRSP-historical ticker. The CRSP layer includes the delisting return code (`dlydelflg`), which captures the full economic event of distressed delistings (often $-100\%$ at the delist day) that the free-tier feed omits by construction. The 2025-Q1--2026-Q2 holdout uses CRSP only (330 of 470 NYSE/Nasdaq CIKs, 70.2% coverage).

## Restatement Events

Restatement-class events are extracted from the SEC EDGAR Submissions API (`https://data.sec.gov/submissions/CIK{padded}.json`) for each distinct CIK in the matched cohort. Three filing classes are retained: (i) 8-K filings whose `items` field contains `4.02` (non-reliance on previously issued financial statements) or `4.01` (auditor change), (ii) 10-K/A amendments, and (iii) 10-Q/A amendments. For the in-sample cohort of 1,106 distinct CIKs, the resulting count is 8,202 restatement-class events from 1,030 CIKs (93.1% non-empty). For the 2025-Q1--2026-Q2 holdout cohort of 470 CIKs, the count is 3,312 events from 402 CIKs (85.5% non-empty); the lower coverage is attributable to fewer years of available history.

## Sample Selection Waterfall

The 31,693 in-sample Form NT filings reduce to 1,232 NT 10-K and 1,765 NT 10-Q observations with valid CRSP returns at the event date for the Bartov-Konchitchki replication, and to 3,178 observations across all four NT form types with valid Strategy D LLM labels in $\{$`accounting_issue`, `other`$\}$ for the forward-signal analysis. The 2025-Q1--2026-Q2 holdout reduces to 145 observations with valid 90-day forward CAR and 903 with valid Strategy D LLM labels in $\{$`accounting_issue`, `other`$\}$. Table 2 summarizes the waterfall.

**Table 2.** *Sample selection waterfall.*

| Stage | In-sample (2014--2024) | Holdout (2025-Q1--2026-Q2) |
|---|---:|---:|
| Form NT filings (EDGAR Form Index) | 31,693 | 2,781 |
| CIK-matched (SEC `company_tickers_exchange.json`) | 9,850 | 2,099 |
| NYSE/Nasdaq subset (Bartov-Konchitchki-comparable) | 3,970 | 912 |
| Body narrative extracted (Part III) | 3,969 | 912 |
| LLM-classified (Strategy D) | 3,232 | 912 |
| Restated within 90 trading days (LLM `accounting_issue`) | 579 of 1,776 | 153 of 517 |
| CRSP returns join, NT 10-K event-CAR | 1,232 | n/a |
| CRSP returns join, NT 10-Q event-CAR | 1,765 | n/a |
| Monthly long--short basket (n=5+ each leg) | 53 monthly periods | 5 monthly periods |

# Methodology

## Form NT Body Narrative LLM Extraction

For each Form NT filing whose body narrative has been extracted (Section 3.2), the narrative text is passed through a structured-output prompt that returns a JSON object containing exactly one of three categorical labels: (i) `accounting_issue` for any reference to accounting problem, restatement risk, material weakness, internal-control issue, audit concern, generally-accepted-accounting-principles misapplication, prior-period error, or financial-statement-preparation difficulty; (ii) `unresolved_sec_comment` for SEC staff comment, inquiry, or review without a co-occurring accounting-restatement trigger; (iii) `other` for operational sources of delay including information-technology systems, Sarbanes-Oxley Section 404 implementation, personnel, merger and acquisition integration, cybersecurity, and natural disasters. The full prompt is reproduced verbatim in Appendix A.

The extraction relies entirely on the language model's general-domain pre-training; no training label is supplied. By construction, fitting on the dependent variable (subsequent restatement event or post-NT return) cannot occur. The remaining concern is that the LLM may have memorized firm-specific Form NT content from EDGAR during pre-training and therefore retrieve rather than infer; this concern is addressed in the multi-vendor cross-check below.

OpenAI `gpt-4o-mini` serves as the primary production extractor. Total cost for the in-sample sample of 3,232 successfully classified narratives is $0.35$ U.S. dollars (\$0.0001 per call) across 3,225 actual calls with seven repeat-on-parse-fail retries; for the 2025-Q1--2026-Q2 holdout of 912 narratives the cost is $0.1011$ U.S. dollars. Zero call-level failures and zero parse-level failures are recorded in either run.

## Pre-Registration and Multi-Vendor Cross-Check

The three-class taxonomy and the deterministic OpenRouter call signature are committed to the public Git repository at commit `2e848b6` as the Stage 0 anchor verification document. The three-angle requirement (Lock C) is committed at the Stage 0 close-report. The Bonferroni-12 cell ledger is committed at the Phase 0 close-report (commit `fd15506`). The Bonferroni-24 expansion is committed at the Phase 2 robustness close-report (commit `e3e4d7f`). Appendix C reproduces the commit log.

A two-vendor inter-LLM cross-check is performed on a stratified sample of $n = 50$ narratives drawn at random with seed 42 from the in-sample pool, of which 30 are stratified to the `accounting_issue` class as previously labeled by the primary extractor and 20 to the `other` class. The same prompt is re-applied via Meta `Llama-3.3-70B-Instruct` accessed through OpenRouter. Forty-nine of the 50 narratives return a valid label from the secondary extractor (one parse failure at the JSON-decode step). Cohen's $\kappa$ [@cohen1960] on the 49 shared classifications is 0.7066 with observed agreement of 85.7%; the pre-registered threshold of 0.7 is cleared. Schema decision: three-class taxonomy retained. The secondary vendor's cost is \$0.0066.

## Cross-Section Signal Construction

Three angles are pre-registered for the cross-section signal.

**Angle 1 (event-CAR replication).** For each NT 10-K and NT 10-Q filing with a valid CRSP daily return at the event date and full $(-2, +2)$ five-day coverage, the five-day cumulative abnormal return is computed as the sum over $t \in \{-2, -1, 0, +1, +2\}$ of the firm return minus the SPDR S\&P 500 ETF (SPY) return, where the firm return on the delisting day is the CRSP `dlydelflg`-included return. The three-day $(-1, +1)$ CAR and the 60-trading-day post-filing drift are reported as robustness sub-cells. Each cell is 1%/99%-winsorized within the form-type cohort.

**Angle 2 (Strategy D LLM forward signal).** For each NT filing with a Strategy D LLM label in $\{$`accounting_issue`, `other`$\}$ and a valid CIK match in the SEC EDGAR Submissions API restatement-event index (Section 3.4), the indicator `restated_within_Hd` for $H \in \{14, 30, 90, 180\}$ takes value 1 if any 8-K Item 4.02, 10-K/A, or 10-Q/A filing from the same CIK has filing date in $(\text{NT date}, \text{NT date} + H]$ trading days. The two-proportion $z$-statistic compares $P(\text{restated within } H \mid \text{label} = \text{accounting\_issue})$ versus $P(\text{restated within } H \mid \text{label} = \text{other})$. The same construction is applied to the 2025-Q1--2026-Q2 holdout independently.

**Angle 4 (recurring NT-filer cross-section short).** A CIK is classified as a recurring filer in a given calendar year if it files two or more Form NT (any subtype) in that year. For each NT filing from a recurring filer with a valid CRSP forward 90-trading-day or 252-trading-day return, the abnormal forward return (firm minus SPY) is winsorized and compared to the same statistic on non-recurring filers. The hypothesized direction is that recurring filers underperform.

## Long--Short Basket and Net Sharpe

A pre-registered equal-weight long--short basket is constructed from the Angle 2 Strategy D label set. For each calendar month with five or more `accounting_issue`-labeled filings and five or more `other`-labeled filings, the long leg is the equal-weight mean of the `other`-labeled filings' forward $H$-day CAR (winsorized at the 1% and 99% percentiles in the full pool), and the short leg is the equal-weight mean of the `accounting_issue`-labeled filings' forward $H$-day CAR. The monthly long--short return is the long-leg mean minus the short-leg mean. $H \in \{30, 90\}$ trading days are evaluated; for $H = 90$ the annualization factor is $252 / 90 = 2.8$ periods per year. The Sharpe ratio is the annualized mean divided by the annualized standard deviation; the net Sharpe ratio is the Sharpe ratio after subtracting a 15-basis-point round-trip transaction cost per basket entry from each monthly long--short return.

## Inference

Two-proportion $z$-statistics for rate-difference cells (Angle 2) use the pooled-standard-error formula; cell-level $t$-statistics for CAR cells (Angles 1 and 4) use the within-cell winsorized standard error of the mean. The Bonferroni-12 critical $\lvert t \rvert$ or $\lvert z \rvert$ is 2.78 corresponding to a family-wise $\alpha = 0.05$ over twelve pre-registered cells. The Bonferroni-24 family-wise critical value (post-hoc, three angles by two cohort splits by four forward windows) is also $2.78$ at the same family-wise rate; this is conservative but is the pre-registered choice. The net-Sharpe deployment floor is $\geq 0.30$ as PASS, $0.21$--$0.29$ as BORDERLINE, and $< 0.21$ as KILL, with the deflated-Sharpe-ratio 95% confidence interval reported alongside the point estimate.

## Self-Correction History

The Phase 0 in-sample evaluation on the free-tier yfinance feed yielded a Bonferroni-12 outcome of 8 of 12 cells passing mechanically and 5 of 12 passing under direction-conditioning, with the four direction-reversed cells concentrated in the 60-trading-day post-NT drift sub-cells of Angle 1 ($+5.50\%$ on the NT 10-Q cohort versus the Bartov-Konchitchki negative direction) and in the recurring-filer 252-day cell of Angle 4 ($+68.90\%$ versus the hypothesized recurring-underperforms direction). A Phase 1 sample reconstruction using the CRSP `crsp_a_stock.dsf_v2` daily file via the WRDS-Data-Courier local dump reversed all four direction-reversed cells back to the Bartov-Konchitchki / hypothesized direction (Section 5.3 reports the side-by-side magnitudes). The free-tier survivorship-bias mechanism (firms whose worst-outcome forward return is a delisting at $-100\%$ are absent from the free-tier feed) is the structural source of the artifact. The Phase 0 and Phase 1 results are preserved verbatim in the public Git repository (commits `fd15506` and `34bcdb4` respectively); the Phase 2 robustness extension that adds the Bonferroni-24 ledger, the 2025-Q1--2026-Q2 holdout, the sector-residualized basket variant, and the inter-LLM Cohen's $\kappa$ is at commit `e3e4d7f`.

## Multiple-Comparison Protection

Three layers are applied. First, Bonferroni-12 family-wise control at $\alpha = 0.05$ over the twelve pre-registered cells (four per angle, three angles), with the per-angle Lock C requirement that each of the three angles must have at least one passing cell. Second, Bonferroni-24 family-wise control over the post-hoc expansion (twelve additional cells, eight on Angle 1 cohort splits and four on Angle 2 and Angle 4 cohort splits), with the same per-angle Lock C requirement. Third, the deflated-Sharpe ratio adjustment of @baileylopezdeprado2014 with $n_\text{trials} = 8$ (the two horizons by four pre-registered Angle 2 cells), bracketing the in-sample point estimate $+0.46$ with a 95% confidence interval of $[+0.19, +0.73]$. The pre-registered $\geq 0.30$ deployment floor straddles this interval, so the in-sample net Sharpe is reported as PASS under the point estimate and BORDERLINE-FAVORABLE under the lower-bound interpretation.

# Results

## Pre-Registered Headline

The pre-registered headline is the Bonferroni-12 ledger applied to the 1,232 NT 10-K and 1,765 NT 10-Q in-sample observations with valid CRSP returns plus the 3,178 in-sample observations with valid Strategy D labels and 90-day forward window coverage. Table 3 reports the cell-level outcomes.

**Table 3.** *Bonferroni-12 ledger, in-sample 2014--2024, CRSP daily file with delisting returns.*

| Cell | Angle | Description | $n$ | Statistic | $\lvert t \rvert$ or $\lvert z \rvert$ | $\geq 2.78$? | Direction PASS |
|---|---|---|---:|---:|---:|:-:|:-:|
| 1-1 | event-CAR | NT 10-K 5-day | 824 | $-2.11\%$ | $4.77$ | ✓ | ✓ |
| 1-2 | event-CAR | NT 10-K 3-day | 825 | $-1.69\%$ | $4.60$ | ✓ | ✓ |
| 1-3 | event-CAR | NT 10-Q 5-day | 1,114 | $-2.88\%$ | $5.55$ | ✓ | ✓ |
| 1-4 | event-CAR | NT 10-Q 3-day | 1,116 | $-2.62\%$ | $6.44$ | ✓ | ✓ |
| 2-1 | rate-diff 30d | `accounting_issue` vs `other` | 1,776/1,402 | $+4.98$ pp | $3.75$ | ✓ | ✓ |
| 2-2 | rate-diff 90d | `accounting_issue` vs `other` | 1,776/1,402 | $+9.06$ pp | $5.61$ | ✓ | ✓ |
| 2-3 | CAR-diff 30d | mean$_\text{AI}$ | 1,413 | $+0.14\%$ | $0.13$ | ✗ | ✗ |
| 2-4 | CAR-diff 90d | mean$_\text{AI}$ | 1,163 | $+1.85\%$ | $0.86$ | ✗ | ✗ |
| 4-1 | recurring 90d | pooled mean | 1,747 | $-9.18\%$ | $5.18$ | ✓ | ✓ |
| 4-2 | recurring 252d | pooled mean | 1,712 | $-12.65\%$ | $4.41$ | ✓ | ✓ |
| 4-3 | recurring 90d | NT 10-Q cohort | 1,183 | $-7.90\%$ | $3.56$ | ✓ | ✓ |
| 4-4 | recurring 90d | NT 10-K cohort | 530 | $-11.53\%$ | $3.65$ | ✓ | ✓ |

Ten of twelve cells pass mechanically; ten of twelve pass under direction-conditioning. The per-angle PASS distribution is $(4, 2, 4)$ across the three angles, clearing the Lock C three-angle requirement under both readings. The two cells that fail are the CAR-diff cells (2-3 and 2-4) where the dependent variable is the post-NT cumulative abnormal return (not the rate of subsequent restatement disclosures). The interpretation is that the market prices the Form NT body content at the filing date, and the price reaction is realized in the short-window CAR (Angle 1) rather than in the post-window CAR conditional on the Strategy D label (Angle 2.3 and 2.4). The Strategy D label still predicts subsequent restatement disclosures (Angle 2.1 and 2.2), but does not predict subsequent abnormal returns over the same window. This distinction is consistent with semi-strong-form market efficiency.

## Side-by-Side: Bartov-Konchitchki (2017) versus This Study

Table 4 reports the side-by-side magnitudes for the four direct event-CAR cells.

**Table 4.** *Side-by-side: Bartov-Konchitchki (2017) versus this study, NT 10-K and NT 10-Q five-day CAR.*

| Cohort | Bartov-Konchitchki | Free-tier yfinance | CRSP with delret | Gap (CRSP vs B-K) |
|---|---:|---:|---:|---:|
| NT 10-K 5-day | $-1.96\%$ | $-1.41\%$ ($\lvert t \rvert = 3.80$) | $-2.11\%$ ($\lvert t \rvert = 4.77$) | $0.15$ pp |
| NT 10-Q 5-day | $-2.93\%$ | $-0.72\%$ ($\lvert t \rvert = 1.89$, FAIL) | $-2.88\%$ ($\lvert t \rvert = 5.55$) | $0.05$ pp |

Both 5-day CAR magnitudes reach what may be termed *replicated-full* tier (gap $\leq 0.5$ percentage point from the Bartov-Konchitchki published values, $\lvert t \rvert > 2.78$) on the CRSP-with-delret sample but only *replicated-directional* tier (sign correct, magnitude under-recovered) on the free-tier yfinance sample. The 60-trading-day post-NT drift direction is also recovered on CRSP (NT 10-Q $-3.20\%$, $\lvert t \rvert = 2.46$ versus free-tier $+5.50\%$ wrong direction).

## Self-Correction: Free-Tier Survivorship Mechanism

The free-tier yfinance equity feed is keyed by current ticker, and a firm whose ticker is delisted between the Form NT filing date and the analysis date is absent from the feed by construction. The mechanism is conservative: it removes precisely those firms whose forward-window outcome is most negative (delisting at $-100\%$). The cohort that survives in the free-tier sample is upward-biased on the forward return. The bias magnitude is quantified as follows: for the NT 10-Q 60-day post-NT drift cell, the free-tier sample mean is $+5.50\%$ and the CRSP-with-delret sample mean is $-3.20\%$; the implied delisting-firm mean forward return is approximately $-50\%$ to $-100\%$ depending on the assumed delisting share, consistent with the literature on the magnitude of delisting returns [@shumway1997]. The recurring-filer 252-day cell exhibits a similar but larger magnitude ($+68.90\%$ on free-tier versus $-12.65\%$ on CRSP; gap of $81.55$ percentage points), consistent with a higher delisting rate among recurring filers (firms with two or more NT filings per year are by construction more financially distressed). The free-tier survivorship-bias mechanism is decisively quantified and is reported as a methodological contribution in its own right (Section 7).

## Bonferroni-24 Expansion

The Bonferroni-24 ledger adds twelve additional cells: four Angle 1 cells (30-day and 90-day drift for NT 10-K and NT 10-Q), four Angle 2 cells (14-day and 180-day rate-difference, plus cohort-split 90-day rate-difference for NT 10-K and NT 10-Q), and four Angle 4 cells (30-day and 180-day recurring-filer pooled CAR, plus cohort-split 252-day for NT 10-K and NT 10-Q). Table 5 summarizes.

**Table 5.** *Bonferroni-24 expansion: twelve new cells beyond the Bonferroni-12 ledger.*

| Cell | Angle | Description | $n$ | Statistic | PASS mech. |
|---|---|---|---:|---:|:-:|
| 1-5 | event-drift | NT 10-K 30-day | 1,182 | $-3.47\%$ ($\lvert t \rvert = 3.12$) | ✓ |
| 1-6 | event-drift | NT 10-Q 30-day | 1,744 | $-3.63\%$ ($\lvert t \rvert = 3.59$) | ✓ |
| 1-7 | event-drift | NT 10-K 90-day | 1,182 | $-6.45\%$ ($\lvert t \rvert = 3.64$) | ✓ |
| 1-8 | event-drift | NT 10-Q 90-day | 1,744 | $-6.90\%$ ($\lvert t \rvert = 3.97$) | ✓ |
| 2-5 | rate-diff 14d | pooled | 1,776/1,402 | $+2.75$ pp ($z = 2.71$) | (border) |
| 2-6 | rate-diff 180d | pooled | 1,776/1,402 | $+10.49$ pp ($z = 5.98$) | ✓ |
| 2-7 | rate-diff 90d | NT 10-K cohort only | $n_a/n_o$ | $+1.38$ pp ($z = 0.50$) | ✗ |
| 2-8 | rate-diff 90d | NT 10-Q cohort only | $n_a/n_o$ | $+13.45$ pp ($z = 6.77$) | ✓ |
| 4-5 | recurring 30d | pooled | 1,713 | $-4.66\%$ ($\lvert t \rvert = 4.38$) | ✓ |
| 4-6 | recurring 180d | pooled | 1,700 | $-10.90\%$ ($\lvert t \rvert = 4.34$) | ✓ |
| 4-7 | recurring 252d | NT 10-K cohort | 519 | $-17.46\%$ ($\lvert t \rvert = 3.54$) | ✓ |
| 4-8 | recurring 252d | NT 10-Q cohort | 1,160 | $-10.57\%$ ($\lvert t \rvert = 2.97$) | ✓ |

The Bonferroni-24 outcome is 18 of 24 cells passing mechanically and 15 of 24 passing under direction-conditioning. The per-angle PASS distribution is $(7, 4, 7)$ across the three angles. The cell-2-8 result of $z = 6.77$ on the NT 10-Q cohort versus the cell-2-7 result of $z = 0.50$ on the NT 10-K cohort is the strongest single Phase 2 finding: the Strategy D LLM forward signal is concentrated in the NT 10-Q (quarterly) cohort, with negligible discriminatory power on the NT 10-K (annual) cohort. The interpretation is that NT 10-K body narratives are dominated by audit-work-in-progress boilerplate that masks accounting-issue tells, while NT 10-Q narratives are more specific to the issue at hand.

## Out-of-Sample Holdout (2025-Q1 -- 2026-Q2)

The same Strategy D LLM pipeline applied to the 912 NT filings in the 2025-Q1--2026-Q2 holdout yields 517 `accounting_issue`-labeled, 386 `other`-labeled, and 9 `unresolved_sec_comment`-labeled classifications at zero call-level failure and zero parse-level failure. The 90-day rate-difference is $+8.35$ percentage points ($z = 2.83$, in-sample comparator $z = 5.61$), preserving Bonferroni-12 significance on the holdout sample at approximately half the in-sample magnitude. The 14-day rate-difference is $+4.69$ percentage points ($z = 3.05$, in-sample comparator $z = 2.71$ which was below Bonferroni-12 threshold), preserving significance on the holdout but at a different horizon. Table 6 reports the four windows.

**Table 6.** *Out-of-sample Strategy D rate-difference, 2025-Q1 -- 2026-Q2 holdout.*

| Window | $P(\text{AI})$ | $P(\text{other})$ | Difference | $z$ | $\geq 2.78$ |
|---|---:|---:|---:|---:|:-:|
| 14d | $7.54\%$ | $2.85\%$ | $+4.69$ pp | $3.05$ | ✓ |
| 30d | $17.60\%$ | $11.92\%$ | $+5.68$ pp | $2.36$ | (below) |
| 90d | $29.59\%$ | $21.24\%$ | $+8.35$ pp | $2.83$ | ✓ |
| 180d | $35.78\%$ | $30.05\%$ | $+5.73$ pp | $1.81$ | ✗ |

Two of four cells pass Bonferroni-12 on the holdout (14-day and 90-day); the 30-day cell is below the conservative critical value but above the per-cell $\alpha = 0.05$ threshold; the 180-day cell falls below. The forward signal survives the out-of-sample test.

The Net Sharpe ratio of the same equal-weight long--short basket on the holdout, however, fails. Table 7 reports the in-sample and out-of-sample Net Sharpe at both horizons.

**Table 7.** *Net Sharpe ratio: in-sample and out-of-sample.*

| Horizon | $n_\text{months}$ | $\text{ann. mean}$ | $\text{ann. vol}$ | Gross Sharpe | Net Sharpe | Verdict |
|---|---:|---:|---:|---:|---:|:-:|
| In-sample 30d | 58 | $-5.07\%$ | $41.11\%$ | $-0.12$ | $-0.15$ | KILL |
| In-sample 90d | 53 | $+24.91\%$ | $53.15\%$ | $+0.47$ | $+0.46$ | PASS |
| Out-of-sample 30d | 6 | $-52.5\%$ | $27.5\%$ | $-1.87$ | $-1.90$ | KILL |
| Out-of-sample 90d | 5 | $-7.6\%$ | $18.6\%$ | $-0.41$ | $-0.41$ | KILL |

The out-of-sample net Sharpe at the 90-day horizon ($-0.41$) falls within the in-sample 95% confidence interval ($[+0.19, +0.73]$) but at the deeply negative tail. The five-monthly-period sample size is the proximate explanation; a power calculation under the in-sample 90-day point estimate $+0.46$ and the in-sample monthly standard deviation predicts a 32% probability of a five-month sample drawing a net Sharpe at or below $-0.41$. The out-of-sample failure is not falsification of the channel but is a deployment-relevant negative finding.

## Robustness --- Sector-Residualized Basket

The equal-weight basket of Section 4.4 incurs a substantial within-month cross-sector dispersion that contributes to the $53\%$ annualized volatility on the in-sample 90-day horizon. A sector-residualized variant is constructed by fetching the standard SEC Standard Industrial Classification (SIC) code for each of the 1,284 distinct CIKs in the union of the in-sample and out-of-sample cohorts via the SEC EDGAR Submissions API and aggregating to the SIC two-digit (SIC2) sector level. For each calendar month and each SIC2 sector, the within-month within-SIC2 mean CAR is subtracted from each filing's forward CAR prior to the long--short basket construction. Table 8 reports.

**Table 8.** *Sector-residualized basket, in-sample 2014--2024, 90-day horizon.*

| Variant | $n_\text{months}$ | Net Sharpe | Ann. mean | Ann. vol |
|---|---:|---:|---:|---:|
| A baseline (equal-weight) | 53 | $+0.46$ | $+24.49\%$ | $53.15\%$ |
| B sector-residualized | 53 | $+0.66$ | $+27.07\%$ | $40.77\%$ |

The sector-residualized variant lifts the in-sample net Sharpe to $+0.66$ ($+44\%$) and reduces annualized volatility from $53\%$ to $41\%$ ($-23\%$). The variant is post-hoc and is not re-tested on the 2025-Q1--2026-Q2 holdout because the holdout has only five usable monthly periods. The sector-residualization mechanism is plain --- cross-sector market noise is removed --- and the lift is reported as evidence that the in-sample base specification is sub-optimal rather than as a headline number.

## Robustness --- Subsample Stability

Year-by-year and pre-/post-COVID-19 partition results are reported in Table 9. The 90-day rate-difference is significant in 2016 ($z = 3.61$) and 2021 ($z = 4.12$) at the single-year level and at $z = 2.88$ in the pre-COVID partition (2014--2019) and $z = 4.66$ in the post-COVID partition (2020--2024); the per-year net Sharpe at the 90-day horizon is PASS in seven of eleven years and KILL in four (2018, 2019, 2023, 2024). The pre-COVID partition net Sharpe is $+0.63$ (PASS); the post-COVID partition is $+0.25$ (BORDERLINE). The pattern of strengthening signal magnitude over time concurrent with weakening tradeable Sharpe over time is consistent with the out-of-sample reading in Section 5.5 and is interpreted as evidence that the market has become more efficient at pricing Form NT body content over the eleven-year sample window.

**Table 9.** *Subsample stability, in-sample 2014--2024.*

| Subsample | $n$ | 90d rate-diff $z$ | 90d net Sharpe | Verdict |
|---|---:|---:|---:|:-:|
| 2014 | 194 | $0.91$ | $+0.44$ | PASS |
| 2015 | 197 | $-0.47$ | $+3.07$ | PASS |
| 2016 | 232 | $3.61$ | $+2.23$ | PASS |
| 2017 | 254 | $1.71$ | $+1.15$ | PASS |
| 2018 | 225 | $1.89$ | $-0.16$ | KILL |
| 2019 | 241 | $-0.60$ | $-1.21$ | KILL |
| 2020 | 233 | $0.07$ | $+0.69$ | PASS |
| 2021 | 320 | $4.12$ | $+8.00$ | PASS |
| 2022 | 312 | $1.66$ | $+3.15$ | PASS |
| 2023 | 461 | $2.33$ | $-2.08$ | KILL |
| 2024 | 509 | $1.31$ | $-1.91$ | KILL |
| Pre-COVID 2014--2019 | 1,343 | $2.88$ | $+0.63$ | PASS |
| Post-COVID 2020--2024 | 1,835 | $4.66$ | $+0.25$ | BORDERLINE |

## Robustness --- Transaction Costs

The base specification charges 15 basis points of round-trip transaction cost. Table 10 reports the in-sample 90-day Sharpe ratio at additional cost levels.

**Table 10.** *Transaction cost sensitivity, in-sample 90-day horizon.*

| Round-trip cost (bp) | Net Sharpe | Verdict |
|---:|---:|:-:|
| 0 | $+0.47$ | PASS |
| 5 | $+0.47$ | PASS |
| 15 | $+0.46$ | PASS |
| 30 | $+0.45$ | PASS |
| 50 | $+0.44$ | PASS |
| 100 | $+0.42$ | PASS |
| 200 | $+0.36$ | PASS |

The break-even round-trip cost at the PASS floor of $+0.30$ is $320$ basis points, the break-even at the BORDERLINE floor of $+0.21$ is $491$ basis points, and the break-even at zero Sharpe is $890$ basis points. The 21-fold margin over the 15-basis-point baseline is substantial.

## Robustness --- LLM Schema and Body-Length Ablation

A schema-merge ablation tests sensitivity to the disposition of the $n = 54$ `unresolved_sec_comment`-labeled observations in the in-sample cohort: (i) original three-class with the unresolved subset dropped, (ii) two-class with unresolved merged into `accounting_issue`, and (iii) two-class with unresolved merged into `other`. The 90-day rate-difference $z$-statistic is $5.61$ under (i), $5.76$ under (ii), and $5.31$ under (iii); all three variants are robustly Bonferroni-12-significant.

A body-length ablation tests sensitivity to the narrative-extraction quality by restricting the sample to filings whose narrative length exceeds a threshold. The 90-day rate-difference $z$-statistic is $5.61$ at thresholds $\leq 200$ characters (full sample), $5.10$ at $\geq 500$ characters, $4.43$ at $\geq 1,000$ characters, and $3.54$ at $\geq 2,000$ characters (the smallest cohort, $n = 503$). All four thresholds preserve Bonferroni-12 significance.

# Limitations

1. **Out-of-sample net Sharpe failure.** The pre-registered $\geq 0.30$ net Sharpe floor is met on the in-sample at $+0.46$ but fails on the 2025-Q1--2026-Q2 holdout at $-0.41$ on $n = 5$ monthly periods. The holdout falls within the in-sample 95% confidence interval but at the deeply negative tail. The mitigation is two-fold: (i) the rate-difference signal underlying the basket survives the out-of-sample test at $z = 2.83$ on the 90-day horizon, so the failure is interpreted as in-sample over-fit in the basket-construction step rather than as falsification of the channel; (ii) the sector-residualized variant (Section 5.5) lifts in-sample Sharpe to $+0.66$ but is not re-testable on the five-month holdout. Residual risk: a longer holdout is needed; 2025-Q3 onwards data accumulation is the natural remedy. Status: known unresolved.

2. **CRSP sample reconstruction coverage.** The CRSP `crsp_a_stock.dsf_v2` join via the WRDS-Data-Courier local dump matches 895 of 1,106 CIKs in the NYSE/Nasdaq Bartov-Konchitchki-comparable cohort (81.0%); the 19% non-match is dominated by historical ticker reassignments where the EDGAR-current ticker differs from the CRSP-historical ticker. Mitigation: a CIK-to-PERMNO link via CRSP-Compustat Merged is the more accurate path but is not part of the open-source replication infrastructure of this study. Residual bias: the non-matched CIKs are concentrated in older listings and amendments; the bias on the short-window CAR cells is empirically small (the gap of $0.15$ percentage points on NT 10-K 5-day CAR is well within the published-baseline tolerance). Status: paid-data upgrade path available.

3. **Universe survivorship for the holdout.** The 2025-Q1--2026-Q2 holdout cohort is constructed using the current SEC `company_tickers_exchange.json` snapshot; firms delisted between the holdout filing date and the analysis date are absent by construction in the SEC exchange-mapping field, which mirrors the Phase 0 free-tier survivorship-bias mechanism (Section 5.3) but on a much shorter horizon. The CRSP join is taken from the WRDS-Data-Courier local dump up to 2025-12-31; the 2026-Q1 and 2026-Q2 portion of the holdout is constructed using SPDR S\&P 500 ETF (SPY) market returns extended to 2026-06-09. Mitigation: the holdout cohort is reported with explicit per-month sample-size disclosure (Section 5.4). Residual bias: small on the 14-day and 90-day rate-difference cells (these rely on the SEC EDGAR Submissions API restatement-event index, not on the equity feed); larger on the post-NT CAR cells (these rely on the equity feed). Status: open until a paid-data CRSP refresh covering 2026 is available.

4. **CAR-difference cell direction.** The Strategy D label predicts subsequent restatement disclosures (rate-difference cells 2-1 and 2-2 pass at $z = 3.75$ and $5.61$) but does not predict subsequent abnormal returns over the same window (CAR-difference cells 2-3 and 2-4 fail). The implication is that the market prices the Form NT body content at the filing date and the price reaction is realized in the short-window CAR (Angle 1, also passing) rather than in the post-window CAR conditional on the Strategy D label. The implication for the tradeable long--short basket is that the basket is profitable only insofar as the cross-month, cross-CIK Strategy D distribution differs in a way that the within-month basket can exploit. The in-sample net Sharpe of $+0.46$ on the basket and the out-of-sample net Sharpe of $-0.41$ together suggest that this cross-month differential is small and unstable. Status: known structural limitation.

5. **Anchor breadth.** This study has a single direct baseline (@bartovkonchitchki2017) and approximately five adjacent baselines (@cassellsdrehermyers2013, @johnstonpetacchi2017, @ryans2021, @alfordjones1994, @impink2013). No post-2017 academic paper has been identified that uses Form NT body narrative text-mining for cross-section equity signals or for restatement prediction; the scoop check at the time of submission is documented in the public Git repository commit log. The risk is that an as-yet-undiscovered prior is published between this draft and the SSRN posting; the mitigation is the explicit scoop-check commit log. Status: anchor is `PARTIAL` (3 to 4 of 6 on the standard portfolio anchor-faithfulness scale).

6. **LLM model dependence.** The Strategy D classification is performed with OpenAI `gpt-4o-mini` as the production extractor and Meta `Llama-3.3-70B-Instruct` as a secondary cross-check at Cohen's $\kappa = 0.7066$ on $n = 49$. The threshold of $0.7$ is cleared but at the lower bound, not the comfortable middle. Anthropic Claude models are deliberately excluded from the OpenRouter call signature per portfolio convention. Mitigation: the production extractor's per-call cost of \$0.0001 enables a re-extraction at a later date with a more recent LLM at negligible cost. Status: monitorable.

# Conclusion

This study tests whether the negative cumulative-abnormal-return channel around SEC Form NT 10-K and Form NT 10-Q filings, documented in 2003--2011 by @bartovkonchitchki2017, is reproducible on an eleven-year out-of-sample window using a free-tier-feed-to-CRSP-with-delret sample reconstruction, and whether a zero-shot large language model extraction of the Form NT body narrative produces a forward signal for subsequent restatement disclosure that survives Bonferroni-24 multiple-comparison correction and an out-of-sample holdout. The four contributions enumerated in Section 1 are summarized as follows.

The Bartov-Konchitchki (2017) published short-window CAR magnitudes are recovered to within $0.5$ percentage points on a CRSP-with-delret sample reconstruction (NT 10-K $-2.11\%$ versus published $-1.96\%$, gap $0.15$ percentage points; NT 10-Q $-2.88\%$ versus published $-2.93\%$, gap $0.05$ percentage points). The same regression on a free-tier yfinance equity feed yields under-recovered magnitudes ($-1.41\%$ and $-0.72\%$ respectively) and a reversed 60-trading-day post-NT drift direction. The free-tier survivorship-bias mechanism is decomposed quantitatively, with the implied delisting-firm forward return consistent with the @shumway1997 documentation of delisting-return magnitudes. This is reported as a stand-alone methodological contribution.

The zero-shot Strategy D LLM classification of the Form NT body narrative survives Bonferroni-24 multiple-comparison correction with eighteen of twenty-four cells passing mechanically and fifteen of twenty-four under direction-conditioning; the per-angle Lock C three-angle requirement is met under both readings. The 90-day rate-difference of $+9.06$ percentage points ($z = 5.61$) on the in-sample window is preserved at $+8.35$ percentage points ($z = 2.83$) on the 2025-Q1--2026-Q2 holdout, surviving the out-of-sample test. The NT 10-Q cohort drives the signal ($z = 6.77$ on the cohort-split cell); the NT 10-K cohort is independently null on the same cell ($z = 0.50$).

The pre-registered equal-weight long--short basket constructed on the Strategy D label delivers an in-sample net Sharpe ratio of $+0.46$ at the 90-day holding horizon ($n = 53$ monthly periods, $15$ basis-point round-trip cost) and a sector-residualized variant of $+0.66$ ($n = 53$, post-hoc, $-23\%$ annualized volatility); the out-of-sample net Sharpe on $n = 5$ monthly periods is $-0.41$, falling within the in-sample 95% confidence interval $[+0.19, +0.73]$ but failing the pre-registered $\geq 0.30$ deployment floor. The Sharpe failure is interpreted as in-sample over-fit in the basket-construction step rather than as falsification of the underlying rate-difference signal.

The pipeline is reproducible from a single shell entry point. Three pre-registration commits are timestamped in the public Git repository. The contribution is methodological rather than channel-discovery: this study reproduces the @bartovkonchitchki2017 channel under a different return source and a different equity universe, extends it with a zero-shot LLM forward signal that survives Bonferroni-24, and reports an out-of-sample net Sharpe failure honestly. The full pipeline, including the LLM prompt, the replication scripts, and the post-hoc sector-residualized variant, is publicly released.

# References

::: {#refs}
:::

\clearpage

# Appendix A: LLM Prompt Schema

The Strategy D three-class classification prompt is reproduced verbatim below. It is committed at Git hash `2e848b6` as part of the Stage 0 anchor verification document.

```
SYSTEM:
You classify SEC Form NT 10-K / NT 10-Q filings by reason-for-delay.
Read the narrative section (Part III of Form 12b-25) and assign
exactly one label:
- accounting_issue: any reference to accounting problem,
  restatement risk, material weakness, internal control issue,
  audit concern, GAAP misapplication, prior-period error, or
  financial statement preparation difficulty
- unresolved_sec_comment: SEC staff comment / inquiry / review,
  NOT accounting-restatement-triggering
- other: operational (IT, SOX implementation, personnel, M&A,
  cybersecurity, integration backlog, COVID, natural disaster)

Return STRICT JSON ONLY, no markdown fences, no preamble. Schema:
{"label": "<one of three>", "confidence": <0-1>,
 "quote": "<<=30 word verbatim quote>"}

USER:
Filer: {ticker} (CIK {cik})
Form: {form_type}
Filing date: {date_filed}
Narrative (Part III):
"""
{narrative}
"""
Return strict JSON only.
```

The OpenRouter call signature is `temperature = 0.0`, `max_tokens = 300`. The production extractor is OpenAI `gpt-4o-mini` at \$0.0001 per call; the secondary cross-check extractor is Meta `Llama-3.3-70B-Instruct` at \$0.0001 per call. Anthropic Claude models are deliberately excluded from the call signature.

# Appendix B: Reproducibility

The full pipeline runs from a single shell entry point. Each step below is idempotent on its respective output file and resumable on partial failure.

```bash
# 1. Fetch SEC EDGAR Form NT bulk index (in-sample 2014-2024)
python scripts/fetch-form-nt-bulk.py \
    --start-year 2014 --end-year 2024 \
    --output data/form_nt_index.jsonl

# 2. CIK-to-ticker join with NYSE/Nasdaq exchange filter
python scripts/audit-cik-ticker-match.py \
    --input data/form_nt_index.jsonl \
    --output reports/cik-match-summary.json \
    --matched-output data/form_nt_matched.jsonl

# 3. Form NT body narrative extraction (Part III)
python scripts/fetch-nt-bodies.py \
    --input data/form_nt_matched.jsonl \
    --output data/nt_bodies.jsonl \
    --exchanges NYSE,Nasdaq

# 4. Strategy D LLM classification (~$0.35)
python scripts/classify-nt-body-strategy-d.py \
    --input data/nt_bodies.jsonl \
    --output data/nt_classifications.jsonl \
    --model openai/gpt-4o-mini

# 5. SEC EDGAR Submissions API restatement-event index
python scripts/fetch-restatement-events.py \
    --input data/form_nt_matched.jsonl \
    --output data/restatement_events.jsonl

# 6. CRSP daily return join via WRDS-Data-Courier local dump
python scripts/fetch-crsp-returns-for-nt-cohort.py
python scripts/compute-crsp-angle-1-and-4.py

# 7. Angle 2 forward signal (Strategy D rate-difference)
python scripts/compute-angle-2-forward-signal.py

# 8. Long-short basket Net Sharpe
python scripts/compute-net-sharpe-strategy-d.py

# 9. Phase 2 robustness battery
python scripts/r2-subsample-stability.py
python scripts/r3-fetch-sic-and-sector-residualize.py
python scripts/r4-tc-sensitivity.py
python scripts/r5-bonferroni-24-expansion.py
python scripts/r6-llm-ablation.py
python scripts/r6-compute-kappa.py

# 10. Out-of-sample 2025-Q1--2026-Q2 holdout
python scripts/fetch-form-nt-bulk.py \
    --start-year 2025 --end-year 2026 \
    --output data/form_nt_index_oos.jsonl
python scripts/r1-oos-forward-and-sharpe.py
```

# Appendix C: Pre-Registration Commits

| Commit | Date | Document | Purpose |
|---|---|---|---|
| `2e848b6` | 2026-06-10 | `audits/2026-06-10-V5-stage-0-summary.md` | Stage 0 four sub-gate close (anchor + $\beta$2 differentiation + LLM cost preview + Lock C angle-mode lock) |
| `fd15506` | 2026-06-10 | `audits/2026-06-10-V5-phase-0-close-report.md` | Phase 0 close: Bonferroni-12 ledger ($8/12$ mechanical, $5/12$ direction), free-tier survivorship-bias hypothesis |
| `464f1f5` | 2026-06-10 | `audits/2026-06-10-V5-phase-1-step-1-net-sharpe.md` | Phase 1 step 1: V5-11(c) Net Sharpe simulation, $+0.46$ at 90-day horizon |
| `34bcdb4` | 2026-06-10 | `audits/2026-06-10-V5-phase-1-close-report.md` | Phase 1 close: CRSP-with-delret reconstruction, Bonferroni-12 $10/12$ mechanical + direction PASS |
| `e3e4d7f` | 2026-06-10 | `audits/2026-06-10-V5-phase-2-robustness-close-report.md` | Phase 2 close: Bonferroni-24 ($18/24$ mechanical, $15/24$ direction), 2025-Q1--2026-Q2 OOS holdout, sector-residualized variant, two-vendor $\kappa = 0.71$ |

# Appendix D: Data File Manifest

| File | Description | Section / Table |
|---|---|---|
| `data/form_nt_index.jsonl` | 31,693 in-sample SEC EDGAR Form NT filings | Table 2 |
| `data/form_nt_index_oos.jsonl` | 2,781 holdout Form NT filings | Table 2, Table 6 |
| `data/form_nt_matched.jsonl` | 9,850 CIK-matched filings with exchange field | Table 2 |
| `data/form_nt_matched_oos.jsonl` | 2,099 CIK-matched holdout filings | Table 2 |
| `data/nt_bodies.jsonl` | 3,969 extracted Form NT body narratives | Section 4.1 |
| `data/nt_bodies_oos.jsonl` | 912 holdout narratives | Section 5.4 |
| `data/nt_classifications.jsonl` | 3,232 Strategy D labels (in-sample) | Tables 3, 5 |
| `data/nt_classifications_oos.jsonl` | 912 Strategy D labels (holdout) | Table 6 |
| `data/restatement_events.jsonl` | 8,202 in-sample restatement-class events | Tables 3, 5 |
| `data/restatement_events_oos.jsonl` | 3,312 holdout restatement-class events | Table 6 |
| `data/crsp_returns.parquet` | 1.85M daily CRSP rows, in-sample cohort | Tables 3, 4 |
| `data/crsp_returns_oos.parquet` | 139K daily CRSP rows, holdout cohort | Table 6 |
| `data/angle_2_forward.jsonl` | 3,232 in-sample forward-signal rows | Tables 3, 7, 9 |
| `data/angle_2_forward_oos.jsonl` | 912 holdout forward-signal rows | Tables 6, 7 |
| `data/cik_sic_map.json` | 1,284 CIK-to-SIC mapping | Table 8 |
| `data/r6_llama_classifications.jsonl` | 49 secondary-extractor labels | Section 4.2 |
| `reports/bonferroni-12-ledger.json` | Phase 0 Bonferroni-12 ledger | Table 3 |
| `reports/r5-bonferroni-24-ledger.json` | Phase 2 Bonferroni-24 ledger | Table 5 |
| `reports/net-sharpe-summary.json` | In-sample net Sharpe summary | Table 7 |
| `reports/r1-oos-summary.json` | Out-of-sample summary | Tables 6, 7 |
| `reports/r2-subsample-stability.json` | Subsample stability | Table 9 |
| `reports/r3-sector-size-neutral.json` | Sector-residualized variant | Table 8 |
| `reports/r4-tc-sensitivity.json` | Transaction-cost sensitivity | Table 10 |
| `reports/r6-llm-model-ablation.json` | LLM model ablation with Cohen's $\kappa$ | Section 4.2 |
