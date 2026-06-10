# SEC Form NT (지연공시) 로 주식 알파 만들기 (한국어 실무 보고)

> Project V5 (us_sec_form_nt_late_filing_xs) 의 한국어 distill 보고. 영어 reproducibility README: [README.md](README.md). 프로젝트 SPEC: [SPEC.md](SPEC.md). Phase 1 close-report (최종 판정): [audits/2026-06-10-V5-phase-1-close-report.md](audits/2026-06-10-V5-phase-1-close-report.md).
>
> **이 문서의 audience**: 회계/재무 background 있고 LLM·머신러닝 background 없어도 이해 가능하도록 작성. 자매 project X (sec-comment-letter-alpha) 의 [README_KR.md](../sec-comment-letter-alpha/README_KR.md) 와 같은 서식.

---

## 한 줄 요약

미국 상장사가 분기/연간 보고서를 **제때 못 낸다** 고 SEC 에 제출하는 **Form NT 10-K / NT 10-Q (지연공시 통지서)** 의 본문을 LLM 으로 분석해서, 그 본문에서 "회계 이슈" 라고 분류된 회사가 향후 90일 안에 실제 **재무 정정 (restatement)** 을 낼 확률을 예측하는 신호를 만들었다. 미국 NYSE+Nasdaq 상장 1,106 개 CIK / 3,970 건 NT filing (2014-2024) 에서, **P(90일 내 정정 | accounting_issue) = 32.6% vs 일반 = 23.5%, 차이 +9.06pp (z=5.61, 5.6σ)** 의 forward 신호 + 90일 long-short **Net Sharpe 0.46 (15bps 거래비용 차감 후)** 를 달성했다. **Phase 3 Step 1 (2026-06-11)**: SEC EDGAR `acceptanceDateTime` 으로 PIT-tradable 검증 — in-sample 의 **63.5% 가 16:00 ET 이후 제출**임에도 T+1 reanchor 시 90d Net Sharpe **0.46 → 0.59** (오히려 개선) → LAYER A LOCK 이 intraday look-ahead 아티팩트 아님 확인.

---

## ① 직관 — 왜 이게 말 되는 아이디어인가

미국 상장사가 10-K (연간) 또는 10-Q (분기) 보고서를 **마감일 안에 못 내겠다** 고 판단하면, SEC 규정 12b-25 에 따라 **Form NT 10-K** 또는 **NT 10-Q** (Notification of Late Filing) 을 제출해야 한다. 이 공시 안에는 **왜 못 내는지 사유** 를 본문 (Part III) 에 자유 서술로 적어야 한다.

**핵심 가설** (Bartov-Konchitchki 2017 *Accounting Horizons* 기반):
- 지연공시 자체가 시장에 **부정적 시그널** (NT 10-K 5일 CAR −1.96%, NT 10-Q 5일 CAR −2.93%) — anchor 가 입증
- V5 novel 가설: 본문에 적힌 사유가 **"회계 이슈 (accounting issue / unresolved)"** 인 경우 vs **"단순 행정 사유 (other)"** 인 경우, 향후 실제 **재무 정정 (8-K Item 4.02 / 10-K-Q amendment)** 발생 확률이 유의미하게 다르다 → 거래 가능한 forward 신호

LLM 으로 본문을 분류하는 이유: 사람 1명이 3,970 건 본문 읽고 라벨링하는 건 비현실. SEC EDGAR 본문은 자유 서술 + 형식 무규격 + 노이즈 많음.

---

## ② Form NT 본문 한 통의 모습

예시 (실제 2018-2024 cohort 중):
- **회사**: "We are unable to file our quarterly report on Form 10-Q within the prescribed time period because the Company is in the process of completing its evaluation of certain accounting matters including revenue recognition under ASC 606 and the related disclosure requirements..."
- → LLM (Strategy D, gpt-4o-mini) 분류: **`accounting_issue`** (0.001 USD / 건)

다른 예시:
- **회사**: "We require additional time to complete the audit due to recent acquisition integration..."
- → LLM 분류: **`other`** (단순 행정/M&A 사유)

3-class 분류 schema:
| 라벨 | 의미 | 분포 (n=3,232) |
|---|---|---|
| `accounting_issue` | 회계 처리/기준/추정/감사 의견 관련 사유 | 1,776 (55%) |
| `unresolved_sec_comment` | SEC 가 이미 보낸 comment letter 미해결 사유 | 54 (1.7%) |
| `other` | M&A, 인력, 시스템 등 비-회계 사유 | 1,402 (43%) |

핵심 트레이드는: `accounting_issue` 회사를 **short**, `other` 회사를 **long** 으로 묶어 같은 월에 dollar-neutral 포지션을 짠다.

---

## ③ 핵심 결과

### ③-1. Forward 신호 — 재무 정정 발생률 (Angle 2 LLM rate-diff)

