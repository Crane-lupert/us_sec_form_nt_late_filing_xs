# SSRN Preprint — 한국어 distill

> 본 문서는 [paper_v2_en.md](paper_v2_en.md) (SSRN 제출용 영문 본문, [paper_v2_en.pdf](paper_v2_en.pdf) 로 렌더링) 의 한국어 distill 보고. 회계/재무 background 가 있고 머신러닝 background 가 없어도 이해 가능하도록 작성.
>
> 영문 PDF render: `bash scripts/render-paper.sh en`

---

## 한 줄 요약

미국 SEC Form NT 10-K / NT 10-Q (지연공시 통지서) 의 본문을 zero-shot 언어모델로 분류해서 향후 90일 안 재무 정정 (8-K Item 4.02, 10-K/A, 10-Q/A) 발생 확률을 예측하는 신호를 만들었다. **in-sample (2014--2024)** 에서 Bartov-Konchitchki (2017) 의 NT 10-K $-1.96\%$ / NT 10-Q $-2.93\%$ 5-day CAR 가 CRSP delret 으로 **각각 $0.15 / 0.05$ percentage point 안에 복제**되고, body-narrative LLM forward 신호의 90일 rate-diff $= +9.06 \text{ pp} (z = 5.61)$ PASS, **PIT acceptance-tradable anchor 하 long-short basket net Sharpe $= 0.59$** (calendar-day anchor 0.46 대비 개선) 가 측정된다. **out-of-sample (2025-Q1 \~ 2026-Q2)** 에서 forward 신호 90일 rate-diff $= +8.35 \text{ pp} (z = 2.83)$ 으로 여전히 PASS, 단 basket 의 monthly usable period 가 $n = 5$ 에 불과해 sharpe 재검증은 보류. 

---

## ① 동기 — Form NT 본문에 무슨 신호가 있나

SEC Rule 12b-25 에 의해 미국 상장사가 10-K (연간) 또는 10-Q (분기) 보고서를 마감일 안에 못 내면 Form NT 10-K 또는 NT 10-Q 를 제출해야 한다. 본문 (Part III of Form 12b-25) 에는 **왜 못 내는지** 자유 서술로 적혀 있다. Bartov-Konchitchki (2017, *Accounting Horizons* 31(4):109--131) 는 2003--2011 표본 (2,115 firms) 에서 NT 10-K 5-day CAR $-1.96\%$, NT 10-Q 5-day CAR $-2.93\%$ 를 보고하면서 본문에 적힌 사유가 회계 이슈일 때 reaction 이 가장 크다고 정성적으로 언급. 본 연구는 이 정성 관찰을 (a) 새로운 11년 표본에 (b) 자동화된 본문 분류로 (c) multiple-comparison 보호를 끼고 quantify 한다.

본문 예시 (실제 cohort 중):
- *"We are unable to file our quarterly report on Form 10-Q within the prescribed time period because the Company is in the process of completing its evaluation of certain accounting matters including revenue recognition under ASC 606..."* → `accounting-issue`
- *"We require additional time to complete the audit due to recent acquisition integration..."* → `other`

3-class schema (`accounting-issue` / `unresolved SEC comment` / `other`). In-sample 분포 ($n = 3{,}232$): AI = 1,776 (55%), unresolved = 54 (1.7%), other = 1,402 (43%).

---

## ② 4 기여 (paper §1)

### 기여 1: CRSP delret 으로 Bartov-Konchitchki 짧은창 CAR 복제 (figure 2)

무료 yfinance feed (current ticker key) 는 delisting firm 을 누락 → forward window 의 worst-case ($-100\%$ delisting) 가 sample 에서 빠짐 → short-window CAR magnitude 가 under-recovered, post-NT 60일 drift 의 sign 이 reversed.

| Cohort | Bartov-K 발표값 | yfinance | **CRSP+delret** | Gap |
|---|---:|---:|---:|---:|
| NT 10-K 5-day CAR | $-1.96\%$ | $-1.41\%$ ($|t|=3.80$) | **$-2.11\%$** ($|t|=4.77$) | **0.15 pp** |
| NT 10-Q 5-day CAR | $-2.93\%$ | $-0.72\%$ ($|t|=1.89$) | **$-2.88\%$** ($|t|=5.55$) | **0.05 pp** |
| NT 10-Q 60-day drift | (down) | $+5.50\%$ (반대 부호) | **$-3.20\%$** ($|t|=2.46$) | direction 복구 |

free-tier feed 의 implied delisted-firm forward return 은 약 $-50\%$ to $-100\%$, Shumway (1997) 의 delisting-return 문헌과 일치. methodology contribution 으로 별도 보고.

### 기여 2: Body-narrative forward 신호 (figure 3)

