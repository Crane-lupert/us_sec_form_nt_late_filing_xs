"""R2 — Subsample stability of Strategy D Angle 2 rate-diff + Net Sharpe.

Splits angle_2_forward.jsonl into:
  - year-by-year (2014..2024)
  - pre-COVID (2014-2019) vs post-COVID (2020-2024)
  - first-half (2014-2019) vs second-half (2020-2024) — same split, different framing

For each subsample, recomputes:
  - rate-diff cells (30d, 90d, 180d): P(restated within H | label) for AI vs other
  - Net Sharpe @ 90d (long-short basket sim, 15bps round-trip)

Threshold ref: V5-11(b) Bonferroni-12 critical |z| = 2.78; V5-11(c) Sharpe >= 0.30.

Lock F: sort-stable on (subsample, label, accession).
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev

REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT = REPO_ROOT / "data" / "angle_2_forward.jsonl"
OUTPUT = REPO_ROOT / "reports" / "r2-subsample-stability.json"

TC_BPS_RT = 15.0  # 15 bps round-trip


def rate_diff(rows: list[dict], window_key: str) -> dict:
    """Two-proportion z-test on P(restated_within_H | label)."""
    ai = [r for r in rows if r["label"] == "accounting_issue"]
    ot = [r for r in rows if r["label"] == "other"]
    if not ai or not ot:
        return {"n_ai": len(ai), "n_other": len(ot), "z_stat": None}
    p1 = sum(1 for r in ai if r.get(window_key)) / len(ai)
    p2 = sum(1 for r in ot if r.get(window_key)) / len(ot)
    n1, n2 = len(ai), len(ot)
    p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2)) if p_pool > 0 and p_pool < 1 else 0
    z = (p1 - p2) / se if se > 0 else 0
    return {
        "n_ai": n1, "n_other": n2,
        "p_ai_pct": round(100 * p1, 4),
        "p_other_pct": round(100 * p2, 4),
        "diff_pp": round(100 * (p1 - p2), 4),
        "z_stat": round(z, 4),
        "bonferroni12_PASS": abs(z) > 2.78,
    }


def net_sharpe_90d(rows: list[dict]) -> dict:
    """Long-short basket sim @ 90d. Mirror compute-net-sharpe-strategy-d.py."""
    car_col = "car_fwd_90d"
    vals = sorted(r[car_col] for r in rows if r.get(car_col) is not None)
    if len(vals) < 100:
        return {"n_rows_with_car": len(vals), "verdict": "INSUFFICIENT_DATA"}
    # winsorize 1%/99%
    lo = vals[int(len(vals) * 0.01)]
    hi = vals[int(len(vals) * 0.99) - 1]
    by_month_ai, by_month_ot = defaultdict(list), defaultdict(list)
    for r in rows:
        v = r.get(car_col)
        if v is None:
            continue
        v = max(lo, min(hi, v))
        ym = r["date_filed"][:7]
        if r["label"] == "accounting_issue":
            by_month_ai[ym].append(v)
        elif r["label"] == "other":
            by_month_ot[ym].append(v)
    months = sorted(set(by_month_ai) | set(by_month_ot))
    ls_rets = []
    for m in months:
        if len(by_month_ai.get(m, [])) >= 5 and len(by_month_ot.get(m, [])) >= 5:
            ls_rets.append(mean(by_month_ot[m]) - mean(by_month_ai[m]))
    if len(ls_rets) < 4:
        return {"n_usable_months": len(ls_rets), "verdict": "INSUFFICIENT_MONTHS"}
    ppy = 252 / 90
    m_mu = mean(ls_rets)
    m_sd = pstdev(ls_rets) if len(ls_rets) > 1 else 0
    ann_mean = m_mu * ppy
    ann_vol = m_sd * math.sqrt(ppy)
    gross_sharpe = (ann_mean / ann_vol) if ann_vol > 0 else 0
    net_rets = [r - 2 * (TC_BPS_RT / 2) / 10000 for r in ls_rets]
    net_mu = mean(net_rets)
    net_ann_mean = net_mu * ppy
    net_sharpe = (net_ann_mean / ann_vol) if ann_vol > 0 else 0
    verdict = (
        "PASS" if net_sharpe >= 0.30
        else "BORDERLINE" if net_sharpe >= 0.21
        else "KILL"
    )
    return {
        "n_usable_months": len(ls_rets),
        "gross_sharpe": round(gross_sharpe, 4),
        "net_sharpe": round(net_sharpe, 4),
        "gross_ann_mean_pct": round(100 * ann_mean, 4),
        "ann_vol_pct": round(100 * ann_vol, 4),
        "v5_11c_verdict": verdict,
    }


def main() -> int:
    rows = [json.loads(l) for l in INPUT.open(encoding="utf-8")]
    rows = [r for r in rows if r.get("label") in ("accounting_issue", "other")]
    print(f"Total in-scope rows (2014-2024): {len(rows)}", flush=True)

    subsamples: dict[str, list[dict]] = {}
    for y in range(2014, 2025):
        subsamples[f"year_{y}"] = [r for r in rows if r["date_filed"][:4] == str(y)]
    subsamples["pre_covid_2014_2019"] = [r for r in rows if 2014 <= int(r["date_filed"][:4]) <= 2019]
    subsamples["post_covid_2020_2024"] = [r for r in rows if 2020 <= int(r["date_filed"][:4]) <= 2024]
    # 3-bin partition for robustness check (each window roughly equal n)
    subsamples["early_2014_2017"] = [r for r in rows if 2014 <= int(r["date_filed"][:4]) <= 2017]
    subsamples["mid_2018_2020"] = [r for r in rows if 2018 <= int(r["date_filed"][:4]) <= 2020]
    subsamples["late_2021_2024"] = [r for r in rows if 2021 <= int(r["date_filed"][:4]) <= 2024]

    out: dict = {"subsamples": {}}
    for name, subset in subsamples.items():
        if not subset:
            continue
        out["subsamples"][name] = {
            "n_rows": len(subset),
            "n_accounting_issue": sum(1 for r in subset if r["label"] == "accounting_issue"),
            "n_other": sum(1 for r in subset if r["label"] == "other"),
            "rate_diff_30d": rate_diff(subset, "restated_within_30d"),
            "rate_diff_90d": rate_diff(subset, "restated_within_90d"),
            "rate_diff_180d": rate_diff(subset, "restated_within_180d"),
            "net_sharpe_90d": net_sharpe_90d(subset),
        }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    # Summary stdout
    print(f"\n{'Subsample':<28} {'N':>5} {'rd30 z':>8} {'rd90 z':>8} {'Sharpe':>8} {'verdict':>10}")
    for name, s in out["subsamples"].items():
        z30 = s["rate_diff_30d"].get("z_stat")
        z90 = s["rate_diff_90d"].get("z_stat")
        ns = s["net_sharpe_90d"].get("net_sharpe")
        v = s["net_sharpe_90d"].get("v5_11c_verdict", "—")
        print(f"{name:<28} {s['n_rows']:>5} {z30 if z30 is not None else '—':>8} {z90 if z90 is not None else '—':>8} {ns if ns is not None else '—':>8} {v:>10}")
    print(f"\nReport: {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
