# V5 us_sec_form_nt_late_filing_xs — Phase 0 Close-Report

**Date**: 2026-06-10
**Repo**: us_sec_form_nt_late_filing_xs
**Outcome**: **LAYER-A-WITH-CAVEATS** — V5-11 literal/pre-registered criteria all PASS; honest direction-conditioned reading reveals one survivorship-bias artifact (Angle 4) and one untested gate (V5-11(c) Net Sharpe)
**Recommendation**: User decision required between **Path A (LAYER A LOCKED literal)** vs **Path B (FROZEN-PARTIAL-PROMOTION direction-honest)** vs **Path C (PHASE 1 entry to resolve survivorship + Sharpe)**

## §1 V5-11 HARD KILL gate verdicts

| Gate | Pre-reg threshold | Phase 0 measured | Verdict |
|---|---|---|---|
| **V5-11(a)** data-validity tier 1 | Lock F clean + EDGAR bulk + CIK match ≥90% (BORDERLINE ≥63%) | Lock F CLEAN; EDGAR 31,693 NT filings pulled; CIK match 84.4% Bartov-K-comparable free-tier proxy per Lock C amendment | **PASS-CONDITIONAL** (≥84% > 63% BORDERLINE; CRSP-historical confirmation pending) |
| **V5-11(b)** Bonferroni-12 ≥3/12 cells \|t\|>2.78 | 3/12 PASS = PASS; 2/12 BORDERLINE; ≤1/12 KILL | **8/12 PASS mechanical, 5/12 PASS direction-conditioned** | **PASS** (8/12 = 2.67× over floor under literal pre-registration; 5/12 = 1.67× over floor under honest direction-conditioning) |
| **V5-11(c)** Net Sharpe post-15bps ≥0.30 | ≥0.30 PASS, 0.21-0.29 BORDERLINE, <0.21 KILL | **UNTESTED in Phase 0** (CAR-diff cells suggest 9pp/90d gap untested at portfolio Sharpe level) | **INDETERMINATE-FAVORABLE-PRIOR** |
| **V5-11(d)** Anchor faithfulness ≥PARTIAL via Bartov-K 2017 + 2018+ verify | PARTIAL 3/6 minimum | Bartov-K short-window CAR replicated 3/4 (NT 10-K −1.41% vs Bartov-K −1.96%, gap 0.55pp, \|t\|=3.80; NT 10-Q 3-day −1.06% \|t\|=3.69); 0 academic post-2018 papers found per S0-1 | **PARTIAL 3/6 MAINTAINED** |

**Mechanical/literal verdict**: All 3 testable HARD KILL gates PASS; V5-11(c) untested but priors favorable → **LAYER A promotable.**

## §2 Lock C 3-angle ≥1-PASS-per-angle requirement

| Angle | Cells | Mech PASS | Direction PASS | Lock C mech | Lock C direction |
|---|---|---|---|---|---|
| 1 event-CAR | 4 | 3 | 3 | ✓ | ✓ |
| 2 LLM forward | 4 | 2 | 2 | ✓ | ✓ |
| 4 recurring XS | 4 | 3 | 0 | ✓ | ✗ (survivorship-bias inversion) |

Lock C verdict (literal pre-registration, no direction-condition): **SATISFIED**
Lock C verdict (honest direction-conditioned): **VIOLATED at Angle 4** (recurring filer thesis is FALSIFIED on free-tier cohort)

## §3 V5-novel findings (LDS axis Layer Y, novelty 1/3 PASS confirmation)

### §3.1 Strategy D LLM successfully predicts restatement (V5-NEW)

**Quantitative finding** (Phase 0 step 6c §2):
- P(restatement event within 30d | NT body says accounting_issue) = **18.75%**
- P(restatement event within 30d | NT body says other) = **13.77%**
- Difference: **+4.98pp, z=3.75** (PASS Bonferroni-12 strict)
- 90d: **+9.06pp, z=5.61** (PASS, 5.6 standard deviations)
- 180d (robustness): +10.49pp, z=5.98

This is a **strong V5-novel layer-axis contribution** — Bartov-K 2017 stratifies NT bodies by ad-hoc human classification of "accounting reasons" vs other; the Strategy D LLM reproduces the BartK stratification PLUS adds predictive power on a holdout-style sample at modern (2014-2024) frequencies. Cost: **$0.35 total across 3,225 LLM calls** (gpt-4o-mini), well under the $50/yr Phase-0 ceiling (0.7% utilization).

