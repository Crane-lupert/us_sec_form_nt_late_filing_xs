# us_sec_form_nt_late_filing_xs — V5

**ID**: V5 — SEC Form NT 10-K/10-Q late filing → NT body LLM-extracted restatement forward signal + recurring filer XS short
**Status**: Phase 3 Step 1 complete (2026-06-11) — Phase 0-2 LAYER A LOCKED retained with OOS-Sharpe caveat; Phase 3 Step 1 PIT acceptance-anchor verified (90d Net Sharpe 0.46 → 0.59); Steps 2 (vintage LLM relabel) + 3 (delisting/borrow proxy) open
**Anchor classification**: PARTIAL 3-4/6 via **Bartov, E. & Konchitchki, Y. (2017) "SEC Filings, Regulatory Deadlines, and Capital Market Consequences" *Accounting Horizons* 31(4):109-127 (SSRN 3065694)** PRIMARY (사용자 cite 4/4 fail post-pivot); 2,115 firms × 9yr; NT 10-Q CAR -2.93%, NT 10-K -1.96%, 사후 drift down
**Bayesian prior LAYER A LOCKED**: ~20-30% (PARTIAL anchor + LDS 5/7 + 사용자 cite 4/4 P8 fail correction)
**Phase 0 duration**: 10-14 days, $0-100 LLM (Strategy D NT body classification)
**Rule 9 verdict**: LAUNCH-with-tag BORDERLINE (P(HARD KILL fire) ~40-60%, WARNING)

## Source-of-truth pointers
- Pre-bootstrap review: `D:/vscode/meta-harness/audits/2026-06-10-V5-sec-form-nt-bootstrap-review.md`
- Autopilot prompt SoT: `D:/vscode/meta-harness/audits/2026-06-10-V5-autopilot-prompt.txt`
- Launch SPEC SoT: `D:/vscode/meta-harness/audits/2026-06-10-V5-launch-spec.md`
- **Phase 3 Step 1 PIT acceptance-anchor**: `audits/2026-06-11-V5-phase-3-step-1-pit-acceptance-anchor.md`

## CRITICAL — V5 Stage 0 sub-gate (사용자 명시 2026-06-10, 4종 의무)

1. **Anchor cite-table 정정** — 사용자 cite 3/4 fail (Files-Sharp-Thompson 2013 JAR MIS-CITED + Kinney-Burgstahler-Martin 2002 JAR SCOPE-MISMATCH + Hribar-Kravet-Wilson 2014 CAR MIS-CITED + Bartov-Coltman-Frey 2022 HALLUCINATED). Bartov-Konchitchki 2017 AH 단일 anchor pivot + 2018-2025 post-Bartov-K WebSearch expansion 의무
2. **β2 differentiation** — β2 us_eight_k_non_reliance_llm (FROZEN-NEGATIVE 2026-04-27) = 8-K Item 4.02 ex-post 정정; V5 = Form NT ex-ante 지연 narrative. Mechanism axis distinct (NT body LLM-extract vs β2 8-K text) — cohort overlap CIK × 분기 cross-tab ≥30% 시 STOP
3. **NT body LLM-extract cost preview** — 3000 filings/yr × $0.001 ≈ $3/yr LLM (Strategy D "accounting issue / unresolved" narrative classification). Dry-run $0.10 → $50/yr ceiling
4. **Angle 1 single-mode lock 차단** — angle 1 (NT event-CAR replication only) = MECHANICAL Bartov-K 2017 replication. Lock C 안 angle 2 (NT→restatement LLM forward) + angle 4 (recurring filer XS) 2-mode 필수

## Data source
- SEC EDGAR Form NT 10-K + NT 10-Q + 12b-25
- sec.gov/cgi-bin/browse-edgar full-text search + bulk
- ~3000 filings/yr, free 10 req/s, no auth

