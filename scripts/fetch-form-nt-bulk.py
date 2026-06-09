"""Phase 0 step 4 — EDGAR Form NT bulk pull (2014Q1 – 2024Q4).

Reads SEC EDGAR quarterly full-indices (`form.idx`) and filters for
Form NT 10-K and Form NT 10-Q rows. Writes JSONL to
`data/form_nt_index.jsonl` (one row per filing).

Endpoint: https://www.sec.gov/Archives/edgar/full-index/{YEAR}/QTR{N}/form.idx

Rate limit: SEC EDGAR allows 10 req/s with proper User-Agent. Script
uses 0.15s sleep between quarterly fetches (44 requests total ≈ 7s).

Lock F compliance: sort-stable on (cik, date_filed, accession_number)
before write. No nondeterministic dedup / aggregation patterns.

Usage:
    python scripts/fetch-form-nt-bulk.py \\
        --start-year 2014 --end-year 2024 \\
        --output data/form_nt_index.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"

# SEC required header — user contact for rate-limit compliance.
# (Hard-coded from CLAUDE.md user-email context; PROHIBITION #2 = API keys, not contact email.)
USER_AGENT = "us_sec_form_nt_late_filing_xs research fawkes4700@gmail.com"

NT_FORM_PREFIXES = ("NT 10-K", "NT 10-Q")  # captures NT 10-K, NT 10-K/A, NT 10-Q, NT 10-Q/A


def fetch_quarter_index(year: int, qtr: int) -> str:
    url = (
        f"https://www.sec.gov/Archives/edgar/full-index/"
        f"{year}/QTR{qtr}/form.idx"
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("latin-1")


def parse_form_idx(idx_text: str, year: int, qtr: int) -> list[dict]:
    """Parse SEC full-index form.idx fixed-width text.

    Header block ends with a row of dashes. Column positions are stable
    across quarters in the modern era:
        Form Type   (col 0)
        Company Name (col 12)
        CIK         (col 74)
        Date Filed  (col 86)
        File Name   (col 98)
    """
    lines = idx_text.splitlines()
    # Locate header separator row (all dashes)
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith("---"):
            start = i + 1
            break
    if start is None:
        raise ValueError(f"Cannot find dashes header in {year}Q{qtr} form.idx")

    # Column positions verified empirically across 2014Q1, 2018Q2, 2024Q3:
    #   form_type    cols  0- 17 (17 chars)
    #   company_name cols 17- 79 (62 chars)
    #   cik          cols 79- 91 (12 chars)
    #   date_filed   cols 91-103 (12 chars; "YYYY-MM-DD" + 2 pad)
    #   file_name    cols 103+   (variable)
    rows: list[dict] = []
    for ln in lines[start:]:
        if not ln.strip():
            continue
        form_type = ln[0:17].strip()
        if not any(form_type.startswith(p) for p in NT_FORM_PREFIXES):
            continue
        company = ln[17:79].strip()
        cik = ln[79:91].strip()
        date_filed = ln[91:103].strip()
        file_name = ln[103:].strip()
        accession = ""
        if file_name.endswith(".txt"):
            # File name pattern: edgar/data/<cik>/<accession>.txt
            accession = file_name.rsplit("/", 1)[-1].removesuffix(".txt")
        rows.append({
            "form_type": form_type,
            "company_name": company,
            "cik": cik,
            "date_filed": date_filed,
            "file_name": file_name,
            "accession_number": accession,
            "year": year,
            "quarter": qtr,
        })
    return rows


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--start-year", type=int, default=2014)
    p.add_argument("--end-year", type=int, default=2024)
    p.add_argument(
        "--output",
        default=str(DATA_DIR / "form_nt_index.jsonl"),
    )
    p.add_argument(
        "--sleep-sec",
        type=float,
        default=0.15,
        help="Sleep between SEC requests (default 0.15s; SEC limit is 10 req/s)",
    )
    args = p.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict] = []
    per_quarter_counts: list[tuple[int, int, int]] = []

    for year in range(args.start_year, args.end_year + 1):
        for qtr in (1, 2, 3, 4):
            try:
                idx_text = fetch_quarter_index(year, qtr)
            except Exception as e:
                print(f"FAIL {year}Q{qtr}: {e}", file=sys.stderr)
                per_quarter_counts.append((year, qtr, -1))
                time.sleep(args.sleep_sec)
                continue
            rows = parse_form_idx(idx_text, year, qtr)
            all_rows.extend(rows)
            per_quarter_counts.append((year, qtr, len(rows)))
            print(f"{year}Q{qtr}: {len(rows)} NT filings")
            time.sleep(args.sleep_sec)

    # Sort-stable on (cik, date_filed, accession_number) per Lock F.
    all_rows.sort(
        key=lambda r: (r["cik"], r["date_filed"], r["accession_number"])
    )

    with open(out_path, "w", encoding="utf-8") as f:
        for r in all_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Summary
    print()
    print(f"Total NT filings: {len(all_rows)}")
    print(f"Output: {out_path}")
    by_form: dict[str, int] = {}
    for r in all_rows:
        by_form[r["form_type"]] = by_form.get(r["form_type"], 0) + 1
    print("By form type:")
    for ft, n in sorted(by_form.items(), key=lambda kv: -kv[1]):
        print(f"  {ft}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
