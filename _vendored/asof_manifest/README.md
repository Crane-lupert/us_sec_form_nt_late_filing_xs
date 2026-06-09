# As-of date manifest — entry point

**Purpose**: portfolio-wide single source of truth for "given a (vendor, source, field), what is the actual data-knowable date?" Removes the per-launch ad-hoc verification burden.

**Origin**: KR23 §6 FnGuide multi-pattern look-ahead bias discovery (2026-06-03) → portfolio-wide audit (2026-06-04) → personal_bot_* fleet sweep (2026-06-05) → system launch (this).

---

## §1 Architecture (3 pieces)

1. **Manifest files** (this directory) — per-vendor JSON catalog of `(vendor, source, field) → classification + shift_recipe`. Authoritative.
2. **Scanner scripts** (`D:/vscode/meta-harness/scripts/build-asof-manifest/`) — refresh manifest from current data dumps. Empirical evidence-driven.
3. **Consumer API** (`D:/vscode/portfolio-coordination/shared-utils/shared_utils/asof.py`) — research repos import this; manifest read happens transparently.

Schema: see `_schema.md` (v1 spec).

---

## §2 Files in this directory

| File | Description | Status |
|---|---|---|
| `_schema.md` | Manifest schema v1 specification | locked |
| `fnguide.json` | FnGuide §A xlsx + §B CSV item codes | seeded from KR23 §6 evidence + portfolio-wide §3.1; empirical scan pending |
| `wrds.json` | WRDS dump §B schemas (Compustat, IBES, CRSP MF, bank_all, ...) | seeded from WRDS snapshot §B + §B.5; empirical datadate→rdq scan pending |
| `dart.json` | DART OpenAPI (single endpoint, SAFE by definition) | complete |
| `yfinance.json` | yfinance prices SAFE + fundamentals need SEC EDGAR | complete |
| `krx.json` | KRX free-tier 시세 + ETF PDF + index const + KIND + KIS WS | complete |
| `sec_edgar.json` | SEC EDGAR filing acceptance-datetime (10-K/10-Q/8-K/485APOS/...) | complete |

---

## §3 Quick lookup workflow

For any new research repo:
```python
from shared_utils.asof import load_panel_with_asof, assert_no_lookahead

# Vendor-specific loader returns panel with as_of_date auto-shifted per manifest
panel = load_panel_with_asof(
    path="E:/Fnguide/매출액_원.xlsx",
    vendor="fnguide",
)
# panel.as_of_date is now correctly shifted (DART rcept_dt cross-ref via external_lookup)

# Guard in any test
assert_no_lookahead(panel, value_cols=["revenue", "operating_income"])
```

If `(vendor, source, field)` is **not** in the manifest, consumer raises `AsofManifestMissingEntryError` — you cannot silently use unaudited data.

---

## §4 How to add a new vendor or field

1. Add entry to the relevant `<vendor>.json` file under `entries`.
2. Cite supporting evidence in `provenance.evidence_audit`.
3. If empirical scan possible (intrinsic anchor field exists OR external cross-ref available), run the scanner to populate `empirical.*` fields.
4. Commit + update `_meta.last_full_rebuild`.

---

## §5 Refresh triggers

- WRDS dump file_count delta ≥ 50 since `_meta.last_full_rebuild` → re-run `wrds_scanner.py`.
- FnGuide dump mtime change → re-run `fnguide_scanner.py`.
- Scanner version bump (logic change) → re-run all affected vendors.
- New vendor / source addition → manual stub + scanner extension.

---

## §6 Authority + governance

- **Meta-harness is single source of truth** for manifest content.
- **Consumer (shared_utils.asof)** is deployed to `portfolio-coordination/shared-utils/` — research repos import it.
- **Manual classification changes** require an audit in `meta-harness/audits/<date>-asof-manifest-<reason>.md`.
- **Empirical scanner runs** auto-update; no audit required (run is the evidence).

---

## §7 Cross-reference

- System launch audit: `audits/2026-06-05-asof-manifest-system-launch.md`
- Portfolio-wide framework: `audits/2026-06-04-asof-date-bias-portfolio-wide-data-source-audit.md`
- Fleet sweep: `audits/2026-06-05-personal-bot-fleet-asof-audit.md`
- KR23 origin: `audits/2026-06-03-KR23-ABANDONED-pre-Phase0-close-report.md` §6
- FnGuide dump snapshot: `data/fnguide-dump-usability-snapshot.md`
- WRDS dump snapshot: `data/wrds-dump-usability-snapshot.md`
- External vendor tier snapshot: `data/external-data-source-tier-snapshot.md`
