"""R6 — Cohen's kappa between gpt-4o-mini and Llama-3.3-70B on shared 50-sample.

Reads:
  data/nt_classifications.jsonl   (gpt-4o-mini, full sample including 50 shared)
  data/r6_llama_classifications.jsonl (Llama-3.3-70B, 50 sample)

Computes:
  - 3-class kappa (accounting_issue / unresolved_sec_comment / other)
  - binary kappa (accounting_issue / other; collapses unresolved into other)
  - per-label confusion matrix
  - rate-diff agreement on 90d restatement signal

Stage 0 S0-3 threshold: kappa >= 0.7 maintains 3-class schema;
< 0.7 triggers binary fallback {accounting_issue, other}.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GPT_PATH = REPO_ROOT / "data" / "nt_classifications.jsonl"
LLAMA_PATH = REPO_ROOT / "data" / "r6_llama_classifications.jsonl"
SAMPLE_PATH = REPO_ROOT / "data" / "r6_llm_ablation_sample.jsonl"
OUTPUT = REPO_ROOT / "reports" / "r6-llm-model-ablation.json"


def cohen_kappa(rater1: list[str], rater2: list[str]) -> dict:
    """Cohen's kappa for two raters with same labels list."""
    if len(rater1) != len(rater2) or not rater1:
        return {"n": 0, "kappa": None}
    n = len(rater1)
    labels = sorted(set(rater1) | set(rater2))
    obs_agree = sum(1 for a, b in zip(rater1, rater2) if a == b) / n
    c1 = Counter(rater1)
    c2 = Counter(rater2)
    exp_agree = sum((c1[l] / n) * (c2[l] / n) for l in labels)
    if exp_agree >= 1:
        return {"n": n, "kappa": None}
    k = (obs_agree - exp_agree) / (1 - exp_agree)
    return {
        "n": n,
        "observed_agreement_pct": round(100 * obs_agree, 2),
        "expected_agreement_pct": round(100 * exp_agree, 2),
        "kappa": round(k, 4),
    }


def main() -> int:
    # Load shared sample
    sample_acc = set()
    for line in SAMPLE_PATH.open(encoding="utf-8"):
        r = json.loads(line)
        sample_acc.add(r["accession_number"])
    print(f"Sample size: {len(sample_acc)}", flush=True)

    # gpt-4o-mini labels (filter to sample)
    gpt: dict[str, str] = {}
    for line in GPT_PATH.open(encoding="utf-8"):
        r = json.loads(line)
        if r["accession_number"] in sample_acc and r.get("label"):
            gpt[r["accession_number"]] = r["label"]

    # Llama labels
    llama: dict[str, str] = {}
    for line in LLAMA_PATH.open(encoding="utf-8"):
        r = json.loads(line)
        if r.get("label"):
            llama[r["accession_number"]] = r["label"]

    # Common ground
    common = sorted(set(gpt) & set(llama))
    print(f"Common (both classified): {len(common)}/{len(sample_acc)}", flush=True)
    r1 = [gpt[a] for a in common]
    r2 = [llama[a] for a in common]

    # 3-class kappa
    k3 = cohen_kappa(r1, r2)
    # binary kappa (collapse unresolved into other)
    def to_binary(x: str) -> str:
        return "accounting_issue" if x == "accounting_issue" else "other"
    r1b = [to_binary(x) for x in r1]
    r2b = [to_binary(x) for x in r2]
    k_bin = cohen_kappa(r1b, r2b)

    # Confusion matrix
    cm: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for a, b in zip(r1, r2):
        cm[a][b] += 1
    cm_out = {a: dict(b) for a, b in cm.items()}

    out = {
        "n_common": len(common),
        "gpt_label_distribution": dict(Counter(r1)),
        "llama_label_distribution": dict(Counter(r2)),
        "kappa_3class": k3,
        "kappa_binary": k_bin,
        "stage_0_S0_3_threshold": 0.7,
        "schema_decision": (
            "3-CLASS_OK" if (k3.get("kappa") or 0) >= 0.7
            else "BINARY_FALLBACK" if (k_bin.get("kappa") or 0) >= 0.7
            else "BOTH_BELOW_FLOOR"
        ),
        "confusion_matrix_gpt_rows_x_llama_cols": cm_out,
        "models": {
            "primary": "openai/gpt-4o-mini (V5 default)",
            "robustness": "meta-llama/llama-3.3-70b-instruct (alt-LLM)",
        },
        "claude_avoidance_note": (
            "anthropic/claude-* not used per user directive 2026-06-10; "
            "Llama-3.3-70B is the robustness pair"
        ),
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print()
    print(f"GPT-4o-mini   dist: {out['gpt_label_distribution']}")
    print(f"Llama-3.3-70B dist: {out['llama_label_distribution']}")
    print(f"3-class kappa: {k3.get('kappa')}  (obs_agree={k3.get('observed_agreement_pct')}%)")
    print(f"Binary kappa:  {k_bin.get('kappa')} (obs_agree={k_bin.get('observed_agreement_pct')}%)")
    print(f"Schema decision: {out['schema_decision']}")
    print(f"Confusion matrix (gpt rows × llama cols):")
    for row, cols in cm_out.items():
        print(f"  {row}: {cols}")
    print(f"\nReport: {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
