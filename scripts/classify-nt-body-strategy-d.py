"""Phase 0 step 6b - Strategy D NT-body LLM classifier (CLAUDE-AVOIDANCE cascade).

Reads NT body narratives from data/nt_bodies.jsonl, classifies each into
one of {accounting_issue, unresolved_sec_comment, other} via OpenRouter
using cheap-tier models first (CLAUDE-AVOIDANCE convention).

Model cascade (per portfolio-coordination CLAUDE-AVOIDANCE):
    PRIMARY      openai/gpt-4o-mini    (~$0.0001/filing)
    ROBUSTNESS   meta-llama/llama-3.3-70b-instruct (for kappa on n=40)
    LAST RESORT  anthropic/claude-haiku-4.5 (only if cheaper models fail format)

Output JSONL keyed by accession_number; resumable.
Budget cap via shared_utils.openrouter_client (project tag =
'us_sec_form_nt_late_filing_xs', portfolio config soft-cap = $10/yr).

Usage:
    python scripts/classify-nt-body-strategy-d.py \\
        --input  data/nt_bodies.jsonl \\
        --output data/nt_classifications.jsonl \\
        --model  openai/gpt-4o-mini \\
        --max-filings 100   # dry-run; -1 = all
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO_ENV = Path(os.environ.get("PORTFOLIO_COORD_ROOT", "D:/vscode/portfolio-coordination")) / ".env"


def load_portfolio_env() -> None:
    """Load OPENROUTER_API_KEY (and related) from portfolio-coordination .env.

    Standard portfolio-coord pattern (lifted from passive_active_flow_disagreement_llm
    and others) — shared_utils.openrouter_client expects OPENROUTER_API_KEY in
    os.environ. We never PRINT the key or test its value, only ensure it is present
    so the shared client can pick it up. Compliant with PROHIBITION #2 (no direct
    lookup / no hardcoding).
    """
    if os.environ.get("OPENROUTER_API_KEY"):
        return
    if not PORTFOLIO_ENV.exists():
        return
    needed = ("OPENROUTER_API_KEY", "OPENROUTER_BASE_URL")
    with PORTFOLIO_ENV.open(encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            for k in needed:
                if line.startswith(k + "="):
                    os.environ[k] = line.split("=", 1)[1].strip().strip('"').strip("'")

SYSTEM_PROMPT = (
    "You classify SEC Form NT 10-K / NT 10-Q filings by reason-for-delay. "
    "Read the narrative section (Part III of Form 12b-25) and assign exactly one label:\n"
    "- accounting_issue: any reference to accounting problem, restatement risk, "
    "material weakness, internal control issue, audit concern, GAAP misapplication, "
    "prior-period error, or financial statement preparation difficulty\n"
    "- unresolved_sec_comment: SEC staff comment / inquiry / review, NOT "
    "accounting-restatement-triggering\n"
    "- other: operational (IT, SOX implementation, personnel, M&A, cybersecurity, "
    "integration backlog, COVID, natural disaster)\n\n"
    "Return STRICT JSON ONLY, no markdown fences, no preamble. Schema:\n"
    '{"label": "<one of three>", "confidence": <0-1>, "quote": "<<=30 word verbatim quote>"}'
)


def build_prompt(row: dict) -> str:
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"---\n"
        f"Filer: {row.get('ticker','?')} (CIK {row.get('cik','?')})\n"
        f"Form: {row.get('form_type','?')}\n"
        f"Filing date: {row.get('date_filed','?')}\n"
        f"Narrative (Part III):\n"
        f'"""\n{row["narrative"]}\n"""\n'
        f"Return strict JSON only."
    )


def parse_response(text: str) -> dict | None:
    """Extract JSON from LLM response; handle some common malformations."""
    text = text.strip()
    # Strip markdown fence if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)
    # Find first { ... } block
    m = re.search(r"\{[^{}]*\"label\"[^{}]*\}", text, flags=re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    label = obj.get("label", "").strip().lower()
    if label not in ("accounting_issue", "unresolved_sec_comment", "other"):
        return None
    return {
        "label": label,
        "confidence": float(obj.get("confidence", 0.0)) if obj.get("confidence") is not None else 0.0,
        "quote": str(obj.get("quote", ""))[:300],
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", default=str(REPO_ROOT / "data" / "nt_bodies.jsonl"))
    p.add_argument(
        "--output", default=str(REPO_ROOT / "data" / "nt_classifications.jsonl")
    )
    p.add_argument("--model", default="openai/gpt-4o-mini")
    p.add_argument("--project", default="us_sec_form_nt_late_filing_xs")
    p.add_argument("--max-filings", type=int, default=-1, help="-1 = all")
    p.add_argument("--max-tokens", type=int, default=300)
    p.add_argument("--min-narrative-chars", type=int, default=200,
                   help="Skip filings whose narrative is shorter than this")
    args = p.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"ERROR: {in_path} not found - run fetch-nt-bodies.py first", file=sys.stderr)
        return 1

    rows = [json.loads(l) for l in in_path.open(encoding="utf-8")]
    rows = [r for r in rows if r.get("narrative_len", 0) >= args.min_narrative_chars]
    print(f"Bodies with narrative >= {args.min_narrative_chars} chars: {len(rows)}", flush=True)
    if args.max_filings > 0:
        rows = rows[:args.max_filings]
        print(f"  capped to first {len(rows)}", flush=True)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done: set[str] = set()
    if out_path.exists():
        for line in out_path.open(encoding="utf-8"):
            try:
                rec = json.loads(line)
                key = (rec["accession_number"], rec.get("model", ""))
                done.add(key)
            except Exception:
                pass
    print(f"Already classified (with same model): {len(done)}", flush=True)

    load_portfolio_env()
    from shared_utils.openrouter_client import OpenRouterClient
    client = OpenRouterClient(project=args.project)

    n_ok = 0
    n_parse_fail = 0
    n_call_fail = 0
    total_usd = 0.0

    with out_path.open("a", encoding="utf-8") as f:
        for i, r in enumerate(rows, 1):
            key = (r["accession_number"], args.model)
            if key in done:
                continue
            prompt = build_prompt(r)
            try:
                resp = client.complete(
                    model=args.model,
                    prompt=prompt,
                    max_tokens=args.max_tokens,
                    temperature=0.0,
                )
            except Exception as e:
                n_call_fail += 1
                f.write(json.dumps({
                    "accession_number": r["accession_number"],
                    "cik": r["cik"], "form_type": r["form_type"],
                    "date_filed": r["date_filed"], "ticker": r["ticker"],
                    "model": args.model,
                    "label": None, "confidence": None, "quote": None,
                    "error": f"call: {e}"[:300],
                }) + "\n")
                f.flush()
                continue
            # OpenRouter response shape: choices[0].message.content + usage.cost
            try:
                text = resp["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError):
                text = ""
            cost = float(resp.get("usage", {}).get("cost", 0.0)) if isinstance(resp, dict) else 0.0
            total_usd += cost
            parsed = parse_response(text)
            if parsed is None:
                n_parse_fail += 1
                f.write(json.dumps({
                    "accession_number": r["accession_number"],
                    "cik": r["cik"], "form_type": r["form_type"],
                    "date_filed": r["date_filed"], "ticker": r["ticker"],
                    "model": args.model,
                    "label": None, "confidence": None, "quote": None,
                    "raw": text[:500],
                    "cost_usd": cost,
                }) + "\n")
            else:
                n_ok += 1
                f.write(json.dumps({
                    "accession_number": r["accession_number"],
                    "cik": r["cik"], "form_type": r["form_type"],
                    "date_filed": r["date_filed"], "ticker": r["ticker"],
                    "model": args.model,
                    **parsed,
                    "cost_usd": cost,
                }, ensure_ascii=False) + "\n")
            f.flush()
            if i % 25 == 0 or i == len(rows):
                print(f"  [{i}/{len(rows)}] ok={n_ok} parse_fail={n_parse_fail} call_fail={n_call_fail} spent=${total_usd:.4f}", flush=True)

    print()
    print(f"DONE - ok={n_ok}, parse_fail={n_parse_fail}, call_fail={n_call_fail}, total_spent=${total_usd:.4f}")
    print(f"Output: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
