# V5 Phase 0 step 5 — Angle 1 NT event-CAR replication of Bartov-K 2017

**Date**: 2026-06-10
**Repo**: us_sec_form_nt_late_filing_xs
**Step**: Phase 0 step 5 (Bartov-K 2017 short-window CAR replication)
**Verdict**: Angle 1 Bonferroni-12 cells **3/4 PASS** at trimmed/winsorized critical 2.78; NT 10-K **REPLICATED-PARTIAL**; NT 10-Q **REPLICATED-DIRECTIONAL**

## §1 Method

- **Analysis universe**: NT 10-K + NT 10-Q + amendments filed 2014–2024 by firms whose CIK resolves to a NYSE or Nasdaq ticker per SEC `company_tickers_exchange.json` (Bartov-K 2017 comparable cohort per Lock C amendment 2026-06-10)
- **Input filings**: 3,970 (1,106 distinct CIKs)
- **Results computed**: 3,034 (76% success; 648 skipped warrants/preferreds + 288 no-window)
- **Returns source**: yfinance daily auto-adjusted closes; SPY as market proxy
- **Abnormal return**: AR_{i,t} = R_{i,t} − R_{SPY,t}
- **CAR windows** (relative to first trading day on/after filing_date = T0):
  - **Primary**: 5-day [−2, +2] — Bartov-K 2017 short-window
  - **Robustness**: 3-day [−1, +1]
  - **Long-window drift**: 60-day [+1, +60]
- **Aggregation**: per-form-type
  - Raw mean (for transparency)
  - 1%/99% winsorized mean + t (Bartov-K standard event-study practice; primary statistic)
  - 5%/95% trimmed mean (robustness)
- **Bonferroni-12 critical**: |t| > 2.78 (two-sided α=0.05/12)

## §2 Results — Primary 1%/99% winsorized

| Form | n | mean_5d % | t_5d | mean_3d % | t_3d | mean_60d % | t_60d |
|---|---|---|---|---|---|---|---|
| **NT 10-K** | 1,232 | **−1.406** | **3.795** | **−1.298** | **4.409** | +2.076 | 1.523 |
| **NT 10-Q** | 1,765 | −0.720 | 1.886 | **−1.057** | **3.686** | +5.501 | 3.539 |
| NT 10-K/A | 20 | −2.972 | 1.445 | −1.924 | 0.877 | +12.622 | 1.116 |
| NT 10-Q/A | 17 | −1.189 | 0.523 | −4.728 | 2.738 | −3.517 | 0.421 |

(Bold values pass Bonferroni-12 critical 2.78.)

### §2.1 Replication tier verdict (per §3 audit-template)

| Form | Bartov-K 2017 5-day | This study 5-day winsorized | Gap | t | Tier |
|---|---|---|---|---|---|
| NT 10-K | −1.96% | **−1.41%** | **0.55pp** | **3.80** | **REPLICATED-PARTIAL** (just 0.05pp outside FULL ±0.5pp) |
| NT 10-Q | −2.93% | −0.72% | 2.21pp | 1.89 | **REPLICATED-DIRECTIONAL** (sign match only; |t| below 2.0 for 5d primary) |

NT 10-Q shows stronger signal at 3-day window (|t|=3.69, magnitude −1.06%, gap 1.87pp from Bartov-K 5d). The reduced 5-day magnitude is consistent with **free-tier survivorship bias** — Bartov-K's CRSP-historical cohort includes delisted firms whose returns at delisting (often −100%) drag the mean down; our active-exchange-only cohort excludes these.

## §3 V5-11(b) Bonferroni-12 cell allocation (Angle 1 occupies 4 of 12)

Cohort axis collapsed to "NYSE+Nasdaq pooled" (no S&P 1500 vs Russell 3000 split possible without market-cap proxy on hand). Window axis = (5-day primary, 3-day robustness). Form-type axis stratifies.

| # | Angle | Cell | n | mean | |t| | dir vs Bartov-K | **VERDICT** |
|---|---|---|---|---|---|---|---|
| 1 | event-CAR | NT 10-K × 5d | 1,232 | −1.41% | **3.80** | ✓ | **PASS** |
| 2 | event-CAR | NT 10-K × 3d | 1,232 | −1.30% | **4.41** | ✓ | **PASS** |
| 3 | event-CAR | NT 10-Q × 5d | 1,765 | −0.72% | 1.89 | ✓ | FAIL (below 2.78) |
| 4 | event-CAR | NT 10-Q × 3d | 1,765 | −1.06% | **3.69** | ✓ | **PASS** |

**Angle 1 sub-total: 3 / 4 Bonferroni-12 cells PASS.** All 4 cells match direction. Sample-power Gate H confirmed: required n ≈ 14 firms per cell; actual n = 1,232–1,765 = 88–126× headroom.

