# V5 Stage 0 sub-gate S0-4 — Angle 1 single-mode lock 차단 (Lock C)

**Date**: 2026-06-10
**Repo**: us_sec_form_nt_late_filing_xs
**Gate**: S0-4 (BLOCKING)
**Verdict**: PASS — Lock C language committed; angle 1 single-mode LAYER A promotion blocked at audit-level

## §1 The risk (사용자 명시 2026-06-10)

Angle 1 = NT event-CAR replication of Bartov-Konchitchki 2017 AH 31(4):109-131 (NT 10-Q CAR −2.93%, NT 10-K −1.96%).

If V5 PASSES on angle 1 alone (i.e., Bonferroni-12 cells 3+/12 all fall on angle-1 rows), this would be:
- **MECHANICAL REPLICATION** of a 9-year-old academic finding
- Zero novelty (replication value only; not LDS axis 7 PASS)
- **β2 family pattern** (8-K SEC EDGAR sister mechanism replication PASS / alpha FAIL) — V5 would be β3 by analogy

The user has pre-flagged this as a single-mode promotion path to be CLOSED before Phase 0 begins.

## §2 Lock C language (committed)

The following text is the authoritative Lock C clause for V5 — referenced by V5-11(b) and V5-11(d) HARD KILL gates.

> **Lock C — V5 angle-stack 3-mode requirement (LAYER A promotion blocker)**
>
> No subset of {angle 1 only}, {angle 1 + angle 2}, {angle 1 + angle 4} can constitute a LAYER A promotion. LAYER A promotion of V5 requires **all three** of:
>
> 1. **Angle 1** (NT event-CAR Bartov-K replication) — at least 1/4 cells PASS Bonferroni-12 |t|>2.78 across (S&P 1500, Russell 3000) × (5-day window primary, 3-day robustness)
> 2. **Angle 2** (NT body LLM Strategy D forward) — at least 1/4 cells PASS Bonferroni-12 |t|>2.78 across (S&P 1500, Russell 3000) × (30-day, 90-day forward restatement-probability or CAR)
> 3. **Angle 4** (recurring NT filer ≥2/yr XS portfolio) — at least 1/4 cells PASS Bonferroni-12 |t|>2.78 across (S&P 1500, Russell 3000) × (30-day, 90-day or 12-month) forward
>
> ≥1/4 cell PASS per angle = **3 angles × 1 each = 3 cells minimum** (matches V5-11(b) Bonferroni-12 ≥3/12 PASS floor exactly).
>
> All other Bonferroni-12 distributions:
> - 3+ cells but concentrated on single angle (e.g., 3/4 on angle 1 only): **NOT LAYER A** — pre-Phase-0 FROZEN-PARTIAL.
> - 3+ cells but missing angle 2 OR angle 4 row: **NOT LAYER A** — pre-Phase-0 FROZEN-PARTIAL.
> - 2/12 (BORDERLINE under V5-11(b)): **NOT LAYER A** regardless of distribution; per Rule 9 BORDERLINE protocol.
> - <2/12 (KILL under V5-11(b)): KILL.
>
> Angle 1 single-mode KILL exception: if angle 1 PASSES but angle 2 + angle 4 both FAIL, output is **REPLICATION-ONLY close-report** (positive but non-novel), classified as MECHANICAL-REPLICATION-CONFIRMED, NOT LAYER A.

## §3 Pre-Phase-0 motivation (audit-level)

### §3.1 Bartov-K 2017 7-year decay risk
- Anchor age at V5 entry: 2017 publication → 9 years stale at 2026-06-10
- LDS axis 7 BORDERLINE (post-publication decay >5yr threshold)
- Replication PASS on angle 1 alone would not differentiate "still alive" from "still measurable but not tradable"
- Recent SEC enforcement (2021, 2023) suggests structure persists, but salience may have re-pricing post-enforcement