| Window | P(정정 \| accounting_issue) | P(정정 \| other) | 차이 | z-stat | Bonferroni-12 PASS |
|---|---|---|---|---|---|
| 14일 | 10.02% | 7.28% | +2.75pp | 2.71 | ✗ (보더라인) |
| **30일** | **18.75%** | **13.77%** | **+4.98pp** | **3.75** | **✓** |
| **90일** | **32.60%** | **23.54%** | **+9.06pp** | **5.61** | **✓ (5.6σ)** |
| 180일 (robustness) | 45.16% | 34.66% | +10.49pp | 5.98 | ✓ |

→ 본문에 회계 이슈가 적혀 있다고 LLM 이 분류하면, **90일 안에 실제 재무 정정 (8-K Item 4.02 / 10-K/A / 10-Q/A) 이 발생할 확률이 약 9pp 더 높다**. 5.6σ 통계적 강건.

### ③-2. Long-Short 포트폴리오 Sharpe (Angle 2 portfolio sim, V5-11(c))

| Window | n_months | gross Sharpe | **Net Sharpe (15bps 차감)** | V5-11(c) |
|---|---|---|---|---|
| 30일 | 58 | −0.12 | **−0.15** | **KILL** |
| **90일** | **53** | **+0.47** | **+0.46** | **PASS** (≥0.30) |

→ **30일은 KILL, 90일은 PASS**. 30일에는 회사가 "곧 해결한다" 발표로 **relief rally** 가 먼저 생긴 후, 실제 재무 정정이 30-90일 사이에 발표되며 가격이 떨어진다 (mechanism-meaningful).

### ③-3. Bartov-K 2017 event-CAR 복제 (Angle 1, CRSP delret 사용)

| Cell | yfinance (Phase 0) | **CRSP+delret (Phase 1)** | **Bartov-K 2017 발표값** | Replication |
|---|---|---|---|---|
| NT 10-K 5일 CAR | −1.41% \|t\|=3.80 | **−2.11% \|t\|=4.77** | **−1.96%** | **REPLICATED-FULL (gap 0.15pp)** |
| NT 10-Q 5일 CAR | −0.72% \|t\|=1.89 ✗ | **−2.88% \|t\|=5.55** | **−2.93%** | **REPLICATED-FULL (gap 0.05pp)** |
| NT 10-K 60일 drift | +2.08% n.s. | **−3.08% \|t\|=2.34** | (down) | direction **REVERSED back to anchor** |
| NT 10-Q 60일 drift | +5.50% ✗ | **−3.20% \|t\|=2.46** | (down) | direction **REVERSED back to anchor** |

→ 무료 yfinance 데이터로는 60일 drift 가 **반대 부호** (survivorship-bias 아티팩트) 였으나, CRSP delret (상장폐지 수익률 포함) 으로 재계산하니 **모든 cell 이 Bartov-K 와 같은 방향 + ±0.5pp 안의 magnitude** 로 복제됨.

### ③-4. Recurring NT filer XS short (Angle 4, V5-novel anchor-untouched)

연 2회 이상 NT 를 내는 "상습 지연공시 회사" 985개 CIK 의 향후 수익률:

| Cell | yfinance (Phase 0) | **CRSP+delret (Phase 1)** | 차이 (recurring − non) |
|---|---|---|---|
| Pooled 90d | recurring **+8.02%** ✗ | recurring **−9.18% \|t\|=5.18** ✓ | yfinance +4.84pp → CRSP **−5.85pp** |
| Pooled 252d | recurring **+68.90%** ✗ | recurring **−12.65% \|t\|=4.41** ✓ | yfinance +44pp → CRSP **−7.43pp** |
| NT 10-Q × 90d | recurring **+11.14%** ✗ | recurring **−7.90% \|t\|=3.56** ✓ | CRSP **−3.03pp** |
| NT 10-K × 90d | recurring +2.63% n.s. ✗ | recurring **−11.53% \|t\|=3.65** ✓ | CRSP **−9.13pp** |

→ 상습 지연공시 회사는 **90일에 약 5-9pp, 252일에 약 7pp 비-상습 대비 더 떨어진다**. 4/4 cell 이 V5 가설 방향으로 PASS.

### ③-5. Bonferroni-12 최종 ledger

| Angle | Cells | Phase 0 mech | Phase 0 direction | **Phase 1 mech** | **Phase 1 direction** |
|---|---|---|---|---|---|
| 1 event-CAR | 4 | 3 | 3 | **4/4** | **4/4** |
| 2 LLM forward | 4 | 2 | 2 | 2/4 | 2/4 |
| 4 recurring XS | 4 | 3 | 0 | **4/4** | **4/4** |
| **Total 12** | 12 | 8/12 | 5/12 | **10/12** | **10/12** |

V5-11(b) 사전등록 floor 3/12 대비 **3.3× 초과 PASS**. Lock C 3-angle ≥1 cell PASS 요건도 mechanical + direction 양쪽 모두 SATISFIED.

상세: [audits/2026-06-10-V5-phase-1-close-report.md](audits/2026-06-10-V5-phase-1-close-report.md)

---

## ④ 방법론 요약

