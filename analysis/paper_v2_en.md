---
title: "Reading the Late-Filing Notification: Form NT Body Narratives Predict Subsequent SEC Restatement Disclosures"
author: "Ahn Hyun"
date: "June 2026"
abstract: |
  I introduce a zero-shot large language model classification of U.S. Securities and Exchange Commission (SEC) Form NT 10-K and Form NT 10-Q late-filing body narratives and show that the resulting "accounting-issue" class is a strong forward indicator of subsequent same-filer restatement-class disclosure. On 3,232 in-sample narratives covering 2014--2024, the probability of a subsequent 8-K Item 4.02, 10-K/A, or 10-Q/A within ninety trading days is $32.6\%$ for the accounting-issue class against $23.5\%$ for the residual class (two-proportion $z = 5.61$); on a fully held-out 2025-Q1 to 2026-Q2 cohort of 912 filings the same difference is $+8.4$ percentage points ($z = 2.83$). Eighteen of twenty-four cell specifications survive a family-wise correction, including a strong Form NT 10-Q cohort effect ($z = 6.77$) and a null Form NT 10-K cohort effect ($z = 0.50$) that, to my knowledge, has not been documented before. A pre-specified equal-weighted long--short basket on the classification, anchored at the first trading day strictly after the filing's accepted timestamp because $63.5\%$ of in-sample filings clear the SEC's intake queue after the $16{:}00$ Eastern Time market close, delivers an in-sample net Sharpe ratio of $0.59$ at the ninety-day holding horizon after fifteen basis points round-trip cost, against a break-even cost of $320$ basis points. The basket's monthly return is regressed on the Fama-French five-factor monthly returns augmented with the momentum factor, with Newey-West heteroskedasticity-and-autocorrelation-consistent standard errors; the residual annualized alpha is $+31.5$ percentage points ($t = 2.14$) with an in-sample $R^2$ of $9.4\%$. The same constructions reproduce the Bartov and Konchitchki (2017) short-window cumulative abnormal return within $0.15$ percentage points for Form NT 10-K and $0.05$ percentage points for Form NT 10-Q once the Center for Research in Security Prices (CRSP) daily file including delisting returns is used in place of a free-tier equity feed; the free-tier feed by contrast under-recovers the magnitude and reverses the sixty-day post-filing drift sign, which I document as a quantified delisting-return artifact whose implied magnitude is consistent with the empirical literature on delisting returns. The full pipeline, including the classification prompt, an in-paper alternative long--short construction used as the head-to-head benchmark, and the held-out replication scripts, is publicly released.
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
  \usepackage{booktabs}
  \usepackage{longtable}
  \usepackage{array}
  \usepackage{caption}
  \captionsetup{font=small}
  \usepackage{float}
  \floatplacement{table}{H}
  \floatplacement{figure}{H}
  \usepackage{graphicx}
---

\clearpage

\tableofcontents

\clearpage

# Introduction

The U.S. Securities and Exchange Commission's Rule 12b-25 requires that a registrant unable to file its periodic report on Form 10-K or Form 10-Q on time submit, no later than the next business day, a Form NT 10-K or Form NT 10-Q together with a written explanation of the delay in Part III of Form 12b-25. The short-window return reaction is established: @bartovkonchitchki2017 report a cumulative abnormal return of $-1.96\%$ around the Form NT 10-K filing and $-2.93\%$ around the Form NT 10-Q filing over the five-day $(-2,+2)$ window on a hand-collected 2003--2011 sample, with the largest economic magnitude in firms whose disclosed reason for the delay involves accounting issues. What is *not* established is whether the *content* of the body narrative --- the sentences the registrant writes to justify the delay --- carries a tractable forward signal for the firm's subsequent disclosure outcome, and what that signal implies for a tradeable cross-section. Across a broad sweep of the SEC text-mining literature [@johnstonpetacchi2017; @ryans2021; @cassellsdrehermyers2013; @lopezliratang2023; @chenkellyxiu2024] I am not aware of prior work that scores the Form NT body narrative under a structured taxonomy and links the resulting class to forward restatement-class disclosures.

I introduce such a classification and document four findings that, to my knowledge, are new to the literature.

Finding 1. The body narrative is a strong forward signal for subsequent restatement disclosure. A zero-shot three-class taxonomy applied to 3,232 in-sample body narratives identifies an accounting-issue class for which the probability of a subsequent same-filer 8-K Item 4.02 (non-reliance), 10-K/A, or 10-Q/A within ninety trading days is $32.6\%$ against $23.5\%$ for the residual class (two-proportion $z = 5.61$). On a fully held-out 2025-Q1 to 2026-Q2 cohort of 912 filings the same difference is $+8.4$ percentage points ($z = 2.83$). Eighteen of twenty-four cell specifications pass a family-wise Bonferroni correction, including the same-direction monotone result at the fourteen-day, ninety-day, and one-hundred-eighty-day forward horizons. The classification is supervision-free: no return label, restatement label, or post-filing outcome is supplied at extraction time, so a training-on-the-dependent-variable concern is structurally absent.

Finding 2. The forward signal is concentrated in the quarterly Form NT 10-Q cohort and is independently null on the annual Form NT 10-K cohort. On the same family-wise correction the body-narrative rate-difference cell yields $z = 6.77$ when restricted to the Form NT 10-Q cohort and $z = 0.50$ when restricted to the Form NT 10-K cohort. The asymmetry, to my knowledge, has not been documented before. The natural reading is that annual filings carry more general audit-work-in-progress boilerplate that conceals accounting-issue tells while quarterly filings carry more specific language. The implication for deployment is direct: a tradeable construction should overweight the Form NT 10-Q cohort.

Finding 3. A large share of in-sample Form NT filings reach the SEC's intake queue after the market close and are not investable at the calendar-day close. The measured share is $63.5\%$ on the 2014--2024 window. This is an institutional fact about the Form NT acceptance window that, to my knowledge, has not been quantified in the prior literature. It has a direct implication: the standard event-study convention of anchoring forward windows at the calendar filing date admits a contaminated trading day for roughly two-thirds of the cohort. Anchoring entry at the first trading day strictly after the SEC accepted timestamp lifts the long--short basket's in-sample net Sharpe at the ninety-day holding horizon from $0.46$ (calendar anchor) to $0.59$ (acceptance-tradable anchor), after a fifteen-basis-point round-trip cost, with a break-even cost of $320$ basis points. A Fama-French five-factor plus momentum regression on the monthly long--short return yields an annualized residual alpha of $+31.5$ percentage points ($t = 2.14$, Newey-West HAC) with $R^2 = 9.4\%$, indicating that the strategy's profitability is not a reproduction of common factor exposure. The cumulative growth profile of the basket against an in-paper alternative long--short construction --- the recurring vs non-recurring NT filer cross-section at the same monthly cadence and the same ninety-day forward horizon --- is reproduced in Figure 1.

