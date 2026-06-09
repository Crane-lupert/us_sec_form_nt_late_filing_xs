# V5 Stage 0 sub-gate S0-1 — Anchor cite-table verify

**Date**: 2026-06-10
**Repo**: us_sec_form_nt_late_filing_xs
**Gate**: S0-1 (BLOCKING)
**Verdict**: PASS-with-correction — single anchor LOCKED, expansion FAIL (0 academic post-Bartov-K)

## §1 Single VERIFIED anchor (post-pivot)

**Bartov, E. & Konchitchki, Y. (2017)** "SEC Filings, Regulatory Deadlines, and Capital Market Consequences" *Accounting Horizons* 31(4):**109-131**, SSRN 3065694, DOI 10.2308/acch-51887.

### §1.1 Verified facts (S0-1 WebSearch corroboration)
- Publisher: American Accounting Association (Allen Press / publications.aaahq.org)
- Article page: https://meridian.allenpress.com/accounting-horizons/article-abstract/31/4/109/52450/
- Open PDF (author host): https://faculty.haas.berkeley.edu/yaniv/files/Papers_Publications/SEC-Filings-Regulatory-Deadlines-Capital-Market-Consequences_Bartov-Konchitchki_AH.pdf
- SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3065694
- CLS Blue Sky synopsis (Nov 2017): NT 10-K CAR −1.96% confirmed; post-filing drift downward confirmed
- Stern Research Highlight + Accounting Today coverage confirmed

### §1.2 Page-range CORRECTION
- **SPEC.md / CLAUDE.md state**: 109-127
- **Verified actual**: 109-131
- Action: All Lock numerical-fact registry entries that quote "109-127" → patch to "109-131" before any close-report
- Lock-V5-1 unaffected (2,115 firms × 9yr)
- Lock-V5-2 unaffected (NT 10-Q CAR −2.93% / NT 10-K −1.96%)

## §2 사용자 cite 4 fail DROP confirmation

| # | Cite | Status | Action |
|---|------|--------|--------|
| 1 | Files, Sharp & Thompson 2013 JAR | MIS-CITED (actual = repeat-restatement 2014 AH) | DROP |
| 2 | Kinney, Burgstahler & Martin 2002 JAR | SCOPE-MISMATCH (earnings surprise materiality) | DROP |
| 3 | Hribar, Kravet & Wilson 2014 | MIS-CITED (RAST not CAR) | DROP |
| 4 | Bartov, Coltman & Frey 2022 | HALLUCINATED (no such paper) | DROP |

All four removed from any anchor argument. Bartov-Konchitchki 2017 AH remains as single VERIFIED anchor pivot.

## §3 2018-2025 post-Bartov-K WebSearch expansion result

### §3.1 Search queries executed
1. `"Form NT 10-Q" OR "Form 12b-25" restatement late filing 2018..2025 academic research`
2. `"Form NT 10-K" late filing returns market reaction event study 2020..2023`
3. `"NT 10-Q" abnormal returns "12b-25" SSRN working paper 2019..2023 site:ssrn.com`
4. `"late filing" SEC enforcement "Form NT" restatement disclosure 2021 SEC charged eight companies`

### §3.2 Academic finding: **0 new event-study papers post-Bartov-K 2017 found**
- No SSRN working paper or refereed academic event-study replicating or extending Bartov-K 2017 found in 2018-2025 search window
- ResearchGate result (Bartov-Defond-Konchitchki Bocconi 2012) = pre-publication version of the same paper, NOT a new study
- **Verdict**: Anchor base **stays PARTIAL 3/6** per autopilot prompt rule ("0 발견 시 anchor PARTIAL 3/6 lock")

### §3.3 Regulatory/practitioner corroboration tier (NOT anchor, but supporting context)
| Source | Year | Substance | Use |
|---|---|---|---|
| SEC press release 2021-76 + Cleary Gottlieb + Harvard Corp Gov | 2021-04 | 8 companies charged for failing to disclose restatements on Form NT; restatement announced 4-14d post-NT | **Angle 2 timing prior**: window 3-21d in SPEC narrowed to **4-14d empirical** by SEC enforcement order data |
| SEC AP 34-98192-s (5 more companies) | 2023 | Continuation of 2021 Form NT enforcement initiative | Confirms regulatory salience persists post-Bartov-K |
| Public Company Advisory Blog 2023 PDF | 2023-09 | Practitioner overview of Form 12b-25 enforcement trend | Context only |
| CBIZ / Olshan Law / Nasdaq press syndication | 2021 | Industry coverage | Context only |

### §3.4 Salience signal from regulatory corroboration
- SEC issued **2 separate enforcement waves (2021 + 2023)** specifically targeting Form NT non-disclosure of restatement intent → confirms V5 Angle 2 mechanism (NT body → restatement forward) has **real-world basis**, not just Bartov-K 2017 academic artifact
- Empirical timing data: restatements announced **4-14d after Form NT** in SEC orders → tighten Angle 2 forward window from 3-21d → 4-14d for primary specification (3-21d kept as robustness)

## §4 Anchor faithfulness verdict (V5-11(d))

- Pre-S0-1: PARTIAL 3-4/6 (single VERIFIED anchor pivot, 사용자 cite 4/4 fail)
- Post-S0-1: **PARTIAL 3/6 LOCKED** (no academic expansion; regulatory corroboration noted but not promoted to anchor tier)
- V5-11(d) gate: PARTIAL ≥ minimum → **PASS** (at floor)

## §5 Stage 0 sub-gate S0-1 verdict

- **PASS-with-correction**
  - PASS: single anchor Bartov-K 2017 AH VERIFIED with primary publisher source
  - Correction: page-range 109-127 → 109-131 (patch downstream artifacts before close-report)
  - Expansion outcome: 0 academic / 2 SEC enforcement actions (4-14d Angle 2 timing prior tightening)
- **BLOCKING resolved** — proceed to S0-2

## §6 Cross-reference
- Launch SPEC: `D:/vscode/meta-harness/audits/2026-06-10-V5-launch-spec.md`
- Pre-bootstrap review: `D:/vscode/meta-harness/audits/2026-06-10-V5-sec-form-nt-bootstrap-review.md`
- Lock-V5-1, Lock-V5-2 unaffected by page-range correction