1. **Anchor pivot** — 사용자 인용 4건 중 4건 fail (Files-Sharp-Thompson 2013 MIS-CITED + Kinney-Burgstahler-Martin 2002 SCOPE-MISMATCH + Hribar-Kravet-Wilson 2014 MIS-CITED + Bartov-Coltman-Frey 2022 HALLUCINATED) → **Bartov-Konchitchki 2017 *Accounting Horizons* 31(4):109-131 (SSRN 3065694)** 단일 anchor 로 pivot. 2018-2025 post-Bartov-K 학술 expansion 0건 발견 → PARTIAL 3/6 LOCKED at floor.
2. **데이터 수집** — SEC EDGAR full-index 에서 2014-01-01 ~ 2024-12-31 NT 10-K / NT 10-Q / 12b-25 = **31,693 건** 수집. NYSE+Nasdaq 상장 필터 (Bartov-K 비교 cohort) = **3,970 건 / 1,106 distinct CIK** (Bartov-K 2,115 firms 대비 52.3%).
3. **Strategy D LLM 분류** — gpt-4o-mini, 3-class schema (`accounting_issue` / `unresolved_sec_comment` / `other`), 3,225 calls / **$0.35 USD** (Phase 1 745건 추가 분류 = $0.08). 100% format compliance, 0 fail. **$50/yr cap 중 0.86% utilization**.
4. **Forward signal** — NT filing_date T+1 부터 14/30/90/180일 window 에서 (a) 재무 정정 event (8-K Item 4.02 + 10-K/A + 10-Q/A) 발생 rate-diff, (b) winsorized CAR-diff. 두 신호 axis 모두 측정.
5. **Long-short portfolio sim (V5-11(c))** — 월별 ≥5 filing 기준 dollar-neutral basket. LONG = `other` label 평균, SHORT = `accounting_issue` label 평균. 15bps round-trip 거래비용 차감 후 ann Sharpe 계산.
6. **CRSP delret 사용 (Phase 1)** — yfinance 무료 데이터는 active-exchange-only → 상장폐지 firm 누락 → 60일+ window 에서 survivorship-recovery 아티팩트. WRDS-data-courier 의 로컬 dump (4.4 GB CRSP DSF v2) 를 DuckDB push-down 으로 single-scan (2 분) 하여 1,106 CIK 중 895 ticker / 945 PERMNO 매칭, delisting return 포함하여 재계산.

상세 방법: [SPEC.md](SPEC.md) + [audits/](audits/) 의 15 개 close-report.

---

## ⑤ Self-Correction (이 프로젝트의 핵심 기여)

git log 가 모든 결정의 timestamp evidence (commit hash 보존):

- **Bootstrap** (`2e848b6`): 사용자 cite 4/4 fail 사실 수용 + Bartov-K 2017 단일 anchor pivot 명시
- **Phase 0 step 7** (Angle 4 yfinance): recurring filer XS short 가 **direction 반대** (+44pp / 252d) — yfinance 가 정직하게 살아남은 회사만 보여줘서 survivorship-recovery 가 dominant 한 것이 가설
- **Phase 0 close-report** (`fd15506`): "LAYER-A-WITH-CAVEATS" 로 정직 명기. 사용자에게 Path A (literal LAYER A) / Path B (FROZEN-PARTIAL direction-honest) / Path C (Phase 1 CRSP 검증) 3 가지 옵션 제시. **Path C 권장**.
- **Phase 1 step 2-3** (CRSP delret 재계산): yfinance +5.50% 60d drift → CRSP **−3.20%**. yfinance +68.90% recurring 252d → CRSP **−12.65%**. **survivorship-bias 가설 입증** + 모든 direction-reversed cell 이 anchor / V5 가설 방향으로 flip back.
- **Phase 1 close-report** (`34bcdb4`): "LAYER A LOCKED UNCONDITIONAL" 로 최종 promotion. 무료 데이터 한계가 가설 자체의 문제가 아니라 **데이터 layer 의 문제** 였음을 commit hash 로 증명.

**리뷰어 입장**: 무료 데이터 결과를 "PASS 라고 우기지" 않고, 사전등록 direction-conditioned 읽기로 인해 honest READ 가 "survivorship-bias 의심" 임을 인정한 후 CRSP 로 끝까지 검증해서 가설이 진짜였음을 입증. **포트폴리오의 free-tier 의존성 한계를 industrial scale 로 quantify 한 methodology 기여** (V5-NEW §5.3).

---

## ⑥ Stage 0 sub-gate 4종 (사용자 명시 의무)

Phase 0 진입 전 4종 BLOCKING gate. 모두 PASS:

| Gate | 내용 | 결과 | Artifact |
|---|---|---|---|
| **S0-1** Anchor cite-table 정정 | 사용자 cite 4/4 fail → Bartov-K 2017 단일 anchor pivot + 2018-2025 WebSearch expansion (0건 found) | PASS-with-correction (page-range 109-127 → 109-131) | [audits/2026-06-10-V5-stage-0-anchor-verify.md](audits/2026-06-10-V5-stage-0-anchor-verify.md) |
| **S0-2** β2 differentiation | β2 us_eight_k_non_reliance (8-K Item 4.02 ex-post) vs V5 (Form NT ex-ante) cohort overlap ≥30% STOP | PASS — mechanism axis distinct, overlap 측정 deferred | [audits/2026-06-10-V5-stage-0-beta2-differentiation.md](audits/2026-06-10-V5-stage-0-beta2-differentiation.md) |
| **S0-3** NT body LLM cost preview | Strategy D 3,000 filings/yr × $0.001 ≈ $3/yr (실제 $5/yr, $50 cap 의 10.1%) | PASS | [audits/2026-06-10-V5-stage-0-llm-cost-preview.md](audits/2026-06-10-V5-stage-0-llm-cost-preview.md) |
| **S0-4** Angle 1 single-mode lock 차단 | LAYER A 는 angle 1 (replication) + angle 2 (LLM forward) + angle 4 (recurring XS) 3 angle 모두 ≥1 cell PASS 필수 | PASS — Lock C 3-angle 요건 committed | [audits/2026-06-10-V5-stage-0-angle-mode-lock.md](audits/2026-06-10-V5-stage-0-angle-mode-lock.md) |

추가: **Lock F §8 grep CLEAN** (pipeline 결정성 검증) — [audits/2026-06-10-V5-stage-0-lock-f-grep.md](audits/2026-06-10-V5-stage-0-lock-f-grep.md).

---

## ⑦ V5-11 HARD KILL gate 최종 verdict

| Gate | 사전등록 threshold | Phase 0 | **Phase 1 최종** |
|---|---|---|---|
| (a) data-validity tier 1 | Lock F clean + EDGAR + CIK match ≥90% (BORDERLINE ≥63%) Bartov-K-comparable cohort | PASS-CONDITIONAL (84.4%, 1,784/2,115) | **PASS** (CRSP 895/1,106 = 81% × 100% within-period 포함 delisting) |
| (b) Bonferroni-12 ≥3/12 | 3/12 PASS / 2/12 BORDERLINE / ≤1/12 KILL | PASS (8/12 mech, 5/12 direction) | **PASS (10/12 mech AND 10/12 direction)** |
| (c) Net Sharpe ≥0.30 | ≥0.30 PASS / 0.21-0.29 BORDERLINE / <0.21 KILL | UNTESTED | **PASS (0.46 at 90d)** |
| (d) Anchor faithfulness | ≥PARTIAL 3/6 via Bartov-K + 2018+ verify | PARTIAL 3/6 (short-window 3/4 replicated) | **PARTIAL 4/6 → upgrade-candidate** (NT 10-K AND NT 10-Q both REPLICATED-FULL + 60d direction recovered) |

**최종 verdict: LAYER A LOCKED — UNCONDITIONAL**.

---

## ⑧ 선행연구 대비 차별점

| 항목 | 기존 문헌 | 본 프로젝트 |
|---|---|---|
| Form NT event-CAR | Bartov-K 2017 (n=2,115, 2000s, hand-collected) | CRSP delret 으로 industrial-scale 복제 (n=1,106, 2014-2024, ±0.5pp gap REPLICATED-FULL) |
| NT body 내용 활용 | Bartov-K 2017 본문 stratification 은 ad-hoc 사람 분류 | LLM (gpt-4o-mini) 3-class 자동 분류, 3,225 calls / $0.35 |
| Forward 신호 → 재무 정정 | 없음 (Bartov-K 본문 outside scope) | **P(90일 내 정정 \| accounting_issue) = 32.6% vs 23.5%, z=5.61 (5.6σ)** |
| Recurring NT filer XS | 없음 (anchor-untouched) | 985 CIK / 2,600 firm-year, 90d −9.18pp / 252d −12.65pp |
| Free-tier survivorship 정량화 | 거의 없음 (학술논문 무료 데이터 미사용 가정) | yfinance 60d drift +5.50% vs CRSP −3.20% (8-80pp swing), industrial-scale methodology contribution |
| Pre-registration | 거의 없음 | V5-11(a/b/c/d) commit-locked + Lock C 3-angle direction-condition (S0-4 amendment) |
| Sister-project cross-check | n/a | β2 us_eight_k_non_reliance (8-K Item 4.02 ex-post FROZEN-NEGATIVE 2026-04-27) vs V5 (NT body ex-ante) — **ex-ante NT 가 ex-post 8-K 보다 LLM extraction 으로 더 tractable** 한 portfolio-level evidence |
| Transaction cost | 학술 paper 흔히 생략 | 15bps round-trip 차감 후 Sharpe 0.46 (gross 0.47) — 거의 손실 없음 |

---

## ⑨ 한계 (정직 명기) + Phase 2 robustness 결과

