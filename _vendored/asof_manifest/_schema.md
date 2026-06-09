# As-of date manifest — schema specification

**Purpose**: per-(vendor, source-file-or-schema, field) record of empirical as-of-date semantics.
Consumer code (`shared_utils/asof.py`) reads this to automatically apply the correct disclosure-date shift, so research repos don't manually verify per-launch.

**Versioning**: schema version `v1` (2026-06-05). Bump on breaking changes only.

---

## §1 Entry key format

```
<vendor>.<source>.<field>
```

Where:
- `vendor` — one of `fnguide` / `wrds` / `dart` / `yfinance` / `krx` / `binance` / `onchain` / `sec_edgar` / `fred` / etc.
- `source` — vendor-specific path or schema identifier:
  - FnGuide xlsx: `E:/Fnguide/매출액_원.xlsx` (file path).
  - FnGuide CSV §B item: `E:/personal_bot_kr_data_fnguide_backup/data_fnguide/<file>.CSV#<item_code>` (file + item code hash).
  - WRDS: `<schema>.<table>` (e.g., `comp_na_daily_all.fundq`).
  - DART: `dart` (single endpoint).
  - SEC EDGAR: `sec_edgar` (single endpoint).
- `field` — column or item identifier:
  - WRDS: column name or `<value_fields>` if applies to all value columns of the table.
  - FnGuide xlsx: filename implies single Item code, so `field = "default"` or specific Item if file bundles multiple.
  - FnGuide CSV §B: Item code (e.g., `FP70904001`).

**Examples**:
- `fnguide.E:/Fnguide/매출액_원.xlsx.default`
- `fnguide.E:/personal_bot_kr_data_fnguide_backup/data_fnguide/한국주식_샤프용EPS_남직원수.CSV#관리종목여부.default`
- `wrds.comp_na_daily_all.fundq.<value_fields>`
- `wrds.tr_ibes.det_xepsus.<forecast_fields>`
- `dart.opendart.rcept_dt`

---

## §2 Entry value schema

```yaml
classification: <enum>           # required
raw_as_of_field: <string|null>   # required — what the source labels as "as-of"
safe_as_of_field: <string|null>  # required — knowable date column to use INSTEAD; null if no intrinsic field
shift_recipe: <enum>             # required
shift_recipe_fallback_days: <int|null>  # required if shift_recipe = "shift_calendar_days" or "shift_business_days"
empirical:                       # optional — populated by scanner runs
  delta_median_days: <number>    #   median (raw_as_of - safe_as_of) in days
  delta_p10_p90: [<number>, <number>]
  n_evidence: <int>
  cross_ref_source: <string>     #   how empirical delta was measured
  last_scanned: <iso8601>
notes: <string|null>             # optional human-readable
provenance:                      # required
  evidence_audit: <string>       #   audit file path establishing this entry
  added: <iso8601>
  last_reviewed: <iso8601>
```

### §2.1 `classification` enum

- `safe` — column-date = knowable date. No shift needed.
- `pattern_a_intrinsic_anchor_available` — column-date = fiscal/aggregation-period end, BUT same-table column carries the knowable date. Shift = use `safe_as_of_field`.
- `pattern_a_no_intrinsic_anchor` — column-date = fiscal/aggregation-period end, no clean anchor in source. Shift = `shift_calendar_days` or `shift_business_days` with conservative fallback.
- `pattern_a_external_cross_ref_required` — column-date = fiscal/aggregation-period end, requires external lookup (e.g., FnGuide → DART rcept_dt). Shift = `external_lookup`.
- `pattern_b_forward_fill_backwards` — vendor stores future event date in past columns. Shift = `external_lookup` (mandatory) + reject of any row where stored date > computed knowable date.
- `pattern_c_latest_restatement` — vendor stores latest revision only. Shift = `use_vintage_source` (e.g., FRED-ALFRED instead of FRED).
- `suspected_<pattern>` — empirically unverified; treat as the worst-case pattern until scanner verifies.
- `static` — time-invariant (e.g., sector code, ticker). No shift concept applies.

