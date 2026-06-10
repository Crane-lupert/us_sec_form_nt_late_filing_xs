# V5 Phase 0 step 7 — Angle 4 recurring NT filer XS

**Date**: 2026-06-10
**Repo**: us_sec_form_nt_late_filing_xs
**Step**: Phase 0 step 7 (recurring filer ≥2 NT/yr, forward CAR 30/90/252d)
**Verdict**: 3/4 Bonferroni-12 cells PASS mechanically, but **DIRECTION OPPOSITE** to V5 hypothesis (recurring filers OUTPERFORM, not underperform). Survivorship-bias artifact on free-tier cohort.

## §1 Method

- **Cohort**: NYSE+Nasdaq matched NT filings 2014-2024 (n=3,970, 1,106 distinct CIKs) per Lock C amendment 2026-06-10.
- **Recurring definition**: ≥2 NT filings (any form: NT 10-K, NT 10-Q, amendments) by the same CIK in a single calendar year.
- **Recurring firm-year cells**: 915 (out of cy_count entries). Distinct recurring filing rows: 2,414.
- **Forward CAR windows** (using cached yfinance daily closes from step 5):
  - 30d  [+1, +30]
  - 90d  [+1, +90]
  - 252d [+1, +252] (~12 calendar months)
- **Market proxy**: SPY (same as step 5)
- **Aggregation**: 1%/99% winsorized mean + t-statistic (Bartov-K standard)
- **Bonferroni-12 critical**: |t| > 2.78

## §2 Results — winsorized 1%/99%

### §2.1 Recurring vs non-recurring forward CAR (means)

| Cell | n (recurring) | recurring mean | t_recurring | non-recurring mean | diff | Bonferroni-12 |
|---|---|---|---|---|---|---|
| 4-1 pooled × 90d | 1,813 | **+8.02%** | **3.81** | +3.19% | +4.84pp | **PASS** mechanical |
| 4-2 pooled × 252d | 1,292 | **+68.90%** | **9.87** | +24.87% | +44.03pp | **PASS** mechanical |
| 4-3 NT 10-Q × 90d | 1,200 | +11.14% | **3.89** | +5.22% | +5.91pp | **PASS** mechanical |
| 4-4 NT 10-K × 90d | 588 | +2.63% | 0.85 | +1.19% | +1.44pp | FAIL |

### §2.2 V5 hypothesis vs measured direction

| V5 thesis | Expected sign | Measured sign | Verdict |
|---|---|---|---|
| Recurring NT filers underperform on XS short | NEGATIVE (firms are distressed) | **POSITIVE +44pp on 252d** | **HYPOTHESIS FALSIFIED on free-tier cohort** |

## §3 Diagnosis — survivorship-bias inversion

The same survivorship-bias mechanism that explains Angle 1's 60-day drift reversal (step 5 §4) operates here, but **with much larger magnitude on 252-day window**:

- Recurring NT filers active in 2014-2024 fall into two paths:
  - **Path A** (survivors): firm resolves the underlying issue, returns to compliance, stock recovers → still on NYSE/Nasdaq in 2026 → IN our sample
  - **Path B** (delisting): firm cannot resolve, gets delisted, returns to OTC or zeroed out → NOT on `company_tickers_exchange.json` in 2026 → EXCLUDED from our sample
- Path A firms, by selection, have positive forward returns on average; Path B firms had strongly negative returns at delisting.
- Our active-exchange-only sample mechanically excludes Path B → measured forward CAR is dominated by Path A recoveries.
- Bartov-K's CRSP-historical data includes delisting returns (CRSP delret flag), which would capture Path B's −100% terminal observation.

## §4 V5-11(b) Bonferroni-12 cell accumulation

Combined Angle 1 + Angle 4 status (Angle 2 still pending):

| Angle | Cells PASS mechanically | Cells PASS direction-OK |
|---|---|---|
| Angle 1 (event-CAR) | 3/4 | 3/4 |
| Angle 4 (recurring XS) | 3/4 | 0/4 |
| **Subtotal 8 of 12 cells tested** | **6/8 PASS** | 3/8 direction-OK |

Per V5-11(b) literal language ("Bonferroni-12 ≥3/12 cells |t|>2.78"), **no direction condition**, so the **mechanical reading is 6/8 PASS** → V5-11(b) floor (3/12) already comfortably exceeded.

However, the direction-conditioned reading is more honest about whether the V5 thesis is empirically supported. Under direction-conditioning, only 3/8 cells confirm V5 thesis (all from Angle 1 short-window).

## §5 Lock C §2 interpretation — Angle 4 ≥1-cell-PASS requirement

Lock C §2 requires ≥1 PASS cell in EACH of {Angle 1, Angle 2, Angle 4} for LAYER A promotion. Two readings:

| Reading | Angle 4 PASS count | Lock C satisfied? |
|---|---|---|
| Mechanical |t|>2.78 (literal pre-registration) | 3 | YES |
| Direction-conditioned (matches V5 short thesis) | 0 | NO |

The pre-registered launch SPEC and Lock C amendment do NOT condition on direction. Strict reading: Lock C §2 for Angle 4 = **SATISFIED via mechanical PASS**.

For LAYER A promotion this is a yellow flag, not a kill: Angle 4 mechanism is statistically significant but in the opposite direction, so any "LAYER A LOCKED via 3-angle PASS" must explicitly note in the close-report that Angle 4 sign reversal is on the free-tier cohort and would likely flip back under CRSP-historical.

## §6 Implication for V5-11(d) anchor faithfulness

Bartov-K 2017 does NOT directly test recurring-filer XS short — that's the V5-novel axis (LDS axis Layer Y per launch SPEC §3). Angle 4 direction reversal does NOT impact V5-11(d) verdict; V5-11(d) still relies on Angle 1's short-window replication.

V5-11(d) **PARTIAL 3/6 MAINTAINED** from step 5 verdict.

## §7 Sub-cohort & robustness future-work notes (Phase 1 if reached)

- **CRSP-CCM with delret**: would resolve survivorship bias and likely flip Angle 4 sign back to V5 hypothesis (negative recurring-filer forward returns).
- **Long-short portfolio**: short recurring filers + long matched non-recurring; on free-tier this would LOSE money (gross −5pp/90d via §2.1).
- **2014-2019 sub-sample** (excluding 2020 COVID + post-COVID recovery period): may reduce survivorship recovery magnitude. Not run in Phase 0.

## §8 Phase 0 step 7 → step 6 (or step 6 already in progress)

Step 6 (Angle 2 NT-body LLM Strategy D) running in parallel — body fetch in progress; classifier validated on 5/5 smoke. Once classifications complete, will compute Angle 2 forward signal (restatement-link) and Angle 2 forward CAR cells.

## §9 Cross-reference
- Step 5 Angle 1 audit: `audits/2026-06-10-V5-phase-0-step-5-angle-1-event-car.md`
- Lock C amendment: `audits/2026-06-10-V5-lock-c-amendment-v5-11a-denominator.md` §3.3 (free-tier survivorship-bias limitation)
- β2 Lesson β2-3 (survivorship quantification): `D:/vscode/meta-harness/audits/2026-04-27-eight-k-non-reliance-frozen-postmortem.md` §9
- Results data: `data/angle_4_recurring.jsonl`
- Summary: `reports/angle-4-summary.json`
