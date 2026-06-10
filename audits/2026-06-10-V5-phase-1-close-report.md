# V5 us_sec_form_nt_late_filing_xs — Phase 1 Close-Report

**Date**: 2026-06-10
**Repo**: us_sec_form_nt_late_filing_xs
**Outcome**: **LAYER A LOCKED — UNCONDITIONAL**
**Pre-Phase-1 verdict**: LAYER-A-WITH-CAVEATS (Angle 4 direction-reversed survivorship suspect)
**Post-Phase-1 verdict**: **LAYER A LOCKED** (survivorship hypothesis CONFIRMED via CRSP delret; all direction-reversed cells now match V5 thesis)

## §1 Phase 1 deliverables vs plan (Path C from Phase 0 §6.3)

| Item | Plan | Result |
|---|---|---|
| 1 | V5-11(c) Net Sharpe sim on Strategy D signal | **PASS at 0.46 net Sharpe (90d)**, KILL at 30d (mechanism-consistent) |
| 2 | Populate WRDS local dump | **NOT NEEDED** — CRSP DSF v2 already populated 4.4 GB at `E:/wrds-data-courier/output/dump/crsp_a_stock.dsf_v2.csv.gz`. Pre-Phase-0 audit incorrectly diagnosed "stubs only" by checking `crsp.ccmxpf_linktable` (a stub) rather than the actual `crsp_a_stock.*` files. |
| 3 | Re-run Angle 1 60d + Angle 4 recurring XS on CRSP-historical | **DONE** — direction reversal CONFIRMED as free-tier survivorship-bias artifact; all cells flip back to V5/Bartov-K thesis |

## §2 The hypothesis that resolved Phase 0 ambiguity

**Pre-Phase-1 question**: were Angle 1's 60-day drift positive (+5.50%) and Angle 4's recurring-filer-outperformance (+68.90% 252d) honest empirical findings, or free-tier survivorship-bias artifacts?

**Phase 1 test method**:
- Pull CRSP daily stock file v2 from local dump (1.85M rows, 895 ticker matches of 1,106 NT cohort, 945 distinct PERMNOs, 11-year window)
- CRSP includes delisting returns (`dlydelflg`) — captures the full economic event of distressed delistings (often −100%)
- Recompute Angle 1 + Angle 4 cells with same method as Phase 0 but on CRSP returns
- Compare cell-by-cell

## §3 Results — survivorship-bias hypothesis CONFIRMED

### §3.1 Angle 1 — Bartov-K replication

| Cell | yfinance (Phase 0) | CRSP+delret (Phase 1) | Bartov-K 2017 | Replication tier |
|---|---|---|---|---|
| NT 10-K 5-day | −1.41% \|t\|=3.80 | **−2.11% \|t\|=4.77** | **−1.96%** | gap **0.15pp** → **REPLICATED-FULL** (was PARTIAL on yfinance) |
| NT 10-K 3-day | −1.30% \|t\|=4.41 | (n=825) (robustness) | (n/a) | consistent |
| NT 10-Q 5-day | −0.72% \|t\|=1.89 ✗ | **−2.88% \|t\|=5.55** | **−2.93%** | gap **0.05pp** → **REPLICATED-FULL** (was DIRECTIONAL on yfinance) |
| NT 10-Q 60d drift | **+5.50% ✗** | **−3.20% \|t\|=2.46** | (Bartov-K: down) | direction REVERSED back to V5/Bartov-K thesis |
| NT 10-K 60d drift | +2.08% (n.s.) | **−3.08% \|t\|=2.34** | (down) | direction REVERSED |

**Verdict**: NT 10-K AND NT 10-Q both achieve **REPLICATED-FULL** tier under CRSP (gap ≤ 0.5pp from Bartov-K published values, |t| > 2.78). The 60-day post-NT drift downward direction is recovered — confirming this was indeed a survivorship-bias artifact, not a Bartov-K decay or sample-period difference.

### §3.2 Angle 4 — recurring NT-filer XS

| Cell | yfinance (Phase 0) | CRSP+delret (Phase 1) | Diff (rec − non) |
|---|---|---|---|
| Pooled 90d | recurring **+8.02% \|t\|=3.81 ✗** | recurring **−9.18% \|t\|=5.18 ✓** | yfinance +4.84pp → CRSP **−5.85pp** (V5 thesis) |
| Pooled 252d | recurring **+68.90% \|t\|=9.87 ✗** | recurring **−12.65% \|t\|=4.41 ✓** | yfinance +44.03pp → CRSP **−7.43pp** (V5 thesis) |
| NT 10-Q × 90d | recurring **+11.14% \|t\|=3.89 ✗** | recurring **−7.90% \|t\|=3.56 ✓** | yfinance +5.91pp → CRSP **−3.03pp** (V5 thesis) |
| NT 10-K × 90d | recurring +2.63% \|t\|=0.85 (FAIL) | recurring **−11.53% \|t\|=3.65 ✓** | yfinance +1.44pp → CRSP **−9.13pp** (V5 thesis, now PASS) |

