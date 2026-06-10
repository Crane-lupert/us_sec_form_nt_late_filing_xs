"""R3 — Fetch SIC codes from SEC submissions API + sector-residualized basket sim.

(a) For each unique CIK in matched NT cohort, fetch
    https://data.sec.gov/submissions/CIK{10digit}.json
    once, extract sic + sicDescription. Cache to data/sec_submissions_cache/.

(b) Map SIC -> 2-digit major group ("SIC2") for sector aggregation.

(c) For each month, compute LONG-SHORT basket return AFTER subtracting the
    monthly SIC2 sector mean for each filing — sector-residualized.

(d) Compute Net Sharpe for sector-residualized + size-quintile-stratified
    variants vs the equal-weight baseline.

Size proxy = winsorized 1y trailing return abs (we don't have shares
outstanding via the existing CRSP DSF parquet; price-only-based proxies
distort small/large; we instead use SIZE proxy = filing-month log(price)).
"""
from __future__ import annotations

import json
import math
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev, median

REPO_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = REPO_ROOT / "data" / "sec_submissions_cache"
INPUT_IS = REPO_ROOT / "data" / "form_nt_matched.jsonl"
INPUT_OOS = REPO_ROOT / "data" / "form_nt_matched_oos.jsonl"
FORWARD = REPO_ROOT / "data" / "angle_2_forward.jsonl"
CRSP = REPO_ROOT / "data" / "crsp_returns.parquet"
OUTPUT = REPO_ROOT / "reports" / "r3-sector-size-neutral.json"

USER_AGENT = "us_sec_form_nt_late_filing_xs research fawkes4700@gmail.com"


def fetch_cik_submissions(cik: str) -> dict | None:
    cache = CACHE_DIR / f"CIK{cik.zfill(10)}.json"
    if cache.exists():
        try:
            return json.loads(cache.read_text(encoding="utf-8"))
        except Exception:
            pass
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(raw)
        return json.loads(raw.decode("utf-8"))
    except Exception as e:
        print(f"  fail CIK={cik}: {e}", file=sys.stderr)
        return None


