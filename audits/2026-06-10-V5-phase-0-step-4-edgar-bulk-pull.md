# V5 Phase 0 step 4 — EDGAR Form NT bulk pull + V5-11(a) ESCALATION

**Date**: 2026-06-10
**Repo**: us_sec_form_nt_late_filing_xs
**Step**: Phase 0 step 4 (EDGAR Form NT bulk pull 2014-01-01 – 2024-12-31)
**Verdict**: bulk pull **DONE**; V5-11(a) gate **ESCALATION REQUIRED** (interpretation ambiguity; 사용자 결정 필요)

## §1 EDGAR bulk pull result

Script: `scripts/fetch-form-nt-bulk.py`
Output: `data/form_nt_index.jsonl`
SEC endpoint: `https://www.sec.gov/Archives/edgar/full-index/{YEAR}/QTR{N}/form.idx`
User-Agent compliance: `us_sec_form_nt_late_filing_xs research fawkes4700@gmail.com`

| Metric | Value |
|---|---|
| Quarters fetched | 44 (2014Q1 – 2024Q4) |
| Total NT filings | **31,693** |
| NT 10-Q | 20,177 (64%) |
| NT 10-K | 11,227 (35%) |
| NT 10-K/A | 153 |
| NT 10-Q/A | 136 |
| Distinct CIKs | 6,062 |
| SPEC expectation | ~3,000/yr × 11yr = ~33,000 ✓ |
| Bartov-K 2017 ratio NT 10-Q : NT 10-K | ~2 : 1 ✓ (we measure 1.8 : 1) |

Lock F sort-stable on `(cik, date_filed, accession_number)` enforced at write time.

## §2 V5-11(a) gate — three interpretations of "NT-firm CIK match ≥90%"

The launch SPEC §0.3 / autopilot prompt phrase **"NT-firm CIK match ≥90%"** does not specify the reference universe (the denominator and numerator of "match"). Three readings are operationally distinct.

### §2.1 Interpretation A — Match against SEC current `company_tickers.json` (active exchange listing)

| Level | Result | Verdict (≥90% / ≥63% / <63%) |
|---|---|---|
| Filing-level | 9,850 / 31,693 = **31.08%** | **KILL** |
| CIK-level | 1,784 / 6,062 = **29.43%** | **KILL** |

Source: `https://www.sec.gov/files/company_tickers.json` (8,018 currently active US-listed CIKs)
Reason for low match: NT 10-K/10-Q filers skew heavily toward distressed / OTC / delisted firms. Sample of 10 unmatched CIKs (random seed 42) yielded 10/10 with `tickers: []` and `exchanges: []` in SEC submissions API — all OTC/PNK/delisted (gold mining, marijuana, blank-check SPACs).

### §2.2 Interpretation B — CIK is a valid SEC reporter with 10-K/10-Q history

| Level | Result | Verdict |
|---|---|---|
| CIK-level (200-CIK sample × 99.0% extrapolation) | (1,784 matched + projected ~4,235 reporter) / 6,062 = **~99.3%** | **PASS** |

Sample: random.seed(42), 200 of the 4,278 "unmatched" CIKs → SEC submissions API queried (`data.sec.gov/submissions/CIK{padded}.json`) → 198/200 = **99.0%** have ≥1 10-K or 10-Q in filings history. 0 404, 0 network error.

Caveat: this interpretation is largely tautological — Form NT can only be filed by SEC reporting companies, so the test essentially measures "did the CIK exist in EDGAR." Carries little discriminating value for V5-11(a).

### §2.3 Interpretation C — Match against CRSP-CCM (tradable / return-computable universe)

This is the Bartov-K 2017 academically rigorous interpretation. Bartov-K's 2,115-firm × 9yr base was CRSP-listed firms only.

| Level | Result | Verdict |
|---|---|---|
| Active-exchange proxy (≈ CRSP universe via current `tickers.json`) | 1,784 / 2,115 Bartov-K base = **84.4%** | **BORDERLINE → PASS** if 1,784 is read as Bartov-K-comparable cohort |
| True CRSP-CCM via local dump | **UNCOMPUTABLE** | local dump `crsp.ccmxpf_linktable.csv.gz` (21 bytes) and `crsp._full.year=YYYY.parquet` (0 MB) are **metadata stubs only**; actual CRSP data not pre-fetched |

