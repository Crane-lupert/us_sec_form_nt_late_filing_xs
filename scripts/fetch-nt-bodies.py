"""Phase 0 step 6a — Fetch Form NT Part III narrative text from SEC EDGAR.

For each matched NT filing, fetches the primary document URL via the
EDGAR submission index page, downloads it, strips HTML, extracts the
"PART III NARRATIVE" section, and caches as JSONL.

Cached output is keyed by accession_number — resumable.

Lock F compliance: input rows already sort-stable; output preserves
input order modulo skipped filings.

Usage:
    python scripts/fetch-nt-bodies.py \\
        --input  data/form_nt_matched.jsonl \\
        --output data/nt_bodies.jsonl \\
        --exchanges NYSE,Nasdaq \\
        --max-filings 100        # dry-run; -1 = all
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "us_sec_form_nt_late_filing_xs research fawkes4700@gmail.com"


def fetch_url(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def find_primary_doc_url(cik: str, accession: str) -> str | None:
    acc_no_dashes = accession.replace("-", "")
    index_url = (
        f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0') or '0'}"
        f"/{acc_no_dashes}/{accession}-index.htm"
    )
    try:
        html = fetch_url(index_url)
    except Exception as e:
        print(f"  index fetch fail {accession}: {e}", file=sys.stderr)
        return None
    # Anchor href in the document table; primary doc is typically the first
    # .htm in /Archives/edgar/data/{cik}/{acc_no_dashes}/ that does NOT
    # contain "-index.htm" and is not a generic /index.htm.
    hrefs = re.findall(r'href="(/Archives/edgar/data/[^"]+\.(?:htm|html|txt))"', html)
    for h in hrefs:
        if "-index.htm" in h:
            continue
        # Prefer primary HTML doc (often dXXXXdntXXk.htm or nt10q.htm)
        if h.lower().endswith((".htm", ".html")):
            return "https://www.sec.gov" + h
    # Fallback: full-submission .txt
    for h in hrefs:
        if h.endswith(".txt"):
            return "https://www.sec.gov" + h
    return None


def extract_part_iii(html: str) -> str:
    """Strip HTML, find PART III NARRATIVE section, return text."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = re.sub(r"&#\d+;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    upper = text.upper()
    # Find PART III NARRATIVE marker (preferred) or PART III
    candidates = [
        ("PART III NARRATIVE", len("PART III NARRATIVE")),
        ("PART III", len("PART III")),
    ]
    start = -1
    for marker, mlen in candidates:
        i = upper.find(marker)
        if i >= 0:
            start = i + mlen
            break
    if start < 0:
        return ""
    # End at PART IV or "SIGNATURE" or end-of-doc
    j_iv = upper.find("PART IV", start)
    j_sig = upper.find("SIGNATURE", start)
    candidates_end = [c for c in (j_iv, j_sig) if c > start]
    end = min(candidates_end) if candidates_end else min(start + 5000, len(text))
    return text[start:end].strip()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", default=str(REPO_ROOT / "data" / "form_nt_matched.jsonl"))
    p.add_argument("--output", default=str(REPO_ROOT / "data" / "nt_bodies.jsonl"))
    p.add_argument("--exchanges", default="NYSE,Nasdaq")
    p.add_argument("--max-filings", type=int, default=-1, help="-1 = all")
    p.add_argument("--sleep-sec", type=float, default=0.15)
    args = p.parse_args()

    exch = set(args.exchanges.split(",")) if args.exchanges else None
    rows = [json.loads(l) for l in Path(args.input).open(encoding="utf-8")]
    rows = [r for r in rows if r.get("ticker")]
    if exch:
        rows = [r for r in rows if r.get("exchange") in exch]
    print(f"Filings in scope: {len(rows)} (exchange filter={exch})", flush=True)
    if args.max_filings > 0:
        rows = rows[:args.max_filings]
        print(f"  capped to first {len(rows)}", flush=True)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Idempotency: load already-cached accession numbers
    done: set[str] = set()
    if out_path.exists():
        for line in out_path.open(encoding="utf-8"):
            try:
                done.add(json.loads(line)["accession_number"])
            except Exception:
                pass
    print(f"Already cached: {len(done)}", flush=True)

    n_fetched = 0
    n_skipped_cached = 0
    n_no_primary = 0
    n_no_narrative = 0
    with out_path.open("a", encoding="utf-8") as f:
        for i, r in enumerate(rows, 1):
            acc = r["accession_number"]
            if acc in done:
                n_skipped_cached += 1
                continue
            url = find_primary_doc_url(r["cik"], acc)
            if not url:
                n_no_primary += 1
                f.write(json.dumps({
                    "accession_number": acc, "cik": r["cik"],
                    "form_type": r["form_type"], "date_filed": r["date_filed"],
                    "ticker": r["ticker"],
                    "narrative": "", "narrative_len": 0,
                    "fetch_error": "no_primary_doc",
                }) + "\n")
                f.flush()
                time.sleep(args.sleep_sec)
                continue
            time.sleep(args.sleep_sec)
            try:
                doc_html = fetch_url(url)
            except Exception as e:
                f.write(json.dumps({
                    "accession_number": acc, "cik": r["cik"],
                    "form_type": r["form_type"], "date_filed": r["date_filed"],
                    "ticker": r["ticker"],
                    "narrative": "", "narrative_len": 0,
                    "fetch_error": f"doc_fetch: {e}",
                }) + "\n")
                f.flush()
                time.sleep(args.sleep_sec)
                continue
            narrative = extract_part_iii(doc_html)
            if not narrative:
                n_no_narrative += 1
            f.write(json.dumps({
                "accession_number": acc, "cik": r["cik"],
                "form_type": r["form_type"], "date_filed": r["date_filed"],
                "ticker": r["ticker"],
                "primary_doc_url": url,
                "narrative": narrative,
                "narrative_len": len(narrative),
            }, ensure_ascii=False) + "\n")
            f.flush()
            n_fetched += 1
            time.sleep(args.sleep_sec)
            if i % 50 == 0 or i == len(rows):
                print(f"  [{i}/{len(rows)}] fetched={n_fetched} skipped_cached={n_skipped_cached} no_primary={n_no_primary} no_narrative={n_no_narrative}", flush=True)

    print()
    print(f"DONE - fetched {n_fetched}, skipped (cached) {n_skipped_cached}, no_primary {n_no_primary}, no_narrative {n_no_narrative}")
    print(f"Output: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
