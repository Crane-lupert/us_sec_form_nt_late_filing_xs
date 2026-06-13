"""Survivorship check (#4) at the extraction layer.

For each Form NT filing in the matched cohort, count how many drop out at
each pipeline stage and compare the body-narrative label distribution and
the subsequent restatement-class rate between (i) filings that survive to
the final basket and (ii) filings that are dropped.

If the dropped subset has a systematically different label or outcome
distribution, the headline result may reflect selection on the dependent
variable.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
REPORTS = REPO / "reports"


def main() -> int:
    matched = [json.loads(l) for l in (DATA / "form_nt_matched.jsonl").open(encoding="utf-8")]
    matched = [r for r in matched if r.get("exchange") in ("NYSE", "Nasdaq")]
    matched_acc = {r["accession_number"]: r for r in matched}
    print(f"NYSE/Nasdaq matched: {len(matched_acc)}")

    bodies = [json.loads(l) for l in (DATA / "nt_bodies.jsonl").open(encoding="utf-8")]
    body_acc = {r["accession_number"] for r in bodies}
    print(f"Body extracted: {len(body_acc)}")

    classifications = [json.loads(l) for l in (DATA / "nt_classifications.jsonl").open(encoding="utf-8")]
    class_label = {r["accession_number"]: r.get("label") for r in classifications
                   if r.get("label") in ("accounting_issue", "unresolved_sec_comment", "other")}
    print(f"Classified (valid 3-class label): {len(class_label)}")

    angle2 = [json.loads(l) for l in (DATA / "angle_2_forward_pit.jsonl").open(encoding="utf-8")]
    in_basket_acc = {r["accession_number"] for r in angle2
                     if r.get("label") in ("accounting_issue", "other")
                     and r.get("car_fwd_90d") is not None}
    print(f"In long-short basket: {len(in_basket_acc)}")

    # Stage drop-out
    dropped_no_body = set(matched_acc) - body_acc
    dropped_no_class = body_acc - set(class_label)
    dropped_unresolved = {a for a, lbl in class_label.items() if lbl == "unresolved_sec_comment"}
    dropped_no_pit_match = (set(class_label) - dropped_unresolved) - set(angle2[0:0].__class__(r["accession_number"] for r in angle2))
    dropped_no_90d_car = {r["accession_number"] for r in angle2
                          if r.get("label") in ("accounting_issue", "other")
                          and r.get("car_fwd_90d") is None}

    print(f"\nDrop-out by stage:")
    print(f"  matched but no body extracted:        {len(dropped_no_body)}")
    print(f"  body but no valid 3-class label:      {len(dropped_no_class)}")
    print(f"  classified unresolved_sec_comment:    {len(dropped_unresolved)}")
    print(f"  classified but no 90d CAR available:  {len(dropped_no_90d_car)}")

    # Label distribution: in-basket vs dropped (where label is known)
    in_basket_labels = Counter(class_label[a] for a in class_label
                                if a in in_basket_acc and class_label[a] in ("accounting_issue", "other"))
    dropped_known_label = Counter(class_label[a] for a in class_label
                                   if a in dropped_no_90d_car
                                   and class_label[a] in ("accounting_issue", "other"))
    print(f"\nLabel distribution AI vs other:")
    print(f"  in-basket:           AI={in_basket_labels['accounting_issue']:>4}  other={in_basket_labels['other']:>4}")
    print(f"  dropped (no 90d CAR): AI={dropped_known_label['accounting_issue']:>4}  other={dropped_known_label['other']:>4}")

    in_share = in_basket_labels['accounting_issue'] / max(1, sum(in_basket_labels.values()))
    out_share = dropped_known_label['accounting_issue'] / max(1, sum(dropped_known_label.values()))
    print(f"  AI share in-basket:   {in_share*100:.1f}%")
    print(f"  AI share dropped:     {out_share*100:.1f}%")
    print(f"  Differential (pp):    {(in_share-out_share)*100:+.1f}")

    # Restatement rate by label, basket vs dropped
    restated_pit = {r["accession_number"]: r.get("restated_within_90d", False) for r in angle2}
    in_basket_rest = Counter()
    in_basket_total = Counter()
    for a in in_basket_acc:
        lbl = class_label.get(a)
        if lbl in ("accounting_issue", "other"):
            in_basket_total[lbl] += 1
            if restated_pit.get(a):
                in_basket_rest[lbl] += 1

    print(f"\nIn-basket restatement-within-90d rate:")
    for lbl in ("accounting_issue", "other"):
        n = in_basket_total[lbl]
        k = in_basket_rest[lbl]
        if n > 0:
            print(f"  {lbl:<20} {k:>4} / {n:>4} = {100*k/n:5.2f}%")

    REPORTS.mkdir(parents=True, exist_ok=True)
    out = {
        "matched_NYSE_Nasdaq": len(matched_acc),
        "body_extracted": len(body_acc),
        "valid_3class_label": len(class_label),
        "in_long_short_basket": len(in_basket_acc),
        "drop_no_body": len(dropped_no_body),
        "drop_no_label": len(dropped_no_class),
        "drop_unresolved": len(dropped_unresolved),
        "drop_no_90d_car": len(dropped_no_90d_car),
        "in_basket_AI_share_pct": round(in_share * 100, 2),
        "dropped_AI_share_pct": round(out_share * 100, 2),
        "differential_pp": round((in_share - out_share) * 100, 2),
    }
    (REPORTS / "survivorship-check.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nReport: {REPORTS / 'survivorship-check.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