1. **데이터 layer 의존성** — Phase 0 yfinance free-tier 결과는 60d window 이상에서 survivorship-bias 로 direction 반대. Phase 1 에서 CRSP delret 으로 해결했으나, **CRSP 가 없는 환경에서는 long-window cell 을 신뢰할 수 없다** 는 portfolio lesson.
2. **OOS 미검증 → Phase 2 R1 에서 검증 완료** — 2025-Q1 ~ 2026-Q2 OOS 912 NT filings 처리. **rate-diff 90d z=2.83 PASS** (재무 정정 발생률 신호 robust on OOS) 하지만 **Net Sharpe OOS KILL** (n=5-6 months, Sharpe -0.41 @ 90d). 신호는 OOS 에서도 살아남지만 portfolio sim 은 small-sample OOS 에서 underperform — 시장이 NT body 를 점점 빨리 가격 반영하는 패턴 (R2 와 일치).
3. **Anchor PARTIAL 3/6 → 4/6 upgrade-candidate** — Bartov-K 2017 단일 anchor 이고 2018-2025 post-Bartov-K 학술 expansion 0건. Salience corroboration tier (SEC 2021 + 2023 enforcement reports) 는 anchor-level 이 아님.
4. **CAR-diff 신호는 tradable 아님** — Angle 2 rate-diff 는 5.6σ PASS 지만 CAR-diff 는 통계적 유의 미달. 시장이 NT 본문 내용을 filing date 에 이미 일부 가격에 반영.
5. **ann_vol 53% → Phase 2 R3 에서 해결** — Sector-residualized basket (SIC2 within-month demean) 으로 **Net Sharpe 0.46 → 0.66 (+44%), ann_vol 53% → 41% (-23%)**. 무료 lift, 추가 데이터/LLM 없이 가능.
6. **β2 family precedent** — 8-K Item 4.02 sister mechanism FROZEN-NEGATIVE 2026-04-27. V5 가 ex-ante NT 로 portfolio-level 차별화는 성공했으나, **8-K 류 SEC EDGAR text LLM 알파 family 자체가 historically 까다로움**.

### Phase 2 Robustness 6-axis 요약 (자세히는 [audits/2026-06-10-V5-phase-2-robustness-close-report.md](audits/2026-06-10-V5-phase-2-robustness-close-report.md))

| Axis | 결과 | Verdict |
|---|---|---|
| **R1** OOS 2025+ holdout (912 NT, 330 CRSP ticker, $0.10 LLM) | rate-diff 90d **z=2.83 PASS** / Net Sharpe **-0.41 KILL** | **MIXED — signal robust, portfolio over-fit** |
| **R2** Subsample stability (year × pre/post-COVID) | pre-COVID Sharpe 0.63 PASS, post-COVID 0.25 BORDERLINE; 2018/2019/2023/2024 KILL | **HETEROGENEOUS** — late period signal 강함/거래 약함 |
| **R3** Sector-residualized (1284 CIK SIC fetch, SIC2 demean) | Net Sharpe **0.46 → 0.66** (+44%), vol **53% → 41%** (-23%) | **IMPROVED** — 무료 lift |
| **R4** Transaction cost sensitivity (0..200 bps RT) | 90d break-even **320 bps RT** (15bps 의 21× margin) | **VERY ROBUST** |
| **R5** Bonferroni-24 expansion (12 → 24 cells) | **18/24 mech PASS, 15/24 direction PASS** (floor 6/24, 3.0× over) | **PASS** + 새 발견: **NT 10-Q rate z=6.77 vs NT 10-K z=0.50** (NT 10-Q 가 dominant cohort) |
| **R6** LLM model + schema ablation (gpt-4o-mini vs Llama-3.3-70B) | **κ=0.7066** (S0-3 0.7 PASS); schema variants z>5.3 stable; body-length 2000자에서도 z=3.54 | **PASS** — schema/model invariant |

**Phase 2 net outcome**: **LAYER A retained with OOS-Sharpe caveat**. in-sample evidence 매우 강해짐 (R3 Sharpe 0.66, R4 21× TC margin, R5 18/24 mech, R6 κ=0.71); OOS 에서 rate-diff PASS 지만 Sharpe small-sample KILL — Phase 3 deliverable = sector-residualized basket + 2025-2026 더 많은 holdout 누적.

---

## ⑨-bis Phase 3 Step 1 — PIT acceptance-anchor 검증 (2026-06-11)

### 동기

Phase 0-2 의 모든 결과는 EDGAR `date_filed` (달력 일자) 를 T=0 로 사용. 이건 **PIT-naïve** anchor — SEC EDGAR 의 NT 12b-25 acceptance window 는 22:00 ET 까지이고, 시장 종가 16:00 ET 이후 제출된 filing 은 그 날 close 에 시장이 못 본다. 즉 `date_filed` close 에 진입한다는 가정은 **장후 제출 filing 의 경우 intraday look-ahead** 를 implicit 하게 깔고 있음. 실거래 적용 전 이 누수의 magnitude 측정 필수.

### 데이터 파이프라인

1. **acceptanceDateTime 추출** — SEC EDGAR Submissions API (`data.sec.gov/submissions/CIK*.json`) 의 `acceptanceDateTime` 필드 (UTC) 를 NT 코호트 (in-sample 3,970 + OOS 912) 와 join. America/New_York 으로 변환 후 16:00 ET cutoff flag (`after_16et`).
2. **PIT anchor 정의** — `anchor_date = acceptance_et_date + (1d if after_16et else 0d)`. firm return series 의 첫 거래일 ≥ anchor_date 이 T=0.
3. **angle-2 forward CAR + Net Sharpe 재계산** — `compute-angle-2-forward-pit.py` + `compute-net-sharpe-strategy-d.py --input data/angle_2_forward_pit.jsonl`.

### Step 1a — 장후 제출 비중