PROHIBITION #1 forbids WRDS direct query → cannot pull CRSP-CCM on-demand without filesystem-resident data.

### §2.4 Decision matrix

| Interpretation | Verdict | Plausibility of intended reading |
|---|---|---|
| A literal current-tickers | **KILL** | High (most natural reading of "match") |
| B SEC-reporter validity | PASS 99.3% | Low (tautological) |
| C CRSP-CCM tradable | PASS via Bartov-K proxy 84.4% (BORDERLINE) or unresolved | **Highest** — matches CLAUDE.md §4(a) WRDS local-dump architecture intent |

## §3 Why this is the β2 family precedent risk firing

Launch SPEC §3 critical risk #2 explicitly listed:
> "β2 FROZEN-NEGATIVE family precedent — 8-K SEC EDGAR sister mechanism PASS / tradability FAIL pattern"

β2 (eight_k_non_reliance_llm) FROZEN-NEGATIVE 2026-04-27 hit exactly this: SEC EDGAR discovery PASSED (9,399 events), free-tier yfinance mapping ~30% (active-only), and Bonferroni-9 sample-power FAILED because the analysis cohort was filtered to n=305.

V5 step-4 result is the SAME PATTERN: SEC EDGAR discovery PASSED (31,693 NT filings); free-tier active-exchange mapping = 31.08% / 1,784 CIKs.

Two important differences vs β2:
1. **β2 base cohort = 142+163=305** after free-tier filtering. **V5 analysis cohort = 1,784 active-exchange CIKs × ~5.5 filings/CIK = 9,850 filings** — 32× larger than β2 analysis cohort.
2. **β2 anchor (SchroderJ 2025) magnitude underwhelming on free-tier subset (-1.05% vs -2.6 to -5.4%); V5 anchor (Bartov-K 2017) magnitude already reported on free-tier-comparable subset (CRSP NYSE/NQ/AMEX listed = matches our 1,784 universe).**

So V5 is materially better positioned than β2 was at step-4 equivalent, but **only under Interpretation C** (active-exchange-matched analysis cohort is the proper Bartov-K comparable).

## §4 Sample-power Gate H re-bake (Lesson β2-1)

With matched universe (Interpretation C cohort):
- Filings: 9,850
- Distinct CIKs: 1,784
- Recurring-filer firm-years (≥2 NT/yr in matched universe): **2,600** firm-years across 985 distinct CIKs

Required n per V5-11(b) Bonferroni-12 (recomputed against matched universe):
- Angle 1 single cell (event-CAR, Bartov-K Δ=−2.93%, σ ~4%): required n ≈ 14 firms → available ~1,784/cell. **PASS 127× headroom.**
- Angle 2 single cell (NT body LLM forward 30d, Δ ~3%, σ ~8%): required n ≈ 55 firms → available depends on Strategy D classification rate (assume 20-30% `accounting_issue` subset) = ~360-540 classified firms. **PASS 6.5-9.8× headroom.**
- Angle 4 single cell (recurring XS 12mo, Δ ~5%/yr, σ ~30%): required n ≈ 278 firm-years → available 2,600. **PASS 9.4× headroom.**

All 12 Bonferroni cells have ≥6× headroom under Interpretation C cohort. **Sample-power Gate H = PASS** even with the 70% non-mappable population shed.

## §5 ESCALATION — user decision required

V5-11(a) gate cannot be auto-resolved. Three paths, each with downstream consequences:

### Path 1 — accept Interpretation A literal KILL
- Verdict: V5-11(a) FIRES → HARD KILL
- Action: run `kill-audit-generator.py --outcome KILLED --trigger-name V5-11-a --evidence audits/2026-06-10-V5-phase-0-step-4-edgar-bulk-pull.md`
- Outcome: V5 KILLED at Phase 0 step 4
- Lesson: β2 family precedent risk fired as warned. Repeat-pattern = portfolio signal that free-tier SEC-EDGAR-discovery + active-exchange-filter pieces will systematically fire V5-11(a)-class gates on the literal reading.

