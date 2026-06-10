"""Phase 3 Step 3 — Differential transaction-cost + borrow-availability proxy
for the recurring-filer cohort.

The recurring NT filer cross-section (paper Angle 3) is constructed on a
cohort heavily concentrated in small-market-capitalization filers; the
production paper's 15 bp round-trip cost assumption and unconstrained-borrow
assumption are therefore optimistic. This script reports:

(a) Filer-level CRSP closing-price distribution at the filing date, split by
    recurring vs non-recurring, NT 10-K vs NT 10-Q, as a market-capitalization
    proxy.
(b) Net Sharpe ratio of the long-short basket under a tiered round-trip
    transaction cost schedule keyed to the price proxy ($5 / $1 thresholds
    common in borrow-availability practice).
(c) "Borrow-restricted" filter: drop filings whose anchor-date closing price
    is below $5 (typically borrow-restricted in retail short-selling) from the
    short leg and recompute the basket.

The paper's Section 6 limitations subsection already flags this concern; this
audit closes Phase 3 Step 3 by quantifying it.
"""
from __future__ import annotations
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median, pstdev

REPO_ROOT = Path(__file__).resolve().parents[1]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.open(encoding="utf-8")]


def main() -> int:
    # ---- (a) Price distribution from the CRSP join ----
    a1 = load_jsonl(REPO_ROOT / "data" / "crsp_angle_1_car.jsonl")
    a4 = load_jsonl(REPO_ROOT / "data" / "crsp_angle_4_recurring.jsonl")

    # The CRSP daily file with dlyprc on the event date is held in the
    # parquet; join it once for our filings of interest.
    import duckdb
    db = duckdb.connect(":memory:")
    print("Loading CRSP daily prices ...", flush=True)
    df = db.execute(
        f"SELECT ticker, dlycaldt, dlyprc FROM "
        f"read_parquet('{REPO_ROOT / 'data' / 'crsp_returns.parquet'}') "
        f"WHERE dlyprc IS NOT NULL"
    ).fetchdf()
    by_tk_date: dict[tuple[str, str], float] = {}
    for tk, dt, prc in zip(df["ticker"], df["dlycaldt"], df["dlyprc"]):
        d_str = dt.strftime("%Y-%m-%d") if hasattr(dt, "strftime") else str(dt)[:10]
        by_tk_date[(tk, d_str)] = float(prc)

    # Each Angle 4 row carries (ticker, date_filed, form_type, recurring)
    enriched = []
    for r in a4:
        key = (r["ticker"], r["date_filed"])
        prc = by_tk_date.get(key)
        if prc is None:
            # search the closest prior trading day within 5d window
            from datetime import datetime, timedelta
            base = datetime.strptime(r["date_filed"], "%Y-%m-%d").date()
            for delta in range(1, 6):
                key_back = (r["ticker"], (base - timedelta(days=delta)).isoformat())
                if key_back in by_tk_date:
                    prc = by_tk_date[key_back]
                    break
        if prc is None:
            continue
        enriched.append({**r, "price": prc})
    print(f"Enriched rows with price: {len(enriched)} / {len(a4)}")

    # Cohort price summary
    cohorts = [
        ("All NT", lambda r: True),
        ("NT 10-K", lambda r: r["form_type"] == "NT 10-K"),
        ("NT 10-Q", lambda r: r["form_type"] == "NT 10-Q"),
        ("Recurring (>=2/yr)", lambda r: r["recurring"]),
        ("Non-recurring", lambda r: not r["recurring"]),
        ("Recurring NT 10-K", lambda r: r["recurring"] and r["form_type"] == "NT 10-K"),
        ("Recurring NT 10-Q", lambda r: r["recurring"] and r["form_type"] == "NT 10-Q"),
    ]
    summary = {}
    print()
    print("=== Price distribution at filing date (closing price proxy) ===")
    print(f"{'Cohort':<30} {'n':>6} {'median':>8} {'mean':>8} {'<$5 share':>10} {'<$1 share':>10}")
    for name, fn in cohorts:
        sub = [r for r in enriched if fn(r)]
        if not sub:
            continue
        prices = sorted(r["price"] for r in sub)
        med = median(prices)
        avg = mean(prices)
        sub5 = sum(1 for p in prices if p < 5.0) / len(prices)
        sub1 = sum(1 for p in prices if p < 1.0) / len(prices)
        summary[name] = {"n": len(sub), "median": round(med, 2), "mean": round(avg, 2),
                        "sub_5_share_pct": round(100*sub5, 2), "sub_1_share_pct": round(100*sub1, 2)}
        print(f"{name:<30} {len(sub):>6} ${med:>7.2f} ${avg:>7.2f} {sub5*100:>9.2f}% {sub1*100:>9.2f}%")

    # ---- (b) Tiered TC schedule on the long-short basket ----
    # Reuse the Angle 2 forward signal (which already has the basket inputs).
    a2 = load_jsonl(REPO_ROOT / "data" / "angle_2_forward.jsonl")

    # Attach price at filing date to each angle-2 row
    a2_enriched = []
    for r in a2:
        key = (r["ticker"], r["date_filed"])
        prc = by_tk_date.get(key)
        if prc is None:
            from datetime import datetime, timedelta
            base = datetime.strptime(r["date_filed"], "%Y-%m-%d").date()
            for delta in range(1, 6):
                key_back = (r["ticker"], (base - timedelta(days=delta)).isoformat())
                if key_back in by_tk_date:
                    prc = by_tk_date[key_back]
                    break
        r["price"] = prc
        if prc is not None and r.get("label") in ("accounting_issue", "other"):
            a2_enriched.append(r)
    print(f"\nAngle-2 rows with price: {len(a2_enriched)} / {len(a2)}")

    # Winsorize CAR globally
    for col in ("car_fwd_30d", "car_fwd_90d"):
        vals = sorted(r[col] for r in a2_enriched if r.get(col) is not None)
        if len(vals) < 100:
            continue
        lo = vals[int(len(vals) * 0.01)]
        hi = vals[int(len(vals) * 0.99) - 1]
        for r in a2_enriched:
            v = r.get(col)
            if v is None: continue
            if v < lo: r[col] = lo
            elif v > hi: r[col] = hi

    def monthly_basket_net_sharpe(rows: list[dict], window: int, tc_bps_rt: float) -> dict:
        car_col = f"car_fwd_{window}d"
        by_m_ai: dict[str, list[float]] = defaultdict(list)
        by_m_ot: dict[str, list[float]] = defaultdict(list)
        for r in rows:
            v = r.get(car_col)
            if v is None: continue
            ym = r["date_filed"][:7]
            (by_m_ai if r["label"] == "accounting_issue" else by_m_ot)[ym].append(v)
        months = sorted(set(by_m_ai) | set(by_m_ot))
        ls = []
        for m in months:
            ai = by_m_ai.get(m, [])
            ot = by_m_ot.get(m, [])
            if len(ai) < 5 or len(ot) < 5: continue
            ls.append(mean(ot) - mean(ai))
        if not ls:
            return {"n_months": 0, "sharpe": None}
        net = [r - 2 * (tc_bps_rt / 2.0) / 10000 for r in ls]
        ppy = 252 / window
        ann_m = mean(net) * ppy
        ann_s = (pstdev(net) if len(net) > 1 else 0) * (ppy ** 0.5)
        sharpe = ann_m / ann_s if ann_s > 0 else 0
        return {"n_months": len(ls), "ann_mean_pct": round(100*ann_m, 4),
                "ann_vol_pct": round(100*ann_s, 4), "sharpe": round(sharpe, 4),
                "tc_bps_rt": tc_bps_rt}

    print()
    print("=== Net Sharpe at differential round-trip cost (90-day horizon) ===")
    tiered = {}
    for tc in (15, 30, 50, 75, 100, 200):
        c = monthly_basket_net_sharpe(a2_enriched, 90, tc)
        tiered[f"tc_{tc}bp"] = c
        print(f"  TC={tc:>4}bp r/t  n_months={c['n_months']:>3}  net Sharpe = {c['sharpe']}")

    # ---- (c) Borrow-restricted filter ----
    print()
    print("=== Borrow-restricted filter (drop short leg filings with price < $5) ===")
    borrow_filtered = []
    for r in a2_enriched:
        if r["label"] == "accounting_issue" and (r.get("price") or 0) < 5.0:
            continue  # drop borrow-restricted short
        borrow_filtered.append(r)
    print(f"After filter: {len(borrow_filtered)} / {len(a2_enriched)}")
    print()
    for tc in (15, 30, 50, 75, 100, 200):
        c = monthly_basket_net_sharpe(borrow_filtered, 90, tc)
        print(f"  TC={tc:>4}bp r/t  n_months={c['n_months']:>3}  net Sharpe = {c['sharpe']}")

    # Persist report
    out = {
        "cohort_price_summary": summary,
        "tiered_tc_sweep_90d": tiered,
        "tiered_tc_sweep_borrow_filtered_90d": {
            f"tc_{tc}bp": monthly_basket_net_sharpe(borrow_filtered, 90, tc)
            for tc in (15, 30, 50, 75, 100, 200)
        },
    }
    rep = REPO_ROOT / "reports" / "phase3-step3-tc-borrow.json"
    rep.parent.mkdir(parents=True, exist_ok=True)
    rep.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nReport: {rep}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