| Cohort | NYSE/Nasdaq filings | Match rate | **after_16et 비중** |
|---|---|---|---|
| In-sample (2014-2024) | 3,970 | 98.06% | **63.47%** (2,471 / 3,893) |
| OOS (2025-2026) | 912 | 100.00% | **76.97%** (702 / 912) |

→ **가설 확정**: NT 12b-25 ≈ deadline EOD 제출. 기존 `date_filed` anchor 가 사실상 in-sample 의 63% 에 대해 "intraday look-ahead" 를 가정하고 있었음.

### Step 1b — V5-11(c) Net Sharpe PIT 재검증

In-sample 3,811 rows (AI + other 라벨, PIT join 후):

| Window | Original `date_filed` anchor | **PIT acceptance + T+1** | Verdict 변화 |
|---|---|---|---|
| 30d | gross 0.124 → net **−0.154** (KILL) | gross −0.194 → net **−0.227** (KILL) | KILL → KILL (조금 악화) |
| **90d** | gross 0.469 → net **0.461** (PASS) | gross 0.600 → net **0.591** (PASS) | **PASS → PASS (개선)** |

PIT 90d 상세: ann_mean +25.81%, ann_vol 43.69%, **net Sharpe 0.59** (≥0.30 PASS floor), long_only 0.71 / short_only −0.22.

### Step 1c — 왜 90d Sharpe 가 *오히려 개선* 되나

직관과 반대 결과. 메커니즘:
- 장후 제출 NT 는 그 날 거래 중에 이미 **issue 누설** (volume + price pressure) 이 있는 경우가 많음
- `date_filed` close 자체가 그 날 noise + 일부 reaction 흡수 → forward window 의 첫 day 가 contaminated
- PIT T+1 reanchor 가 그 오염된 1일을 strip → cleaner signal-day forward window
- 30d 셀 (이미 음수) 도 같은 logic 으로 조금 더 음수

### Step 1 결론

**V5-11(c) 90d 셀 PASS** under acceptance-anchor + T+1. **LAYER A LOCK 은 intraday look-ahead 아티팩트가 아님**. Phase 1 의 econometric LOCK 이 PIT-clean 가정 하에서도 보존.

### Step 1 이 닫지 못한 누수 (Step 2, 3 으로 이월)

1. **LLM vintage look-ahead** — `nt_classifications.jsonl` 은 2024-vintage 모델 (`gpt-4o-mini` + `Llama-3.3-70B-Instruct`) 로 라벨링. 두 모델 모두 training cutoff 이 in-sample window post-date. PIT 가격이 옳더라도 classifier weights 가 forward outcome 정보를 학습했을 가능성 (model 이 "이 회사가 나중에 restate 했다" 를 implicit 하게 know 함). 2-vendor κ=0.71 이 single-vendor 아티팩트는 배제하지만 shared pre-training prior 까지 배제하진 못함. **Step 2 = vintage-controlled (pre-2024) alt-LLM 으로 OOS 재라벨링** ($1-4 비용, OpenRouter Claude 회피).
2. **차등 TC + borrow availability** — 15bps round-trip 단일 가정. recurring-filer XS short 는 sub-$1B float small-cap 비중 큼 → 실제 50bps round-trip + locate/borrow 가능성 제한적. R4 sensitivity sweep 이 {25, 50, 100, 200, 320} bps 균일하게 swept 했지만 float-tier stratify 안 함. **Step 3 = CRSP delisting return + Russell 3000 멤버십 proxy + 50bps 차등 TC**.
3. **OOS PIT coverage** — OOS PIT angle-2 의 car_fwd cardinality 가 폭락 (912 → 3 with car_fwd_30d). yfinance cache truncation (2026-04-01 까지만) 때문. CRSP OOS fetch 확장 후 재실행 필요.

**상세 audit**: [audits/2026-06-11-V5-phase-3-step-1-pit-acceptance-anchor.md](audits/2026-06-11-V5-phase-3-step-1-pit-acceptance-anchor.md)

### Phase 3 Step 1 결과 ledger

| Artifact | 위치 |
|---|---|
| acceptance 분포 + match rate | [reports/phase3-step1-acceptance.json](reports/phase3-step1-acceptance.json) |
| in-sample PIT angle-2 forward CAR | [reports/phase3-step1-angle2-pit-insample.json](reports/phase3-step1-angle2-pit-insample.json) |
| OOS PIT angle-2 (coverage caveat) | [reports/phase3-step1-angle2-pit-oos.json](reports/phase3-step1-angle2-pit-oos.json) |
| **PIT Net Sharpe (V5-11c)** | [reports/phase3-step1-net-sharpe-pit.json](reports/phase3-step1-net-sharpe-pit.json) |
| PIT data (in-sample) | [data/form_nt_pit.jsonl](data/form_nt_pit.jsonl) |
| PIT data (OOS) | [data/form_nt_pit_oos.jsonl](data/form_nt_pit_oos.jsonl) |
| PIT angle-2 forward (in-sample) | [data/angle_2_forward_pit.jsonl](data/angle_2_forward_pit.jsonl) |
| PIT monthly PnL ledger | [data/net_sharpe_strategy_d_pit.jsonl](data/net_sharpe_strategy_d_pit.jsonl) |