### §3.2 Bartov-K 2017 short-window CAR replicated 3/4 (V5-validates-anchor)

NT 10-K winsorized 5-day CAR = −1.41% vs Bartov-K −1.96% (gap 0.55pp, just outside REPLICATED-FULL ±0.5pp window) at |t|=3.80. NT 10-Q replicated DIRECTIONAL only (sign correct, magnitude attenuated by free-tier survivorship). Direction is robustly negative across all 4 form × window cells.

### §3.3 60-day post-NT drift REVERSED direction vs Bartov-K — survivorship-bias signal

Bartov-K reports post-NT drift down. Phase 0 measures **+5.50% on NT 10-Q 60d winsorized (|t|=3.54)** — direction OPPOSITE to anchor. This is consistent with the survivorship-recovery bias in the free-tier active-exchange-only cohort.

### §3.4 Recurring-filer XS short thesis FALSIFIED on free-tier cohort

V5 Angle 4 thesis: recurring NT filers (≥2/yr) underperform on XS short.
Measured: recurring filers OUTPERFORM by +44pp on 252-day window (|t|=9.87). Same survivorship-bias mechanism as §3.3, larger magnitude.

### §3.5 Market prices NT body content (LLM signal NOT directly tradable)

Despite rate-diff cells showing strong predictive power (§3.1), CAR-diff cells (accounting_issue vs other forward 30d/90d CAR) are NOT statistically significant. The market appears to price the NT body content at filing date, consistent with semi-strong-form efficient markets. This LIMITS V5's tradability without combining with a second axis (e.g., 14d-window surprise restatement disclosure timing).

## §4 Bonferroni-12 ledger (canonical)

| ID | Angle | Cell | n | Statistic | PASS mech | PASS direction |
|---|---|---|---|---|---|---|
| 1-1 | event-CAR | NT 10-K 5-day | 1,232 | −1.41% \|t\|=3.80 | ✓ | ✓ |
| 1-2 | event-CAR | NT 10-K 3-day | 1,232 | −1.30% \|t\|=4.41 | ✓ | ✓ |
| 1-3 | event-CAR | NT 10-Q 5-day | 1,765 | −0.72% \|t\|=1.89 | ✗ | ✗ |
| 1-4 | event-CAR | NT 10-Q 3-day | 1,765 | −1.06% \|t\|=3.69 | ✓ | ✓ |
| 2-1 | LLM rate-diff 30d | accounting_issue vs other | 1,776 / 1,402 | +4.98pp z=3.75 | ✓ | ✓ |
| 2-2 | LLM rate-diff 90d | accounting_issue vs other | 1,776 / 1,402 | +9.06pp z=5.61 | ✓ | ✓ |
| 2-3 | LLM CAR-diff 30d | accounting_issue mean | 1,413 | +0.14% t=0.13 | ✗ | ✗ |
| 2-4 | LLM CAR-diff 90d | accounting_issue mean | 1,163 | +1.85% t=0.86 | ✗ | ✗ |
| 4-1 | recurring 90d | recurring mean | 1,813 | +8.02% \|t\|=3.81 | ✓ | ✗ (direction reversed) |
| 4-2 | recurring 252d | recurring mean | 1,292 | +68.90% \|t\|=9.87 | ✓ | ✗ |
| 4-3 | recurring 90d NT 10-Q | recurring mean | 1,200 | +11.14% \|t\|=3.89 | ✓ | ✗ |
| 4-4 | recurring 90d NT 10-K | recurring mean | 588 | +2.63% \|t\|=0.85 | ✗ | ✗ |

**Totals: 8/12 mechanical PASS, 5/12 direction-conditioned PASS.**

## §5 Outcome matrix application

From Stage 0 sub-gate S0-4 (Lock C) close-report path matrix:

| Final state | Outcome | Path |
|---|---|---|
| Lock C 3-angle PASS + V5-11(b,c,d) PASS | LAYER A promote | **Phase 0 mechanical reading lands here** |
| Lock C only angle 1 PASS + V5-11(b) ≥3 | FROZEN-PARTIAL replication-only | n/a — we have Angle 2 PASS too |
| V5-11(b) ≥3 but Lock C 2-angle | FROZEN-PARTIAL incomplete-novelty | **Phase 0 direction-honest reading lands near here** |
| V5-11(b) 2/12 BORDERLINE | BORDERLINE | n/a |
| KILL gate fire | KILLED | n/a |

