"""R6 — LLM model + schema ablation.

(a) Schema ablation: binary fallback. The current Strategy D 3-class
    schema includes `unresolved_sec_comment` (n=54) as a separate label.
    The Stage 0 sub-gate S0-3 committed a binary fallback {accounting_issue,
    other} if kappa < 0.7 — we never had to use it, but we test sensitivity
    here by computing rate-diff under THREE merge variants:
      original  - 3-class, drop unresolved_sec_comment (current V5)
      merge_ai  - 2-class, merge unresolved_sec_comment into accounting_issue
      merge_ot  - 2-class, merge unresolved_sec_comment into other

(b) Body-length ablation: filter to filings whose NT body has >= 200
    characters of meaningful text (drop "no narrative found" and very
    short bodies). Sensitivity of signal to text-quality threshold.

Note: Cross-LLM ablation (gpt-4o-mini -> Claude Haiku 4.5) requires
additional LLM spend and is deferred until a sample-size budget is
agreed; this script only does within-existing-data robustness.
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT = REPO_ROOT / "data" / "angle_2_forward.jsonl"
NT_BODIES = REPO_ROOT / "data" / "nt_bodies.jsonl"
CLASSIFICATIONS = REPO_ROOT / "data" / "nt_classifications.jsonl"
OUTPUT = REPO_ROOT / "reports" / "r6-llm-schema-ablation.json"


def two_prop_z(p1: float, n1: int, p2: float, n2: int) -> tuple[float, float]:
    p_pool = (p1 * n1 + p2 * n2) / (n1 + n2) if (n1 + n2) > 0 else 0
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2)) if 0 < p_pool < 1 else 0
    diff = p1 - p2
    z = diff / se if se > 0 else 0
    return diff, z


def rate_diff(rows: list[dict], window_key: str, ai_label: str = "accounting_issue") -> dict:
    ai = [r for r in rows if r["label"] == ai_label]
    ot = [r for r in rows if r["label"] == "other"]
    if not ai or not ot:
        return {"verdict": "INSUFFICIENT"}
    n1, n2 = len(ai), len(ot)
    p1 = sum(1 for r in ai if r.get(window_key)) / n1
    p2 = sum(1 for r in ot if r.get(window_key)) / n2
    diff, z = two_prop_z(p1, n1, p2, n2)
    return {
        "n_ai": n1, "n_other": n2,
        "p_ai_pct": round(100 * p1, 4),
        "p_other_pct": round(100 * p2, 4),
        "diff_pp": round(100 * diff, 4),
        "z_stat": round(z, 4),
        "bonferroni12_PASS": abs(z) > 2.78,
    }


def main() -> int:
    rows_all = [json.loads(l) for l in INPUT.open(encoding="utf-8")]
    print(f"Total angle_2_forward rows: {len(rows_all)}", flush=True)
    label_dist = Counter(r["label"] for r in rows_all)
    print(f"Label distribution: {dict(label_dist)}", flush=True)

    # (a) Schema variants
    variants: dict[str, list[dict]] = {}

    # original: 3-class, drop unresolved_sec_comment
    variants["original_3class_drop_unresolved"] = [
        r for r in rows_all if r["label"] in ("accounting_issue", "other")
    ]

    # merge_ai: 2-class, merge unresolved_sec_comment INTO accounting_issue
    variants["merge_unresolved_into_AI"] = [
        {**r, "label": "accounting_issue" if r["label"] == "unresolved_sec_comment" else r["label"]}
        for r in rows_all
        if r["label"] in ("accounting_issue", "other", "unresolved_sec_comment")
    ]

    # merge_ot: 2-class, merge unresolved_sec_comment INTO other
    variants["merge_unresolved_into_other"] = [
        {**r, "label": "other" if r["label"] == "unresolved_sec_comment" else r["label"]}
        for r in rows_all
        if r["label"] in ("accounting_issue", "other", "unresolved_sec_comment")
    ]

    out: dict = {"schema_variants": {}}
    print(f"\n{'Variant':<40} {'n':>6} {'90d z':>8} {'180d z':>8}")
    for name, rows in variants.items():
        rd90 = rate_diff(rows, "restated_within_90d")
        rd180 = rate_diff(rows, "restated_within_180d")
        rd30 = rate_diff(rows, "restated_within_30d")
        rd14 = rate_diff(rows, "restated_within_14d")
        out["schema_variants"][name] = {
            "n": len(rows),
            "label_distribution": dict(Counter(r["label"] for r in rows)),
            "rate_diff_14d": rd14,
            "rate_diff_30d": rd30,
            "rate_diff_90d": rd90,
            "rate_diff_180d": rd180,
        }
        print(f"{name:<40} {len(rows):>6} {rd90.get('z_stat', '—'):>8} {rd180.get('z_stat', '—'):>8}")

    # (b) Body-length ablation
    print("\nBody-length ablation:", flush=True)
    bodies = {}
    if NT_BODIES.exists():
        for line in NT_BODIES.open(encoding="utf-8"):
            r = json.loads(line)
            bodies[r["accession_number"]] = len(r.get("narrative", "") or "")
    print(f"  bodies indexed: {len(bodies)}", flush=True)

    out["body_length_variants"] = {}
    base_rows = variants["original_3class_drop_unresolved"]
    for threshold in (0, 100, 200, 500, 1000, 2000):
        kept = [r for r in base_rows if bodies.get(r["accession_number"], 0) >= threshold]
        rd90 = rate_diff(kept, "restated_within_90d")
        out["body_length_variants"][f"min_chars_{threshold}"] = {
            "threshold_chars": threshold,
            "n_rows": len(kept),
            "rate_diff_90d": rd90,
        }
        print(f"  min_chars>={threshold:>5}: n={len(kept):>5} 90d z={rd90.get('z_stat', '—')}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\nReport: {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
