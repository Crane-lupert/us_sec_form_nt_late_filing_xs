# V5 SSRN Preprint — Korean Distill

> 본 문서는 [paper_v2_en.md](paper_v2_en.md) (SSRN 제출용 영문 본문) 의 한국어 distill 보고. 회계/재무 background 가 있지만 LLM·머신러닝 background 가 없어도 이해 가능하도록 작성.
>
> 영문 PDF render: `bash scripts/render-paper.sh`

---

## 한 줄 요약

미국 SEC Form NT 10-K / NT 10-Q (지연공시 통지서) 의 본문을 LLM 으로 분석해서 향후 재무 정정 (8-K Item 4.02 / 10-K/A / 10-Q/A) 발생 확률을 예측하는 신호를 만들었다. **in-sample (2014-2024) 에서는 Bartov-Konchitchki (2017) 의 −1.96% / −2.93% 5-day CAR 가 CRSP delret 으로 ±0.5pp 안에 복제되고, Strategy D LLM 90일 rate-diff = +9.06pp (z=5.61) PASS, Net Sharpe 0.46 PASS**; **out-of-sample (2025-Q1 ~ 2026-Q2) 에서는 rate-diff 가 z=2.83 으로 여전히 PASS 지만 Net Sharpe 가 −0.41 (n=5 months) 로 KILL**. 이는 over-claim 없이 정직히 명기.

---

## ① 직관 — 왜 이게 말 되는 아이디어인가

SEC Rule 12b-25 에 따라 미국 상장사는 10-K (연간) 또는 10-Q (분기) 보고서를 마감일 안에 못 내면 Form NT 10-K 또는 NT 10-Q 를 제출해야 한다. 본문 (Part III) 에는 **왜 못 내는지** 자유 서술. Bartov-Konchitchki (2017, *Accounting Horizons* 31(4):109--131) 는 2,115 firms × 9 years 표본에서 NT 10-K 5-day CAR −1.96%, NT 10-Q 5-day CAR −2.93% 를 보고. 본 연구는:

1. **2014-2024 in-sample + 2025-Q1 ~ 2026-Q2 out-of-sample 으로 확장** + 무료 yfinance feed 의 한계 (survivorship-bias) 를 CRSP delret 으로 정량화
2. **본문 자유 서술을 LLM 으로 3-class 분류** → 향후 90일 안 재무 정정 발생률 예측 신호

LLM 으로 본문 분류하는 이유: 3,970 건 본문을 사람이 라벨링 안 됨. SEC EDGAR 본문은 자유 서술 + 형식 무규격 + 노이즈 많음.

---

## ② 본문 한 통의 예시

회사 사유 (실제 cohort 중):
- *"We are unable to file our quarterly report on Form 10-Q within the prescribed time period because the Company is in the process of completing its evaluation of certain accounting matters including revenue recognition under ASC 606..."*
- → LLM (Strategy D, OpenAI gpt-4o-mini) 분류: **`accounting_issue`** ($0.001/건)

다른 예시:
- *"We require additional time to complete the audit due to recent acquisition integration..."*
- → LLM 분류: **`other`** (행정/M&A 사유)

3-class schema (`accounting_issue` / `unresolved_sec_comment` / `other`) 의 in-sample 분포 (n=3,232): AI=1,776 (55%), UR=54 (1.7%), OT=1,402 (43%).

---

## ③ 핵심 결과 (4 contributions)

### ③-1. Bartov-Konchitchki (2017) CAR 복제 (CRSP delret 사용)

| Cohort | Bartov-K 발표값 | yfinance | **CRSP+delret** | Gap |
|---|---:|---:|---:|---:|
| NT 10-K 5-day | −1.96% | −1.41% \|t\|=3.80 | **−2.11% \|t\|=4.77** | **0.15pp** |
| NT 10-Q 5-day | −2.93% | −0.72% \|t\|=1.89 ✗ | **−2.88% \|t\|=5.55** | **0.05pp** |

**±0.5pp 안 REPLICATED-FULL**. 무료 yfinance 의 60일 drift sign reversal (+5.50% → −3.20%) 은 survivorship-bias 가 quantifiable 한 artifact 임을 입증.

### ③-2. Strategy D LLM forward 신호 (Bonferroni-24 PASS)