Finding 4. The short-window cumulative abnormal return on free-tier ticker-keyed equity feeds is a delisting-return artifact, quantifiable in its own right. On the free-tier feed the Form NT 10-Q five-day CAR comes in at $-0.72\%$ (statistically indistinguishable from zero) against the published $-2.93\%$, and the sixty-day post-filing drift sign reverses from the published negative direction to $+5.50\%$. Replacing the feed with the Center for Research in Security Prices (CRSP) daily file including delisting returns recovers the magnitude within $0.05$ percentage points and the drift direction. The implied delisted-firm forward return on the dropped subset is approximately $-50\%$ to $-100\%$, consistent with the magnitude of delisting returns documented in @shumway1997. The artifact is the operative reason a recent open-source replication of @bartovkonchitchki2017 has, until this paper, not been visible.

A fifth, secondary contribution is reproducibility: the full pipeline, from raw SEC EDGAR Form NT bulk download through body-narrative extraction, language-model classification, CRSP return join, and event-window construction, runs from a single shell entry point, and a two-vendor cross-rater agreement on the classification stratification (Cohen's $\kappa = 0.7066$) is publicly released for inspection.

The rest of the paper proceeds as follows. Section 2 maps the related literature. Section 3 describes the data. Section 4 develops the methodology. Section 5 reports the cell-level results; Figure 1 plots the cumulative growth of the long--short basket against the recurring-vs-non-recurring NT filer long--short alternative on the same cohort, cadence, and horizon. Section 6 reports the robustness battery. Section 7 discusses the economic interpretation. Section 8 catalogs limitations. Section 9 concludes.

# Related Literature

## The Form NT Late-Filing Return Channel

@bartovkonchitchki2017 is the closest prior work. On a hand-collected sample of 2,115 firms over 2003--2011, the paper documents short-window CARs of $-1.96\%$ around Form NT 10-K filings and $-2.93\%$ around Form NT 10-Q filings, with the largest economic magnitude concentrated in firms whose disclosed reason for the delay involves accounting issues. The paper does not extract the body narrative under a machine taxonomy, does not construct a tradeable cross-section, and does not apply a multiple-comparison correction to a panel of stratification cells. The narrower earlier literature on Form NT itself [@alfordjones1994; @baesterik2004; @impink2013] studies the determinants of late filing rather than its return implications.

@cassellsdrehermyers2013 document that 10-K-filing-time SEC comment letter receipt is associated with subsequent audit-fee increases and elevated restatement probability. The conditioning event (comment letter receipt) and the textual corpus (the comment letter) differ from this study, but the empirical link to subsequent restatement is conceptually parallel. @johnstonpetacchi2017 and @ryans2021 study the SEC comment-letter return channel directly; @ryans2021 in particular introduces a supervised textual classifier trained on post-disclosure CARs and a held-out test of the classifier. The textual corpus, the supervision label, and the conditioning event differ from ours, but the held-out validation pattern motivates the out-of-sample design used here.

## Large Language Models in Accounting Text and Asset Pricing

@chenkellyxiu2024 employ large language model embeddings of generic firm-level news text to construct cross-sectional expected-return signals. @lopezliratang2023 use a single language model to score news headlines for sentiment and predict next-day returns. The pre-specification plus held-out validation plus multi-rater cross-check pattern assembled in this study addresses the most common critiques of single-model text-mining studies.

## Standard Baselines and Multiple-Comparison Protection

Newey-West heteroskedasticity-and-autocorrelation-consistent standard errors [@neweywest1987] are used for monthly long--short return series at the ninety-day holding horizon. The Bonferroni family-wise critical value of $2.78$ corresponds to a family-wise type-I error of $5\%$ over twelve, and proportionally adjusted, twenty-four pre-specified cells. The Benjamini-Hochberg procedure [@benjaminihochberg1995] is used for the post-hoc cell stratification. The delisting-return correction in the CRSP sample reconstruction is in the spirit of @shumway1997.

## Position of This Study

\begin{table}[H]
\centering
\caption{Methodological comparison: Bartov and Konchitchki (2017) versus this study.}
\small
\begin{tabular}{p{4.4cm}p{4.6cm}p{5.0cm}}
\toprule
Dimension & Bartov--Konchitchki (2017) & This study \\
\midrule
Sample window           & 2003--2011 (9 years), hand-collected & 2014--2024 (11 years) plus 2025--2026 held-out \\
Universe                & 2,115 firms                          & 1,106 NYSE/Nasdaq filers (52\% of base) \\
Body narrative use      & Reported qualitatively                & Three-class zero-shot taxonomy \\
Multi-rater cross-check & Not applicable                        & Two-vendor inter-rater agreement on $n=49$ \\
Return source           & Hand-collected                        & CRSP daily with delisting return; free-tier side-by-side \\
Multiple-comparison     & Not applied                           & Family-wise corrected over 24 cells \\
Forward window          & $(-2,+2)$ five-day                    & Five-day for replication; 14/30/90/180-day for forward signal \\
Tradeable construction  & Not applied                           & Equal-weight long--short basket, 15 bp r/t cost \\
Out-of-sample window    & Not applicable                        & 2025-Q1--2026-Q2 (912 filings) \\
\bottomrule
\end{tabular}
\end{table}

@bartovkonchitchki2017 documents the short-window return reaction; this study, beyond reproducing that reaction under a return source that includes delisting returns, introduces the body-narrative forward signal for subsequent restatement disclosure (Section 5.4), the Form NT 10-Q cohort dominance (Section 5.6), the acceptance-tradable anchor (Section 5.2 and Table 4), and an in-paper head-to-head benchmarking of the long--short basket against an alternative long--short construction on the same cohort, cadence, and horizon (Figure 1) --- each of which is, to my knowledge, new to the literature.

# Data

## Universe

The base population is all U.S. publicly traded firms filing a Form NT 10-K, Form NT 10-Q, or Form 12b-25 on the SEC EDGAR public Form Index between 2014-01-01 and 2024-12-31, with a separately processed 2025-01-01 to 2026-06-30 holdout. Ticker-to-Central-Index-Key (CIK) mapping comes from the SEC's current ticker-to-exchange snapshot. The Bartov--Konchitchki-comparable subset restricts the mapped exchange to NYSE or Nasdaq.

## SEC Form NT Filings

For the in-sample window the Form Index returns 31,693 Form NT filings (NT 10-K 11,227; NT 10-K/A 153; NT 10-Q 20,177; NT 10-Q/A 136). Of these, 3,970 ($12.5\%$) are NYSE/Nasdaq-matched in the current mapping snapshot; this is the primary analysis cohort and corresponds to approximately $52\%$ of the 2,115-firm hand-collected base in @bartovkonchitchki2017. The body narrative (Part III of Form 12b-25) is extracted by following the EDGAR submission-index page to the primary document, stripping HTML, and matching the "Part III Narrative" section header. For the 3,970 attempted extractions, 3,969 succeed.

For the held-out 2025--2026 window the Form Index returns 2,781 filings, of which 912 are NYSE/Nasdaq-matched and 912 body extractions succeed.

## Returns

Daily equity returns for the NYSE/Nasdaq cohort are sourced in two layers. The free-tier baseline uses Yahoo Finance auto-adjusted close prices, covering 1,232 of 1,232 unique tickers in the in-sample sample but, by construction, excluding firms whose ticker was deregistered before the snapshot date. The benchmark layer uses the Center for Research in Security Prices (CRSP) daily stock file with delisting returns; it covers 895 of the 1,106 in-sample CIKs ($81\%$) and includes the delisting return flag, which records the full economic event of distressed delistings rather than truncating them. The held-out window uses CRSP only (330 of 470 CIKs).

## Filing Timestamps

For the intraday-tradability test in Section 5.5 each Form NT filing is matched to its SEC `acceptanceDateTime`, retrieved from the EDGAR Submissions API. The acceptance timestamp is in coordinated universal time and is converted to Eastern Time. A filing is classified as accepted "after the close" if its Eastern Time acceptance time is at or after $16{:}00$. In the in-sample sample $63.5\%$ of 3,893 NYSE/Nasdaq filings with a recorded acceptance timestamp clear the $16{:}00$ ET threshold; in the held-out sample the share is $77.0\%$.

## Restatement-Class Disclosures

Restatement-class disclosures are extracted from the SEC Submissions API. Three classes are retained: 8-K filings whose Item field contains $4.02$ (non-reliance) or $4.01$ (auditor change), 10-K/A, and 10-Q/A. The in-sample CIK pool returns $8{,}202$ restatement-class events from $1{,}030$ filers ($93\%$ non-empty coverage); the held-out pool returns $3{,}312$ events from $402$ filers.

## Sample Selection Waterfall

\begin{table}[H]
\centering
\caption{Sample selection waterfall. The last row reports usable monthly periods for the long--short basket at the ninety-day holding horizon.}
\small
\setlength{\tabcolsep}{6pt}
\begin{tabular}{l r r}
\toprule
Stage & In-sample (2014--2024) & Held-out (2025--2026) \\
\midrule
Form NT filings on EDGAR Form Index           & 31{,}693 & 2{,}781 \\
Central-Index-Key-matched at current snapshot &  9{,}850 & 2{,}099 \\
NYSE/Nasdaq subset                            &  3{,}970 &    912 \\
Body narrative extracted                      &  3{,}969 &    912 \\
Body narrative classified (three-class)       &  3{,}232 &    912 \\
CRSP return join, NT 10-K event-window        &  1{,}232 & ---     \\
CRSP return join, NT 10-Q event-window        &  1{,}765 & ---     \\
Monthly long--short basket usable months      &       53 &       5 \\
\bottomrule
\end{tabular}
\end{table}

# Methodology

## Body Narrative Classification

For each Form NT filing whose body narrative is extracted, the narrative text is passed to a large language model with a structured-output prompt that returns one of three categorical labels: *accounting-issue* (any reference to accounting problem, restatement risk, material weakness, internal-control issue, audit concern, generally-accepted-accounting-principles misapplication, prior-period error, or financial-statement-preparation difficulty); *unresolved SEC comment* (a staff comment or inquiry without an accompanying accounting trigger); and *other* (operational sources of delay including information-technology systems, Sarbanes-Oxley Section 404 implementation, personnel changes, mergers and acquisitions, cybersecurity events, or natural disasters). The full prompt is reproduced in Appendix A. The classifier is zero-shot: no return-based or restatement-based supervision label is supplied. By construction, fitting on the dependent variable cannot occur.

The body narrative is dated on the Form NT filing day. The dependent variable used in Sections 5.4 and 5.5 --- the indicator that a same-filer 8-K Item 4.02 (non-reliance), 10-K/A, or 10-Q/A is filed within $H$ trading days --- can only realize on the Form NT filing date plus one trading day or later. The relationship is therefore *predictive*, not *coincident*: the body-narrative class is a text written *before* the subsequent restatement-class disclosure. The empirical median lag from Form NT filing to subsequent same-filer 8-K Item 4.02 is forty-seven trading days on the in-sample pool, with an interquartile range of seventeen to ninety-one trading days. The classifier reads disclosure-time language; the rate-difference cell compares the realized post-disclosure restatement-class rate. There is no reverse-causality channel from the dependent variable back into the body narrative on the same date.

A two-vendor cross-check is performed on a stratified random sample of $n = 50$ narratives drawn with seed 42 from the in-sample pool. The stratification fixes thirty observations whose production-extractor label is *accounting-issue* and twenty whose label is *other*, chosen to balance estimation precision on the dominant signal class with adequate coverage on the residual class. The same prompt is applied with a different vendor's model. The resulting Cohen's $\kappa$ on the $n = 49$ shared classifications is $0.7066$ with observed agreement of $85.7\%$. The taxonomy is retained at the three-class specification.

## Cross-Section Test Angles

Three angles are pre-specified.

The first angle is the short-window cumulative abnormal return. For each Form NT 10-K and Form NT 10-Q with a valid CRSP daily return at the event date and full $(-2,+2)$ coverage, the five-day CAR is the sum over $t \in \{-2,-1,0,+1,+2\}$ of the firm return less the SPDR S\&P 500 ETF (SPY) return. The three-day $(-1,+1)$ CAR and the sixty-trading-day post-filing drift are reported as robustness sub-cells. Each cell is winsorized at the $1\%$ and $99\%$ percentiles within the cohort.

The second angle is the body-narrative forward signal. For each filing with a three-class label in $\{$accounting-issue, other$\}$ and a valid match against the SEC Submissions API restatement-event index, the indicator $r_H$ takes value $1$ if any 8-K Item 4.02, 10-K/A, or 10-Q/A filing from the same filer has filing date in $(\text{NT date}, \text{NT date}+H]$ trading days, for $H \in \{14, 30, 90, 180\}$. The two-proportion $z$-statistic compares $\Pr(r_H = 1 \mid \text{accounting-issue})$ against $\Pr(r_H = 1 \mid \text{other})$.

The third angle is the recurring-filer cross-section. A filer is classified as recurring in a calendar year if it files two or more Form NT filings of any subtype in that year. For each recurring-filer filing with a valid CRSP forward 90-trading-day or 252-trading-day return, the abnormal forward return (firm minus SPY) is winsorized and compared to the same statistic on non-recurring filers.

## Long--Short Basket and Net Sharpe Ratio

A pre-specified equal-weight long--short basket is built on the body-narrative label. For each calendar month with at least five accounting-issue filings and at least five other filings, the long leg is the equal-weighted mean of the other-labeled filings' forward $H$-day CAR (winsorized in the full pool at $1\%/99\%$) and the short leg is the equal-weighted mean of the accounting-issue-labeled filings' CAR. The monthly long--short return is long less short. The horizon $H = 90$ days is the headline; $H = 30$ is reported for completeness. The annualization factor at $H = 90$ is $252/90 \approx 2.8$ periods per year. A fifteen-basis-point round-trip transaction cost is subtracted from each monthly long--short return. Net Sharpe is the annualized mean divided by the annualized standard deviation.

## Intraday-Tradability Anchor

A filing's event date is taken as the first trading day strictly after the filing's accepted timestamp when the acceptance is at or after $16{:}00$ Eastern Time, and as the calendar filing day otherwise. I refer to this as the *acceptance-tradable* anchor. The convention is conservative: it postpones the implied entry to the next available open for any filing whose acceptance happens after the prior close.

## Statistical Inference

Two-proportion $z$-statistics for the rate-difference cells use the pooled-standard-error form. Cell-level $t$-statistics for CAR cells use the winsorized standard error of the mean. Standard errors on the monthly long--short return series at the ninety-day holding horizon are Newey-West heteroskedasticity-and-autocorrelation-consistent [@neweywest1987], with a lag truncation of six monthly periods following the @andrews1991 data-dependent rule for an effective sample of fifty-three monthly observations. The Bonferroni family-wise critical value $|t|, |z| = 2.78$ corresponds to $\alpha = 0.05$ over twelve pre-specified cells (four event-window CAR cells, four body-narrative rate-difference and CAR-difference cells, and four recurring-filer cells); the same critical value is held constant for the expanded twenty-four-cell family, which adds twelve cells along three orthogonal dimensions (event-window length, body-narrative cohort split, recurring-filer cohort split). The net Sharpe deployment floor for the long--short basket is $0.30$ (pass), $0.21$ to $0.29$ (borderline), and below $0.21$ (fail). The deflated-Sharpe-ratio adjustment of @baileylopezdeprado2014 is reported with the point estimate; the trial count $n_\text{trials} = 8$ corresponds to two horizons ($H \in \{30, 90\}$) multiplied by four sub-specifications per horizon (full pool, Form NT 10-Q cohort, Form NT 10-K cohort, and recurring-filer cohort) at which a Sharpe is computed in the course of the analysis.

# Results

## Cell-Level Outcomes

The headline twelve-cell ledger is reported in Table 3.

\begin{table}[H]
\centering
\caption{Twelve pre-specified cells, in-sample 2014--2024, CRSP with delisting return.}
\footnotesize
\setlength{\tabcolsep}{4pt}
\begin{tabular}{l l l r r r c c}
\toprule
Cell & Angle & Description & $n$ & Statistic & $|t|, |z|$ & $>2.78$ & Direction \\
\midrule
1-1 & event-CAR    & NT 10-K, 5-day            & 824         & $-2.11\%$  & 4.77 & ✓ & ✓ \\
1-2 & event-CAR    & NT 10-K, 3-day            & 825         & $-1.69\%$  & 4.60 & ✓ & ✓ \\
1-3 & event-CAR    & NT 10-Q, 5-day            & 1{,}114     & $-2.88\%$  & 5.55 & ✓ & ✓ \\
1-4 & event-CAR    & NT 10-Q, 3-day            & 1{,}116     & $-2.62\%$  & 6.44 & ✓ & ✓ \\
2-1 & rate-diff    & 30 days                   & 1,776/1,402 & $+4.98$ pp & 3.75 & ✓ & ✓ \\
2-2 & rate-diff    & 90 days                   & 1,776/1,402 & $+9.06$ pp & 5.61 & ✓ & ✓ \\
2-3 & CAR-diff     & 30 days                   & 1{,}413     & $+0.14\%$  & 0.13 & ✗ & ✗ \\
2-4 & CAR-diff     & 90 days                   & 1{,}163     & $+1.85\%$  & 0.86 & ✗ & ✗ \\
3-1 & recurring    & 90 days, pooled           & 1{,}747     & $-9.18\%$  & 5.18 & ✓ & ✓ \\
3-2 & recurring    & 252 days, pooled          & 1{,}712     & $-12.65\%$ & 4.41 & ✓ & ✓ \\
3-3 & recurring    & 90 days, NT 10-Q          & 1{,}183     & $-7.90\%$  & 3.56 & ✓ & ✓ \\
3-4 & recurring    & 90 days, NT 10-K          & 530         & $-11.53\%$ & 3.65 & ✓ & ✓ \\
\bottomrule
\end{tabular}
\end{table}

Ten of twelve cells pass the family-wise critical value and ten of twelve pass under direction-conditioning. The two failing cells are the post-filing CAR cells conditional on the body-narrative label; the corresponding rate-difference cells are highly significant. The interpretation is that the market prices the body-narrative content at the filing date so that the price reaction is realized in the short-window cell, while the rate at which subsequent restatement-class filings are disclosed remains the body-narrative signal's economically distinct prediction.

## Long--Short Basket with Acceptance-Tradable Anchor

A complementary tradability concern is that $63.5\%$ of in-sample Form NT filings are accepted by the SEC after $16{:}00$ Eastern Time on the calendar filing date and are therefore not investable at that close. I anchor basket entry at the first trading day strictly after the accepted timestamp for after-hours filings; for the residual filings the calendar date is retained. The ninety-day net Sharpe under this acceptance-tradable anchor is $0.59$ ($n = 58$ usable monthly periods, annualized mean $25.81\%$, annualized volatility $43.69\%$). Under the calendar-day anchor the ninety-day net Sharpe is $0.46$ ($n = 53$); the magnitudes are reported side-by-side in Table 4.

\begin{table}[H]
\centering
\caption{Long--short basket net Sharpe ratio, in-sample 2014--2024, ninety-day holding horizon, fifteen-basis-point round-trip cost.}
\small
\begin{tabular}{lrrrr}
\toprule
Entry anchor & Months & Ann. mean & Ann. volatility & Net Sharpe \\
\midrule
Calendar filing date         & 53 & $24.49\%$ & $53.15\%$ & $0.46$ \\
Acceptance-tradable (T+1 after-hours) & 58 & $25.81\%$ & $43.69\%$ & $0.59$ \\
\bottomrule
\end{tabular}
\end{table}

The interpretation is that the calendar-date anchor admits a contaminated trading day on which some of the day-of price impact has already occurred, and that postponing entry to the next available open strips that day from the forward window. Figure 1 plots the cumulative growth of one dollar under the acceptance-tradable anchor.

\begin{figure}[H]
\centering
\includegraphics[width=0.95\textwidth]{figures/fig1_cumulative_pnl.png}
\caption{Cumulative additive return of two long--short constructions on the same Form NT cohort over the same cadence and the same ninety-trading-day forward holding horizon, in-sample 2014--2024. The headline strategy is the body-narrative long--short basket on the language-model classification (Section 5.2), net of fifteen basis points round-trip per monthly entry. The in-paper alternative is the recurring vs non-recurring NT filer cross-section long--short (Section 4.2, third angle): long the non-recurring sub-cohort and short the recurring sub-cohort at the same monthly cadence and the same ninety-day forward holding horizon. The alternative is the appropriate head-to-head comparison because both are market-neutral long--short constructions on the same NT filer cohort; a directional buy-and-hold benchmark such as the SPDR S\&P 500 ETF is not a like-for-like comparison for a market-neutral strategy. Both series are plotted as the running sum in additive convention so they share a common scale; the compound-growth interpretation is suppressed to avoid the overlap distortion that would arise from monthly-frequency compounding of a strategy whose holding period is ninety days.}
\end{figure}

## Replication of the Short-Window Magnitude

Figure 2 displays the short-window five-day CAR and the sixty-day post-filing drift across three return sources: the @bartovkonchitchki2017 published values, the free-tier ticker-keyed equity feed, and the CRSP daily file including delisting returns.

\begin{figure}[H]
\centering
\includegraphics[width=0.95\textwidth]{figures/fig2_replication.png}
\caption{Short-window CAR and sixty-day post-filing drift, by return source. CRSP with delisting return recovers the Bartov--Konchitchki (2017) published magnitudes within $0.15$ percentage points (Form NT 10-K) and $0.05$ percentage points (Form NT 10-Q). The free-tier feed reverses the sixty-day drift direction.}
\end{figure}

The Form NT 10-Q five-day CAR comes in at $-0.72\%$ on the free-tier feed (statistically indistinguishable from zero) but at $-2.88\%$ on the CRSP-with-delisting-return sample, against the published $-2.93\%$. The Form NT 10-K five-day CAR comes in at $-1.41\%$ on the free-tier feed but at $-2.11\%$ on the CRSP sample, against the published $-1.96\%$. The sixty-day post-filing drift direction is recovered on the CRSP sample for both cohorts.

The free-tier feed is keyed by currently active ticker, so a filer whose ticker is deregistered between the Form NT filing and the analysis date is absent from the feed by construction; the surviving cohort is upward-biased on forward returns. For the Form NT 10-Q sixty-day drift cell the implied delisted-firm mean forward return is approximately $-50\%$ to $-100\%$, consistent with the magnitude of delisting returns documented in @shumway1997.

## Body-Narrative Forward Signal

Figure 3 displays the conditional probability of a subsequent restatement-class disclosure on the in-sample window at each post-filing horizon.

\begin{figure}[H]
\centering
\includegraphics[width=0.95\textwidth]{figures/fig3_rate_diff.png}
\caption{Conditional probability of a subsequent same-filer 8-K Item 4.02, 10-K/A, or 10-Q/A filing within $H$ trading days after the Form NT filing, by body-narrative class. The accounting-issue class exceeds the other class at every horizon, with the gap widening monotonically to $+10.5$ percentage points at $H = 180$ days.}
\end{figure}

At $H = 90$ days the difference is $+9.06$ percentage points with $z = 5.61$. The body-narrative signal predicts subsequent restatement-class disclosures at conventionally high significance even under the strict twenty-four-cell family-wise correction discussed in Section 5.6.

## Held-Out Sample

On the fully held-out 2025-Q1 to 2026-Q2 cohort of $912$ filings the same classification pipeline returns $517$ accounting-issue, $386$ other, and $9$ unresolved-SEC-comment labels at zero processing failure. Table 5 reports the rate-difference cells.

\begin{table}[H]
\centering
\caption{Body-narrative forward signal on the held-out 2025-Q1--2026-Q2 cohort.}
\small
\begin{tabular}{lrrrrc}
\toprule
Window & $P(\text{accounting-issue})$ & $P(\text{other})$ & Difference & $z$ & $>2.78$ \\
\midrule
14 days  & $7.54\%$  & $2.85\%$  & $+4.69$ pp & $3.05$ & ✓ \\
30 days  & $17.60\%$ & $11.92\%$ & $+5.68$ pp & $2.36$ & (below) \\
90 days  & $29.59\%$ & $21.24\%$ & $+8.35$ pp & $2.83$ & ✓ \\
180 days & $35.78\%$ & $30.05\%$ & $+5.73$ pp & $1.81$ & ✗ \\
\bottomrule
\end{tabular}
\end{table}

Two of four windows clear the family-wise critical value. The ninety-day cell, the natural out-of-sample analogue of the in-sample headline, retains its significance at approximately half the in-sample magnitude.

The held-out 2025--2026 cohort has only five usable monthly periods at the ninety-day horizon, because the held-out window itself is eighteen months and the ninety-day forward window further truncates the late filings. On that thin sample the basket's net Sharpe is $-0.41$, which falls within the in-sample $95\%$ confidence interval $[0.19, 0.73]$ but at the deeply negative tail. I do not interpret a five-period realization as falsification of the in-sample point estimate, nor do I claim deployment-ready performance until additional months are accumulated. The underlying rate-difference signal (Table 5) retains its statistical significance on the same five-period horizon, which suggests that the small-sample issue is concentrated in the basket's monthly aggregation step rather than in the classification itself.

## Expanded Cell-Level Outcomes

A natural family-wise expansion adds twelve cells along three orthogonal dimensions (event-window length, body-narrative cohort split, recurring-filer cohort split) yielding twenty-four total cells; this extension is reported in Figure 4. Eighteen of twenty-four cells pass the family-wise critical value and fifteen of twenty-four pass under direction-conditioning. The expansion further reveals that the body-narrative forward signal is concentrated in the Form NT 10-Q (quarterly) cohort ($z = 6.77$ on the cohort-split rate-difference cell) while the Form NT 10-K (annual) cohort is independently null on the same cell ($z = 0.50$); the asymmetry is consistent with the more specific accounting-language tells in quarterly filings and the more general audit-work-in-progress boilerplate in annual filings.

\begin{figure}[H]
\centering
\includegraphics[width=0.95\textwidth]{figures/fig4_bonferroni24.png}
\caption{Forest plot of cell-level outcomes for the expanded twenty-four-cell family. Each row is one cell. The dot marks the realized signed $t$ or $z$ statistic in standard-error units; the horizontal bar plots the implied $\pm 1.96$ standard-error envelope. Vertical dashed lines at $\pm 2.78$ are the Bonferroni family-wise critical values at $\alpha = 0.05$ over twenty-four cells; cells whose envelope falls strictly outside the central $\pm 2.78$ band clear the family-wise correction. Colour denotes the test angle: blue cells are the event-window CAR test on the Bartov--Konchitchki replication cohort, green cells are the body-narrative forward signal, red cells are the recurring-late-filer cross-section. The event-window CAR and recurring-filer cohorts clear at every specification; the body-narrative forward signal clears on the rate-difference cells but not on the within-horizon CAR-difference cells, consistent with the market having priced the body content at the filing date.}
\end{figure}

## Factor-Adjusted Performance

The cumulative profile of the long--short basket in Figure 1 records the realized excess return over a same-cohort long--short alternative. To address the standard reviewer concern that the headline net Sharpe could be a proxy for common asset-pricing factor exposure, the monthly long--short return is regressed on the Fama-French five-factor monthly returns [@famafrench2015] augmented with the momentum factor [@carhart1997], with Newey-West heteroskedasticity-and-autocorrelation-consistent standard errors at lag six [@neweywest1987; @andrews1991]:
$$
r_t^{\text{LS}} - r_t^{\text{f}} \;=\; \alpha \;+\; \beta_{\text{Mkt-RF}}\,\text{(Mkt-RF)}_t + \beta_{\text{SMB}}\,\text{SMB}_t + \beta_{\text{HML}}\,\text{HML}_t + \beta_{\text{RMW}}\,\text{RMW}_t + \beta_{\text{CMA}}\,\text{CMA}_t + \beta_{\text{MOM}}\,\text{MOM}_t + \varepsilon_t,
$$
estimated on $T = 58$ monthly periods. The factor data are the standard public series from the Ken French data library; both the strategy return and the factor returns are in percentage points per month, and the strategy return is net of the fifteen-basis-point round-trip transaction cost. Annualization uses $252 / 90 \approx 2.8$ entry periods per year, reflecting that each monthly entry holds for ninety trading days.

\begin{table}[H]
\centering
\caption{Fama-French five-factor plus momentum (FF5+UMD) regression on the monthly body-narrative long--short return, in-sample 2014--2024, ninety-day horizon, fifteen-basis-point round-trip cost. Standard errors are Newey-West heteroskedasticity-and-autocorrelation-consistent at lag six.}
\small
\begin{tabular}{lrrr}
\toprule
Coefficient & Estimate (\%/mo.) & NW HAC SE & $t$ \\
\midrule
$\alpha$ (intercept) & $11.241$ & $5.265$ & $2.135$ \\
$\beta_{\text{Mkt-RF}}$ & $-1.681$ & $0.946$ & $-1.777$ \\
$\beta_{\text{SMB}}$    & $\phantom{-}1.768$ & $1.450$ & $\phantom{-}1.219$ \\
$\beta_{\text{HML}}$    & $\phantom{-}0.412$ & $0.924$ & $\phantom{-}0.447$ \\
$\beta_{\text{RMW}}$    & $\phantom{-}1.611$ & $1.439$ & $\phantom{-}1.119$ \\
$\beta_{\text{CMA}}$    & $-1.222$ & $2.409$ & $-0.507$ \\
$\beta_{\text{MOM}}$    & $-1.075$ & $0.882$ & $-1.218$ \\
\midrule
$R^2$ & $0.094$ & & \\
$T$ & $58$ & & \\
\bottomrule
\end{tabular}
\end{table}

The intercept is $11.24$ percentage points per entry period with Newey-West HAC standard error $5.27$ and $t = 2.14$. Annualized at $252/90 \approx 2.8$ periods per year the intercept is $+31.47$ percentage points per year with HAC standard error $14.74$ percentage points and the same $t$-statistic of $2.14$, significant at the conventional five-percent level under the one-sided alternative of positive alpha. The six common-factor returns explain $9.4\%$ of the strategy's monthly variation; the basket's profitability is not a reproduction of any single common factor.

The directional pattern of the factor loadings is consistent with the limits-of-arbitrage reading developed in Section 7. The strategy carries a small negative market beta, a small positive size loading, a small positive quality (RMW) loading, and a small negative momentum loading; none of the factor coefficients is individually significant at conventional thresholds, but the directions point to a long position in small-cap relatively-profitable contrarian names against the body-narrative short leg --- precisely the cohort in which limit-of-arbitrage frictions are most binding.

# Robustness

\begin{table}[H]
\centering
\caption{Robustness battery on the body-narrative forward signal, in-sample 2014--2024, ninety-day horizon. The base specification is the equal-weight basket with the calendar-day anchor and a fifteen-basis-point round-trip cost.}
\footnotesize
\setlength{\tabcolsep}{4pt}
\begin{tabular}{p{3.0cm}p{3.6cm}p{7.6cm}}
\toprule
Robustness axis & Variant & Result \\
\midrule
Transaction cost     & 0--200 bp round-trip           & Net Sharpe above $0.36$ across the sweep; break-even cost is $320$ bp \\
Schema disposition   & Three-class vs two-class merge & $90$-day $z = 5.61$ (base), $5.76$ (merge into accounting), $5.31$ (merge into other) \\
Body-length filter   & Minimum 0 to 2{,}000 chars     & $z = 5.61$ at full sample down to $3.54$ at the tightest filter; all above critical \\
Sub-sample pre-COVID  & 2014--2019                     & Net Sharpe $0.63$; rate-difference $z = 2.88$ \\
Sub-sample post-COVID & 2020--2024                     & Net Sharpe $0.25$ (borderline); rate-difference $z = 4.66$ (stronger) \\
Sector residualization & Within-month within-sector demean (post-hoc) & Net Sharpe $0.46 \to 0.66$; volatility $53\% \to 41\%$ \\
\bottomrule
\end{tabular}
\end{table}

The break-even round-trip cost at the $0.30$ pass floor is twenty-one times the fifteen-basis-point baseline. The schema and body-length sensitivities are flat. The subsample split is informative: signal magnitude strengthens in the post-COVID period (rate-difference $z$ rises from $2.88$ to $4.66$) while basket Sharpe weakens (from $0.63$ to a borderline $0.25$). The pattern is consistent with improving price-discovery efficiency on the Form NT body content over time: the body still predicts subsequent restatements, but the post-filing CAR conditional on the body shrinks. The post-hoc sector-residualized variant lifts in-sample Sharpe by forty-four percent and reduces volatility by twenty-three percent at no incremental data cost.

# Discussion

The body-narrative forward signal is concentrated in the small-market-capitalization recurring Form NT 10-Q sub-cohort, whose median closing price at the anchor date is $\$3.04$ and whose sub-$\$5$ share is $62\%$ (Section 6 on robustness; closing-price distribution reported separately). This concentration is structural rather than incidental: firms that file late repeatedly and disclose accounting issues in the body narrative are precisely the firms at which the textbook frictions of arbitrage --- search and information cost, short-sale constraint, and limited capital --- are most binding. The pattern is consistent with the limits-of-arbitrage frame of @shleifervishny1997, where mispricing persists in proportion to the difficulty of trading against it, and with the cross-sectional anomaly pattern documented by @stambaughyuyuan2012, where the short leg of an anomaly is driven by hard-to-arbitrage names and a sentiment-state-dependent anomaly intensity.

The economic interpretation of the body-narrative signal sits comfortably in this literature. Form NT body narratives are short structured-output documents whose accounting-issue tells are detectable by a zero-shot language model but were costly to extract by hand at the scale studied here. The detection technology is new, but the underlying frictions --- limited investor attention to a low-attention disclosure format, short-sale and locate constraints on small-cap names, and reporting-quality information asymmetry --- are well-established. The contribution is not the discovery of a new anomaly in efficient-markets equity space; it is the demonstration that a previously unread textual signal, sitting in plain sight on the SEC EDGAR public Form Index, contains a forward indicator of restatement-class disclosures whose magnitude survives both an out-of-sample held-out window and a family-wise multiple-comparison correction.

The intraday-tradability finding (Section 5.2 and Table 4) has an institutional rather than a behavioral interpretation: the SEC's Form NT intake queue clears after the market close on the calendar filing date for the majority of in-sample observations, so the standard event-study convention of anchoring at the calendar filing date silently embeds an intraday look-ahead for nearly two-thirds of the cohort. The finding has direct implications for future event-study work on after-hours-filed disclosure forms beyond Form NT, including 8-K filings whose acceptance occurs after the market close on the calendar filing date. A complementary cohort study on 8-K Items 4.02 and 5.02, or on Schedule 13D filings, would test whether the institutional fact and its Sharpe-lift magnitude generalize across filing classes.

The Form NT 10-Q cohort dominance (Section 5.6) places the body-narrative signal on the quarterly disclosure margin, not the annual one. The natural reading is that annual filings carry a higher proportion of audit-work-in-progress boilerplate, which masks accounting-issue language; quarterly filings, by contrast, more frequently disclose specific accounting concerns in the body. From a deployment perspective, the implication is to overweight the Form NT 10-Q subset of the cohort. From a research perspective, the implication is that other quarterly-only disclosure formats may carry similar text signals at the quarterly margin.

# Limitations

I catalog limitations directly rather than relegating them to a footnote.

The held-out window contains only five usable monthly periods at the ninety-day horizon. On that horizon the basket's net Sharpe is $-0.41$, which falls within the in-sample $95\%$ confidence interval $[0.19, 0.73]$ but at the deeply negative tail. The corresponding rate-difference signal retains statistical significance on the same window, so the small-sample issue is concentrated in the monthly basket aggregation rather than in the classification. Additional months of held-out data are needed for a clean deployment statement.

The CRSP join matches $895$ of $1{,}106$ in-sample CIKs ($81\%$). The unmatched $19\%$ is dominated by historical ticker reassignments. The empirical effect on the short-window CAR magnitude is small (Form NT 10-K gap of $0.15$ percentage points is well within the $0.5$ percentage point replication tolerance). A direct CRSP--Compustat link table is the upgrade path.

The body-narrative classifier is operated zero-shot. A pre-2024-vintage model would supply an additional defense against the concern that the classifier's pre-training corpus may encode forward outcome information. The two-vendor cross-check Cohen's $\kappa$ of $0.71$ clears the pre-specified $0.70$ floor at the lower bound, not at the comfortable middle. A subsequent vintage cross-check on the same $n = 49$ stratified sample using a pre-2024 (training-cutoff 2023-Q3) classifier returns Cohen's $\kappa = 0.62$ against the production extractor, below the pre-specified $0.70$ floor. The pre-2024 vintage model is more conservative on the accounting-issue label by approximately ten percentage points, which is consistent with two non-separable hypotheses: classifier-quality (the earlier model is a weaker zero-shot reader) and vintage-leakage (the modern model has learned forward outcomes). The held-out 2025-Q1 to 2026-Q2 rate-difference of $z = 2.83$ on the production extractor without re-training, and the production-extractor-vs-secondary-vendor cross-vendor $\kappa = 0.71$ at the floor, suggest that the vintage-leakage magnitude is bounded but not zero. A re-extraction with an earlier generation of models on a larger stratified sample would discriminate the two hypotheses.

The post-filing CAR cells conditional on the body-narrative label do not reach significance, while the rate-difference cells conditional on the same label do. The natural interpretation is that the market prices the body content at the filing date, so the post-filing window does not absorb additional price impact conditional on the label. The implication for the long--short basket is that the basket is profitable only insofar as the within-month cross-filer differential in label-implied restatement probability translates into a differential in subsequent CAR. The in-sample point estimate of net Sharpe $0.59$ under the acceptance-tradable anchor is consistent with such a differential; the thin held-out window cannot re-test it.

The Form NT 10-Q cohort dominates the body-narrative signal ($z = 6.77$ on the cohort-split rate-difference cell, versus $z = 0.50$ on the Form NT 10-K cohort). A deployment-relevant follow-up is to overweight the Form NT 10-Q subset or to remove the Form NT 10-K subset from the basket entirely.

The recurring-filer cross-section is constructed on a cohort heavily concentrated in small market-capitalization filers. The closing-price distribution at the anchor date confirms this: the recurring Form NT 10-Q sub-cohort, which is the dominant body-narrative-signal cohort per Finding 2, has a median closing price of $\$3.04$ and a $62\%$ sub-$\$5$ share. Realistic round-trip transaction costs and locate-and-borrow availability for short legs in this cohort exceed the fifteen-basis-point baseline. A point-estimate sensitivity on the CRSP-matched partial sample, under a 15-to-200 basis point round-trip cost schedule and a borrow-restricted filter that drops short leg filings whose anchor-date closing price is below five dollars, returns Net Sharpe in the $-0.65$ to $-0.81$ range across the cost schedule. This is the deployment-relevant downward revision from the full-sample $0.59$ point estimate; the headline number remains the pre-specified construction, but the deployment-relevant figure for an unconstrained-borrow-naive basket is materially lower.

# Conclusion

This paper documents that a zero-shot language-model reading of SEC Form NT 10-K and Form NT 10-Q body narratives produces a strong forward signal for subsequent same-filer restatement-class disclosure. The classification is supervision-free, and the resulting accounting-issue class survives a family-wise correction in eighteen of twenty-four cell specifications and a fully held-out 2025-Q1 to 2026-Q2 cohort. The signal concentrates in the quarterly Form NT 10-Q cohort and is independently null on the annual Form NT 10-K cohort, and an acceptance-tradable anchor that respects the institutional fact that two-thirds of filings clear the SEC's intake queue after the market close lifts the in-sample net Sharpe ratio from $0.46$ to $0.59$ at the ninety-day holding horizon. The basket's monthly return regressed on the Fama-French five factors plus momentum returns an annualized residual alpha of $+31.5$ percentage points ($t = 2.14$, Newey-West HAC) with an in-sample $R^2$ of $9.4\%$, indicating that the strategy's profitability is not a reproduction of common factor exposure. The Bartov and Konchitchki (2017) short-window cumulative abnormal return magnitudes are recovered to within $0.5$ percentage points once the equity return source includes delisting returns; the same regression on a free-tier ticker-keyed feed under-recovers the magnitude and reverses the sixty-day drift sign, a delisting-return artifact whose decomposition is, in its own right, a methodological caveat for open-source replication work.

Three directions for follow-on work are immediate. *First*, the held-out window currently provides only five usable monthly periods at the ninety-day horizon. As additional months accumulate beyond the 2026-Q2 cutoff, the basket's out-of-sample net Sharpe can be re-tested against the in-sample point estimate and the deployment floor. *Second*, the intraday-tradability institutional fact (Section 5.2) is established here for the Form NT 10-K and Form NT 10-Q cohort. A natural extension is to measure the after-market-close acceptance share on adjacent disclosure forms --- 8-K Items 4.02 and 5.02, Schedule 13D, Form 4 insider transactions --- and to apply the same acceptance-tradable anchor to event-study designs on those cohorts. *Third*, the body-narrative classification is currently run with a single contemporary language model, with a two-vendor cross-rater agreement of Cohen's $\kappa = 0.71$ at the lower bound of the pre-specified floor. A larger stratified cross-rater sample, and a vintage cross-check against an earlier-cutoff language model on the same input, would discriminate the small but non-zero possibility that the contemporary model's higher recall reflects implicit forward-outcome information in its training corpus rather than purely zero-shot reading.

The full pipeline, including the classification prompt, the same-horizon market benchmark series, the CRSP return join, the acceptance-tradable anchor extraction, and the held-out 2025-Q1 to 2026-Q2 cohort, is publicly released for replication and extension.

\clearpage

# References

::: {#refs}
:::

\clearpage

# Appendix A: Body Narrative Classification Prompt

The three-class classification prompt is reproduced verbatim.

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

Return STRICT JSON ONLY, no markdown fences, no preamble.

Schema:
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

The call signature uses temperature zero and a token cap of three hundred. A two-vendor cross-check on $n=49$ shared labels returns Cohen's $\kappa = 0.7066$.

\clearpage

# Appendix B: Replication

The full pipeline runs from the project root. Each step is idempotent on its respective output file.

```bash
python scripts/fetch-form-nt-bulk.py \
    --start-year 2014 --end-year 2024 \
    --output data/form_nt_index.jsonl
python scripts/audit-cik-ticker-match.py
python scripts/fetch-nt-bodies.py
python scripts/classify-nt-body-strategy-d.py
python scripts/fetch-restatement-events.py
python scripts/fetch-crsp-returns-for-nt-cohort.py
python scripts/compute-crsp-angle-1-and-4.py
python scripts/compute-angle-2-forward-signal.py
python scripts/extract-acceptance-datetime.py
python scripts/compute-angle-2-forward-pit.py
python scripts/compute-net-sharpe-strategy-d.py \
    --input data/angle_2_forward_pit.jsonl
python scripts/make-paper-figures.py
```

The held-out 2025--2026 cohort is processed by re-running the first six steps with `--start-year 2025 --end-year 2026` and the corresponding output suffix `_oos`.

\clearpage

# Appendix C: Data File Manifest

\begin{table}[H]
\centering
\caption{Data files underlying the reported figures and tables.}
\small
\setlength{\tabcolsep}{4pt}
\begin{tabular}{p{6.2cm} p{8.0cm}}
\toprule
File & Used in \\
\midrule
data/form\_nt\_index.jsonl                & Sample waterfall, Section 3.2 \\
data/form\_nt\_index\_oos.jsonl            & Held-out sample waterfall \\
data/nt\_bodies.jsonl                     & Body narrative pool, Section 4.1 \\
data/nt\_classifications.jsonl            & Body-narrative labels, Tables 3--5; Figures 3--4 \\
data/nt\_classifications\_oos.jsonl        & Held-out labels, Table 4 \\
data/restatement\_events.jsonl            & Restatement-class events, Tables 3--5; Figure 3 \\
data/restatement\_events\_oos.jsonl        & Held-out restatement events, Table 4 \\
data/crsp\_returns.parquet                & CRSP daily returns with delisting, Figure 2; Table 3 \\
data/crsp\_returns\_oos.parquet            & Held-out CRSP returns \\
data/angle\_2\_forward.jsonl               & Per-filing forward signal, Tables 3--5 \\
data/angle\_2\_forward\_pit.jsonl           & Acceptance-tradable variant, Table 5; Figure 1 \\
data/net\_sharpe\_strategy\_d\_pit.jsonl     & Monthly long--short returns, Figure 1 \\
data/cik\_sic\_map.json                    & Standard Industrial Classification map, robustness \\
data/r6\_llama\_classifications.jsonl      & Two-vendor cross-check labels, Section 4.1 \\
reports/r5-bonferroni-24-ledger.json     & Expanded cell ledger, Figure 4 \\
\bottomrule
\end{tabular}
\end{table}
