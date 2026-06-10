"""Phase 0 step 5 — Angle 1 NT event-CAR replication of Bartov-K 2017.

Reads matched NT filings (data/form_nt_matched.jsonl, ticker resolved
column populated), fetches daily prices via yfinance for each unique
ticker over a window covering all of that ticker's filing dates ±60
trading days, and computes simple market-adjusted CAR per filing for:
    - 5-day event window [-2, +2]  (Bartov-K 2017 primary)
    - 3-day event window [-1, +1]  (robustness)
    - 60-day post-event drift [+1, +60]  (Bartov-K long-window)

Market proxy = SPY (auto-adjusted close).

Resumable per β2 lesson β2-3: per-ticker price JSONL cache at
data/yfinance_cache/{TICKER}.jsonl; idempotent re-runs skip cached
tickers.

Lock F compliance: per-filing rows sorted-stable on
(cik, date_filed, accession_number) before write.

Usage:
    python scripts/compute-angle-1-event-car.py \\
        --input  data/form_nt_matched.jsonl \\
        --output data/angle_1_car.jsonl \\
        --report reports/angle-1-summary.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import mean, pstdev
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = REPO_ROOT / "data" / "yfinance_cache"

EVENT_PRE = 5    # buffer trading days before filing date
EVENT_POST = 65  # buffer trading days after (covers 60d drift window)


def _load_filings(path: Path, exchange_filter: tuple[str, ...] | None) -> list[dict]:
    rows = [json.loads(l) for l in path.open(encoding="utf-8")]
    rows = [r for r in rows if r.get("ticker")]
    if exchange_filter:
        rows = [r for r in rows if r.get("exchange") in exchange_filter]
    return rows


def _trimmed_mean(vals: list[float], lo_pct: float, hi_pct: float) -> tuple[float, int]:
    if not vals:
        return 0.0, 0
    sv = sorted(vals)
    n = len(sv)
    lo = int(n * lo_pct / 100)
    hi = int(n * (100 - hi_pct) / 100)
    if hi <= lo:
        return mean(sv), n
    sub = sv[lo:hi]
    return mean(sub), len(sub)


def _ticker_window(filings_for_ticker: list[dict]) -> tuple[date, date]:
    dates = sorted(datetime.strptime(r["date_filed"], "%Y-%m-%d").date() for r in filings_for_ticker)
    start = dates[0] - timedelta(days=EVENT_PRE * 2)
    end = dates[-1] + timedelta(days=EVENT_POST * 2)
    return start, end


def _fetch_yf_prices(ticker: str, start: date, end: date) -> list[dict]:
    """Returns list of {date, close} sorted by date."""
    import yfinance as yf
    df = yf.download(
        ticker,
        start=start.isoformat(),
        end=(end + timedelta(days=1)).isoformat(),
        auto_adjust=True,
        progress=False,
        threads=False,
        actions=False,
    )
    if df.empty:
        return []
    # yfinance returns MultiIndex columns when single ticker; flatten:
    if hasattr(df.columns, "nlevels") and df.columns.nlevels > 1:
        df.columns = df.columns.get_level_values(0)
    if "Close" not in df.columns:
        return []
    out: list[dict] = []
    for ts, row in df["Close"].items():
        try:
            close = float(row)
        except (TypeError, ValueError):
            continue
        if close != close:  # NaN check
            continue
        out.append({"date": ts.date().isoformat(), "close": close})
    out.sort(key=lambda r: r["date"])
    return out


def _ensure_ticker_cache(ticker: str, start: date, end: date, sleep_sec: float) -> list[dict]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    safe_ticker = ticker.replace("/", "_").replace("\\", "_")
    cache_path = CACHE_DIR / f"{safe_ticker}.jsonl"
    if cache_path.exists() and cache_path.stat().st_size > 0:
        return [json.loads(l) for l in cache_path.open(encoding="utf-8")]
    try:
        rows = _fetch_yf_prices(ticker, start, end)
    except Exception as e:
        print(f"  yfinance error for {ticker}: {e}", file=sys.stderr)
        rows = []
    with cache_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    time.sleep(sleep_sec)
    return rows


def _build_return_series(price_rows: list[dict]) -> list[tuple[str, float]]:
    """Convert close prices to simple daily returns (today/yesterday - 1)."""
    out: list[tuple[str, float]] = []
    prev_close: float | None = None
    for r in price_rows:
        close = r["close"]
        if prev_close is not None and prev_close > 0:
            out.append((r["date"], close / prev_close - 1.0))
        prev_close = close
    return out


def _index_dates(returns: list[tuple[str, float]]) -> dict[str, int]:
    return {d: i for i, (d, _r) in enumerate(returns)}


def _compute_car(
    firm_returns: list[tuple[str, float]],
    market_returns: list[tuple[str, float]],
    filing_date: str,
    window_start: int,
    window_end: int,
) -> tuple[float | None, int]:
    """Market-adjusted CAR.

    For each trading day in the window, abnormal_return = firm_r - market_r.
    Sum across the window. filing_date used to anchor T=0.

    Window indices are relative to filing date:
        - first firm trading day >= filing_date defines T=0 (event day)
        - window_start = -2 means 2 trading days before T=0
        - window_end = +2 means 2 trading days after T=0
    """
    firm_idx = _index_dates(firm_returns)
    # Locate T=0 = first firm trading day on or after filing_date
    sorted_firm_dates = [d for d, _ in firm_returns]
    t0 = None
    for d in sorted_firm_dates:
        if d >= filing_date:
            t0 = d
            break
    if t0 is None:
        return None, 0
    t0_idx = firm_idx[t0]
    start_idx = t0_idx + window_start
    end_idx = t0_idx + window_end
    if start_idx < 0 or end_idx >= len(firm_returns):
        return None, 0
    market_lookup = dict(market_returns)
    car = 0.0
    n_days = 0
    for i in range(start_idx, end_idx + 1):
        d, fr = firm_returns[i]
        mr = market_lookup.get(d)
        if mr is None:
            continue
        car += (fr - mr)
        n_days += 1
    return car, n_days


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", default=str(REPO_ROOT / "data" / "form_nt_matched.jsonl"))
    p.add_argument("--output", default=str(REPO_ROOT / "data" / "angle_1_car.jsonl"))
    p.add_argument("--report", default=str(REPO_ROOT / "reports" / "angle-1-summary.json"))
    p.add_argument("--sleep-sec", type=float, default=0.30)
    p.add_argument("--max-tickers", type=int, default=-1, help="-1 = all")
    p.add_argument(
        "--exchanges",
        default="NYSE,Nasdaq",
        help="Comma-separated exchange filter (Bartov-K comparable = NYSE,Nasdaq). Pass '' to disable.",
    )
    args = p.parse_args()

    exch_filter: tuple[str, ...] | None = None
    if args.exchanges:
        exch_filter = tuple(args.exchanges.split(","))
    rows = _load_filings(Path(args.input), exch_filter)
    print(f"Loaded {len(rows)} matched filings (exchange filter={exch_filter})", flush=True)

    # Group by ticker
    by_ticker: dict[str, list[dict]] = {}
    for r in rows:
        by_ticker.setdefault(r["ticker"], []).append(r)
    tickers = sorted(by_ticker)
    print(f"Distinct tickers: {len(tickers)}", flush=True)
    if args.max_tickers > 0:
        tickers = tickers[:args.max_tickers]
        print(f"  capped to first {len(tickers)} (smoke mode)", flush=True)

    # SPY market proxy — fetch full Phase-0 window once
    all_filing_dates = sorted(r["date_filed"] for r in rows)
    spy_start = (datetime.strptime(all_filing_dates[0], "%Y-%m-%d").date()
                 - timedelta(days=EVENT_PRE * 2))
    spy_end = (datetime.strptime(all_filing_dates[-1], "%Y-%m-%d").date()
               + timedelta(days=EVENT_POST * 2))
    print(f"Fetching SPY {spy_start} → {spy_end}", flush=True)
    spy_prices = _ensure_ticker_cache("SPY", spy_start, spy_end, args.sleep_sec)
    spy_returns = _build_return_series(spy_prices)
    print(f"  SPY return days: {len(spy_returns)}", flush=True)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []

    n_skip_no_price = 0
    n_skip_no_window = 0

    for ti, ticker in enumerate(tickers, 1):
        tfilings = by_ticker[ticker]
        tw_start, tw_end = _ticker_window(tfilings)
        price_rows = _ensure_ticker_cache(ticker, tw_start, tw_end, args.sleep_sec)
        if not price_rows:
            n_skip_no_price += len(tfilings)
            if ti % 50 == 0 or ti == len(tickers):
                print(f"[{ti}/{len(tickers)}] {ticker}: no prices (cum results={len(results)}, skip_no_price={n_skip_no_price})", flush=True)
            continue
        firm_returns = _build_return_series(price_rows)
        for r in tfilings:
            filing_date = r["date_filed"]
            car5, n5 = _compute_car(firm_returns, spy_returns, filing_date, -2, +2)
            car3, n3 = _compute_car(firm_returns, spy_returns, filing_date, -1, +1)
            car_drift60, n60 = _compute_car(firm_returns, spy_returns, filing_date, +1, +60)
            if car5 is None and car3 is None:
                n_skip_no_window += 1
                continue
            results.append({
                "cik": r["cik"],
                "ticker": ticker,
                "accession_number": r["accession_number"],
                "form_type": r["form_type"],
                "date_filed": filing_date,
                "year": r["year"],
                "car_5d": car5,
                "car_5d_n": n5,
                "car_3d": car3,
                "car_3d_n": n3,
                "car_drift60d": car_drift60,
                "car_drift60d_n": n60,
            })
        if ti % 50 == 0 or ti == len(tickers):
            print(f"[{ti}/{len(tickers)}] {ticker}: cum results={len(results)} skip(no_price={n_skip_no_price}, no_window={n_skip_no_window})", flush=True)

    # Sort-stable on (cik, date_filed, accession_number)
    results.sort(key=lambda r: (r["cik"], r["date_filed"], r["accession_number"]))
    with out_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    # Summary by form-type (raw + 5%/95% trimmed)
    def summary(rows_in: list[dict], col: str) -> dict:
        vals = [r[col] for r in rows_in if r[col] is not None]
        if not vals:
            return {"n": 0}
        m = mean(vals)
        s = pstdev(vals) if len(vals) > 1 else 0.0
        t = (m / (s / len(vals) ** 0.5)) if s > 0 else 0.0
        tm5, n_trim = _trimmed_mean(vals, 5.0, 5.0)
        return {
            "n": len(vals),
            "mean_pct": round(100 * m, 4),
            "stdev_pct": round(100 * s, 4),
            "t_stat": round(t, 3),
            "trimmed_5_95_pct": round(100 * tm5, 4),
            "trimmed_n": n_trim,
        }

    out_summary = {
        "input": str(Path(args.input)),
        "n_filings_total_matched": len(rows),
        "n_results": len(results),
        "skip_no_price": n_skip_no_price,
        "skip_no_window": n_skip_no_window,
        "bartov_k_2017_published": {
            "NT 10-Q 5-day CAR": -2.93,
            "NT 10-K 5-day CAR": -1.96,
        },
        "by_form_type": {},
    }
    for ft in sorted({r["form_type"] for r in results}):
        ft_rows = [r for r in results if r["form_type"] == ft]
        out_summary["by_form_type"][ft] = {
            "n_filings": len(ft_rows),
            "car_5d": summary(ft_rows, "car_5d"),
            "car_3d": summary(ft_rows, "car_3d"),
            "car_drift60d": summary(ft_rows, "car_drift60d"),
        }

    rep_path = Path(args.report)
    rep_path.parent.mkdir(parents=True, exist_ok=True)
    with rep_path.open("w", encoding="utf-8") as f:
        json.dump(out_summary, f, indent=2)

    print()
    print(json.dumps(out_summary["by_form_type"], indent=2))
    print(f"\nResults: {out_path}")
    print(f"Report:  {rep_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