### §3.2 β2 family precedent
β2 8-K Item 4.02 sister:
- SchroderJ 2025 baseline replication FAILED (active-only survivorship −0.84% vs −2.6 to −5.4% envelope)
- Cross-section alpha FAILED (|t|=0.57 < Bonferroni-9 critical 2.77)
- Outcome: FROZEN-NEGATIVE
- **V5 angle 1 alone replicating Bartov-K** would NOT prove anything more than β2 already proved (signed-direction OK, magnitude underwhelming without paid-data)

### §3.3 Novelty axis (Launch SPEC §3 1/3 PASS)
Per launch SPEC: Novelty PASSES on **Layer** axis only (LLM NT body extract + restatement forward + recurring filer XS). Angle 1 contributes ZERO novelty under this scoring — it's exactly the layer Bartov-K 2017 already published.

## §4 Operationalization in V5-11

### §4.1 V5-11(b) Bonferroni-12 verdict matrix (updated reading)
| Distribution | Without Lock C | With Lock C (S0-4 applied) |
|---|---|---|
| 4/4 angle 1, 0/4 angle 2, 0/4 angle 4 | PASS (4/12 cells) | FROZEN-PARTIAL — replication-only close-report |
| 3/4 angle 1, 0/4 angle 2, 0/4 angle 4 | PASS (3/12 cells) | FROZEN-PARTIAL |
| 2/4 angle 1, 1/4 angle 2, 0/4 angle 4 | PASS (3/12 cells) | FROZEN-PARTIAL (missing angle 4) |
| 1/4 angle 1, 1/4 angle 2, 1/4 angle 4 | PASS (3/12 cells) | **LAYER A** (all 3 angles represented) |
| 2/4 angle 1, 2/4 angle 2, 1/4 angle 4 | PASS (5/12 cells) | **LAYER A** |
| 2/12 any distribution | BORDERLINE | BORDERLINE |
| ≤1/12 any distribution | KILL | KILL |

### §4.2 V5-11(d) anchor-faithfulness interaction
Lock C does NOT change V5-11(d) anchor-faithfulness threshold (PARTIAL ≥ 3/6 via Bartov-K + Stage 0 verify per S0-1).
Lock C operates orthogonally as a structural/novelty gate.

## §5 Close-report path matrix

| Final state | Outcome | Close-report path |
|---|---|---|
| Lock C 3-angle PASS + V5-11(b,c,d) PASS | LAYER A promote | `audits/...-V5-LAYER-A-promotion.md` |
| Lock C only angle 1 PASS + V5-11(b) ≥3 | FROZEN-PARTIAL replication-only | `audits/...-V5-FROZEN-PARTIAL-replication-only.md` |
| V5-11(b) ≥3 but Lock C 2-angle | FROZEN-PARTIAL incomplete-novelty | `audits/...-V5-FROZEN-PARTIAL-incomplete-novelty.md` |
| V5-11(b) 2/12 | BORDERLINE | `audits/...-V5-BORDERLINE.md` (Rule 9 protocol) |
| V5-11(b) ≤1/12 OR (c) Sharpe <0.21 OR (d) anchor FAIL | KILL | `audits/...-V5-KILLED-close.md` |
| Lock F US-data violation | KILL | `audits/...-V5-KILLED-Lock-F-close.md` |
| Stage 0 S0-2 overlap ≥30% | STOP | `audits/...-V5-STOP-beta2-overlap.md` |

## §6 S0-4 verdict

- **PASS** — Lock C committed (§2 above is canonical text)
- **3-angle PASS requirement** locked in V5-11(b) verdict matrix (§4.1)
- **Replication-only close-report path** added (§5)
- **BLOCKING resolved** — Stage 0 sub-gate complete; proceed to Phase 0 step 3 (Lock F §8 grep)

## §7 Cross-reference
- Launch SPEC §3: `D:/vscode/meta-harness/audits/2026-06-10-V5-launch-spec.md`
- Bartov-K 2017 anchor: `audits/2026-06-10-V5-stage-0-anchor-verify.md`
- β2 family precedent: `D:/vscode/meta-harness/audits/2026-04-27-eight-k-non-reliance-frozen-postmortem.md`
- Kill-audit generator (close-report scaffold): `D:/vscode/meta-harness/templates/kill-audit-generator.py`