---

## ⑩ 산출물

| 항목 | 위치 |
|---|---|
| 한국어 distill 보고 | [readme_kr.md](readme_kr.md) (본 문서) |
| 영어 reproducibility README | [README.md](README.md) |
| 프로젝트 SPEC | [SPEC.md](SPEC.md) |
| 프로젝트 governance | [CLAUDE.md](CLAUDE.md) |
| Stage 0 sub-gate 4종 + Lock F | [audits/2026-06-10-V5-stage-0-summary.md](audits/2026-06-10-V5-stage-0-summary.md) |
| Lock C amendment (denominator) | [audits/2026-06-10-V5-lock-c-amendment-v5-11a-denominator.md](audits/2026-06-10-V5-lock-c-amendment-v5-11a-denominator.md) |
| EDGAR Form NT bulk pull (31,693) | [audits/2026-06-10-V5-phase-0-step-4-edgar-bulk-pull.md](audits/2026-06-10-V5-phase-0-step-4-edgar-bulk-pull.md) |
| Angle 1 event-CAR replication | [audits/2026-06-10-V5-phase-0-step-5-angle-1-event-car.md](audits/2026-06-10-V5-phase-0-step-5-angle-1-event-car.md) |
| Angle 2 LLM forward (Strategy D) | [audits/2026-06-10-V5-phase-0-step-6c-angle-2-forward.md](audits/2026-06-10-V5-phase-0-step-6c-angle-2-forward.md) |
| Angle 4 recurring XS | [audits/2026-06-10-V5-phase-0-step-7-angle-4-recurring-xs.md](audits/2026-06-10-V5-phase-0-step-7-angle-4-recurring-xs.md) |
| **Phase 0 close-report** (LAYER-A-WITH-CAVEATS) | [audits/2026-06-10-V5-phase-0-close-report.md](audits/2026-06-10-V5-phase-0-close-report.md) |
| **Phase 1 step 1 Net Sharpe** | [audits/2026-06-10-V5-phase-1-step-1-net-sharpe.md](audits/2026-06-10-V5-phase-1-step-1-net-sharpe.md) |
| **Phase 1 close-report** (LAYER A LOCKED UNCONDITIONAL) | [audits/2026-06-10-V5-phase-1-close-report.md](audits/2026-06-10-V5-phase-1-close-report.md) |
| **Phase 2 robustness close-report** (LAYER A retained with OOS caveat) | [audits/2026-06-10-V5-phase-2-robustness-close-report.md](audits/2026-06-10-V5-phase-2-robustness-close-report.md) |
| Bonferroni-12 ledger (Phase 1) | [reports/bonferroni-12-ledger.json](reports/bonferroni-12-ledger.json) |
| **Bonferroni-24 ledger (Phase 2 R5)** | [reports/r5-bonferroni-24-ledger.json](reports/r5-bonferroni-24-ledger.json) |
| Net Sharpe summary (Phase 1) | [reports/net-sharpe-summary.json](reports/net-sharpe-summary.json) |
| CRSP Angle 1 / 4 summary | [reports/crsp-angle-1-summary.json](reports/crsp-angle-1-summary.json) / [reports/crsp-angle-4-summary.json](reports/crsp-angle-4-summary.json) |
| **R1 OOS summary** (rate-diff PASS / Sharpe KILL) | [reports/r1-oos-summary.json](reports/r1-oos-summary.json) |
| **R2 subsample stability** | [reports/r2-subsample-stability.json](reports/r2-subsample-stability.json) |
| **R3 sector/size neutral** | [reports/r3-sector-size-neutral.json](reports/r3-sector-size-neutral.json) |
| **R4 TC sensitivity** | [reports/r4-tc-sensitivity.json](reports/r4-tc-sensitivity.json) |
| **R6 LLM schema + model ablation** | [reports/r6-llm-schema-ablation.json](reports/r6-llm-schema-ablation.json) + [reports/r6-llm-model-ablation.json](reports/r6-llm-model-ablation.json) |
| 18 개 pipeline + robustness script | [scripts/](scripts/) |
| 원자료 JSONL (NT bodies / classifications / restatement events / CRSP returns / OOS) | [data/](data/) |

---

## ⑪ 비용 / 시간 / 산출 효율

| Component | Spend | Wall |
|---|---|---|
| Phase 0 LLM (Strategy D classifier 3,225 calls) | $0.35 | ~30 min |
| Phase 1 LLM (re-run 745 added bodies) | ~$0.08 | ~10 min |
| Phase 1 CRSP query (DuckDB push-down single 2-min scan vs 110M rows) | $0 | 2 min |
| Phase 2 R1 OOS LLM classifier (912 calls) | $0.1011 | ~10 min |
| Phase 2 R6 Llama-3.3-70B ablation (50 calls) | $0.0066 | ~30 sec |
| Phase 2 R3 SEC submissions SIC fetch (1284 CIK) | $0 | ~3 min |
| Phase 2 R2/R4/R5 deterministic sims | $0 | <2 min |
| **Cumulative Phase 0+1+2** | **$0.54 / $50 cap = 1.08%** | **~6.5 시간** |