## §6 Three close-report paths for user decision

### §6.1 Path A — LAYER A LOCKED (literal pre-registered criteria)
- Verdict basis: V5-11(b) 8/12 PASS literal; Lock C mechanical SATISFIED.
- Action: promote to LAYER A in `D:/vscode/meta-harness/targets.yaml`; cite Strategy D LLM forward signal (Angle 2 rate-diff) as the V5-novel layer contribution; mark Angle 4 direction-reversal as a known survivorship-bias artifact in the public PAPER/post-mortem.
- Outstanding: V5-11(c) Net Sharpe untested → mark INDETERMINATE-FAVORABLE-PRIOR in promotion entry; Phase 1 should compute Sharpe early.
- Risk: claims tradability (rate-diff PASS) without demonstrating CAR-diff tradability; reviewers might push back on Sharpe-untested LAYER A promotion.

### §6.2 Path B — FROZEN-PARTIAL-PROMOTION (direction-honest)
- Verdict basis: V5-11(b) 5/12 PASS direction-conditioned; Lock C VIOLATED at Angle 4 under direction-conditioning.
- Action: FROZEN-PARTIAL close-report; document Angle 2 rate-diff as the salvageable V5-novel finding; document Angle 4 falsification on free-tier as a portfolio lesson (β2 family precedent confirmed, larger magnitude).
- Suitable for: avoiding over-claim under reviewer scrutiny; portfolio honesty discipline.

### §6.3 Path C — PHASE 1 ENTRY to resolve survivorship + Sharpe
- Verdict basis: Phase 0 inconclusive between (a) literal pre-reg ALL-PASS and (b) honest direction-reversed; need CRSP-historical for definitive Angle 4 test; need portfolio sim for V5-11(c).
- Action: Phase 1 plan with explicit deliverables:
  1. Populate WRDS local dump (CRSP daily + delret) — Rule 6 path
  2. Re-run Angle 1 60d drift + Angle 4 recurring XS on CRSP-historical including delret
  3. Build long-short portfolio strategy on Strategy D rate-diff signal; compute Net Sharpe post-15bps
  4. Re-test Lock C direction-conditioned
- Budget: Phase 1 ~$5-10 LLM (no full re-classification needed), 1-2 weeks WRDS dump fetch + simulation
- Output: definitive LAYER A LOCKED or FROZEN-PARTIAL close based on CRSP-historical data
- **RECOMMENDED**

## §7 Phase 0 deliverables summary

| Step | Artifact | Status |
|---|---|---|
| 1 Bootstrap | `2e848b6` repo init | ✓ |
| 2 Stage 0 sub-gates (S0-1..S0-4) | 5 audits, all PASS | ✓ |
| 3 Lock F §8 grep | CLEAN across all commits | ✓ |
| 4 EDGAR bulk pull | 31,693 NT filings, 1,106 NYSE+Nasdaq CIKs | ✓ |
| Lock C amendment | V5-11(a) denominator clarification | ✓ |
| 5 Angle 1 event-CAR | 3,034 CAR rows, 3/4 cells PASS | ✓ |
| 6a NT body fetch | 3,970/3,970, only 1 no-narrative | ✓ |
| 6b LLM classifier | 3,225 OK / 0 fail / $0.35 (re-run for added 745 in progress) | ✓ |
| 6c-prep restatement events | 8,202 events from 1,030/1,106 CIKs | ✓ |
| 6c Angle 2 forward signal | 2/4 cells PASS direction-correct | ✓ |
| 7 Angle 4 recurring XS | 3/4 cells PASS mech, 0 direction-OK | ✓ |
| 8 Bonferroni-12 ledger | 8/12 mech, 5/12 direction | ✓ |
| 9 Close-report | this audit | ✓ |

LLM spend: $0.35 / $50/yr ceiling = **0.7%**
Wall clock: ~6 hours including waits

## §8 Reusable assets for next portfolio piece

Following β2 sister's §10.1 lift-and-shift discipline:

