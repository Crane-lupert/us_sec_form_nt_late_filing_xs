"""Phase 1 step 2 - Pull CRSP-historical daily returns (with delret) for the
NYSE+Nasdaq NT-filer cohort, via WRDS local dump (Rule 6).

Reads E:/wrds-data-courier/output/dump/crsp_a_stock.dsf_v2.csv.gz
(4.4 GB, ~110M rows) via DuckDB push-down predicate, filters to:

  - ticker IN ( our 1,106 matched tickers from form_nt_matched.jsonl )
  - dlycaldt BETWEEN 2013-01-01 AND 2025-12-31  (covers event windows)

Output: data/crsp_returns.parquet with columns
  (permno, ticker, dlycaldt, dlyret, dlydelflg, primaryexch, dlyprc)

Critical Phase 1 difference vs Phase 0 yfinance:
  - dlyret includes CRSP-style delisting return (delret) on delist day
  - delisted firms whose ticker is gone from SEC current snapshot ARE
    represented (CRSP history is permno-keyed, not ticker-keyed)
  - Survivorship-recovery bias mitigated

Lock F clean — single deterministic query, sort-stable on
(permno, dlycaldt).

Usage:
    python scripts/fetch-crsp-returns-for-nt-cohort.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DSF_PATH = "E:/wrds-data-courier/output/dump/crsp_a_stock.dsf_v2.csv.gz"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", default=str(REPO_ROOT / "data" / "form_nt_matched.jsonl"))
    p.add_argument("--output", default=str(REPO_ROOT / "data" / "crsp_returns.parquet"))
    p.add_argument("--exchanges", default="NYSE,Nasdaq")
    p.add_argument("--start-date", default="2013-01-01")
    p.add_argument("--end-date", default="2025-12-31")
    args = p.parse_args()

    exch = set(args.exchanges.split(","))
    rows = [json.loads(l) for l in Path(args.input).open(encoding="utf-8")]
    rows = [r for r in rows if r.get("exchange") in exch and r.get("ticker")]
    tickers = sorted({r["ticker"] for r in rows})
    print(f"Tickers in scope: {len(tickers)}", flush=True)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists():
        print(f"Output already exists; delete to re-fetch: {out_path}")
        return 0

    import duckdb
    db = duckdb.connect(":memory:")

    # Push-down predicate: DuckDB pre-filters the CSV scan via the WHERE
    # clause. Ticker list passed as a parameter via VALUES.
    print("Building DuckDB view over CRSP dsf_v2 (one scan)...", flush=True)
    t0 = time.time()

    # Use prepared statement with parameter list
    placeholder_list = ",".join(["?"] * len(tickers))
    sql = f"""
        COPY (
            SELECT
                permno,
                ticker,
                dlycaldt,
                dlyret,
                dlydelflg,
                primaryexch,
                dlyprc
            FROM read_csv_auto('{DSF_PATH}', all_varchar=false, ignore_errors=false, sample_size=10000)
            WHERE ticker IN ({placeholder_list})
              AND dlycaldt >= ?
              AND dlycaldt <= ?
            ORDER BY permno, dlycaldt
        )
        TO '{out_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """
    params = list(tickers) + [args.start_date, args.end_date]
    db.execute(sql, params)
    elapsed = time.time() - t0
    print(f"Done in {elapsed:.1f}s", flush=True)

    # Quick stats
    df = db.execute(f"SELECT COUNT(*) AS n, COUNT(DISTINCT ticker) AS n_tickers, COUNT(DISTINCT permno) AS n_permnos FROM read_parquet('{out_path.as_posix()}')").fetchdf()
    print(df)
    print(f"Output: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