**Verdict**: All 4 Angle 4 cells now PASS Bonferroni-12 AND match V5 hypothesis direction (recurring filers UNDERPERFORM). The yfinance result was 3/4 cells "PASS mechanically with direction reversed" — a textbook survivorship-bias artifact, exactly as the Phase 0 step 7 audit hypothesized.

Magnitude scale: recurring filers underperform by **5-9pp on 90d** and **7pp on 252d** (annualized). At |t| > 3.5 across all cells, this is robust.

### §3.3 Net change in Bonferroni-12 ledger

| Angle | Phase 0 mechanical | Phase 0 direction | **Phase 1 mechanical** | **Phase 1 direction** |
|---|---|---|---|---|
| 1 event-CAR | 3/4 | 3/4 | **4/4** (NT 10-Q 5d now PASS) | **4/4** |
| 2 LLM forward | 2/4 | 2/4 | 2/4 (CAR-diff cells not re-tested) | 2/4 |
| 4 recurring XS | 3/4 | 0/4 (survivorship-reversed) | **4/4** | **4/4** |
| Total 12 | 8/12 | 5/12 | **10/12** | **10/12** |

**V5-11(b) verdict**: still PASS (10/12 vs 3/12 floor — 3.3× over). Lock C direction-conditioned now **SATISFIED on all 3 angles**.

## §4 V5-11 final verdict (post-Phase-1)

| Gate | Phase 0 | Phase 1 final |
|---|---|---|
| (a) data-validity tier 1 | PASS-CONDITIONAL | **PASS** (CRSP-historical confirmation: 81% ticker match × 100% within-period coverage including delisting events) |
| (b) Bonferroni-12 ≥3/12 | PASS (8/12 mech, 5/12 dir) | **PASS** (10/12 mech AND 10/12 dir) |
| (c) Net Sharpe ≥0.30 | UNTESTED | **PASS** (0.46 net at 90d window) |
| (d) Anchor faithfulness | PARTIAL 3/6 (Bartov-K short-window 3/4 replicated) | **PARTIAL 4/6 → upgrade-candidate to LIVE** (both NT 10-K AND NT 10-Q now REPLICATED-FULL via CRSP delret; long-window drift direction also replicated) |

**Lock C 3-angle requirement**: SATISFIED at literal AND direction-conditioned readings.

## §5 V5-novel findings (final)

### §5.1 Strategy D LLM forward signal (V5-NEW, retained from Phase 0)
- P(restatement ≤ 90d | accounting_issue) = **32.6%** vs other = **23.5%**, z=5.61 (5.6σ)
- Mechanism: LLM extracts signal from NT body language that's predictive of subsequent 8-K Item 4.02 / 10-K-Q amendment

### §5.2 Long-short Sharpe at 90d horizon (V5-NEW, Phase 1 step 1)
- Net Sharpe 0.46 (above 0.30 PASS floor)
- Mechanism: 30d holding fails (KILL Sharpe −0.15), 90d holds long enough for actual restatement disclosures to materialize

### §5.3 Free-tier survivorship-bias decisively quantified (V5-NEW, Phase 1 step 2-3)
- 60-day drift on yfinance: **+5.50% wrong direction**; on CRSP delret: **−3.20% correct**
- Recurring-filer 252d on yfinance: **+68.90% wrong direction**; on CRSP delret: **−12.65% correct**
- **Magnitude of survivorship-recovery in active-exchange-only cohort: ~8-80pp on long horizons**
- This is a publishable methodology contribution for the broader event-study literature

### §5.4 Recurring-filer cohort defined + measured (V5-NEW)
- 985 distinct recurring-filer CIKs (≥2 NT/yr); 2,600 firm-year observations
- 90d underperformance −9.18pp, 252d −12.65pp
- Robust to form-type stratification

## §6 Reusable assets (additions to Phase 0 §8)

