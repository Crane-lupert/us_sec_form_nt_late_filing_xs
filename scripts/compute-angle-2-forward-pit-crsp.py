"""Phase 3 / Step 1 sub-deliverable — Angle 2 forward CAR under PIT anchor,
CRSP returns layer (OOS coverage extension).

OOS PIT (compute-angle-2-forward-pit.py + _oos input) suffers from the
yfinance cache truncating around 2026-04 for many OOS tickers; the forward
CAR cardinality collapses (912 -> 3 with car_fwd_30d) which makes the
monthly long-short basket re-test impossible. This script replaces the
yfinance equity feed with the CRSP OOS daily file
(data/crsp_returns_oos.parquet) which extends through 2025-12 (and includes
the early 2026 days for the in-sample bridge). SPY market subtractor is
still taken from the yfinance cache for SPY only (extends to 2026-06).

Inputs:
    --classifications  data/nt_classifications_oos.jsonl
    --pit              data/form_nt_pit_oos.jsonl
    --crsp             data/crsp_returns_oos.parquet
    --output           data/angle_2_forward_pit_oos_crsp.jsonl

Sort-stable on (cik, anchor_date, accession_number).

Usage:
    python scripts/compute-angle-2-forward-pit-crsp.py
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SPY_CACHE = REPO_ROOT / "data" / "yfinance_cache" / "SPY.jsonl"


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _spy_return_series() -> dict[str, float]:
    rows = sorted(
        (json.loads(l) for l in SPY_CACHE.open(encoding="utf-8")),
        key=lambda r: r["date"],
    )
    out: dict[str, float] = {}
    prev: float | None = None
    for r in rows:
        c = r["close"]
        if prev is not None and prev > 0:
            out[r["date"]] = c / prev - 1.0
        prev = c
    return out


def _forward_car(firm_ret: list[tuple[str, float]],
                 mkt: dict[str, float],
                 anchor_date: str,
                 horizon: int) -> float | None:
    t0 = None
    for i, (d, _) in enumerate(firm_ret):
        if d >= anchor_date:
            t0 = i
            break
    if t0 is None:
        return None
    end_idx = t0 + horizon
    if end_idx >= len(firm_ret):
        return None
    car = 0.0
    n = 0
    for i in range(t0 + 1, end_idx + 1):
        d, fr = firm_ret[i]
        mr = mkt.get(d)
        if mr is None:
            continue
        car += fr - mr
        n += 1
    return car if n > 0 else None


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--classifications", default=str(REPO_ROOT / "data" / "nt_classifications_oos.jsonl"))
    p.add_argument("--pit", default=str(REPO_ROOT / "data" / "form_nt_pit_oos.jsonl"))
    p.add_argument("--crsp", default=str(REPO_ROOT / "data" / "crsp_returns_oos.parquet"))
    p.add_argument("--restatements", default=str(REPO_ROOT / "data" / "restatement_events_oos.jsonl"))
    p.add_argument("--output", default=str(REPO_ROOT / "data" / "angle_2_forward_pit_oos_crsp.jsonl"))
    args = p.parse_args()

    cls_rows = {
        r["accession_number"]: r
        for r in (json.loads(l) for l in Path(args.classifications).open(encoding="utf-8"))
        if r.get("label") in ("accounting_issue", "unresolved_sec_comment", "other")
    }
    pit_rows = [json.loads(l) for l in Path(args.pit).open(encoding="utf-8")]
    print(f"PIT rows: {len(pit_rows)}  Classified: {len(cls_rows)}", flush=True)

    # Compute PIT anchor date per filing
    for r in pit_rows:
        d = _parse_date(r["acceptance_et_date"])
        if r["after_16et"]:
            d = d + timedelta(days=1)
        r["anchor_date"] = d.isoformat()

    # Load CRSP OOS returns
    import duckdb
    db = duckdb.connect(":memory:")
    df = db.execute(
        f"SELECT ticker, dlycaldt, dlyret FROM read_parquet('{args.crsp}') "
        f"WHERE dlyret IS NOT NULL ORDER BY ticker, dlycaldt"
    ).fetchdf()
    by_ticker: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for tk, dt, ret in zip(df["ticker"], df["dlycaldt"], df["dlyret"]):
        d_str = dt.strftime("%Y-%m-%d") if hasattr(dt, "strftime") else str(dt)[:10]
        by_ticker[tk].append((d_str, float(ret)))
    for tk in by_ticker:
        by_ticker[tk].sort(key=lambda r: r[0])
    print(f"CRSP tickers: {len(by_ticker)}", flush=True)

    spy = _spy_return_series()
    print(f"SPY market days: {len(spy)}", flush=True)

    # Restatement events index by CIK
    rst_by_cik: dict[str, list[date]] = defaultdict(list)
    for line in Path(args.restatements).open(encoding="utf-8"):
        rr = json.loads(line)
        try:
            rst_by_cik[rr["cik"].lstrip("0") or "0"].append(_parse_date(rr["filing_date"]))
        except (KeyError, ValueError):
            continue
    for k in rst_by_cik:
        rst_by_cik[k].sort()

    joined: list[dict] = []
    for pit in pit_rows:
        cls = cls_rows.get(pit["accession_number"])
        if not cls:
            continue
        ticker = pit.get("ticker") or cls.get("ticker")
        cik_norm = (pit.get("cik") or cls.get("cik")).lstrip("0") or "0"
        anchor = pit["anchor_date"]
        anchor_d = _parse_date(anchor)

        # Restatement check
        future_rst = [d for d in rst_by_cik.get(cik_norm, []) if d > anchor_d]
        first_rst = future_rst[0] if future_rst else None
        days_to_rst = (first_rst - anchor_d).days if first_rst else None

        firm_ret = by_ticker.get(ticker, [])
        car30 = _forward_car(firm_ret, spy, anchor, 30) if firm_ret else None
        car90 = _forward_car(firm_ret, spy, anchor, 90) if firm_ret else None

        row = {
            "accession_number": pit["accession_number"],
            "cik": pit.get("cik") or cls.get("cik"),
            "ticker": ticker,
            "form_type": pit.get("form_type") or cls.get("form_type"),
            "original_date_filed": pit.get("date_filed_original") or pit.get("original_date_filed") or pit.get("date_filed"),
            "anchor_date": anchor,
            "acceptance_et_date": pit["acceptance_et_date"],
            "after_16et": pit["after_16et"],
            "label": cls["label"],
            "first_restatement_after": first_rst.isoformat() if first_rst else None,
            "days_to_first_restatement": days_to_rst,
            "restated_within_14d": bool(first_rst and days_to_rst <= 14),
            "restated_within_30d": bool(first_rst and days_to_rst <= 30),
            "restated_within_90d": bool(first_rst and days_to_rst <= 90),
            "restated_within_180d": bool(first_rst and days_to_rst <= 180),
            "car_fwd_30d": car30,
            "car_fwd_90d": car90,
            # downstream consumer compatibility:
            "date_filed": anchor,
        }
        joined.append(row)

    joined.sort(key=lambda r: (r["cik"], r["anchor_date"], r["accession_number"]))
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for r in joined:
            f.write(json.dumps(r) + "\n")

    # Summary
    n_car30 = sum(1 for r in joined if r["car_fwd_30d"] is not None)
    n_car90 = sum(1 for r in joined if r["car_fwd_90d"] is not None)
    from collections import Counter
    label_dist = Counter(r["label"] for r in joined)
    print()
    print(f"Joined: {len(joined)}")
    print(f"  with car_fwd_30d: {n_car30}")
    print(f"  with car_fwd_90d: {n_car90}")
    print(f"  label distribution: {dict(label_dist)}")
    print(f"Output: {out_path}")

    # Rate-diff cells on CRSP-extended OOS
    import math
    def rate(rows, key, label):
        sub = [r for r in rows if r["label"] == label]
        n = len(sub)
        k = sum(1 for r in sub if r[key])
        return k, n
    print()
    print("=== Rate-diff cells (OOS PIT, CRSP-extended) ===")
    for H in (14, 30, 90, 180):
        k1, n1 = rate(joined, f"restated_within_{H}d", "accounting_issue")
        k2, n2 = rate(joined, f"restated_within_{H}d", "other")
        if n1 == 0 or n2 == 0:
            continue
        p1 = k1 / n1
        p2 = k2 / n2
        pp = (k1 + k2) / (n1 + n2)
        se = math.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2)) if 0 < pp < 1 else 0
        z = (p1 - p2) / se if se > 0 else 0
        print(f"  {H:>3}d: AI={p1*100:.2f}% ({k1}/{n1})  OT={p2*100:.2f}% ({k2}/{n2})  diff={(p1-p2)*100:+.2f}pp  z={z:+.3f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