## Operational guardrails (P1 anti-pattern only)
### Strict 3 binary anti-pattern (KILL)
1. **Lock F US-data deterministic violation** → KILL
2. **Lock C pre-reg sign / Bonferroni-12 / angle-lock post-hoc change** → KILL
3. **Data-validity HARD KILL** (graduated 3-tier):
   - **V5-11(a)** Lock F clean + EDGAR Form NT bulk + NT-firm CIK matching ≥90% **against Bartov-K 2017 comparable cohort (US-major-exchange-listed)** → binary clean / fire. Free-tier proxy via SEC `company_tickers.json` measured 84.4% (1,784/2,115) on 2026-06-10 → **PASS-CONDITIONAL** pending CRSP-historical confirmation. See `audits/2026-06-10-V5-lock-c-amendment-v5-11a-denominator.md` for full canonical language.
   - **V5-11(b)** Bonferroni-12 cells ≥3/12 |t|>2.78 (3 angle [event-CAR / restatement-prob LLM / recurring filer XS] × 2 cohort × 2 forward): PASS ≥3 / BORDERLINE 2 / KILL ≤1
   - **V5-11(c)** Net Sharpe post-15bps ≥0.30: PASS / BORDERLINE 0.21-0.29 / KILL <0.21. **Phase 1 PASS 0.46 (90d) → Phase 3 Step 1 PIT-clean re-verification 0.59 (90d)**.
   - **V5-11(d)** Anchor faithfulness ≥PARTIAL via Bartov-K 2017 AH + Stage 0 2018+ verify
   - **V5-11(e)** **PIT-tradable anchor lock** (added 2026-06-11) — T=0 must use SEC EDGAR `acceptanceDateTime` (ET); after-hours (≥16:00 ET) reanchored to T+1. In-sample after-hours share 63.47%; V5-11(c) survives.

## 4-layer governance (mandatory)
### (a) WRDS access — local dump path only (Rule 6)
- `crsp_a_stock.dsf_v2` + `comp_na_daily_all.funda` (Compustat earnings forecast)
- SEC EDGAR = direct, WRDS 미경유
### (b) LLM call — portfolio-coordination only (Rule 6)
- $0-100 (Strategy D NT narrative classification optional)
### (c) External-API reachability (Rule 7)
- sec.gov public; Day-0 CDP corroboration 권고
### (d) As-of date semantics (Rule 8 vendored asof)
- NT filing_date → event window T+1; sort-stable on (CIK, filing_date)
- **PIT acceptance-anchor (Phase 3 Step 1, 2026-06-11)** — `anchor_date = acceptance_et_date + (1d if after_16et else 0d)`. EDGAR `date_filed` 단독 사용 금지 (intraday look-ahead). `data/form_nt_pit.jsonl` + `data/form_nt_pit_oos.jsonl` 가 canonical PIT join.

## Skills imported
@D:/vscode/meta-harness/skills/karpathy-guidelines/SKILL.md
@D:/vscode/meta-harness/skills/abandon-criteria/SKILL.md
@D:/vscode/meta-harness/skills/drift-watchdog/SKILL.md
@D:/vscode/meta-harness/skills/protected-long-task/SKILL.md
@D:/vscode/meta-harness/skills/inter-repo-autonomy/SKILL.md
@D:/vscode/meta-harness/skills/repo-autonomy-overnight/SKILL.md

## §0.4 Risks + Distinct value-add

### Distinct value-add (1/3 PASS)
- NT body LLM-extract "accounting issue/unresolved" → restatement forward signal — Bartov-K 2017 본문 outside scope
- Recurring NT filer (연 2회+) XS short — anchor-untouched layer
- Cohort 2,100+ distinct firms/9yr (W3 PASS)

### 4 critical risks
1. **사용자 cite 3/4 P8 FAIL** — single anchor Bartov-K 2017 의존; Stage 0 추가 anchor WebSearch 의무
2. **β2 FROZEN-NEGATIVE family precedent** — 8-K SEC EDGAR sister mechanism PASS / tradability FAIL pattern
3. **Axis 7 post-publication 7y Bartov-K decay** (LDS BORDERLINE)
4. **NT body LLM cost preview** Strategy D dependency

### Y1 anomaly framing (NOT applicable)
V5 = PARTIAL anchor + 사용자 origin (option A). Anchor-free 아님.

## Public push gate
- `gh push` / `git push` 금지

## Cross-reference
- `D:/vscode/meta-harness/CLAUDE.md` — governance hub
- `D:/vscode/meta-harness/docs/portfolio-research-rules.md` §1.5 + §1.5.11
- β2 sister: `D:/vscode/eight_k_non_reliance_llm/` FROZEN-NEGATIVE 2026-04-27 close-report

**End of CLAUDE.md (≤200 lines).**
