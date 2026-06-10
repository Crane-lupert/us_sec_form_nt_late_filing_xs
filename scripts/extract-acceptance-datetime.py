"""Phase 3 / Step 1 — extract acceptanceDateTime for matched NT cohort.

Walks data/form_nt_matched.jsonl (+ _oos) and joins each row's
(cik, accession_number) against data/sec_submissions_cache/CIK{padded}.json
(filings.recent.accessionNumber index). Converts the UTC acceptanceDateTime
to America/New_York and flags filings accepted after 16:00 ET as T+1 anchor.

Output: data/form_nt_pit.jsonl (in-sample) + data/form_nt_pit_oos.jsonl (OOS)
columns: cik, accession_number, date_filed, ticker, exchange, form_type,
         acceptance_utc, acceptance_et_date, acceptance_et_time,
         after_16et, anchor_date  (= acceptance_et_date if not after_16et
                                    else next trading day will be resolved
                                    downstream against firm price series)

Lock F sort-stable on (cik, date_filed, accession_number).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / "data" / "sec_submissions_cache"

ET = ZoneInfo("America/New_York")
CUTOFF = time(16, 0)  # market close 16:00 ET


def _load_jsonl(p: Path) -> list[dict]:
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _pad_cik(cik: str) -> str:
    return cik.zfill(10)


def _index_submissions_recent(cik_padded: str) -> dict[str, dict]:
    """Return accession_number -> {acceptanceDateTime, filingDate, form} from
    the cached submissions JSON's 'filings.recent' block.
    """
    p = CACHE_DIR / f"CIK{cik_padded}.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text(encoding="utf-8"))
    rec = d.get("filings", {}).get("recent", {})
    accs = rec.get("accessionNumber", [])
    accept = rec.get("acceptanceDateTime", [])
    fdates = rec.get("filingDate", [])
    forms = rec.get("form", [])
    out: dict[str, dict] = {}
    for i, acc in enumerate(accs):
        out[acc] = {
            "acceptanceDateTime": accept[i] if i < len(accept) else None,
            "filingDate": fdates[i] if i < len(fdates) else None,
            "form": forms[i] if i < len(forms) else None,
        }
    return out


def _parse_utc(s: str) -> datetime | None:
    """SEC stores acceptanceDateTime as 'YYYY-MM-DDTHH:MM:SS.000Z' (UTC)."""
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def process(rows: list[dict]) -> tuple[list[dict], dict]:
    by_cik: dict[str, list[dict]] = {}
    for r in rows:
        by_cik.setdefault(r["cik"], []).append(r)

    out: list[dict] = []
    n_total = len(rows)
    n_matched = 0
    n_unmatched = 0
    n_no_accept = 0
    n_after_16et = 0
    n_before_16et = 0

    for cik, rs in by_cik.items():
        idx = _index_submissions_recent(_pad_cik(cik))
        for r in rs:
            acc = r["accession_number"]
            meta = idx.get(acc)
            row_out = {
                "cik": cik,
                "accession_number": acc,
                "date_filed": r["date_filed"],
                "ticker": r.get("ticker"),
                "exchange": r.get("exchange"),
                "form_type": r["form_type"],
            }
            if meta is None:
                n_unmatched += 1
                row_out.update({
                    "acceptance_utc": None,
                    "acceptance_et_date": None,
                    "acceptance_et_time": None,
                    "after_16et": None,
                    "match_status": "no_match_in_recent",
                })
                out.append(row_out)
                continue
            n_matched += 1
            utc_str = meta.get("acceptanceDateTime")
            dt_utc = _parse_utc(utc_str) if utc_str else None
            if dt_utc is None:
                n_no_accept += 1
                row_out.update({
                    "acceptance_utc": utc_str,
                    "acceptance_et_date": None,
                    "acceptance_et_time": None,
                    "after_16et": None,
                    "match_status": "matched_no_acceptance",
                })
                out.append(row_out)
                continue
            dt_et = dt_utc.astimezone(ET)
            after = dt_et.time() >= CUTOFF
            if after:
                n_after_16et += 1
            else:
                n_before_16et += 1
            row_out.update({
                "acceptance_utc": utc_str,
                "acceptance_et_date": dt_et.date().isoformat(),
                "acceptance_et_time": dt_et.time().isoformat(timespec="seconds"),
                "after_16et": after,
                "match_status": "ok",
            })
            out.append(row_out)

    # Lock F sort
    out.sort(key=lambda r: (r["cik"], r["date_filed"], r["accession_number"]))

    stats = {
        "n_total": n_total,
        "n_matched_in_recent": n_matched,
        "n_unmatched_in_recent": n_unmatched,
        "n_matched_no_acceptance": n_no_accept,
        "n_after_16et": n_after_16et,
        "n_before_16et": n_before_16et,
        "after_16et_share_pct": (
            round(100.0 * n_after_16et / max(1, n_after_16et + n_before_16et), 2)
        ),
        "match_rate_pct": round(100.0 * n_matched / max(1, n_total), 2),
    }
    return out, stats


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--in-input", default=str(REPO_ROOT / "data" / "form_nt_matched.jsonl"))
    p.add_argument("--in-output", default=str(REPO_ROOT / "data" / "form_nt_pit.jsonl"))
    p.add_argument("--oos-input", default=str(REPO_ROOT / "data" / "form_nt_matched_oos.jsonl"))
    p.add_argument("--oos-output", default=str(REPO_ROOT / "data" / "form_nt_pit_oos.jsonl"))
    p.add_argument("--report", default=str(REPO_ROOT / "reports" / "phase3-step1-acceptance.json"))
    args = p.parse_args()

    report = {}
    for label, inp, outp in [
        ("in_sample", args.in_input, args.in_output),
        ("oos", args.oos_input, args.oos_output),
    ]:
        print(f"=== {label} ===", flush=True)
        rows = _load_jsonl(Path(inp))
        print(f"  loaded {len(rows)} matched filings", flush=True)
        # only NYSE/Nasdaq (Bartov-K comparable cohort)
        rows = [r for r in rows if r.get("exchange") in ("NYSE", "Nasdaq")]
        print(f"  NYSE/Nasdaq filter: {len(rows)} rows", flush=True)

        out, stats = process(rows)
        op = Path(outp)
        op.parent.mkdir(parents=True, exist_ok=True)
        with op.open("w", encoding="utf-8") as f:
            for r in out:
                f.write(json.dumps(r) + "\n")
        print(f"  wrote {op}", flush=True)
        print(f"  stats: {stats}", flush=True)
        report[label] = stats

    rep = Path(args.report)
    rep.parent.mkdir(parents=True, exist_ok=True)
    rep.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nreport -> {rep}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
