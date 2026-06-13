"""Fetch Fama-French 5-factor + Momentum (UMD) monthly returns from the
Ken French data library and write to data/ff5_umd_monthly.jsonl.

Free, public source. No authentication required. Columns:
    Mkt-RF, SMB, HML, RMW, CMA, MOM, RF
in monthly percentage points (Ken French convention).
"""
from __future__ import annotations

import io
import json
import urllib.request
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"

FF5_URL = ("https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/"
           "ftp/F-F_Research_Data_5_Factors_2x3_CSV.zip")
MOM_URL = ("https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/"
           "ftp/F-F_Momentum_Factor_CSV.zip")
HEADERS = {"User-Agent": "us_sec_form_nt_late_filing_xs research fawkes4700@gmail.com"}


def _download_and_extract(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        name = zf.namelist()[0]
        return zf.read(name).decode("latin-1")


def _parse_monthly(text: str, cols: list[str]) -> dict[str, dict[str, float]]:
    """Parse Ken French CSV format. Returns {ym: {col: pct}}."""
    out: dict[str, dict[str, float]] = {}
    started = False
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            if started:
                # Monthly section ends at first blank line after start
                break
            continue
        parts = [p.strip() for p in line.split(",")]
        if not started:
            # Header row: first column is empty or "Date", remaining cols match
            if len(parts) >= len(cols) + 1:
                # Detect header by requiring every target column to appear.
                header_match = all(c in parts for c in cols)
                if header_match:
                    started = True
            continue
        # Data row: YYYYMM,val1,val2,...
        date = parts[0]
        if not (date.isdigit() and len(date) == 6):
            # Annual section starts at YYYY (4 digits)
            break
        ym = f"{date[:4]}-{date[4:6]}"
        row = {}
        for i, c in enumerate(cols, start=1):
            try:
                row[c] = float(parts[i])
            except (IndexError, ValueError):
                row[c] = None
        out[ym] = row
    return out


def main() -> int:
    print("Fetching FF5 monthly...", flush=True)
    ff5_text = _download_and_extract(FF5_URL)
    ff5 = _parse_monthly(ff5_text, ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"])
    print(f"  FF5 months: {len(ff5)} from {min(ff5)} to {max(ff5)}", flush=True)

    print("Fetching UMD (momentum)...", flush=True)
    mom_text = _download_and_extract(MOM_URL)
    mom = _parse_monthly(mom_text, ["Mom"])
    mom = {ym: {"MOM": v["Mom"]} for ym, v in mom.items() if v.get("Mom") is not None}
    print(f"  MOM months: {len(mom)} from {min(mom)} to {max(mom)}", flush=True)

    # Merge
    all_ym = sorted(set(ff5) & set(mom))
    rows = []
    for ym in all_ym:
        row = {"year_month": ym}
        row.update(ff5[ym])
        row.update(mom[ym])
        rows.append(row)

    out = DATA / "ff5_umd_monthly.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"\nWrote {out}: {len(rows)} monthly observations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
