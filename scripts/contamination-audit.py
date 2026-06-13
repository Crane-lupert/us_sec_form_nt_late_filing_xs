"""Contamination audit (#8): redact firm-identifying tokens from the body
narrative and re-classify. If the classification changes after redaction,
the production extractor is retrieving firm-specific information from its
pre-training corpus rather than inferring from the narrative text alone.

Sample size n = 20 stratified random with seed 42 (limited to keep LLM
cost ~$0.01-0.02).

Output: data/contamination_audit.jsonl
        reports/contamination-audit.json
"""
from __future__ import annotations

import json
import os
import random
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
REPORTS = REPO / "reports"
PORTFOLIO_ENV = Path("D:/vscode/portfolio-coordination/.env")


def load_portfolio_env() -> None:
    if os.environ.get("OPENROUTER_API_KEY"):
        return
    if not PORTFOLIO_ENV.exists():
        return
    with PORTFOLIO_ENV.open(encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            for k in ("OPENROUTER_API_KEY", "OPENROUTER_BASE_URL"):
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
    "Return STRICT JSON ONLY: {\"label\": \"<one of three>\", "
    "\"confidence\": <0-1>, \"quote\": \"<<=30 word verbatim quote>\"}"
)


def redact(text: str, firm_name: str | None, ticker: str | None, cik: str | None) -> str:
    out = text
    if firm_name:
        out = re.sub(re.escape(firm_name), "[REDACT_NAME]", out, flags=re.IGNORECASE)
        # Common abbreviations
        first_word = firm_name.split()[0]
        if len(first_word) > 3:
            out = re.sub(re.escape(first_word), "[REDACT_NAME]", out, flags=re.IGNORECASE)
    if ticker:
        out = re.sub(re.escape(ticker), "[REDACT_TICKER]", out)
    if cik:
        out = re.sub(re.escape(cik), "[REDACT_CIK]", out)
    # Generic patterns
    out = re.sub(r"\b\d{2}/\d{2}/\d{4}\b", "[REDACT_DATE]", out)
    out = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "[REDACT_DATE]", out)
    out = re.sub(r"\b\d{10}\b", "[REDACT_CIK]", out)  # 10-digit CIK
    out = re.sub(r"\b\d{3}-\d{3}-\d{4}\b", "[REDACT_PHONE]", out)
    out = re.sub(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", "[REDACT_EMAIL]", out)
    out = re.sub(r"\b(?:Mr|Ms|Mrs|Dr)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b", "[REDACT_PERSON]", out)
    return out


def parse_response(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)
    m = re.search(r"\{[^{}]*\"label\"[^{}]*\}", text, flags=re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    label = (obj.get("label") or "").strip().lower()
    if label not in ("accounting_issue", "unresolved_sec_comment", "other"):
        return None
    return {"label": label,
            "confidence": float(obj.get("confidence", 0.0) or 0.0),
            "quote": str(obj.get("quote", ""))[:300]}


def main() -> int:
    random.seed(42)
    bodies = [json.loads(l) for l in (DATA / "nt_bodies.jsonl").open(encoding="utf-8")]
    bodies = [r for r in bodies if (r.get("narrative_len") or 0) >= 200]

    # Stratify by previously assigned production-extractor label
    prev = {r["accession_number"]: r.get("label") for r in
            (json.loads(l) for l in (DATA / "nt_classifications.jsonl").open(encoding="utf-8"))}

    by_label: dict[str, list[dict]] = {}
    for r in bodies:
        lbl = prev.get(r["accession_number"])
        if lbl not in ("accounting_issue", "other"):
            continue
        by_label.setdefault(lbl, []).append(r)

    n_per = 10
    sample = []
    for lbl in ("accounting_issue", "other"):
        rs = by_label.get(lbl, []).copy()
        random.shuffle(rs)
        sample.extend(rs[:n_per])
    print(f"Stratified sample: {len(sample)} (10 AI + 10 other)")

    load_portfolio_env()
    sys.path.insert(0, "D:/vscode/portfolio-coordination")
    from shared_utils.openrouter_client import OpenRouterClient
    client = OpenRouterClient(project="us_sec_form_nt_late_filing_xs")

    out = []
    total_usd = 0.0
    for i, r in enumerate(sample, 1):
        firm = r.get("company_name") or r.get("matched_title")
        tk = r.get("ticker")
        cik = r.get("cik")
        narrative = r["narrative"]
        redacted = redact(narrative, firm, tk, cik)

        prompt_orig = (f"{SYSTEM_PROMPT}\n\n---\n"
                       f"Filer: {tk} (CIK {cik})\nForm: {r.get('form_type')}\n"
                       f"Filing date: {r.get('date_filed')}\n"
                       f"Narrative (Part III):\n\"\"\"\n{narrative}\n\"\"\"\n"
                       f"Return strict JSON only.")
        prompt_redact = (f"{SYSTEM_PROMPT}\n\n---\n"
                         f"Filer: [REDACT_TICKER] (CIK [REDACT_CIK])\n"
                         f"Form: {r.get('form_type')}\n"
                         f"Filing date: [REDACT_DATE]\n"
                         f"Narrative (Part III):\n\"\"\"\n{redacted}\n\"\"\"\n"
                         f"Return strict JSON only.")

        try:
            resp_o = client.complete(model="openai/gpt-4o-mini", prompt=prompt_orig,
                                      max_tokens=300, temperature=0.0)
            resp_r = client.complete(model="openai/gpt-4o-mini", prompt=prompt_redact,
                                      max_tokens=300, temperature=0.0)
        except Exception as e:
            print(f"  call fail at {i}: {e}", file=sys.stderr)
            continue
        text_o = resp_o["choices"][0]["message"]["content"]
        text_r = resp_r["choices"][0]["message"]["content"]
        cost = (float(resp_o.get("usage", {}).get("cost", 0) or 0)
                + float(resp_r.get("usage", {}).get("cost", 0) or 0))
        total_usd += cost

        lab_o = parse_response(text_o)
        lab_r = parse_response(text_r)
        agree = (lab_o and lab_r and lab_o["label"] == lab_r["label"])
        out.append({
            "accession_number": r["accession_number"],
            "ticker": tk, "form": r.get("form_type"),
            "production_label": prev.get(r["accession_number"]),
            "rerun_original": lab_o["label"] if lab_o else None,
            "rerun_redacted": lab_r["label"] if lab_r else None,
            "agree": bool(agree),
            "cost_usd": round(cost, 5),
        })
        print(f"  [{i:>2}/{len(sample)}] orig={lab_o['label'] if lab_o else 'fail'}  redact={lab_r['label'] if lab_r else 'fail'}  agree={agree}  ${total_usd:.4f}")

    (DATA / "contamination_audit.jsonl").write_text(
        "\n".join(json.dumps(r) for r in out), encoding="utf-8")

    agree_n = sum(1 for r in out if r["agree"])
    REPORTS.mkdir(parents=True, exist_ok=True)
    summary = {
        "n_sample": len(out),
        "agreement_orig_vs_redacted": agree_n,
        "agreement_pct": round(100 * agree_n / max(1, len(out)), 2),
        "total_cost_usd": round(total_usd, 4),
    }
    (REPORTS / "contamination-audit.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nAgreement after redaction: {agree_n}/{len(out)} = {summary['agreement_pct']}%")
    print(f"Total LLM cost: ${total_usd:.4f}")
    print(f"Report: {REPORTS / 'contamination-audit.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
