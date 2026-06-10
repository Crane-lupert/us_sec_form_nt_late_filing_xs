"""Phase 3 Step 2 — Cohen's kappa between gpt-4o-mini (production) and
pre-2024-vintage classifier (gpt-3.5-turbo) on the same 50-sample stratified
random draw, to bound the LLM vintage look-ahead concern.

gpt-3.5-turbo has a public training cutoff of 2023-Q3 per OpenAI documentation,
which strictly precedes the bulk of the in-sample window's NT filings and the
entirety of the post-2024-restatement-disclosure outcome population. If the
production extractor's accuracy is replicated by the pre-2024 model at the same
sample, vintage look-ahead is bounded.
"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def load_labels(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.open(encoding="utf-8"):
        r = json.loads(line)
        if r.get("label"):
            out[r["accession_number"]] = r["label"]
    return out


def cohen_kappa(pairs: list[tuple[str, str]]) -> tuple[float, float]:
    n = len(pairs)
    if n == 0:
        return 0.0, 0.0
    obs = sum(1 for a, b in pairs if a == b) / n
    cats = sorted({l for pair in pairs for l in pair})
    pe = 0.0
    for c in cats:
        pa = sum(1 for a, _ in pairs if a == c) / n
        pb = sum(1 for _, b in pairs if b == c) / n
        pe += pa * pb
    if pe >= 1.0:
        return 0.0, obs
    return (obs - pe) / (1.0 - pe), obs


def main() -> int:
    gpt4 = load_labels(REPO_ROOT / "data" / "nt_classifications.jsonl")
    gpt35 = load_labels(REPO_ROOT / "data" / "r6_gpt35_classifications.jsonl")
    llama = load_labels(REPO_ROOT / "data" / "r6_llama_classifications.jsonl")

    common = set(gpt35) & set(gpt4)
    print(f"gpt-4o-mini coverage: {len(gpt4)}")
    print(f"gpt-3.5-turbo coverage: {len(gpt35)}")
    print(f"Llama-3.3-70B coverage: {len(llama)}")
    print(f"Common (gpt-4o ∩ gpt-3.5): {len(common)}")
    print()

    pairs_4_35 = [(gpt4[k], gpt35[k]) for k in sorted(common)]
    pairs_4_llama = [(gpt4[k], llama[k]) for k in sorted(set(llama) & set(gpt4))]
    pairs_35_llama = [(gpt35[k], llama[k]) for k in sorted(set(gpt35) & set(llama))]

    cases = [
        ("gpt-4o-mini  vs gpt-3.5-turbo (vintage pre-2024)", pairs_4_35),
        ("gpt-4o-mini  vs Llama-3.3-70B (cross-vendor)",   pairs_4_llama),
        ("gpt-3.5-turbo vs Llama-3.3-70B (vintage x vendor)", pairs_35_llama),
    ]

    out = {"cells": {}}
    for name, pairs in cases:
        k3, obs = cohen_kappa(pairs)
        # binary collapse
        bin_pairs = [
            (a if a == "accounting_issue" else "other",
             b if b == "accounting_issue" else "other")
            for a, b in pairs
        ]
        k2, obs2 = cohen_kappa(bin_pairs)
        dist_a = dict(Counter(p[0] for p in pairs))
        dist_b = dict(Counter(p[1] for p in pairs))
        print(f"--- {name} (n={len(pairs)}) ---")
        print(f"  3-class kappa = {k3:.4f}  obs_agree = {obs*100:.2f}%")
        print(f"  binary  kappa = {k2:.4f}  obs_agree = {obs2*100:.2f}%")
        print(f"  dist A: {dist_a}")
        print(f"  dist B: {dist_b}")
        out["cells"][name] = {
            "n": len(pairs),
            "kappa_3class": round(k3, 4),
            "obs_agreement_3class_pct": round(100 * obs, 2),
            "kappa_binary": round(k2, 4),
            "dist_A": dist_a,
            "dist_B": dist_b,
        }

    s0_3_threshold = 0.7
    main_pair = out["cells"]["gpt-4o-mini  vs gpt-3.5-turbo (vintage pre-2024)"]
    out["vintage_lookahead_verdict"] = (
        "VINTAGE-INVARIANT" if main_pair["kappa_3class"] >= s0_3_threshold else "VINTAGE-SENSITIVE"
    )
    out["s0_3_floor"] = s0_3_threshold

    rep = REPO_ROOT / "reports" / "phase3-step2-llm-vintage-kappa.json"
    rep.parent.mkdir(parents=True, exist_ok=True)
    rep.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print()
    print(f"Vintage look-ahead verdict: {out['vintage_lookahead_verdict']}")
    print(f"Report: {rep}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