P(restatement-class event within $H$ days | NT body says accounting-issue) 가 in-sample 에서:

| Window | P(AI) | P(other) | Diff | $z$ | family-wise critical 2.78 |
|---|---:|---:|---:|---:|:-:|
| 14d | 10.02% | 7.28% | $+2.75$ pp | 2.71 | (border) |
| 30d | 18.75% | 13.77% | $+4.98$ pp | 3.75 | ✓ |
| **90d** | **32.60%** | **23.54%** | **$+9.06$ pp** | **5.61** | ✓ |
| 180d | 45.16% | 34.66% | $+10.49$ pp | 5.98 | ✓ |

OOS 2025-Q1 \~ 2026-Q2 ($n = 912$ filings) 에서 90일 rate-diff $= +8.35$ pp, $z = 2.83$ → in-sample magnitude 의 약 절반이지만 여전히 family-wise critical 통과.

24-cell expansion (event-window length × cohort split × forward window 의 grid) 에서 **18/24 mech PASS, 15/24 direction PASS** (figure 4). cohort-split 분석: NT 10-Q cohort 90일 rate-diff $z = 6.77$ vs NT 10-K cohort $z = 0.50$ → **NT 10-Q 가 dominant signal cohort**. 분기 본문이 회계 issue 의 tell 을 더 구체적으로 노출.

### 기여 3: Long-short basket with acceptance-tradable anchor (figure 1)

In-sample NT filings 의 **$63.5\%$ 가 16:00 ET 이후 SEC 에 accept** 됨. calendar filing-date close 에 진입한다는 가정은 그 filings 에 대해 intraday look-ahead 가짐. **PIT acceptance-tradable anchor** (16:00 이후 acceptance 면 다음 trading day 진입; 그 외 calendar day 유지) 적용 시:

| Entry anchor | Months | Ann. mean | Ann. vol | Net Sharpe |
|---|---:|---:|---:|---:|
| Calendar filing date | 53 | 24.49% | 53.15% | $0.46$ |
| **Acceptance-tradable** (T+1 after-hours) | 58 | 25.81% | 43.69% | **$0.59$** |

calendar anchor 가 filing-day intraday price impact (이미 가격에 반영된 부분) 을 일부 흡수하던 게 stripped → cleaner forward window → Sharpe 개선. 15bp round-trip 후 net Sharpe $0.59$, break-even 320bp (현실 비용의 약 21배 안전마진).

cumulative excess return (figure 1) 은 58개 monthly entry 의 90-day excess return 누적합. terminal $\approx +540$ percentage points. compound-growth interpretation 은 overlap distortion 회피 위해 의도적으로 suppress.

**Factor-adjusted performance** (paper §5.7, FF5+UMD regression, Newey-West HAC lag=6):
- Annualized residual α = **+31.47%/yr** (HAC SE 14.74%, **t = 2.14**) → 5% 유의수준 PASS
- Factor loadings (none individually significant at conventional t): β_Mkt-RF = −1.68, β_SMB = +1.77 (small-cap), β_RMW = +1.61 (quality), β_MOM = −1.07 (contrarian)
- R² = 9.4% → 6-factor model 이 strategy variation 의 9% 만 설명. 나머지는 alpha.
- Factor loading direction 이 §7 Discussion limits-of-arbitrage reading 과 일치 (small-cap quality-of-disclosure cohort 의 contrarian signal).

OOS holdout 의 $n = 5$ monthly periods 는 sharpe 재검증에 부족 ($n = 5$ 에서 net Sharpe $-0.41$ 이지만 in-sample 95% CI $[0.19, 0.73]$ 의 deeply negative tail). signal 자체는 OOS 에서 유지되므로 small-sample 문제로 해석.

### 기여 4: 재현가능성

`bash scripts/render-paper.sh en` 으로 paper PDF, `python scripts/make-paper-figures.py` 로 4 figures. raw 부터 알파까지 단일 entry-point pipeline (appendix B). Two-vendor cross-check on $n = 49$ stratified random sample yields Cohen's $\kappa = 0.7066$ at observed agreement $85.7\%$ → 3-class schema 보존.

---

## ③ 한계 (paper §6)