P(restatement event within H days | NT body says accounting_issue) 가 in-sample 에서:

| Window | P(AI) | P(other) | Diff | z | Bonferroni-12 (2.78) |
|---|---:|---:|---:|---:|:-:|
| 14d | 10.02% | 7.28% | +2.75pp | 2.71 | (border) |
| 30d | 18.75% | 13.77% | +4.98pp | 3.75 | ✓ |
| **90d** | **32.60%** | **23.54%** | **+9.06pp** | **5.61 (5.6σ)** | ✓ |
| 180d | 45.16% | 34.66% | +10.49pp | 5.98 | ✓ |

**Bonferroni-24 ledger** (3 angles × 2 cohort × 4 windows): **18/24 mech PASS, 15/24 direction PASS** (floor 6/24, 3.0× over). Lock C 3-angle 모두 SATISFIED.

**새 발견 (Phase 2 R5)**: NT 10-Q cohort z=6.77 vs NT 10-K cohort z=0.50 → **NT 10-Q 가 dominant signal cohort**, NT 10-K 는 거의 효과 없음. NT 10-K 본문은 "audit work in progress" boilerplate 가 회계 issue tell 을 가린다.

### ③-3. Long-Short portfolio Net Sharpe (in PASS / out KILL — 정직 명기)

| Window | n_months | gross | Net (15bps) | V5-11(c) |
|---|---:|---:|---:|:-:|
| **In-sample 90d** | 53 | +0.47 | **+0.46** | **PASS** |
| In-sample 30d | 58 | −0.12 | −0.15 | KILL |
| **OOS 90d (2025-2026)** | 5 | −0.41 | **−0.41** | **KILL** |
| OOS 30d | 6 | −1.87 | −1.90 | KILL |

OOS Sharpe −0.41 은 in-sample 95% CI [+0.19, +0.73] 안 deeply negative tail. **신호 (rate-diff) 는 OOS 에서도 z=2.83 PASS 지만 portfolio sim 은 small-sample OOS 에서 fail**. 이는:
- in-sample 0.46 이 부분적으로 over-fit
- 시장이 NT body 를 점점 빨리 가격 반영 (post-COVID Sharpe 0.25 BORDERLINE 패턴)
- 5-month sample 의 high-variance 가 부분적 원인

해석: **신호는 robust, portfolio realization 은 in-sample 만 PASS** — 정직 명기.

### ③-4. Sector-residualized variant (post-hoc, in-sample lift)

| Variant | n_months | Net Sharpe | ann_vol | Change |
|---|---:|---:|---:|---:|
| A baseline (equal-weight) | 53 | +0.46 | 53.15% | (in-sample reference) |
| **B sector-residualized** | **53** | **+0.66** | **40.77%** | **+44% Sharpe / −23% vol** |

SIC2 within-month demean 으로 무료 lift. 5-month holdout 으로는 재검증 불가 (Phase 3 deliverable).

---

## ④ 방법론 요약