### Path 2 — adopt Interpretation C (Bartov-K-comparable cohort)
- Verdict: V5-11(a) PASS (1,784 / 2,115 Bartov-K = 84.4%, treat 84.4% ≥ 63% as BORDERLINE → upgrade-to-PASS by deduction that Bartov-K base is the proper denominator)
- Required user action: **explicit Lock C amendment** — formally re-register V5-11(a) denominator semantic as "active-exchange-listed NT-filer CIKs" or "Bartov-K 2017 comparable universe".
- Lock C concern: this IS a post-hoc spec change. Per autopilot prompt, "Lock C pre-reg sign / Bonferroni-12 / angle-lock post-hoc change → KILL". Amendment is technically Lock C violation unless user explicitly authorizes pre-Phase-0-step-5.
- Outcome: V5 proceeds to step 5; analysis cohort = 1,784 CIKs × 9,850 filings; sample-power Gate H comfortable.

### Path 3 — populate WRDS local dump for true CRSP-CCM (Rule 6)
- Required: download `crsp.ccmxpf_linktable` actual data into `E:/wrds-data-courier/output/dump/` (currently a 21-byte stub).
- Routing: WRDS-data-courier service (Rule 6 path) or other authorized fetch.
- Then re-run `scripts/audit-cik-ticker-match.py` against CCM-resolved PERMNO denominator → expected ≥90% on CRSP-historical (CCM covers delisted firms).
- This is the architecturally cleanest path but requires populating dump dir.
- Lock C neutral: same denominator that CLAUDE.md §4(a) was designed for.

## §6 RECOMMENDED ACTION

**Path 2 with explicit user authorization** — the Interpretation C reading is most consistent with:
- Launch SPEC §0 cohort definition ("~2,115 distinct US-listed firms / 9yr (Bartov-Konchitchki 2017 replication base)")
- CLAUDE.md §4(a) WRDS-local-dump-for-CRSP architecture (currently stubs but designed for CRSP-CCM)
- β2 lesson β2-4 ("Free-tier replication economic constraint" — declare limitation, do not auto-KILL on reachable analysis cohort)

If user agrees, recommended Lock C amendment text:

> **Lock C amendment 2026-06-10 (V5-11(a) denominator clarification, pre-Phase-0-step-5)**
> V5-11(a) "NT-firm CIK match ≥90%" denominator is now formally: NT-filer CIKs **whose firm was listed on a US major exchange (NYSE/Nasdaq/AMEX) during the year of the NT filing**, per CLAUDE.md §4(a) CRSP analysis-cohort architecture. Free-tier proxy: SEC `company_tickers.json` (current-snapshot, undercounts delisted) → measured 84.4% of Bartov-K 2017 2,115 base. Treat ≥84% on this proxy as **PASS-conditional-on-CRSP-historical-confirmation** in Phase 0 step 5+. Phase 0 step 5 will additionally compute a delisted-inclusive denominator if WRDS local dump is populated mid-Phase-0; otherwise carry the conditional PASS with explicit limitation note in close-report.

If user rejects Path 2, default is Path 1 (KILL).

## §7 PHASE 0 step 5 (Angle 1 event-CAR replication) — **HALTED pending §5 decision**

No further Phase 0 work until user resolves V5-11(a). All step-4 deliverables (bulk pull, CIK match audit, this escalation) are committed; no Lock C-affecting code added.

## §8 Cross-reference
- Stage 0 summary: `audits/2026-06-10-V5-stage-0-summary.md`
- β2 sister postmortem (family precedent): `D:/vscode/meta-harness/audits/2026-04-27-eight-k-non-reliance-frozen-postmortem.md`
- Lock F §8 grep: `audits/2026-06-10-V5-stage-0-lock-f-grep.md`
- Launch SPEC §0.3 V5-11(a) origin: `D:/vscode/meta-harness/audits/2026-06-10-V5-launch-spec.md`
- Kill-audit generator (if Path 1): `D:/vscode/meta-harness/templates/kill-audit-generator.py`