1. **OOS basket sharpe 미확정**: holdout 의 90일 horizon 에 usable monthly periods $n = 5$ → basket sim 재검증 불가. signal (rate-diff) 은 OOS 에서 유지되므로 small-sample issue 가 basket aggregation 단계에 한정.
2. **CRSP join coverage $81\%$**: ticker reassignment 로 인한 19% 미매치. short-window CAR magnitude 영향은 작음 ($0.15$ pp gap 으로 입증).
3. **LLM vintage look-ahead** 정량화 (paper §6): gpt-3.5-turbo (training cutoff 2023-Q3) 으로 같은 $n=50$ stratified sample re-classify → 3-class $\kappa = 0.6154$ (sub-0.70 floor). gpt-3.5-turbo 는 accounting-issue label 에 약 10pp 더 conservative. 두 가설 분리 불가 — (a) classifier-quality (earlier model 이 weaker zero-shot reader) vs (b) vintage-leakage (2024 vintage 가 implicit forward outcome 학습). OOS 2025-Q1\~2026-Q2 $z = 2.83$ (production extractor) 이 leakage magnitude 의 upper bound 를 제공하지만 zero 는 아님. larger $n \geq 200$ stratified cross-check 권장 (deferred).
4. **CAR-diff null, rate-diff PASS**: 시장이 본문을 filing date 에 가격 반영 → conditional CAR 은 null, conditional rate (subsequent restatement disclosure) 만 economic distinct prediction.
5. **NT 10-Q dominant**: NT 10-K cohort 의 신호는 $z = 0.50$ 로 null. deployment 시 NT 10-K subset 제외 가능.
6. **Recurring filer 의 borrow cost 정량화 (paper §6)**: recurring NT 10-Q sub-cohort (dominant body-narrative-signal cohort) 의 anchor-date closing price median **$3.04**, sub-$5 share **62%**. CRSP-matched partial sample ($n = 1{,}356$ of $3{,}232$ angle-2 rows) 위에서 borrow-restricted filter (drop short leg with anchor-date close $<5\$$) × {15, 25, 50, 100, 200} bp round-trip cost schedule → net Sharpe **$-0.65$ ~ $-0.81$** range. 즉 full-sample $0.59$ headline 의 deployment-relevant downward revision. unconstrained-borrow-naive deployment 는 infeasible. borrow-availability sourcing (e.g., S3 Partners locate API) 후 large-cap-only subset 으로 capacity 재산정 필요.

---

## ④ 산출물

| 항목 | 위치 |
|---|---|
| 영문 SSRN preprint | [paper_v2_en.pdf](paper_v2_en.pdf) (21 페이지) |
| 영문 source | [paper_v2_en.md](paper_v2_en.md) |
| BibTeX references | [refs.bib](refs.bib) |
| 4 figures (PNG) | [figures/](figures/) |
| Render script | `bash scripts/render-paper.sh [en|kr]` |
| 한국어 distill (본 문서) | [README_KR.md](README_KR.md) |

---

## ⑤ 데이터 핵심 숫자 요약

| 항목 | 값 |
|---|---|
| Annualized FF5+UMD residual α | **+31.47%/yr** (HAC SE 14.74%, t = 2.14) |
| FF5+UMD R² | 9.4% |
| Strategy 90d L/S terminal (cumulative additive) | ~+540 pp |
| In-paper alternative (recurring-filer L/S) terminal | ~+277 pp |
| In-sample window | 2014-01-01 \~ 2024-12-31 |
| OOS window | 2025-01-01 \~ 2026-06-30 |
| Form NT filings (in-sample) | 31,693 |
| NYSE/Nasdaq matched | 3,970 (Bartov-Konchitchki cohort 의 52%) |
| Body-narrative classified | 3,232 |
| CRSP returns matched (CIK level) | 895 / 1,106 = 81% |
| OOS Form NT filings | 2,781 |
| OOS NYSE/Nasdaq matched | 912 |
| OOS classified | 912 (100% success) |
| LLM cost (in-sample + OOS) | $0.45 USD |
| Inter-LLM Cohen's $\kappa$ — gpt-4o-mini vs Llama-3.3-70B ($n = 49$) | 0.7066 |
| Inter-LLM Cohen's $\kappa$ — gpt-4o-mini vs gpt-3.5-turbo (vintage, $n = 50$) | 0.6154 (sub-floor) |
| In-sample net Sharpe (90d, PIT anchor) | $+0.59$ |
| In-sample net Sharpe (90d, calendar anchor) | $+0.46$ |
| Sub-$5 borrow-restricted net Sharpe (90d, full TC schedule) | $-0.65$ ~ $-0.81$ |
| OOS PIT CRSP-extended rate-diff 14d $z$ / 90d $z$ | 2.87 / 2.71 |
| OOS basket net Sharpe (90d, $n_{\text{months}} = 5$) | $-0.35$ (CRSP) / $-0.41$ (yfinance) |
| Break-even round-trip cost (at PASS 0.30, full sample) | 320 bp |
| Bonferroni-24 PASS count (mechanical) | 18 / 24 |
| Bonferroni-24 PASS count (direction-conditioned) | 15 / 24 |

---

**문의**: GitHub issues 또는 fawkes4700@gmail.com
