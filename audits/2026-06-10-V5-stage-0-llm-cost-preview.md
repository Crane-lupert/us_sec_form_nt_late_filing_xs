# V5 Stage 0 sub-gate S0-3 — NT body LLM-extract cost preview

**Date**: 2026-06-10
**Repo**: us_sec_form_nt_late_filing_xs
**Gate**: S0-3 (BLOCKING)
**Verdict**: PASS — cost envelope comfortably below $50/yr ceiling at primary + robustness specs
**Execution**: paper exercise (no actual LLM call this turn — first call deferred to Phase 0 step 6)

## §1 Strategy D classifier schema (locked)

**3-class single-axis classifier on Form NT body — Part III "Narrative explanation of inability to file"**.

| Label | Definition | Bartov-K 2017 mapping |
|---|---|---|
| `accounting_issue` | Body language references accounting issue, restatement risk, material weakness, auditor concern, internal control issue, GAAP misapplication, prior-period error, or any item that would plausibly precede an 8-K Item 4.02 / 4.01 within 4-14d (SEC 2021 enforcement window) | "accounting reasons" subset (Bartov-K finds this subset drives the NT 10-Q effect, predicts grace-period failure) |
| `unresolved_sec_comment` | Body references unresolved SEC staff comment, ongoing review, regulatory inquiry, but NOT accounting-restatement-triggering | "SEC investigation" subset |
| `other` | Operational reasons: IT/SOX/cybersecurity/personnel/integration/M&A backlog/ordinary delay | Residual |

### §1.1 Schema objectivity prior
β2 sister analog (3-axis on 8-K Item 4.02): error_type κ = **0.89** (PASS far above 0.7). V5 single-axis classification on shorter, more structured Form NT body language → expected κ ≥ 0.85 at primary spec.

### §1.2 Pre-registered abandon trigger (κ floor)
If inter-rater κ < 0.7 on n=40 cross-vendor (Opus 4.7 + Sonnet 4.6 + Haiku 4.5) sample → schema-objectivity FAIL → downgrade to binary {accounting_issue, other} fallback (Lesson β2-1).

## §2 Prompt template (locked, lift from β2 schema validation framework)

```
SYSTEM:
You classify SEC Form NT 10-K / NT 10-Q filings by reason-for-delay.
Read the narrative section (Part III of Form 12b-25) and assign exactly one label:
- accounting_issue: any reference to accounting problem, restatement risk, material weakness,
  internal control issue, audit concern, GAAP misapplication, prior-period error
- unresolved_sec_comment: SEC staff comment / inquiry / review, NOT accounting-restatement-triggering
- other: operational (IT, SOX implementation, personnel, M&A, cybersecurity, integration backlog)

Return strict JSON: {"label": "<one of three>", "confidence": <0-1>, "quote": "<≤30 word verbatim quote anchoring decision>"}

USER:
Filer: {COMPANY_NAME}
CIK: {CIK}
Form: {FORM_TYPE}  (NT 10-K or NT 10-Q)
Filing date: {FILING_DATE}
Narrative (Part III):
"""
{NARRATIVE_TEXT}
"""
```

### §2.1 Token budget per filing
- System prompt: ~140 tokens
- User prompt template overhead: ~60 tokens
- Narrative text (Form NT Part III typical 100-400 words): ~140-560 tokens
- **Input total per filing**: ~340-760 tokens (midpoint 550)
- **Output JSON**: ~80-120 tokens (midpoint 100)

## §3 Cost calculation (primary + robustness)

### §3.1 Single-vendor primary (Haiku 4.5)

Haiku 4.5 list pricing (2026-Q2): $1.00/MTok input, $5.00/MTok output.

Per filing:
- Input: 550 tok × $1.00/M = $0.00055
- Output: 100 tok × $5.00/M = $0.00050
- **Total per filing**: ~$0.00105 ≈ **$0.001**

