# us_sec_form_nt_late_filing_xs (V5)

SEC Form NT 10-K/10-Q late filing → NT body LLM-extracted restatement forward signal + recurring filer XS short.

## Status
Phase 0 entry — bootstrapped 2026-06-10. Phase 1 LAYER A LOCKED. Phase 2 6-axis robustness retained with OOS-Sharpe caveat. **Phase 3 Steps 1+2+3 closed 2026-06-11** — (1) PIT acceptance-anchor verified, in-sample after-hours filing share 63.5% (OOS 77.0%), 90d **per-position Sharpe 0.46 → 0.59** under acceptance_et + T+1 reanchor; (2) vintage LLM relabel gpt-4o-mini vs gpt-3.5-turbo (2023-Q3 cutoff) κ=0.6154 sub-0.70 floor, classifier-quality vs vintage-leakage 가설 분리 불가 (larger n≥200 deferred); (3) sub-$5 borrow-restricted Sharpe −0.65 ~ −0.81 (recurring NT 10-Q sub-cohort median closing price $3.04, sub-$5 share 62%), deployment-relevant downward revision from 0.59 headline. OOS CRSP-extended PIT 14d z=2.87 / 90d z=2.71 family-wise PASS. **Sanity-check battery 2026-06-13** (audit `2026-06-13-V5-sanity-check-battery.md`) — per-position Sharpe 0.59 ↔ **per-capital Sharpe ≈ 0.29** (4.3 overlapping 90d positions, independence approximation; honest range 0.29 ≤ SR_cap ≤ 0.59); FF5+UMD per-position α=+31.5%/yr (t=2.14) ↔ per-capital α ≈ +15%/yr; **tail-dependence sweep** (winsor 0.5/99.5→0.54, 1/99 base→0.59, 2/98→0.57, trunc ±100→−0.33, trunc ±50→−0.04, no winsor→0.23) → strategy 는 tail bet; **selection-bias differential** (dropped 1,252 of 3,959 의 AI share 61.3% vs in-basket 52.3%, −8.9pp one-sided toward less-distressed cohort); **spanning regression** body-narrative L/S ~ recurring L/S α=7.71pp/mo (t=1.40 borderline, R²=0.4%); **contamination audit** 20/20 REDACT_* agreement; **DSR** 0.99 (n_trials=8) → 0.90 (n_trials=128). SSRN preprint v2 draft (`analysis/paper_v2_en.pdf`) committed and revised post-sanity per-position/per-capital propagation; `origin/main` public-pushed. iter 14 V-batch. Rule 9 LAUNCH-with-tag BORDERLINE P(fail) 40-60%, LDS LIVE-DEPLOYABLE 5/7.

## Quick links
- SoT: `D:/vscode/meta-harness/audits/2026-06-10-V5-*.md`
- Spec: SPEC.md / CLAUDE.md

## Anchor (pivot — 사용자 cite 4/4 fail)
- **Primary**: Bartov-Konchitchki 2017 *Accounting Horizons* 31(4):109-127 (SSRN 3065694) — 2,115 firms × 9yr, NT 10-Q CAR -2.93%

## Stage 0 sub-gate (4종)
1. Anchor cite-table 정정 + 2018-2025 post-Bartov-K verify
2. β2 differentiation (8-K Item 4.02 vs Form NT delay narrative, CIK × 분기 cross-tab ≥30% STOP)
3. NT body LLM-extract cost preview ($50/yr ceiling)
4. Angle 1 single-mode lock 차단 (angle 2 + 4 cross-check 의무)

## Cohort
2,100+ distinct firms / 9yr ✓ W3 PASS.
