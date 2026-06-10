# V5 us_sec_form_nt_late_filing_xs — Launch SPEC

**Date**: 2026-06-10
**ID**: V5 / **Repo**: `us_sec_form_nt_late_filing_xs` / **Pod**: Disclosure-Regulatory
**Verdict**: LAUNCH-with-tag BORDERLINE (Rule 9 P(fail) 40-60%)
**LDS**: 5/7 LIVE-DEPLOYABLE
**Anchor faithfulness**: PARTIAL 3-4/6 (single VERIFIED anchor pivot)

## §0 Identity

- Pod: Disclosure-Regulatory
- Data source: SEC EDGAR Form NT 10-K / Form NT 10-Q (Rule 12b-25) — free 10 req/s
- Cohort: ~2,115 distinct US-listed firms / 9yr (Bartov-Konchitchki 2017 replication base)
- Frequency: ~3,000 filings/yr

## §0.3 Identity locks

- **V5-11 Data-validity HARD KILL**:
  - (a) Lock F + EDGAR Form NT bulk pull working + NT-firm CIK match ≥90% (BORDERLINE ≥63%)
  - (b) Bonferroni-12 ≥3/12 cells |t|>2.78 (BORDERLINE ≥2/12)
  - (c) Net Sharpe post-15bps ≥0.30 (BORDERLINE ≥0.21) — **Phase 1 PASS at 0.46 (90d); Phase 3 Step 1 PIT acceptance-anchor re-verification 0.59 (90d)**
  - (d) Anchor faithfulness ≥PARTIAL via Bartov-K 2017 AH + Stage 0 2018+ academic verify
  - (e) **Phase 3 PIT-tradable lock** (added 2026-06-11): T=0 anchor must use SEC EDGAR `acceptanceDateTime` with after-hours (≥16:00 ET) reanchored to T+1. In-sample after-hours share **63.47%**, OOS **76.97%** — gate measured, V5-11(c) 90d Sharpe **STRENGTHENED** under PIT (0.46 → 0.59). See `audits/2026-06-11-V5-phase-3-step-1-pit-acceptance-anchor.md`.
- WRDS 미사용 (EDGAR public) — Lock F US-data scope still applies (3-pattern §8 grep 의무)
- LLM via `shared_utils.openrouter_client` 또는 claude-openai-proxy localhost:8787 only

## §0.4 Bayesian prior + Rule 9 risks

- Discovery-form prior: ~25% (Disclosure event-study family + LLM extraction layer)
- P(fail) = 40-60% → LAUNCH-with-tag BORDERLINE (Rule 9)
- Pre-acknowledged HIGH-risk:
  1. Anchor Bartov-K 2017 7-year post-publication decay (LDS axis 7 BORDERLINE)
  2. 사용자 cite P8 verify 3/4 fail (single anchor pivot — Stage 0 2018+ academic verify 의무)
  3. β2 us_eight_k_non_reliance_llm FROZEN-NEGATIVE overlap risk (CIK × 분기 cross-tab Phase 0 의무)

## §1 Anchor (PIVOT — single VERIFIED)

**Bartov, E. & Konchitchki, Y. (2017)** "SEC Filings, Regulatory Deadlines, and Capital Market Consequences" *Accounting Horizons* 31(4):109-127, SSRN 3065694.
- Sample: 2,115 firms × 9yr (Lock-V5-1)
- NT 10-Q 5-day CAR: -2.93% (Lock-V5-2)
- NT 10-K 5-day CAR: -1.96% (Lock-V5-2)
- Post-NT drift down (long-term return reversal direction)

**사용자 cite 3 fail + 1 HALLUCINATED**: Files-Sharp-Thompson 2013 JAR MIS-CITED (실재 = repeat restatement 2014 AH) / Kinney-Burgstahler-Martin 2002 JAR SCOPE-MISMATCH (earnings surprise materiality) / Hribar-Kravet-Wilson 2014 MIS-CITED (RAST not CAR) / Bartov-Coltman-Frey 2022 HALLUCINATED — 4종 모두 DROP.

**Stage 0 의무 expansion**: 2018-2025 post-Bartov-K WebSearch `("Form NT 10-Q" OR "Form 12b-25") AND (restatement OR "late filing")` — Stage 0 audit 결과로 anchor base 확장 시도.

**PwC 2023 PCA Blog**: practitioner observation only — context, NOT anchor.

## §2 Mechanism

3-angle stack:
- **Angle 1** (replication): NT 10-Q/10-K filing date 기준 5-day CAR Bartov-K 2017 replication (S&P 1500 / Russell 3000 양 cohort).
- **Angle 2** (LLM forward): NT body LLM-extract narrative ("accounting issue identified" / "audit unresolved" / "other") → 3-21d 내 restatement 8-K Item 4.02 또는 4.01 probability forward signal.
- **Angle 4** (recurring XS): Recurring NT filer (연 ≥2회) firm-level cross-section short 12-mo forward portfolio.