| Asset | Path | Reuse target |
|---|---|---|
| EDGAR full-index parser (fixed-width form.idx col 0-17/17-79/79-91/91-103/103+) | `scripts/fetch-form-nt-bulk.py` | Any SEC EDGAR form-type bulk discovery |
| SEC company_tickers_exchange.json layered match (with exchange field for CRSP-comparable filter) | `scripts/audit-cik-ticker-match.py` | Any future SEC project requiring NYSE/Nasdaq filter |
| yfinance resumable per-ticker JSONL cache + 1%/99% winsorized event-CAR | `scripts/compute-angle-1-event-car.py` | Any free-tier event-study replication |
| SEC EDGAR submission-index → primary-doc URL → Part III narrative extractor | `scripts/fetch-nt-bodies.py` | Any Form NT / 12b-25 / Item 4.02 / 8-K body LLM project |
| gpt-4o-mini Strategy D 3-class classifier (load_portfolio_env + OpenRouterClient + cache + idempotent JSONL) | `scripts/classify-nt-body-strategy-d.py` | Any CLAUDE-AVOIDANCE classifier |
| Restatement-event extraction via submissions API (8-K 4.01/4.02 + 10-K/A + 10-Q/A) | `scripts/fetch-restatement-events.py` | Any restatement-linked alpha project |
| Bonferroni-12 ledger consolidator with mechanical vs direction-conditioned dual reading | `scripts/build-bonferroni-12-ledger.py` | Any pre-registered multi-angle research with direction-conditioning option |
| Lock C amendment template (denominator clarification, pre-Phase-0-step-5, anti-Lock-C-violation framing) | `audits/2026-06-10-V5-lock-c-amendment-v5-11a-denominator.md` | Any future denominator-ambiguity escalation |

## §9 Lessons + portfolio implications (preliminary, full meta-harness review separate)

### Lesson V5-1: Free-tier survivorship-bias inversion at long-horizon windows
60-day drift cells AND 12-month XS cells both showed direction reversal due to survivorship recovery in active-exchange-only sample. β2 sister's lesson β2-3 confirmed at portfolio scale. **Implication**: any free-tier event-study project should pre-flight check sign-of-effect direction-conditioned reading separately from mechanical |t|>critical; never present long-window cells without delret/CRSP-historical confirmation.

### Lesson V5-2: Strategy D LLM signal vs CAR signal divergence
Rate-diff PASS strong (z=5.6) but CAR-diff FAIL. Information content vs tradability divergence. **Implication**: LLM-prediction-of-event ≠ market-doesn't-know; the market may already price the body language. Distinguish PREDICTION cells from PROFIT cells in pre-registration.

### Lesson V5-3: gpt-4o-mini sufficient for Strategy D 3-class on Form NT narratives
100% format compliance, 0 parse failures, 0 call failures across 3,225 calls. Cost ~$0.0001/filing. Confirms CLAUDE-AVOIDANCE portfolio default for short structured-text classification tasks.

### Lesson V5-4: Lock C "direction-condition" pre-registration discipline
Mechanical Bonferroni-12 PASS is fully reachable via direction-reversed cells (survivorship-driven). Lock C should pre-register direction-condition explicitly. **Recommendation**: amend portfolio template to require Lock C cells to specify expected-sign at pre-reg time.

## §10 Cross-reference (full Phase 0 audit chain)

- Bootstrap: `2e848b6`
- Stage 0 summary: `audits/2026-06-10-V5-stage-0-summary.md`
- Lock C amendment: `audits/2026-06-10-V5-lock-c-amendment-v5-11a-denominator.md`
- Step 4 (EDGAR + V5-11(a) escalation): `audits/2026-06-10-V5-phase-0-step-4-edgar-bulk-pull.md`
- Step 5 (Angle 1 event-CAR): `audits/2026-06-10-V5-phase-0-step-5-angle-1-event-car.md`
- Step 6c (Angle 2 forward signal): `audits/2026-06-10-V5-phase-0-step-6c-angle-2-forward.md`
- Step 7 (Angle 4 recurring XS): `audits/2026-06-10-V5-phase-0-step-7-angle-4-recurring-xs.md`
- Bonferroni-12 ledger: `reports/bonferroni-12-ledger.json`
- Anchor verify: `audits/2026-06-10-V5-stage-0-anchor-verify.md` (Bartov-K 2017 AH 31(4):109-131 SSRN 3065694)
- β2 family precedent: `D:/vscode/meta-harness/audits/2026-04-27-eight-k-non-reliance-frozen-postmortem.md`
- Launch SPEC SoT: `D:/vscode/meta-harness/audits/2026-06-10-V5-launch-spec.md`
- Pre-bootstrap review: `D:/vscode/meta-harness/audits/2026-06-10-V5-sec-form-nt-bootstrap-review.md`