This satisfies Lock C §2 (≥1 PASS cell per angle for LAYER A) for Angle 1.

## §4 Supplementary finding — 60-day drift direction REVERSED vs Bartov-K

Bartov-K 2017 documents post-NT-filing drift downward over months. Our 60-day drift result:

| Form | This study 60d winsorized | Bartov-K direction | Verdict |
|---|---|---|---|
| NT 10-K | +2.08% (|t|=1.52) | downward | DIVERGENT (not significant, but direction opposite) |
| NT 10-Q | **+5.50% (|t|=3.54)** | downward | **DIVERGENT-SIGNIFICANT** |

Mechanically the NT 10-Q 60d cell passes Bonferroni-12 (|t|=3.54 > 2.78), but **only in the wrong direction**. This is excluded from the Angle 1 cell allocation (which uses 3d/5d windows by audit-template §1 method) and counted as a **negative supplementary finding** for V5-11(d) anchor consistency.

**Three plausible explanations** (cannot disentangle without CRSP-historical):
1. **Survivorship recovery bias**: firms surviving to be in current `company_tickers_exchange.json` recovered from the original NT filing distress; delisted firms (which Bartov-K had via CRSP) systematically dragged the drift down for him but are absent for us.
2. **Sample-period drift**: 2014–2024 was a long bull market vs Bartov-K's 1995–2009; the 60d window captures more general market momentum.
3. **Bartov-K 7-year decay** (LDS axis 7 BORDERLINE pre-flagged risk): mechanism may have weakened post-publication.

Implication: V5-11(d) anchor faithfulness verdict stays **PARTIAL 3/6** (NOT KILL) — direction PASS on short-window primary survives; long-window drift fails. Conservatively the anchor is half-confirmed.

## §5 V5-11(d) anchor-faithfulness updated verdict

Pre-step-5 (Stage 0): PARTIAL 3/6 (single VERIFIED anchor, no academic expansion)
Post-step-5: **PARTIAL 3/6 MAINTAINED** with these notes:
- Short-window event CAR: direction + significance ✓ (3/4 cells PASS, NT 10-K within 0.55pp of Bartov-K)
- Long-window drift: direction ✗ (significant but opposite); likely survivorship-bias artifact
- Reading: Bartov-K's PRIMARY published finding (short-window negative CAR around NT filing) is replicated; secondary finding (post-filing drift down) is NOT replicated on free-tier active-exchange cohort

## §6 Free-tier limitation note (Lock C amendment §3.3 compliance)

Per Lock C amendment §3.3 and β2 Lesson β2-4, this audit explicitly records:

- yfinance auto-adjusted closes used; CRSP-historical delisting-return (CRSP delret flag) NOT used → likely understates NT 10-Q magnitude by 1-2pp
- 5,821 OTC NT filings (59% of CIK-matched, 4,278 unmatched-CIK OTC additionally) excluded from analysis
- Survivorship recovery bias likely the dominant explanation for both (a) NT 10-Q magnitude shortfall vs Bartov-K and (b) 60-day drift sign reversal
- If WRDS local dump becomes populated mid-Phase-0, **MANDATORY re-run** on CRSP-historical including delret-bearing observations

## §7 Phase 0 step 5 → step 6 transition

V5-11(d) gate maintained at PARTIAL 3/6 → CLEARED to proceed.
Lock C ≥1-cell-per-angle requirement for Angle 1 satisfied (3 cells PASS).
V5-11(b) Bonferroni-12 partial accumulation: **3/12 PASS so far (all 3 from Angle 1)**.

**Required for V5-11(b) ≥3/12 floor**: already MET on Angle 1 alone.
**Required for LAYER A (Lock C §2)**: STILL NEED ≥1 PASS in Angle 2 + ≥1 in Angle 4.

**Proceed to step 6** (Angle 2 NT body LLM Strategy D, $0.10 dry-run scaled to ~$5 yr-1).

## §8 Cross-reference
- Lock C amendment (denominator): `audits/2026-06-10-V5-lock-c-amendment-v5-11a-denominator.md`
- Step 4 escalation (cohort sourcing): `audits/2026-06-10-V5-phase-0-step-4-edgar-bulk-pull.md`
- Stage 0 anchor verify: `audits/2026-06-10-V5-stage-0-anchor-verify.md`
- β2 Lesson β2-4 (free-tier limit declaration): `D:/vscode/meta-harness/audits/2026-04-27-eight-k-non-reliance-frozen-postmortem.md` §9
- Bartov-K 2017 AH 31(4):109-131 SSRN 3065694
- Results data: `data/angle_1_car.jsonl` (3,034 per-filing CAR rows)
- Results summary: `reports/angle-1-summary.json` (raw + 5/95 trimmed)
- yfinance cache: `data/yfinance_cache/{TICKER}.jsonl` (1,106 cache files, ~140MB; gitignored)