### §2.2 `shift_recipe` enum

- `none` — pass through.
- `use_intrinsic_anchor` — replace as_of_date with the `safe_as_of_field` value from same row.
- `shift_calendar_days` — `as_of_date = raw_date + shift_recipe_fallback_days` (calendar days).
- `shift_business_days` — `as_of_date = raw_date + shift_recipe_fallback_days` (business days).
- `external_lookup` — call a vendor-specific resolver (e.g., DART OpenAPI rcept_dt cross-reference; KRX KIND announcement lookup). The resolver must be implemented in `shared_utils.asof._resolvers`.
- `use_vintage_source` — directive to switch data source entirely (Pattern C).
- `reject` — mark this field as not usable; consumer raises if accessed.

---

## §3 Top-level manifest file structure

Each `<vendor>.json` is one JSON document:

```json
{
  "_meta": {
    "schema_version": "v1",
    "vendor": "<vendor>",
    "last_full_rebuild": "<iso8601>",
    "scanner_version": "<commit-hash-or-tag>",
    "dump_root_or_endpoint": "<path-or-URL>",
    "notes": "<free-text>"
  },
  "entries": {
    "<entry_key>": { ...entry_value... },
    "...": "..."
  }
}
```

---

## §4 Consumer API

`shared_utils.asof` (deployed to portfolio-coordination/shared-utils):

```python
def load_manifest(vendor: str) -> dict:
    """Load <vendor>.json manifest from meta-harness/data/asof-manifest/."""

def asof_shift(vendor: str, source: str, field: str, raw_date) -> pd.Timestamp:
    """Look up the entry and apply the shift recipe. raw_date is the column-date.
    Returns the corrected knowable-by date."""

def load_panel_with_asof(path: str, vendor: str, **kwargs) -> pd.DataFrame:
    """Vendor-specific panel loader. Output guarantees an 'as_of_date' column
    that has been shifted per manifest. Raises if vendor field not in manifest."""

def assert_no_lookahead(panel: pd.DataFrame, value_cols: list = None) -> None:
    """Pytest-friendly: assert no row has disclosure_date > as_of_date_used
    while value_cols is non-null. Cross-references with manifest classifications."""
```

---

## §5 Refresh protocol

Scanner scripts in `D:/vscode/meta-harness/scripts/build-asof-manifest/`:
- `wrds_scanner.py` — reads dump csv.gz files, computes empirical datadate→rdq / fpedats→anndats deltas.
- `fnguide_scanner.py` — reads E:/Fnguide/ + §B dump, cross-references DART OpenAPI rcept_dt for 50-firm sample.
- `dart_scanner.py` / `yfinance_scanner.py` / `krx_scanner.py` — trivial (sources are knowable-date-stamped by definition).

Trigger to re-run:
1. WRDS dump file_count delta ≥ 50 since `_meta.last_full_rebuild`.
2. FnGuide dump update (file mtime change on E:/Fnguide/ or backup root).
3. Manual refresh requested by user.
4. Scanner version bump (logic change).

After re-run, scanner overwrites the affected `<vendor>.json` and bumps `_meta.last_full_rebuild`. Consumers reload automatically (no in-process cache; manifest read every call OR per-session cached, configurable).

---

## §6 Authority + propagation

- **Single source of truth**: `D:/vscode/meta-harness/data/asof-manifest/`.
- **Consumer location**: `D:/vscode/portfolio-coordination/shared-utils/shared_utils/asof.py`.
- **Research repo usage**: `from shared_utils.asof import load_panel_with_asof, assert_no_lookahead`. The manifest read is from meta-harness path; portfolio-coordination is the API.
- **Modification policy**: manifest entries can be added or empirical fields refreshed by scanner; manual classification changes require an audit in `meta-harness/audits/<date>-asof-manifest-<reason>.md`.

End of schema spec.