## §3 Novelty 3-axis

| Axis | Score | Note |
|---|---|---|
| 방법론 | N | Event-study standard |
| 데이터 | N | Form NT EDGAR public |
| Layer | Y | LLM NT body extract + restatement forward + recurring filer XS — anchor 본문 외 |

**종합 1/3 PASS** — angle 2 + angle 4 가 novelty edge. Angle 1 단독은 MECHANICAL replication (Stage 0 sub-gate S0-4 lock).

## §4 β2 differentiation (Stage 0 S0-2)

β2 us_eight_k_non_reliance_llm (FROZEN-NEGATIVE 2026-04-27):
- 8-K Item 4.02 ex-post non-reliance disclosure / κ 0.89 validated / alpha not (n=305)

V5 vs β2:
- Filing form: 8-K (ex-post) vs NT (ex-ante)
- Timing: post-restatement vs pre-restatement
- LLM target: 8-K Item 4.02 text vs NT body "accounting issue / unresolved"
- Mechanism overlap 추정 <30%; Cohort overlap 추정 ≤15%

Phase 0 코드에 CIK × 분기 cross-tab overlap audit 1회 실행 의무. ≥30% 시 STOP + 사용자 escalate.

## §5 Phase 0 step

1. Bootstrap external repo (Bash heredoc; .claude/settings.json deny WRDS-import + OPENROUTER_API_KEY direct + gh push)
2. Stage 0 sub-gates S0-1..S0-4 (BLOCKING)
3. Lock F §8 grep
4. EDGAR Form NT bulk pull 2014-01-01 ~ 2024-12-31
5. Angle 1 event-CAR replication
6. Angle 2 NT body LLM Strategy D ($0.10 dry-run → $50/yr scale)
7. Angle 4 recurring filer XS 12mo
8. Bonferroni-12 + Net Sharpe ledger
9. V5-11 verdict commit + close-report on FAIL

## §5b Phase 3 (added 2026-06-11)

PIT-tradable lock + LLM vintage leakage + delisting/borrow proxy.

1. **Step 1 (completed 2026-06-11)** — `extract-acceptance-datetime.py` + `compute-angle-2-forward-pit.py` + Net Sharpe re-run on PIT input. V5-11(c) 90d net Sharpe **0.59** (vs 0.46 pre-registered). `audits/2026-06-11-V5-phase-3-step-1-pit-acceptance-anchor.md`.
2. **Step 2 (open)** — Vintage-controlled (pre-2024 cutoff) alt-LLM re-extraction on OOS 2024+ to test classifier-weight forward leakage. OpenRouter Claude avoidance.
3. **Step 3 (open)** — CRSP delisting return + Russell 3000 / float-tier borrow-availability proxy + differentiated TC sweep ({15, 25, 50} bps × {full, large-cap-only} cohort).

## §6 LDS 5/7

Axis 1 PASS (3,000/yr) / Axis 3 PASS (daily) / Axis 4 PASS (2,115) / Axis 5 PASS ($3/yr LLM + 15bps) / Axis 6 PASS (12b-25 stable) / Axis 2 unknown / Axis 7 BORDERLINE (Bartov-K 7y post-pub) → LIVE-DEPLOYABLE.

## §7 Lock numerical-fact registry (§0.5 cross-audit)

- Lock-V5-1: 2,115 firms × 9yr (Bartov-K 2017 AH 31(4):109-127)
- Lock-V5-2: NT 10-Q CAR -2.93% / NT 10-K CAR -1.96%
- Lock-V5-3: Bonferroni-12 cells (3 angle × 2 cohort × 2 forward)
- Lock-V5-4: Net Sharpe ≥0.30 (BORDERLINE 0.21)
- Lock-V5-5: EDGAR CIK match ≥90% (BORDERLINE 63%)
- Lock-V5-6: LLM spend ceiling $50/yr
- Lock-V5-7: **PIT acceptance-anchor** (added 2026-06-11) — `anchor_date = acceptance_et_date + (1d if after_16et else 0d)`; in-sample after-hours share 63.47%, Net Sharpe 90d 0.59 (PIT) vs 0.46 (date_filed). Lock-V5-4 deployment floor SATISFIED under PIT-clean.

## §8 Reviewer override

Rule 9 P(fail) 40-60% LAUNCH-with-tag BORDERLINE — 사용자 명시 iter 14 V-batch LAUNCH 결정. Single-anchor pivot 감수, β2 mechanism-axis distinct + Stage 0 anchor expansion 의무.
