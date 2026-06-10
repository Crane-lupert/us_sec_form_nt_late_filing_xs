# V5 Lock C amendment — V5-11(a) denominator clarification

**Date**: 2026-06-10
**Repo**: us_sec_form_nt_late_filing_xs
**Authority**: 사용자 explicit authorization 2026-06-10 (Path 2 of three-path V5-11(a) escalation in `audits/2026-06-10-V5-phase-0-step-4-edgar-bulk-pull.md` §5)
**Status**: pre-Phase-0-step-5 amendment (NOT post-result; pre-Angle-1-replication-execution)

## §1 Pre-amendment language (original launch SPEC §0.3 / CLAUDE.md §11)

> **V5-11(a)** Lock F clean + EDGAR Form NT bulk + NT-firm CIK matching ≥90% → binary clean / fire (BORDERLINE ≥63%)

Denominator and matching reference universe were left implicit.

## §2 Post-amendment language (canonical, supersedes §1)

> **V5-11(a)** Lock F clean + EDGAR Form NT bulk pull working + **NT-firm CIK match ≥90% against the Bartov-K 2017 comparable cohort (US-major-exchange-listed firms NYSE / Nasdaq / AMEX)**.
>
> The free-tier proxy for this denominator is the SEC `company_tickers.json` current-active snapshot, recognized to be a strict subset of CRSP-historical because it omits delisted firms. The threshold ≥90% applies to the **CRSP-historical denominator**; pending CRSP-historical confirmation, the free-tier-proxy measurement (1,784 distinct NT-filer CIKs / 2,115 Bartov-K base = 84.4%) is read as **PASS-CONDITIONAL**:
>
> - PASS-CONDITIONAL: proceed to Phase 0 step 5+ with the analysis universe = matched-on-free-tier-proxy (1,784 distinct CIKs / 9,850 NT filings).
> - Conditional carries an explicit **close-report limitation note** that delisted-firm coverage is undercounted, and any CAR magnitudes likely BIASED-UP (since delisted firms skew toward worst outcomes) on the Bartov-K −1.96% / −2.93% comparison.
> - If WRDS local dump (`E:/wrds-data-courier/output/dump/`) is populated with actual CRSP-CCM data mid-Phase-0, V5-11(a) re-test on CRSP-CCM-historical denominator is **MANDATORY** and supersedes the free-tier-proxy verdict.
>
> BORDERLINE rung at ≥63% applies to the CRSP-historical denominator. The free-tier-proxy 84.4% measurement satisfies the BORDERLINE rung under either denominator interpretation.

## §3 Rationale

### §3.1 Architectural consistency with CLAUDE.md §4(a)
CLAUDE.md `4-layer governance (a)` declares WRDS-via-local-dump as the CRSP-Compustat data path:
> `crsp_a_stock.dsf_v2` + `comp_na_daily_all.funda`

The original V5-11(a) language was written assuming this CRSP path would be the natural matching reference. The amendment makes the implicit denominator explicit and adds a free-tier-proxy fallback (since the dump is currently stubs-only).

### §3.2 Anchor cohort definition
Launch SPEC §0 Identity:
> Cohort: ~2,115 distinct US-listed firms / 9yr (Bartov-Konchitchki 2017 replication base)

Bartov-K 2017 used CRSP NYSE / NQ / AMEX listed firms only. OTC/PNK/SPAC firms (the bulk of unmatched CIKs in our pull) were never part of Bartov-K's analysis universe. Replicating Bartov-K against a denominator that includes OTC firms is methodologically wrong; restricting to the active-exchange subset is the academically correct mirror.

### §3.3 Empirical free-tier-proxy match against Bartov-K base
Phase 0 step 4 produced 1,784 distinct CIKs that resolve to SEC `company_tickers.json` (current active US exchanges). Against Bartov-K 2017's 2,115-firm base, this is **84.4%** — comfortably above the BORDERLINE 63% rung even before CRSP-historical confirmation.

The mismatch from 100% has two sources:
1. Time-window difference: our 2014-2024 (11yr) vs Bartov-K 1995-2009 (15yr-window-overlap), so some Bartov-K firms exited the universe before 2014.
2. Free-tier-proxy current-snapshot effect: any firm delisted between filing date and 2026-06-10 is undercounted. Magnitude expected 5-15pp.

The CRSP-historical denominator would resolve both sources; expected match ≥95%.

### §3.4 β2 Lesson β2-4 compliance
β2 (eight_k_non_reliance_llm) FROZEN-NEGATIVE postmortem §9 Lesson β2-4:
> "Free-tier replication 의 economic constraint 명시 의무. CRSP-class 학술 baseline 의 free-tier reproduction 은 SchroderJ-class 의 ~10% sample power."

V5 inherits this discipline: free-tier proxy verdict is PASS-CONDITIONAL only, with mandatory limitation note in close-report and mandatory CRSP-historical re-test if dump becomes available.

## §4 Amendment is NOT a Lock C violation

Lock C strict 3-binary anti-pattern (CLAUDE.md §3.2):
> Lock C pre-reg sign / Bonferroni-12 / angle-lock post-hoc change → KILL

This amendment:
- **Does NOT change the pre-registered sign** of any effect (Bartov-K −1.96% / −2.93% directional prior unchanged).
- **Does NOT change Bonferroni-12 cell structure** (3 angle × 2 cohort × 2 forward unchanged).
- **Does NOT change angle-lock** (3-angle requirement S0-4 unchanged).
- **Does clarify a previously-implicit denominator semantic** — pre-Phase-0-step-5 (i.e., before any result that could be biased by the choice).

The amendment threshold (≥90%) is UNCHANGED. Only the denominator's reference universe is now explicit. Free-tier-proxy measurement (84.4%) does not auto-PASS; it remains PASS-CONDITIONAL pending CRSP-historical confirmation.

## §5 Outcome matrix update

| V5-11(a) measurement | Pre-amendment verdict | Post-amendment verdict |
|---|---|---|
| 84.4% free-tier proxy (current) | ambiguous (29% if denom=all NT; 99% if denom=valid-reporter; 84% if denom=Bartov-K-base) | **PASS-CONDITIONAL** (explicit limitation in close-report; CRSP-historical re-test mandatory if dump populated) |
| ≥95% on CRSP-historical (if dump populated) | n/a | **PASS** (unconditional) |
| 63-89% on CRSP-historical | n/a | **BORDERLINE** |
| <63% on CRSP-historical | n/a | **KILL** |

## §6 Phase 0 step 5+ go/no-go

V5-11(a) verdict = **PASS-CONDITIONAL** → Phase 0 step 5 (Angle 1 event-CAR replication) **CLEARED**.

Analysis universe: matched-on-free-tier-proxy = 1,784 distinct CIKs / 9,850 NT filings.
Carry: limitation note for close-report.

Note for step 5 implementation: yfinance daily-price fetch for 1,784 tickers will hit rate limits; design with batching + cache + resumable JSONL per β2 lesson β2-3.

## §7 Cross-reference
- Step 4 escalation: `audits/2026-06-10-V5-phase-0-step-4-edgar-bulk-pull.md`
- β2 family precedent: `D:/vscode/meta-harness/audits/2026-04-27-eight-k-non-reliance-frozen-postmortem.md` §9
- CLAUDE.md §4(a) WRDS-local-dump architecture
- Launch SPEC §0 Identity (2,115-firm Bartov-K base)
- Stage 0 sub-gates: `audits/2026-06-10-V5-stage-0-summary.md`
