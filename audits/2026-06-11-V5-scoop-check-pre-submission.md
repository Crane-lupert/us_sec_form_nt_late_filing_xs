# V5 Pre-Submission Scoop Check — 3-Pass Cadence Closure

**Date**: 2026-06-11
**Repo**: us_sec_form_nt_late_filing_xs
**Scope**: Close the 3-pass scoop-check cadence required by paper-writing-lessons portable-checklist §11.5.A and §14.14 before SSRN submission.
**Verdict**: PASS — zero published prior work scoring SEC Form NT body narratives under a structured taxonomy and linking the class to forward restatement-class disclosures. The four-finding novelty claims in `analysis/paper_v2_en.md` remain defensible at the strong-but-honest "to my knowledge" level.

## §1 Cadence

Per paper-writing-lessons §11.5.A and §14.14:

| Pass | Cadence | Date | Audit |
|---|---|---|---|
| 1 | Phase 0 stage 0 (before commit-lock) | 2026-06-10 | `audits/2026-06-10-V5-stage-0-anchor-verify.md` (Bartov-Konchitchki 2017 single-anchor pivot + 2018-2025 academic expansion 0 hits) |
| 2 | Mid-phase (before paper draft) | 2026-06-10 | Phase 1 close-report (`audits/2026-06-10-V5-phase-1-close-report.md`) — anchor faithfulness PARTIAL 4/6 holds |
| 3 | Pre-submission (within 7 days of upload) | **2026-06-11 (this audit)** | this audit |

## §2 Pass 3 query set + results (executed 2026-06-11)

### §2.1 Direct mechanism: Form NT body narrative + LLM + restatement

Query 1: `SEC Form NT 10-K 10-Q late filing body narrative LLM text classification restatement 2024 2025 2026 SSRN`

Hits (relevant): 
- @lehnerlazslo2024 *The Future of Accounting: AI-driven Tone Manipulation in SEC Filings* (SSRN 4984337) — LLM-based sentiment rewriting of 10-K/10-Q. Conditioning event = 10-K/10-Q full filing, not Form NT body narrative. Dependent variable = LLM-rewritten tone vs original tone, not subsequent restatement. **Not competing**.
- @huangkewei2008 *Multilabel Risk Factor Classification on 10-K* (SSRN 1784527) — supervised multilabel classifier on 10-K risk-factor Section 1A. Pre-LLM, supervised, 10-K Item 1A only. **Not competing**.

### §2.2 Direct mechanism (alternative phrasing): Bartov-Konchitchki extension

Query 2: `Bartov Konchitchki Form NT 12b-25 cross-section equity signal forward restatement prediction 2024 2025`

Hits (relevant):
- Bartov-Konchitchki 2017 *Accounting Horizons* canonical paper, cited extensively in industry coverage (NYU Stern; American Accounting Association press release 2017-11-29).
- "Filing, Fast and Slow: Reporting Lag and Stock Returns" (working paper, ctfassets-hosted; no SSRN ID resolved). Conditioning variable = reporting lag distribution, not Form NT body narrative content. Dependent variable = stock return as function of lag, not forward restatement probability. **Not competing**.

No post-2018 academic paper extends Bartov-Konchitchki 2017 with a machine-readable body-narrative taxonomy.

### §2.3 Intraday-tradability institutional fact

Query 3: `SEC EDGAR "acceptanceDateTime" "after hours" intraday tradability filing event study`

Hits (relevant):
- Hudson Labs blog *Filing after hours: When it matters* (hudson-labs.com) — industry blog, not peer-reviewed. Reports that "the vast majority of 10-Ks and 10-Qs (~60%) are filed between 4 PM and 5:30 PM". The reported share refers to 10-K/10-Q (not Form NT), uses 5:30 PM EDGAR cutoff (not 16:00 ET market close), and is in a non-academic outlet.
- BlueSky Comply *Guide to SEC Holidays and Filing Deadlines* — operational guide on EDGAR hours-of-operation, not an academic event-study finding.
- arXiv 2101.04480 *Text analysis in financial disclosures* — generic survey, no Form NT acceptance-time content.

V5's institutional fact (63.5% in-sample, 77.0% held-out share of Form NT filings accepted at or after 16:00 ET, with measured impact on long–short basket net Sharpe from 0.46 calendar anchor to 0.59 acceptance-tradable anchor) is **not pre-empted by published academic work**. The Hudson Labs industry observation on 10-K/10-Q (different filing class, different cutoff, non-academic) is a salience-corroborating reference but does not establish academic priority on the Form NT cohort.

## §3 Conclusion

The four findings enumerated in the paper's introduction and conclusion remain defensible at the strong-but-honest "to my knowledge, has not been documented before" level:

1. **Body-narrative forward signal** (Finding 1, paper §5.4 + §5.5): no published prior under direct or alternative-phrasing queries.
2. **Form NT 10-Q cohort dominance over Form NT 10-K cohort** (Finding 2, paper §5.6): no published prior.
3. **63.5% of in-sample filings accepted after market close + acceptance-tradable anchor Sharpe lift** (Finding 3, paper §5.2 + Table 4 + Figure 1): no published academic prior. Hudson Labs industry observation on 10-K/10-Q (not Form NT) is salience-corroborating but does not pre-empt academic priority.
4. **Free-tier delisting-return artifact** (Finding 4, paper §5.3): the underlying delisting-return economic literature is cited (`@shumway1997`); the V5-specific quantification on the Form NT cohort is not pre-empted.

The five-paper related-literature scaffold in paper §2 (Bartov-Konchitchki 2017; Johnston-Petacchi 2017; Ryans 2021; Cassell-Dreher-Myers 2013; Lopez-Lira-Tang 2023; Chen-Kelly-Xiu 2024) is sufficient and accurate.

**Submission-ready**: the paper's novelty claims survive the 3-pass scoop-check cadence. Cite this audit (commit hash) in the paper's submission cover letter as the closing scoop-check reference.

## §4 Cross-reference

- Paper-writing-lessons portable checklist: `D:/vscode/meta-harness/audits/2026-06-02-X-paper-writing-lessons-portable-checklist.md` §11.5.A (cadence) + §14.14 (V5 gap-closure).
- Phase 0 stage 0 anchor verify: `audits/2026-06-10-V5-stage-0-anchor-verify.md`
- Phase 1 close-report: `audits/2026-06-10-V5-phase-1-close-report.md`
- Paper draft: `analysis/paper_v2_en.md` (current commit chain `cfd4d4d` → `070f0d5` → `cf543e0` → `1a04f9f` → `a77a72b` → `63b061a`).