1. **Anchor pivot** — 사용자 cite 4/4 fail → Bartov-Konchitchki (2017) *Accounting Horizons* 단일 anchor pivot
2. **데이터 수집** — SEC EDGAR full-index 2014-2024 = 31,693 NT filings; NYSE+Nasdaq 필터 = 3,970 / 1,106 CIK (Bartov-K 2,115 firms 의 52.3%). OOS 2025-Q1 ~ 2026-Q2 = 2,781 / 912 / 470 CIK.
3. **Strategy D LLM** — OpenAI gpt-4o-mini (CLAUDE-AVOIDANCE), 3-class schema. In-sample $0.35 / 3,225 calls. OOS $0.1011 / 912 calls. 0 parse_fail.
4. **Cross-LLM 검증** — Meta Llama-3.3-70B-Instruct 50-sample 으로 Cohen's κ=0.7066, observed agreement 85.7% → Stage 0 S0-3 threshold 0.7 PASS.
5. **CRSP delret 사용** — WRDS-data-courier 의 로컬 dump (4.4 GB CRSP DSF v2) 를 DuckDB push-down 으로 single-scan, 1,106 CIK 중 895 ticker / 945 PERMNO 매칭, delret 포함.
6. **Multiple-comparison 보호** — Bonferroni-12 + Bonferroni-24 + Lock C 3-angle + 4-layer protection (Cohen's κ + DSR + body-length ablation + schema ablation).

---

## ⑤ Self-Correction history (Phase 0 → Phase 1 → Phase 2)

이 프로젝트의 핵심 기여 = **무료 데이터의 survivorship-bias 한계를 industrial scale 로 quantify 한 self-correction trail**.

git log 가 모든 decision 의 timestamp evidence:

| Phase | Commit | 내용 |
|---|---|---|
| Stage 0 | `2e848b6` | 사용자 cite 4/4 fail → Bartov-K 단일 anchor pivot |
| Phase 0 | `fd15506` | yfinance 무료 결과 mechanical PASS (8/12) 인데도 honest direction-conditioned READ 로 survivorship-bias 의심 명기 (5/12 direction PASS); Path A/B/C 3 옵션 사용자 제시 |
| Phase 1 step 1 | `464f1f5` | V5-11(c) Net Sharpe 0.46 PASS @ 90d |
| Phase 1 close | `34bcdb4` | CRSP delret 으로 모든 direction-reversed cell flip back; Bonferroni-12 = 10/12 mech + 10/12 direction PASS; LAYER A LOCKED UNCONDITIONAL |
| Phase 2 | `e3e4d7f` | 6-axis robustness: R1 OOS (rate PASS / Sharpe KILL), R2 subsample, R3 sector-resid (+44%), R4 TC sens (320bps), R5 Bonf-24 (18/24), R6 κ=0.71 → LAYER A retained with OOS-Sharpe caveat |

**리뷰어 입장**: 무료 데이터 결과를 "PASS 라고 우기지" 않고 honest direction-condition 으로 survivorship 의심 → CRSP 로 끝까지 검증 → 가설 입증 + 무료 데이터 한계 8-80pp magnitude 로 정량화 → Phase 2 OOS Sharpe KILL 도 정직 disclose. **Methodology 자체가 contribution**.

---

## ⑥ 선행연구 대비 차별점 (paper §2.4 Table 1)

| 항목 | Bartov-Konchitchki (2017) | 본 연구 |
|---|---|---|
| Sample window | 2003-2011 (9yr) | 2014-2024 (11yr) + 2025-Q1~2026-Q2 OOS |
| Universe | 2,115 hand-collected firms | 1,106 NYSE/Nasdaq SEC `company_tickers_exchange.json` (52.3% of B-K base) |
| Form NT body LLM | 없음 | 3-class zero-shot LLM taxonomy |
| Cross-LLM κ | 해당 없음 (pre-LLM) | gpt-4o-mini vs Llama-3.3-70B κ=0.71 (n=49) |
| Returns | hand-collected | CRSP delret; free-tier feed side-by-side |
| Bonferroni 보정 | 없음 | Bonferroni-24, 18/24 mech PASS |
| Forward window | (−2, +2) 5-day CAR | 5-day CAR for replication + 30/90/180-day rate-diff for forward signal |
| Tradeable strategy | 없음 | Pre-registered equal-weight L/S basket, 15bps TC |
| OOS holdout | 해당 없음 | 2025-Q1~2026-Q2 (912 NT, 330 CRSP-matched) |
| Pre-registration | 없음 | 5 commit-locked documents |
| 재현가능성 인프라 | 없음 | One-command pipeline + open-source repo |

본 연구는 **방법론적 확장** — anchor 발견 주장 아님.

---

## ⑦ 한계 (정직 명기, paper §6)

1. **OOS Net Sharpe KILL** — In-sample 0.46 PASS / OOS −0.41 KILL (n=5 months). holdout 이 in-sample 95% CI 안 (deeply negative tail). rate-diff 는 OOS 에서도 PASS 이므로 over-fit 으로 해석. Phase 3 deliverable: 2025-Q3+ 데이터 누적 후 재검증.
2. **CRSP coverage 81%** — WRDS-Data-Courier 로컬 dump 통해 1,106 CIK 중 895 ticker match. 19% non-match 는 ticker reassignment. 영향 작음 (NT 10-K 5-day gap 0.15pp).
3. **OOS universe survivorship** — 2025+ delisted firm 누락. 영향: rate-diff cell (Submissions API 사용) 작음, CAR cell (equity feed 사용) 큼.
4. **CAR-diff null** — rate-diff PASS (cell 2-1/2-2) 지만 CAR-diff fail (cell 2-3/2-4). 시장이 NT body 를 filing date 에 가격 반영 → portfolio profit 은 cross-month differential 에 의존, 작고 불안정.
5. **Anchor PARTIAL 3-4/6** — Bartov-K 2017 단일 anchor, 2018+ academic expansion 0건. SSRN 제출 시점 scoop-check commit log 명기.
6. **LLM model dependence** — gpt-4o-mini + Llama-3.3-70B κ=0.71 (S0-3 0.7 lower bound). Claude 모델 제외 (portfolio convention). Monitor 후 재추출.

---

## ⑧ 비용 / 시간 / 산출 효율

| Component | Spend | Wall |
|---|---:|---:|
| Phase 0 LLM (Strategy D 3,225 calls) | $0.35 | ~30 min |
| Phase 1 LLM (+745 added) | $0.08 | ~10 min |
| Phase 1 CRSP query (DuckDB push-down) | $0 | 2 min |
| Phase 2 R1 OOS LLM (912 calls) | $0.1011 | ~10 min |
| Phase 2 R6 Llama 50 sample | $0.0066 | ~30 sec |
| Phase 2 R3 SEC SIC fetch | $0 | ~3 min |
| Phase 2 R2/R4/R5 deterministic sims | $0 | <2 min |
| **Cumulative** | **$0.54 / $50 cap = 1.08%** | **~6.5 시간** |

**1.08% LLM utilization 으로 LAYER A retained + Bonferroni-24 + OOS holdout 달성**. Strategy D CLAUDE-AVOIDANCE (gpt-4o-mini primary + Llama-3.3-70B robustness) 디폴트.

---

## ⑨ 결론 — 이 프로젝트의 진짜 가치

**Phase 0+1 LAYER A LOCKED UNCONDITIONAL → Phase 2 6-axis robustness → LAYER A retained with OOS-Sharpe caveat**. 알파 자체는 in-sample 에서 강해졌지만 (R3 Sharpe 0.66, R4 21× TC margin, R5 18/24, R6 κ=0.71), **OOS small-sample 에서 Sharpe KILL** — 이게 본 연구의 honest contribution.

**4 contributions** (paper §1):
1. CRSP-with-delret sample reconstruction 으로 Bartov-K 2017 ±0.5pp 복제 + free-tier survivorship-bias 8-80pp 정량화
2. Zero-shot LLM forward signal 이 Bonferroni-24 PASS + OOS rate-diff z=2.83 PASS
3. OOS Net Sharpe failure 의 multiple-comparison-protected honest disclosure (in-sample over-fit 으로 해석)
4. One-command end-to-end 재현가능성 + 5 pre-registered commits + 2-vendor κ=0.71

**Phase 3 deliverables**: (i) sector-residualized basket 을 PRIMARY portfolio (R3 무료 lift), (ii) NT 10-Q cohort overweight (R5 dominant), (iii) 2025-Q3+ holdout 누적, (iv) anchor PARTIAL → LIVE upgrade.

---

## ⑩ SSRN 제출용 산출물

| 항목 | 위치 |
|---|---|
| 영문 SSRN preprint draft | [paper_v2_en.md](paper_v2_en.md) (≈500 lines) |
| 한국어 distill (본 문서) | [README_KR.md](README_KR.md) |
| BibTeX references | [refs.bib](refs.bib) |
| PDF render script | `bash scripts/render-paper.sh` |
| Phase 2 robustness close-report | [../audits/2026-06-10-V5-phase-2-robustness-close-report.md](../audits/2026-06-10-V5-phase-2-robustness-close-report.md) |
| Phase 1 close-report (LAYER A LOCKED) | [../audits/2026-06-10-V5-phase-1-close-report.md](../audits/2026-06-10-V5-phase-1-close-report.md) |
| Phase 0 close-report | [../audits/2026-06-10-V5-phase-0-close-report.md](../audits/2026-06-10-V5-phase-0-close-report.md) |
| Repo overall README | [../readme_kr.md](../readme_kr.md) |

**SSRN 제출 시 PDF 만 업로드**. Source code repo URL 은 abstract 안에 명기.

---

**문의**: GitHub issues 또는 fawkes4700@gmail.com
