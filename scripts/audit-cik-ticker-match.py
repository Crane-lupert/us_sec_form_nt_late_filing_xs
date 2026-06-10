"""Phase 0 step 4 — CIK → ticker match audit (V5-11(a) gate).

Joins NT filings (from `data/form_nt_index.jsonl`) to SEC's master
company tickers JSON (`https://www.sec.gov/files/company_tickers.json`)
and computes the share of distinct NT-filing CIKs that resolve to an
active US-listed ticker.

V5-11(a) gate (per launch SPEC):
    PASS      ≥ 90%
    BORDERLINE 63 – 89.9 %
    KILL      < 63%

The SEC tickers file is a *current-as-of-fetch* snapshot, so historical
delisted firms (frequent in NT 10-K population — distressed filers)
will NOT match. The 90% bar is therefore a high bar.

Sort-stable on (cik, date_filed, accession_number) preserved from input.

Usage:
    python scripts/audit-cik-ticker-match.py \\
        --input data/form_nt_index.jsonl \\
        --output reports/cik-match-summary.json
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "us_sec_form_nt_late_filing_xs research fawkes4700@gmail.com"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
TICKERS_EXCHANGE_URL = "https://www.sec.gov/files/company_tickers_exchange.json"


def fetch_tickers() -> dict[str, dict]:
    """Combine the two SEC tickers JSONs so we get (ticker + exchange).

    company_tickers.json:           {idx: {cik_str, ticker, title}}
    company_tickers_exchange.json:  {fields, data: [[cik, name, ticker, exchange]]}

    Exchange is the additional field — values {Nasdaq, NYSE, OTC, CBOE, None}.
    Used to filter for Bartov-K 2017 comparable cohort (NYSE/Nasdaq/AMEX).
    """
    req = urllib.request.Request(TICKERS_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = json.loads(resp.read().decode("utf-8"))
    by_cik: dict[str, dict] = {}
    for row in raw.values():
        cik = str(row["cik_str"]).lstrip("0") or "0"
        by_cik[cik] = {"ticker": row["ticker"], "title": row["title"], "exchange": None}
    # Layer in exchange info
    try:
        req2 = urllib.request.Request(TICKERS_EXCHANGE_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req2, timeout=60) as resp:
            exc = json.loads(resp.read().decode("utf-8"))
        fields = exc["fields"]
        i_cik = fields.index("cik")
        i_exch = fields.index("exchange")
        for row in exc["data"]:
            cik = str(row[i_cik]).lstrip("0") or "0"
            if cik in by_cik:
                by_cik[cik]["exchange"] = row[i_exch]
    except Exception as e:
        print(f"WARNING: cannot fetch {TICKERS_EXCHANGE_URL}: {e}", file=sys.stderr)
    return by_cik


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", default=str(REPO_ROOT / "data" / "form_nt_index.jsonl"))
    p.add_argument(
        "--output",
        default=str(REPO_ROOT / "reports" / "cik-match-summary.json"),
    )
    p.add_argument(
        "--matched-output",
        default=str(REPO_ROOT / "data" / "form_nt_matched.jsonl"),
        help="Per-filing JSONL with ticker resolution column",
    )
    args = p.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"ERROR: {in_path} not found — run fetch-form-nt-bulk.py first", file=sys.stderr)
        return 1

    print(f"Loading NT index: {in_path}")
    nt_rows = [json.loads(l) for l in in_path.open(encoding="utf-8")]
    print(f"  rows: {len(nt_rows)}")

    print(f"Fetching SEC tickers: {TICKERS_URL}")
    tickers = fetch_tickers()
    print(f"  CIKs in tickers JSON: {len(tickers)}")

    # Per-filing resolution
    matched_rows = []
    matched_cik_set: set[str] = set()
    unmatched_cik_set: set[str] = set()

    for r in nt_rows:
        cik = r["cik"].lstrip("0") or "0"
        info = tickers.get(cik)
        if info:
            matched_cik_set.add(cik)
            matched_rows.append({
                **r,
                "ticker": info["ticker"],
                "matched_title": info["title"],
                "exchange": info.get("exchange"),
            })
        else:
            unmatched_cik_set.add(cik)
            matched_rows.append({
                **r,
                "ticker": None,
                "matched_title": None,
                "exchange": None,
            })

    n_filings = len(nt_rows)
    n_matched_filings = sum(1 for r in matched_rows if r["ticker"])
    n_distinct_cik = len(matched_cik_set | unmatched_cik_set)
    n_matched_cik = len(matched_cik_set)

    # Per-form-type rates
    by_form_filings: Counter = Counter()
    by_form_matched_filings: Counter = Counter()
    for r in matched_rows:
        ft = r["form_type"]
        by_form_filings[ft] += 1
        if r["ticker"]:
            by_form_matched_filings[ft] += 1

    # Per-exchange breakdown for Bartov-K-comparable cohort sizing
    exchange_counter: Counter = Counter()
    bartov_k_ciks: set[str] = set()  # NYSE + Nasdaq matched CIKs
    bartov_k_filings = 0
    for r in matched_rows:
        if not r["ticker"]:
            continue
        ex = r["exchange"] or "Unknown"
        exchange_counter[ex] += 1
        if ex in ("NYSE", "Nasdaq"):
            bartov_k_ciks.add(r["cik"].lstrip("0") or "0")
            bartov_k_filings += 1

    summary = {
        "input_path": str(in_path),
        "n_filings_total": n_filings,
        "n_filings_matched": n_matched_filings,
        "filing_level_match_pct": round(100 * n_matched_filings / max(n_filings, 1), 2),
        "n_distinct_cik": n_distinct_cik,
        "n_distinct_cik_matched": n_matched_cik,
        "cik_level_match_pct": round(100 * n_matched_cik / max(n_distinct_cik, 1), 2),
        "by_form_type": {
            ft: {
                "n": by_form_filings[ft],
                "n_matched": by_form_matched_filings[ft],
                "match_pct": round(
                    100 * by_form_matched_filings[ft] / max(by_form_filings[ft], 1), 2
                ),
            }
            for ft in sorted(by_form_filings)
        },
        "v5_11a_gate": {
            "pass_threshold_pct": 90.0,
            "borderline_min_pct": 63.0,
            "verdict_filing_level": (
                "PASS" if (100 * n_matched_filings / max(n_filings, 1)) >= 90
                else "BORDERLINE" if (100 * n_matched_filings / max(n_filings, 1)) >= 63
                else "KILL"
            ),
            "verdict_cik_level": (
                "PASS" if (100 * n_matched_cik / max(n_distinct_cik, 1)) >= 90
                else "BORDERLINE" if (100 * n_matched_cik / max(n_distinct_cik, 1)) >= 63
                else "KILL"
            ),
        },
        "bartov_k_comparable_cohort": {
            "exchange_filter": ["NYSE", "Nasdaq"],
            "n_filings": bartov_k_filings,
            "n_distinct_cik": len(bartov_k_ciks),
            "vs_bartov_k_2017_base_2115": round(100 * len(bartov_k_ciks) / 2115, 2),
        },
        "exchange_breakdown_of_matched": dict(exchange_counter),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    matched_out = Path(args.matched_output)
    matched_out.parent.mkdir(parents=True, exist_ok=True)
    with matched_out.open("w", encoding="utf-8") as f:
        for r in matched_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print()
    print(f"Filings matched: {n_matched_filings}/{n_filings} = {summary['filing_level_match_pct']}%")
    print(f"Distinct CIKs matched: {n_matched_cik}/{n_distinct_cik} = {summary['cik_level_match_pct']}%")
    print(f"V5-11(a) filing-level verdict: {summary['v5_11a_gate']['verdict_filing_level']}")
    print(f"V5-11(a) CIK-level verdict:    {summary['v5_11a_gate']['verdict_cik_level']}")
    print()
    print("Bartov-K-comparable cohort (NYSE + Nasdaq only):")
    print(f"  Filings: {bartov_k_filings}")
    print(f"  Distinct CIKs: {len(bartov_k_ciks)} ({summary['bartov_k_comparable_cohort']['vs_bartov_k_2017_base_2115']}% of Bartov-K 2,115 base)")
    print(f"  Exchange breakdown: {dict(exchange_counter)}")
    print(f"Summary: {out_path}")
    print(f"Per-filing matched: {matched_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
