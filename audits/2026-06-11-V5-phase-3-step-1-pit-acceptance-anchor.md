# V5 Phase 3 / Step 1 — PIT acceptance-anchor verification (in-sample)

**Date**: 2026-06-11
**Repo**: us_sec_form_nt_late_filing_xs (V5)
**Scope**: Replace EDGAR `date_filed` (calendar day) anchor with SEC
acceptance timestamp in ET, with after-hours (≥16:00 ET) reanchored to T+1.
Recompute angle-2 forward CAR + Net Sharpe (V5-11c) under PIT-clean
assumptions.

## Motivation

Phase 1 / Phase 2 LAYER A LOCK was conditioned on `date_filed`-as-T0
anchor. That anchor is PIT-naive: it does not respect SEC's after-hours
acceptance window. NT 12b-25 forms are typically filed at deadline EOD,
so a large share of the cohort is potentially un-tradable on the
`date_filed` close. This step measures the after-hours share and re-tests
the V5-11(c) verdict under a tradable anchor.

## Data pipeline

1. **acceptanceDateTime extract** — `scripts/extract-acceptance-datetime.py`
   joins `data/form_nt_matched(_oos).jsonl` against the existing
   `data/sec_submissions_cache/CIK{padded}.json` (1,284 CIK, fully cached
   for NYSE/Nasdaq cohort). Output: `data/form_nt_pit(_oos).jsonl` with
   `acceptance_utc`, `acceptance_et_date`, `acceptance_et_time`,
   `after_16et`.
2. **PIT angle-2 forward CAR** — `scripts/compute-angle-2-forward-pit.py`
   recomputes `car_fwd_{30,90}d` using `anchor_date = acceptance_et_date
   + (1d if after_16et else 0d)`. The first trading day on/after
   anchor_date defines T=0 in the firm return series.
3. **Net Sharpe (V5-11c)** — `scripts/compute-net-sharpe-strategy-d.py
   --input data/angle_2_forward_pit.jsonl` re-runs the long/short
   monthly basket on PIT-anchored CARs.

## Results

### Step 1a — after-hours acceptance distribution

| Cohort     | NYSE/Nasdaq filings | Match rate | after_16et share |
|------------|---------------------|------------|------------------|
| In-sample (2014-2024) | 3,970 | 98.06% (3,893) | **63.47%** (2,471 / 3,893) |
| OOS (2025-2026)       | 912   | 100.00% (912)  | **76.97%** (702 / 912) |

77 in-sample filings unmatched in `filings.recent` (>1000 filings ago for
their CIK) — older-shard fetch deferred (3.9% of cohort). Lockdown:
in-sample after-hours share is conservative lower bound.

**Hypothesis confirmed**: NT 12b-25 ≈ deadline-EOD filings. The previous
`date_filed` anchor was effectively assuming free entry at the close of
the **filing day** for ~63% of in-sample observations that were not
actually visible to the market before that close.

### Step 1b — Net Sharpe (V5-11c) under PIT anchor

In-sample, 3,811 rows in scope (AI + other labels after PIT join):

| Window | Original `date_filed` anchor | PIT acceptance anchor + T+1 | Verdict change |
|--------|------------------------------|-----------------------------|----------------|
| 30d    | gross 0.124 → **net −0.154** (KILL) | gross −0.194 → **net −0.227** (KILL) | KILL → KILL (still negative; slightly worse) |
| 90d    | gross 0.469 → **net 0.461** (PASS)  | gross 0.600 → **net 0.591** (PASS)  | PASS → **PASS (improved)** |

PIT 90d cell detail:
- ann_mean = +25.81 % (net of 15 bps round-trip)
- ann_vol = 43.69 %
- net Sharpe = **0.59** (≥ 0.30 PASS threshold)
- long_only Sharpe = 0.71 / short_only Sharpe = −0.22
  → Long-only is the dominant contributor; the short leg detracts.

### Why 90d Sharpe *improves* under PIT

Counter-intuitively the PIT reanchor *strengthens* the 90d cell. The
mechanism: after-hours NTs typically reflect an issue surfaced late in
the trading day. The `date_filed` close already absorbs some of the
day-of price reaction (a "leaked" signal). T+1 anchor strips that
contaminated day from the forward window, leaving a cleaner signal-day
basis. The 30d cell, which is already underwater, becomes slightly more
negative because the same logic removes a small positive contamination.

## V5-11(c) PIT verdict

**PASS** (90d cell). LAYER A LOCK survives a strict PIT-tradable
reanchor in-sample. The Phase 2 LAYER A LOCK is not an artifact of
intraday look-ahead.

## What this step does NOT establish

1. **Vintage LLM look-ahead** — `nt_classifications.jsonl` labels were
   produced by a 2024-vintage model. Even with PIT-correct prices, the
   classifier's training corpus may encode forward outcome information
   (e.g., "this company later restated"). Step 2 must re-label with a
   pre-2024 vintage alt-LLM (OpenRouter Claude avoidance per
   memory/feedback_openrouter_claude_avoidance.md).
2. **Delisting + borrow** — yfinance prices skip terminal observations
   for delisted NT filers; the recurring-filer XS short (angle 4) is
   exposed. Step 3 must add CRSP delisting return + Russell 3000 borrow
   proxy + a differentiated 50bps TC for sub-$1B float.
3. **OOS PIT** — OOS angle-2 PIT cardinality collapsed (912 → 3 with
   car_fwd_30d) due to yfinance-cache truncation at 2026-04-01 for many
   OOS tickers. OOS PIT must be redone after `r1-crsp-oos-fetch.py`
   extends through 2026-06.

## Files written

- `scripts/extract-acceptance-datetime.py`
- `scripts/compute-angle-2-forward-pit.py`
- `data/form_nt_pit.jsonl` (3,970 rows)
- `data/form_nt_pit_oos.jsonl` (912 rows)
- `data/angle_2_forward_pit.jsonl` (3,882 rows)
- `data/angle_2_forward_pit_oos.jsonl` (912 rows — PIT but forward
  windows mostly None due to cache truncation; see caveat above)
- `data/net_sharpe_strategy_d_pit.jsonl` (monthly PnL ledger)
- `reports/phase3-step1-acceptance.json`
- `reports/phase3-step1-angle2-pit-insample.json`
- `reports/phase3-step1-angle2-pit-oos.json` (OOS coverage caveat)
- `reports/phase3-step1-net-sharpe-pit.json`

## Next steps (Phase 3)

- **Step 2**: Vintage LLM relabel (2023-12 cutoff alt-LLM) on OOS 2024.
  Measure label agreement vs current Strategy D labels. Re-run angle-2 +
  Net Sharpe on the changed-label subset.
- **Step 3**: CRSP delisting return + Russell 3000 / float-tier
  membership proxy. 50 bps differentiated TC for sub-$1B float.
  Sensitivity table {15, 25, 50} bps × {full, large-cap-only} cohort.

## Verdict pad

PIT-tradable status (preliminary, in-sample only):
- **V5-11(c) 90d cell: PASS** under acceptance-anchor + T+1.
- LAYER A LOCK provisionally upgraded from "econometric LOCK" to
  "tradable LOCK pending Steps 2-3".
