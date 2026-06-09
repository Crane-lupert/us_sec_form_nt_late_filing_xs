# V5 Stage 0 — Summary (all 4 BLOCKING sub-gates resolved)

**Date**: 2026-06-10
**Repo**: us_sec_form_nt_late_filing_xs
**Verdict**: PASS — Stage 0 complete; cleared to proceed to Phase 0 step 4 (EDGAR Form NT bulk pull)

## §1 Sub-gate results

| Gate | Subject | Verdict | Artifact |
|---|---|---|---|
| S0-1 | Anchor cite-table verify + 2018-2025 expansion | PASS-with-correction (page-range 109-127 → 109-131) | `audits/2026-06-10-V5-stage-0-anchor-verify.md` |
| S0-2 | β2 differentiation + CIK×Q cross-tab plan | PASS (a priori); empirical deferred to Phase 0 step 4 | `audits/2026-06-10-V5-stage-0-beta2-differentiation.md` |
| S0-3 | NT body LLM cost preview | PASS — Year-1 $5.05 / $50 cap = 10.1% | `audits/2026-06-10-V5-stage-0-llm-cost-preview.md` |
| S0-4 | Angle 1 single-mode LAYER A blocker | PASS — Lock C 3-angle requirement committed | `audits/2026-06-10-V5-stage-0-angle-mode-lock.md` |
| Lock F §8 | Pipeline determinism grep | CLEAN (4/4 patterns) | `audits/2026-06-10-V5-stage-0-lock-f-grep.md` |

## §2 Key locks added / modified in Stage 0

| Lock | Source | Effect |
|---|---|---|
| Page-range correction | S0-1 | Bartov-K 2017 AH 31(4):**109-131** (was 109-127) |
| Anchor base | S0-1 | PARTIAL 3/6 LOCKED (0 academic post-Bartov-K papers found) |
| Angle 2 forward window tighten | S0-1 | 4-14d primary (SEC 2021 enforcement empirical), 3-21d robustness |
| β2 cross-tab STOP threshold | S0-2 | ≥30% CIK×Q overlap → STOP + escalate |
| Sample-power Gate H pre-bake | S0-2 | All 12 Bonferroni cells exceed required-n (smallest: angle 4 needs 278 firm-yrs vs ~2,880-4,770 available) |
| Strategy D schema | S0-3 | 3-class {accounting_issue, unresolved_sec_comment, other} |
| Strategy D κ floor | S0-3 | <0.7 → binary fallback {accounting_issue, other} |
| Lock C 3-angle promotion | S0-4 | LAYER A requires ≥1 PASS cell in each of angle 1, 2, 4 |
| Replication-only close-report path | S0-4 | Added to outcome matrix (angle-1-only PASS → FROZEN-PARTIAL) |

## §3 V5-11 HARD KILL gate readiness after Stage 0

| Gate | Pre-Stage-0 | Post-Stage-0 |
|---|---|---|
| V5-11(a) Lock F + EDGAR + CIK ≥90% | Lock F unverified | Lock F **CLEAN**; EDGAR + CIK pending step 4 |
| V5-11(b) Bonferroni-12 ≥3/12 | metric only | metric + Lock C 3-angle distribution requirement (§4.1 of S0-4 matrix) |
| V5-11(c) Net Sharpe ≥0.30 | metric only | unchanged (no Stage 0 input) |
| V5-11(d) Anchor PARTIAL via Bartov-K + 2018+ verify | TBD | **PARTIAL 3/6 LOCKED at floor** (S0-1) |

## §4 Phase 0 step sequence (Stage 0 → step 9)

| Step | Status | Next action |
|---|---|---|
| 1. Bootstrap | DONE (commit 2e848b6) | — |
| 2. Stage 0 sub-gates | **DONE (this audit)** | — |
| 3. Lock F §8 grep | DONE (CLEAN) | re-run after each code-adding commit |
| 4. EDGAR Form NT bulk pull 2014-01-01 ~ 2024-12-31 | pending | write `scripts/fetch-form-nt-bulk.py` |
| 5. Angle 1 event-CAR replication | pending | requires step 4 |
| 6. Angle 2 NT body LLM Strategy D | pending | requires step 4 + cost-preview locked |
| 7. Angle 4 recurring-filer XS 12mo | pending | requires step 4 |
| 8. Bonferroni-12 + Net Sharpe ledger | pending | requires steps 5-7 |
| 9. V5-11 verdict + close-report | pending | terminal |

## §5 Risks acknowledged post-Stage 0

1. **0 academic post-Bartov-K papers** found (S0-1) — single-anchor pivot risk remains; partially mitigated by SEC 2021 + 2023 enforcement corroboration tier (not anchor-level but salience-confirming).
2. **Bartov-K page-range correction** — minor cite error in launch SPEC; patch downstream artifacts before close-report.
3. **β2 cohort overlap empirical pending** — prior estimate 5-15%, well below 30% STOP, but must be measured.
4. **LLM cost confidence** — pricing snapshot 2026-Q2; if Haiku 4.5 pricing changes mid-Phase-0, re-estimate (10× headroom available).
5. **Lock C may force FROZEN-PARTIAL** even on Bonferroni-12 ≥3/12 — accepted by 사용자 (precludes mechanical-replication-only LAYER A promotion).

## §6 Cross-reference
- Autopilot prompt SoT: `D:/vscode/meta-harness/audits/2026-06-10-V5-autopilot-prompt.txt`
- Launch SPEC SoT: `D:/vscode/meta-harness/audits/2026-06-10-V5-launch-spec.md`
- Pre-bootstrap review: `D:/vscode/meta-harness/audits/2026-06-10-V5-sec-form-nt-bootstrap-review.md`
- β2 sister postmortem: `D:/vscode/meta-harness/audits/2026-04-27-eight-k-non-reliance-frozen-postmortem.md`
