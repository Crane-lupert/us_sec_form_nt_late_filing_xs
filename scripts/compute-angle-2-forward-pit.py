"""Phase 3 / Step 1 — Angle 2 forward CAR under PIT anchor.

Same logic as compute-angle-2-forward-signal.py, but the T=0 anchor is the
SEC acceptance timestamp in ET (not the EDGAR date_filed):

  - filings accepted before 16:00 ET     -> anchor = acceptance_et_date
  - filings accepted at/after 16:00 ET   -> anchor = acceptance_et_date + 1 day
                                             (next trading day resolved
                                              via the firm return series)

Inputs:
    --classifications  data/nt_classifications.jsonl     (in-sample)
                       data/nt_classifications_oos.jsonl (oos)
    --pit              data/form_nt_pit.jsonl (or _oos)

Output:  data/angle_2_forward_pit.jsonl (or _oos.jsonl)
   - keeps original `date_filed` in `original_date_filed`
   - overwrites `date_filed` with the PIT anchor so the downstream
     compute-net-sharpe-strategy-d.py consumes the PIT-correct date.

Lock F sort-stable on (cik, date_filed, accession_number).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import mean, pstdev

REPO_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = REPO_ROOT / "data" / "yfinance_cache"


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _winsorize_t(vals: list[float], lo_pct: float = 1.0, hi_pct: float = 1.0) -> dict:
    sv = sorted(v for v in vals if v is not None)
    n = len(sv)
    if n == 0:
        return {"n": 0, "mean_pct": None, "t_stat": None}
    a = int(n * lo_pct / 100)
    b = max(int(n * (100 - hi_pct) / 100) - 1, a)
    lo_val = sv[a]
    hi_val = sv[b]
    w = [min(max(v, lo_val), hi_val) for v in sv]
    m = mean(w)
    s = pstdev(w) if len(w) > 1 else 0.0
    t = m / (s / (len(w) ** 0.5)) if s > 0 else 0.0
    return {"n": len(w), "mean_pct": round(100 * m, 4), "stdev_pct": round(100 * s, 4),
            "t_stat": round(t, 3)}


def _read_price_cache(ticker: str) -> list[dict]:
    safe = ticker.replace("/", "_")
    p = CACHE_DIR / f"{safe}.jsonl"
    if not p.exists() or p.stat().st_size == 0:
        return []
    return [json.loads(l) for l in p.open(encoding="utf-8")]


def _return_series(prices: list[dict]) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    prev: float | None = None
    for r in prices:
        c = r["close"]
        if prev is not None and prev > 0:
            out.append((r["date"], c / prev - 1.0))
        prev = c
    return out


def _forward_car(firm_ret: list[tuple[str, float]], mkt: dict[str, float],
                 anchor_date: str, end_days: int) -> float | None:
    t0_idx = None
    for i, (d, _) in enumerate(firm_ret):
        if d >= anchor_date:
            t0_idx = i
            break
    if t0_idx is None:
        return None
    end_idx = t0_idx + end_days
    if end_idx >= len(firm_ret):
        return None
    car = 0.0
    n_days = 0
    for i in range(t0_idx + 1, end_idx + 1):
        d, fr = firm_ret[i]
        mr = mkt.get(d)
        if mr is None:
            continue
        car += fr - mr
        n_days += 1
    return car if n_days > 0 else None


def _pit_anchor(rec: dict) -> str | None:
    """Compute PIT anchor date.

    if after_16et True  -> acceptance_et_date + 1 calendar day
    if after_16et False -> acceptance_et_date
    if no acceptance    -> None (caller should skip / fallback)
    """
    if rec.get("acceptance_et_date") is None:
        return None
    et = _parse_date(rec["acceptance_et_date"])
    if rec.get("after_16et"):
        et = et + timedelta(days=1)
    return et.isoformat()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--classifications", required=True)
    p.add_argument("--pit", required=True)
    p.add_argument("--restatements", default=str(REPO_ROOT / "data" / "restatement_events.jsonl"))
    p.add_argument("--output", required=True)
    p.add_argument("--report", required=True)
    p.add_argument("--windows", default="14,30,90,180")
    args = p.parse_args()

    cls_path = Path(args.classifications)
    pit_path = Path(args.pit)
    rst_path = Path(args.restatements)
    for label, q in (("classifications", cls_path), ("pit", pit_path), ("restatements", rst_path)):
        if not q.exists():
            print(f"ERROR: {label} {q} not found", file=sys.stderr)
            return 1

    cls_rows = [json.loads(l) for l in cls_path.open(encoding="utf-8") if l.strip()]
    cls_rows = [r for r in cls_rows if r.get("label") in ("accounting_issue", "unresolved_sec_comment", "other")]
    print(f"Classified rows: {len(cls_rows)}", flush=True)

    pit_rows = [json.loads(l) for l in pit_path.open(encoding="utf-8") if l.strip()]
    pit_idx: dict[str, dict] = {r["accession_number"]: r for r in pit_rows}
    print(f"PIT rows: {len(pit_rows)}", flush=True)

    rst_rows = [json.loads(l) for l in rst_path.open(encoding="utf-8") if l.strip()]
    print(f"Restatement-event rows: {len(rst_rows)}", flush=True)

    rst_by_cik: dict[str, list[date]] = defaultdict(list)
    for r in rst_rows:
        if not r.get("filing_date"):
            continue
        try:
            rst_by_cik[r["cik"].lstrip("0") or "0"].append(_parse_date(r["filing_date"]))
        except ValueError:
            continue
    for k in rst_by_cik:
        rst_by_cik[k].sort()

    windows_days = [int(w) for w in args.windows.split(",")]

    spy = _read_price_cache("SPY")
    spy_ret = dict(_return_series(spy)) if spy else {}

    joined: list[dict] = []
    by_ticker_cls: dict[str, list[dict]] = defaultdict(list)
    n_no_pit = 0
    n_pit_indeterminate = 0
    for r in cls_rows:
        by_ticker_cls[r["ticker"]].append(r)
    for ticker, tfilings in by_ticker_cls.items():
        prices = _read_price_cache(ticker)
        firm_ret = _return_series(prices) if prices else []
        for r in tfilings:
            pit_rec = pit_idx.get(r["accession_number"])
            if pit_rec is None:
                n_no_pit += 1
                continue
            anchor = _pit_anchor(pit_rec)
            if anchor is None:
                n_pit_indeterminate += 1
                continue
            nt_d = _parse_date(r["date_filed"])
            cik_norm = r["cik"].lstrip("0") or "0"
            rst_dates = rst_by_cik.get(cik_norm, [])
            future = [d for d in rst_dates if d > nt_d]
            first_rst = future[0] if future else None
            row_out = {
                "accession_number": r["accession_number"],
                "cik": r["cik"],
                "ticker": ticker,
                "form_type": r["form_type"],
                "original_date_filed": r["date_filed"],
                "date_filed": anchor,             # PIT-effective
                "acceptance_et_date": pit_rec.get("acceptance_et_date"),
                "acceptance_et_time": pit_rec.get("acceptance_et_time"),
                "after_16et": pit_rec.get("after_16et"),
                "label": r["label"],
                "first_restatement_after": first_rst.isoformat() if first_rst else None,
                "days_to_first_restatement": (first_rst - nt_d).days if first_rst else None,
            }
            for w in windows_days:
                row_out[f"restated_within_{w}d"] = bool(first_rst and (first_rst - nt_d).days <= w)
            if firm_ret and spy_ret:
                for w in (30, 90):
                    row_out[f"car_fwd_{w}d"] = _forward_car(firm_ret, spy_ret, anchor, w)
            else:
                for w in (30, 90):
                    row_out[f"car_fwd_{w}d"] = None
            joined.append(row_out)

    joined.sort(key=lambda r: (r["cik"], r["date_filed"], r["accession_number"]))

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for r in joined:
            f.write(json.dumps(r) + "\n")

    # Compute Bonferroni-12 cells for Angle 2 PIT
    out: dict = {
        "n_classified": len(cls_rows), "n_joined": len(joined),
        "n_no_pit_match": n_no_pit, "n_pit_indeterminate": n_pit_indeterminate,
        "windows_days": windows_days,
        "anchor_definition": "acceptance_et_date + (1d if after_16et else 0d)",
    }

    by_label: dict[str, list[dict]] = defaultdict(list)
    for r in joined:
        by_label[r["label"]].append(r)
    ai = by_label["accounting_issue"]
    ot = by_label["other"]

    # CAR-diff cells (the cells that feed Net Sharpe)
    car_cells: dict[str, dict] = {}
    for w in (30, 90):
        ai_v = [r[f"car_fwd_{w}d"] for r in ai if r[f"car_fwd_{w}d"] is not None]
        ot_v = [r[f"car_fwd_{w}d"] for r in ot if r[f"car_fwd_{w}d"] is not None]
        s_ai = _winsorize_t(ai_v)
        s_ot = _winsorize_t(ot_v)
        diff = None
        if s_ai["mean_pct"] is not None and s_ot["mean_pct"] is not None:
            diff = round(s_ai["mean_pct"] - s_ot["mean_pct"], 4)
        car_cells[f"car_diff_{w}d"] = {
            "accounting_issue": s_ai,
            "other": s_ot,
            "diff_pct_ai_minus_other": diff,
        }
    out["car_diff_cells"] = car_cells
    out["label_distribution"] = {lab: len(by_label[lab]) for lab in ("accounting_issue", "unresolved_sec_comment", "other")}
    out["after_16et_share_in_joined_pct"] = round(
        100.0 * sum(1 for r in joined if r.get("after_16et")) / max(1, len(joined)), 2
    )

    rep_path = Path(args.report)
    rep_path.parent.mkdir(parents=True, exist_ok=True)
    with rep_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print()
    print(f"PIT joined: {len(joined)}  (no_pit={n_no_pit}, indeterminate={n_pit_indeterminate})")
    print(f"after_16et share: {out['after_16et_share_in_joined_pct']}%")
    print("Label distribution:", out["label_distribution"])
    print("\nCAR-diff cells (PIT anchor):")
    for k, v in car_cells.items():
        print(f"  {k}: AI mean={v['accounting_issue']['mean_pct']}% n={v['accounting_issue']['n']} t={v['accounting_issue']['t_stat']} | other={v['other']['mean_pct']}% n={v['other']['n']} | diff={v['diff_pct_ai_minus_other']}pp")
    print()
    print(f"Output: {out_path}")
    print(f"Report: {rep_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