At ~3,000 filings/yr:
- **Annual cost** = $0.001 × 3,000 = **$3.15/yr** (single-vendor primary)

### §3.2 3-vendor ensemble robustness (Opus 4.7 + Sonnet 4.6 + Haiku 4.5) — n=40 κ-validation only

Pricing snapshot:
- Opus 4.7: $15/$75 per MTok → per filing ≈ $0.0083 + $0.0075 = $0.0158
- Sonnet 4.6: $3/$15 per MTok → per filing ≈ $0.00165 + $0.0015 = $0.00315
- Haiku 4.5: $1/$5 per MTok → per filing ≈ $0.001

Ensemble per filing on κ-validation subset: $0.0158 + $0.00315 + $0.001 ≈ **$0.020**
- n=40 κ-validation: 40 × $0.020 = **$0.80 one-time**

### §3.3 Strategy D total Phase 0 + Year 1 budget

| Component | Cost | Note |
|---|---|---|
| S0-3 dry-run (100 sample × single-vendor Haiku) | $0.10 | Validate pipeline, sanity-check format |
| Schema κ-validation (40 × 3-vendor) | $0.80 | One-time pre-Phase-1 |
| Year-1 full classification (3,000 × single-vendor Haiku) | $3.15 | Production run |
| Robustness re-classification (Sonnet 4.6 on n=300 stratified) | ~$1.00 | Vendor-invariance check |
| **Year-1 total** | **~$5.05** | **vs $50/yr ceiling = 10.1% utilization** |

### §3.4 Backfill (2014-2024 historical, ~27,000 filings)
- 27,000 × $0.001 = **$27.00 one-time** for full Bartov-K sample period (still below $50 ceiling year-1).
- Practical split: backfill in Phase 0 step 6 → year-1 quota.

## §4 Routing constraint (PROHIBITION #2 compliance)

Per autopilot prompt PROHIBITION #2: NO direct OPENROUTER_API_KEY / ANTHROPIC_API_KEY / OPENAI_API_KEY lookup.

**Required routing path**:
```python
from shared_utils.openrouter_client import OpenRouterClient   # portfolio-coordination wrapper
# OR
import requests
resp = requests.post("http://localhost:8787/v1/messages", json=payload)   # claude-openai-proxy
```

Both routes carry the budget-cap mechanism + atomic-io semantics validated by β2 sister repo (4 patches `f4719d1`, `5c10c1e`, `0a2f269`).

### §4.1 Phase 0 step 6 entrypoint (deferred — first actual call)
- Script: `scripts/classify-nt-body-strategy-d.py` (to be written Phase 0 step 6)
- Resumable JSONL output: `data/nt_classifications.jsonl`
- Budget cap: `$50/yr` enforced via `shared_utils.budget_cap`
- Fleiss κ contamination check on n=40 sample using `skills/llm-batch-extraction/SKILL.md` framework
- Idempotency: cache by (CIK, accession_number, vendor)

## §5 S0-3 verdict

- **PASS** — primary cost envelope $5.05/yr at single-vendor + robustness = **10.1% of $50/yr ceiling**
- **Full backfill** (2014-2024, ~27K filings) = $27 one-time, still below ceiling
- **Prompt template locked** (Strategy D 3-class)
- **Routing constraint compliant** (no direct API key lookup)
- **Pre-registered κ floor 0.7** for schema objectivity (Lesson β2-1)
- **BLOCKING resolved** — proceed to S0-4

## §6 Cross-reference
- β2 prompt-pattern source: `D:/vscode/eight_k_non_reliance_llm/src/eight_k_non_reliance_llm/classify_ensemble.py`
- β2 lessons: postmortem §9 (Gate H sample power) + §10.1 (lift-and-shift code)
- Skill: `D:/vscode/meta-harness/skills/llm-batch-extraction/SKILL.md`
- Pricing source: Anthropic published pricing 2026-Q2 (claude-opus-4-7, claude-sonnet-4-6, claude-haiku-4-5)
