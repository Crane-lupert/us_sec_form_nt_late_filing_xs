"""Phase 0 step 6c-prep - Fetch restatement-class events per CIK.

For each distinct matched CIK, fetches SEC submissions API
(data.sec.gov/submissions/CIK{padded}.json) and extracts filings that
constitute restatement events:

  - 8-K with Item 4.02 (non-reliance on previously issued statements)
  - 8-K with Item 4.01 (auditor change, often linked to restatements)
  - 10-K/A and 10-Q/A (amendments to periodic reports)

Output JSONL: one row per restatement-class event with
  (cik, ticker, filing_date, accession_number, form, items, primary_form)

Used downstream by Angle 2 forward-signal join: for each NT filing,
detect whether a restatement-class event from same CIK followed within
{4-14d (SEC enforcement window), 30d, 90d}.

Resumable per-CIK; idempotent on (CIK, accession_number).

Usage:
    python scripts/fetch-restatement-events.py \\
        --input  data/form_nt_matched.jsonl \\
        --output data/restatement_events.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "us_sec_form_nt_late_filing_xs research fawkes4700@gmail.com"

# Restatement-class form types of interest:
AMENDMENT_FORMS = ("10-K/A", "10-Q/A", "20-F/A", "10-K/A AMEND", "10-Q/A AMEND")
EIGHT_K_FORMS = ("8-K", "8-K/A", "6-K", "6-K/A")
RESTATEMENT_ITEMS = ("4.02", "4.01")  # within 8-K body


def fetch_submissions(cik: str) -> dict | None:
    padded = cik.lstrip("0").zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{padded}.json"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError, OSError) as e:
        print(f"  CIK {cik}: {e}", file=sys.stderr)
        return None


def is_restatement_event(form: str, items: str) -> str | None:
    """Return event-class label if this filing is a restatement-class event."""
    form = (form or "").strip()
    items_str = (items or "").strip()
    if form in AMENDMENT_FORMS:
        return "amendment"
    if form.startswith("10-K") and form.endswith("/A"):
        return "amendment"
    if form.startswith("10-Q") and form.endswith("/A"):
        return "amendment"
    if form in EIGHT_K_FORMS or form.startswith("8-K"):
        if any(it in items_str for it in RESTATEMENT_ITEMS):
            return "8k_item_4_02" if "4.02" in items_str else "8k_item_4_01"
    return None


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", default=str(REPO_ROOT / "data" / "form_nt_matched.jsonl"))
    p.add_argument("--output", default=str(REPO_ROOT / "data" / "restatement_events.jsonl"))
    p.add_argument("--exchanges", default="NYSE,Nasdaq")
    p.add_argument("--sleep-sec", type=float, default=0.15)
    args = p.parse_args()

    rows = [json.loads(l) for l in Path(args.input).open(encoding="utf-8")]
    if args.exchanges:
        ex = set(args.exchanges.split(","))
        rows = [r for r in rows if r.get("exchange") in ex]
    ciks = sorted({r["cik"] for r in rows})
    print(f"Distinct CIKs to scan: {len(ciks)}", flush=True)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    done_ciks: set[str] = set()
    if out_path.exists():
        for line in out_path.open(encoding="utf-8"):
            try:
                done_ciks.add(json.loads(line)["cik"])
            except Exception:
                pass
    print(f"CIKs already processed: {len(done_ciks)}", flush=True)

    n_events = 0
    n_fail = 0
    with out_path.open("a", encoding="utf-8") as f:
        for i, cik in enumerate(ciks, 1):
            if cik in done_ciks:
                continue
            sub = fetch_submissions(cik)
            time.sleep(args.sleep_sec)
            if sub is None:
                n_fail += 1
                continue
            recent = sub.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            items = recent.get("items", [])
            dates = recent.get("filingDate", [])
            accs = recent.get("accessionNumber", [])
            tickers = sub.get("tickers") or [None]
            ticker = tickers[0] if tickers else None
            for j, form in enumerate(forms):
                item_str = items[j] if j < len(items) else ""
                label = is_restatement_event(form, item_str)
                if label is None:
                    continue
                f.write(json.dumps({
                    "cik": cik,
                    "ticker": ticker,
                    "form": form,
                    "items": item_str,
                    "filing_date": dates[j] if j < len(dates) else None,
                    "accession_number": accs[j] if j < len(accs) else None,
                    "event_class": label,
                }) + "\n")
                n_events += 1
            f.flush()
            if i % 50 == 0 or i == len(ciks):
                print(f"  [{i}/{len(ciks)}] events={n_events} fail={n_fail}", flush=True)

    print()
    print(f"DONE - {n_events} restatement-class events written, {n_fail} CIK fetches failed")
    print(f"Output: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