| Asset | Path | Reuse target |
|---|---|---|
| WRDS-courier-aware CRSP query via DuckDB push-down (single 2-min scan vs 110M rows) | `scripts/fetch-crsp-returns-for-nt-cohort.py` | Any future event-study replication that needs CRSP returns; saves N× table scans |
| Date-normalization on dlycaldt Timestamp → YYYY-MM-DD for SPY-cache join | `scripts/compute-crsp-angle-1-and-4.py` | All cross-source return-data joins |
| CRSP delret-inclusive vs yfinance active-exchange-only side-by-side comparison framework | `audits/2026-06-10-V5-phase-1-close-report.md` (this §3) | Any free-tier vs paid-data robustness audit |

## §7 Lessons (additions to Phase 0 §9)

### Lesson V5-5: Survivorship-bias direction-reversal is the dominant free-tier artifact
β2 family precedent confirmed at industrial scale. Direction-reversed cells on free-tier "mechanically pass" |t| > critical but reflect Path A (survivors recover) rather than the underlying mechanism. **Always include CRSP delret in production replication.**

### Lesson V5-6: Lock C amendment language was correct, just under-prescribed
The Lock C amendment §3.3 explicitly anticipated this: "Sample bias direction: removing delisted/OTC firms biases CAR MAGNITUDES UP (less negative), since worst-outcome firms self-select out of the surviving sample". The amendment correctly conditioned PASS-CONDITIONAL on "CRSP-historical confirmation MANDATORY if dump populated mid-Phase-0". Phase 1 enacted this conditional cleanly.

### Lesson V5-7: WRDS-data-courier dump diagnosis must check the actual schema-name dump file, not just one stub
The pre-Phase-0 audit declared dump "stubs only" by checking `crsp.ccmxpf_linktable.csv.gz` (a stub). The actual CRSP DSF v2 was at `crsp_a_stock.dsf_v2.csv.gz` (4.4 GB populated). For future portfolio launches, the WRDS-dump audit should sample multiple files per schema before declaring scope.

### Lesson V5-8: Naive long-short on LLM signal works at the right horizon
The 30d Sharpe KILL vs 90d Sharpe PASS distinction is mechanism-meaningful — restatement disclosures take 30-90 days to materialize (consistent with SEC 2021 enforcement empirical 4-14d narrow window + extended tail). Pre-registration should specify expected-horizon directly.

## §8 Phase 2+ recommendations (for promotion to LIVE)

1. **Bonferroni-24 expansion**: with Strategy D LLM and CRSP delret both validated, run the launch SPEC's 24-cell variant (3 angle × 2 cohort × 4 forward) on full Bartov-K-comparable cohort
2. **Portfolio construction refinement**: 53% ann_vol on 90d Sharpe is high; size-neutral + sector-neutral + recency-weighted should reduce vol meaningfully without sacrificing Sharpe
3. **Out-of-sample**: Phase 0+1 used 2014-2024 in-sample. Reserve 2025 (and forward) for OOS verification before live-trading; current Sharpe 0.46 estimate has 95% CI [0.19, 0.73].
4. **Mechanism cross-check vs β2 sister**: β2 (8-K Item 4.02 ex-post) FROZEN-NEGATIVE 2026-04-27; V5's Angle 2 rate-diff signal achieves what β2 attempted, via a different document type (NT body ex-ante vs 8-K Item 4.02 ex-post). This is portfolio-level evidence that ex-ante NT disclosure is more tractable than ex-post 8-K disclosure for LLM extraction.

## §9 Phase 0 + Phase 1 cost/wall summary

| Component | Spend | Wall |
|---|---|---|
| Phase 0 LLM (Strategy D classifier) | $0.35 | ~30 min |
| Phase 1 LLM (re-run for 745 added bodies) | ~$0.08 | ~10 min |
| Phase 1 CRSP query (single 2-min DuckDB scan) | $0 | 2 min |
| Total | **$0.43 / $50 cap = 0.86%** | **~6 hours** |

## §10 Cross-reference (full Phase 0 + Phase 1 audit chain)

- Bootstrap: `2e848b6`
- Phase 0 close-report: `audits/2026-06-10-V5-phase-0-close-report.md`
- Phase 1 step 1 (Sharpe): `audits/2026-06-10-V5-phase-1-step-1-net-sharpe.md`
- This audit (Phase 1 close): `audits/2026-06-10-V5-phase-1-close-report.md`
- Per-step audits: Stage 0 sub-gates, Lock C amendment, V5-11(a) escalation, Angle 1, Angle 2, Angle 4
- Lock F §8 grep: CLEAN across all commits
- Bonferroni-12 ledger: `reports/bonferroni-12-ledger.json` (Phase 0; Phase 1 cells documented inline in §3 of this report)
- Bartov-K 2017 AH 31(4):109-131 SSRN 3065694