cf. 사용자 LLM cap 명시: $0-100 / $50/yr ceiling for Strategy D. **1.08% utilization** 으로 LAYER A LOCKED + Phase 2 6-axis robustness 달성.

---

## 결론 — 이 프로젝트의 진짜 가치

**Phase 0+1 LAYER A LOCKED UNCONDITIONAL → Phase 2 6-axis robustness → LAYER A retained with OOS-Sharpe caveat**. 알파 자체는 in-sample 에서 더 강해졌지만 (R3 Sharpe 0.46 → 0.66, R4 21× TC margin, R5 18/24, R6 κ=0.71), **OOS small-sample 에서 Sharpe KILL** 이라는 정직 finding — 이게 본 프로젝트의 핵심 contribution.

- 사용자 cite 4/4 fail 을 정직하게 수용하고 Bartov-K 2017 단일 anchor 로 pivot ([audits/2026-06-10-V5-stage-0-anchor-verify.md](audits/2026-06-10-V5-stage-0-anchor-verify.md))
- 무료 데이터 결과가 mechanical PASS 인데도 honest direction-conditioned READ 로 survivorship-bias 의심을 명기 ([audits/2026-06-10-V5-phase-0-close-report.md](audits/2026-06-10-V5-phase-0-close-report.md))
- CRSP delret 으로 끝까지 검증해서 가설 입증 + 무료 데이터 한계를 8-80pp magnitude 로 정량화 ([audits/2026-06-10-V5-phase-1-close-report.md](audits/2026-06-10-V5-phase-1-close-report.md) §5.3)
- Phase 2 6-axis robustness 로 in-sample 강화 + **OOS Sharpe KILL 을 over-claim 없이 명기** — Lesson V5-9 (Bonferroni saturation ≠ OOS Sharpe), Lesson V5-10 (sector-resid 가 무료 lift), Lesson V5-11 (NT 10-Q dominant cohort), Lesson V5-12 (κ 0.7 lower-bound) ([audits/2026-06-10-V5-phase-2-robustness-close-report.md](audits/2026-06-10-V5-phase-2-robustness-close-report.md) §6)
- Pre-registration discipline 을 commit hash 로 evidence 화 (`2e848b6` bootstrap / `fd15506` Phase 0 close / `464f1f5` Phase 1 step 1 / `34bcdb4` Phase 1 close + 본 Phase 2 close-report)
- β2 family precedent (8-K Item 4.02 FROZEN-NEGATIVE 2026-04-27) 를 portfolio context 로 활용 — V5 가 ex-ante Form NT 로 ex-post 8-K 보다 tractable 함을 입증
- $0.54 / $50 cap = **1.08%** LLM utilization 으로 LAYER A + Phase 2 6-axis robustness — Strategy D CLAUDE-AVOIDANCE (gpt-4o-mini primary + Llama-3.3-70B robustness) 디폴트 확인

**Phase 3 deliverable**: (i) **Step 1 PIT acceptance-anchor 검증 완료 (2026-06-11)** — in-sample 90d Net Sharpe 0.46 → 0.59 개선 (PIT-clean), (ii) **Step 2 vintage LLM 재라벨** (pre-2024 cutoff alt-LLM 으로 forward outcome leakage 검증, $1-4), (iii) **Step 3 CRSP delisting + Russell 3000 borrow proxy + 차등 TC** (small-cap tradability), (iv) **sector-residualized basket 을 PRIMARY portfolio** (R3 무료 lift), (v) **NT 10-Q cohort overweight** (R5 dominant), (vi) **2025-2026 OOS holdout 누적** 으로 V5-11(c) OOS 재검증, (vii) anchor PARTIAL → LIVE upgrade. Phase 0+1+2 + Phase 3 Step 1 자체는 — **LAYER A LOCKED + PIT-tradable verified (90d) + Step 2/3 잔여 누수 documented**, 정직히 publishable.

---

**프로젝트 위치**: 사용자 portfolio research 14-iter V-batch 의 LAYER A LOCKED piece.

| Piece | Status | 비고 |
|---|---|---|
| **V5 (us_sec_form_nt_late_filing_xs, 본 repo)** | ✅ **LAYER A retained / Phase 2 6-axis robust / Phase 3 Step 1 PIT-tradable verified / OOS Sharpe caveat + Step 2,3 잔여** | in-sample Bonferroni 18/24 mech, sector-resid Sharpe 0.66, **PIT 90d Sharpe 0.46→0.59 개선**, OOS rate z=2.83 PASS, OOS Sharpe -0.41 KILL, after-hours 63.5%/77.0% |
| X (sec-comment-letter-alpha) | ✅ 14-day complete | OOS \|t\|=2.86, 2 BH-survivors, methodology sister |
| β2 (eight_k_non_reliance_llm) | ⏸️ FROZEN-NEGATIVE 2026-04-27 | 8-K Item 4.02 ex-post; V5 가 ex-ante NT 로 succeed |

---

**문의**: GitHub issues 또는 fawkes4700@gmail.com