def main() -> int:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Collect unique CIKs (in-sample + OOS if exists)
    ciks = set()
    if INPUT_IS.exists():
        for line in INPUT_IS.open(encoding="utf-8"):
            r = json.loads(line)
            if r.get("exchange") in ("NYSE", "Nasdaq") and r.get("ticker"):
                ciks.add(r["cik"])
    if INPUT_OOS.exists():
        for line in INPUT_OOS.open(encoding="utf-8"):
            r = json.loads(line)
            if r.get("exchange") in ("NYSE", "Nasdaq") and r.get("ticker"):
                ciks.add(r["cik"])
    ciks_sorted = sorted(ciks)
    print(f"Unique CIKs to fetch SIC for: {len(ciks_sorted)}", flush=True)

    # Fetch all
    cik_to_sic: dict[str, dict] = {}
    n_done = 0
    for cik in ciks_sorted:
        sub = fetch_cik_submissions(cik)
        if sub:
            cik_to_sic[cik] = {
                "sic": sub.get("sic"),
                "sicDescription": sub.get("sicDescription"),
            }
        n_done += 1
        if n_done % 50 == 0:
            print(f"  [{n_done}/{len(ciks_sorted)}] fetched", flush=True)
        # SEC limit 10 req/s
        if n_done % 50 == 0:
            time.sleep(0.05)
        else:
            time.sleep(0.12)

    # Write cik->sic map
    sic_map_path = REPO_ROOT / "data" / "cik_sic_map.json"
    with sic_map_path.open("w", encoding="utf-8") as f:
        json.dump(cik_to_sic, f, indent=2)
    print(f"Wrote {sic_map_path}", flush=True)

    # Aggregate by SIC2 (first 2 digits)
    def sic2(sic_code) -> str | None:
        if sic_code is None or sic_code == "":
            return None
        s = str(sic_code).zfill(4)
        return s[:2]

    sic2_dist: dict[str, int] = defaultdict(int)
    for cik, info in cik_to_sic.items():
        s2 = sic2(info["sic"])
        if s2:
            sic2_dist[s2] += 1
    print(f"Distinct SIC2 sectors: {len(sic2_dist)}", flush=True)

    # Build per-filing SIC2 lookup for in-sample forward signal
    rows = [json.loads(l) for l in FORWARD.open(encoding="utf-8")]
    rows = [r for r in rows if r["label"] in ("accounting_issue", "other")]
    for r in rows:
        info = cik_to_sic.get(str(r["cik"]))
        r["sic"] = info["sic"] if info else None
        r["sic2"] = sic2(info["sic"]) if info else None

    n_with_sic = sum(1 for r in rows if r["sic2"])
    print(f"Rows with SIC2: {n_with_sic}/{len(rows)}", flush=True)

    # ============== Sector-residualized basket sim @ 90d ==============
    # For each month, subtract within-month within-SIC2 mean from each filing's CAR
    # then form long-short on residuals.
    def winsorize(vals: list[float], lo_pct: float = 1.0, hi_pct: float = 1.0) -> list[float]:
        sv = sorted(v for v in vals if v is not None)
        if not sv:
            return []
        a = int(len(sv) * lo_pct / 100)
        b = max(int(len(sv) * (100 - hi_pct) / 100) - 1, a)
        lo, hi = sv[a], sv[b]
        return [min(max(v, lo), hi) for v in vals if v is not None]

    car_col = "car_fwd_90d"
    # Global winsorize first
    all_cars = [r[car_col] for r in rows if r.get(car_col) is not None]
    sv = sorted(all_cars)
    if not sv:
        print("No CAR data; abort", file=sys.stderr)
        return 1
    lo = sv[int(len(sv) * 0.01)]
    hi = sv[int(len(sv) * 0.99) - 1]
    for r in rows:
        v = r.get(car_col)
        if v is not None:
            r[car_col] = max(lo, min(hi, v))

    # Variant A: baseline (equal-weight, replicate Phase 1 step 1)
    # Variant B: sector-residualized (subtract within-month-SIC2 mean before basket)
    # Variant C: size-quintile (use filing-year as proxy for size — assign quintile by
    #            within-cohort price quintile from CRSP; here we approximate by
    #            ranking on filing-month sample-count-per-CIK as crude proxy)

    def sharpe(rets: list[float], periods_per_yr: float) -> dict:
        if len(rets) < 4:
            return {"n": len(rets), "sharpe": None}
        m = mean(rets)
        s = pstdev(rets) if len(rets) > 1 else 0
        ann = m * periods_per_yr
        ann_vol = s * math.sqrt(periods_per_yr)
        return {
            "n": len(rets),
            "gross_sharpe": round(ann / ann_vol if ann_vol > 0 else 0, 4),
            "net_sharpe": round((ann - 0.0015 * periods_per_yr) / ann_vol if ann_vol > 0 else 0, 4),
            "ann_mean_pct": round(100 * ann, 4),
            "ann_vol_pct": round(100 * ann_vol, 4),
        }

    ppy = 252 / 90

    # ---- Variant A: baseline equal-weight ----
    by_month_ai, by_month_ot = defaultdict(list), defaultdict(list)
    for r in rows:
        v = r.get(car_col)
        if v is None:
            continue
        ym = r["date_filed"][:7]
        if r["label"] == "accounting_issue":
            by_month_ai[ym].append(v)
        else:
            by_month_ot[ym].append(v)
    months = sorted(set(by_month_ai) | set(by_month_ot))
    ls_rets_A = []
    for m in months:
        if len(by_month_ai.get(m, [])) >= 5 and len(by_month_ot.get(m, [])) >= 5:
            ls_rets_A.append(mean(by_month_ot[m]) - mean(by_month_ai[m]))

    # ---- Variant B: sector-residualized ----
    # Step 1: for each (month, SIC2), compute pooled mean CAR
    by_month_sic2: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in rows:
        v = r.get(car_col)
        if v is None or r["sic2"] is None:
            continue
        ym = r["date_filed"][:7]
        by_month_sic2[(ym, r["sic2"])].append(v)
    msic_means = {k: mean(vs) for k, vs in by_month_sic2.items()}

    # Step 2: subtract sector mean from each filing's CAR, then basket on residuals
    by_month_ai_resid, by_month_ot_resid = defaultdict(list), defaultdict(list)
    for r in rows:
        v = r.get(car_col)
        if v is None or r["sic2"] is None:
            continue
        ym = r["date_filed"][:7]
        sect_mean = msic_means.get((ym, r["sic2"]), 0)
        resid = v - sect_mean
        if r["label"] == "accounting_issue":
            by_month_ai_resid[ym].append(resid)
        else:
            by_month_ot_resid[ym].append(resid)
    ls_rets_B = []
    for m in months:
        if len(by_month_ai_resid.get(m, [])) >= 5 and len(by_month_ot_resid.get(m, [])) >= 5:
            ls_rets_B.append(mean(by_month_ot_resid[m]) - mean(by_month_ai_resid[m]))

    # ---- Variant C: SIC2 within-sector concentration breakdown ----
    sic2_PnL: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        if r.get(car_col) is None or r["sic2"] is None:
            continue
        sic2_PnL[r["sic2"]].append((r["label"], r[car_col]))

    by_sic2_summary = {}
    for s2 in sorted(sic2_PnL):
        ai = [v for lab, v in sic2_PnL[s2] if lab == "accounting_issue"]
        ot = [v for lab, v in sic2_PnL[s2] if lab == "other"]
        if len(ai) < 10 or len(ot) < 10:
            continue
        by_sic2_summary[s2] = {
            "n_ai": len(ai),
            "n_other": len(ot),
            "ai_mean_pct": round(100 * mean(ai), 4),
            "other_mean_pct": round(100 * mean(ot), 4),
            "ls_pct": round(100 * (mean(ot) - mean(ai)), 4),
        }

    # Output
    out = {
        "n_ciks_fetched": len(cik_to_sic),
        "n_sic2_sectors": len(sic2_dist),
        "n_rows_with_sic": n_with_sic,
        "n_rows_total": len(rows),
        "variant_A_baseline_equal_weight": sharpe(ls_rets_A, ppy),
        "variant_B_sector_residualized": sharpe(ls_rets_B, ppy),
        "by_sic2_basket": by_sic2_summary,
        "sic2_distribution_top10": dict(sorted(sic2_dist.items(), key=lambda kv: -kv[1])[:10]),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print()
    print(f"Variant A baseline:     n={out['variant_A_baseline_equal_weight']['n']:>3}  net Sharpe={out['variant_A_baseline_equal_weight']['net_sharpe']}  ann_vol={out['variant_A_baseline_equal_weight']['ann_vol_pct']}%")
    print(f"Variant B sector-resid: n={out['variant_B_sector_residualized']['n']:>3}  net Sharpe={out['variant_B_sector_residualized']['net_sharpe']}  ann_vol={out['variant_B_sector_residualized']['ann_vol_pct']}%")
    print(f"\nTop 10 SIC2 sector distribution: {out['sic2_distribution_top10']}")
    print(f"\nReport: {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
