"""asof — as-of-date semantics consumer (vendored to each research repo).

Deployment pattern (2026-06-05 bootstrap-time vendored copy):
    <repo>/_vendored/asof.py              ← this module (copy of meta-harness template)
    <repo>/_vendored/asof_manifest/       ← sibling manifest snapshot
        ├── _manifest.lock                 ← SHA256 + schema_version pin
        ├── fnguide.json
        ├── wrds.json
        └── ... (one per vendor)

Manifest SoT: D:/vscode/meta-harness/data/asof-manifest/<vendor>.json
Schema spec:  D:/vscode/meta-harness/data/asof-manifest/_schema.md
Sync utility: D:/vscode/meta-harness/scripts/asof-vendored/sync.py

Usage in research repos:
    from _vendored.asof import load_panel_with_asof, assert_no_lookahead, check_drift

    # Drift check (call once at session start or before backtest)
    drift = check_drift()
    if drift.schema_breaking:
        raise SystemExit("re-bootstrap required: schema version mismatch")
    if not drift.in_sync:
        print(f"warning: {drift.drifted_files} are stale; consider sync")

    # Auto-shifted panel load
    panel = load_panel_with_asof("E:/Fnguide/매출액_원.xlsx", vendor="fnguide")
    assert_no_lookahead(panel, value_cols=["revenue", "operating_income"])

Public API:
    SUPPORTED_SCHEMA_VERSIONS — tuple of versions this module supports
    load_manifest(vendor) -> dict
    classify(vendor, source, field) -> dict (entry record)
    asof_shift(vendor, source, field, raw_date, **lookup_kwargs) -> pd.Timestamp
    load_panel_with_asof(path, vendor, **kwargs) -> pd.DataFrame
    assert_no_lookahead(panel, value_cols=None) -> None
    register_resolver(name, fn) -> None
    check_drift(strict_schema=True) -> DriftResult
    DriftResult — dataclass with .in_sync, .drifted_files, .schema_breaking, .report()

Conventions:
    - Vendored manifest path = `Path(__file__).parent / "asof_manifest"` (auto-discover).
    - Override via `ASOF_MANIFEST_ROOT` env var if needed.
    - Wildcard matching: entries with '*' or '<...>' in keys match by glob.
    - Missing entry → AsofManifestMissingEntryError.
    - Schema-version mismatch → SchemaVersionMismatchError (always raises if strict_schema=True).
    - Entry-content drift → warning only; user runs sync.py explicitly.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pandas as pd


# ============================================================================
# Schema-version pinning
# ============================================================================

SUPPORTED_SCHEMA_VERSIONS = ("v1",)


# ============================================================================
# Manifest location — auto-discover sibling `asof_manifest/` folder
# ============================================================================

def _default_manifest_root() -> Path:
    """Vendored layout: <repo>/_vendored/asof.py + <repo>/_vendored/asof_manifest/.
    If the sibling folder exists, use it. Otherwise fall back to meta-harness SoT
    (for meta-harness internal testing or direct development).
    """
    # env override has highest priority
    env_root = os.environ.get("ASOF_MANIFEST_ROOT")
    if env_root:
        return Path(env_root)
    # sibling auto-discover
    sibling = Path(__file__).resolve().parent / "asof_manifest"
    if sibling.exists() and any(sibling.glob("*.json")):
        return sibling
    # fallback (development / meta-harness internal)
    return Path("D:/vscode/meta-harness/data/asof-manifest")


_DEFAULT_MANIFEST_ROOT = _default_manifest_root()


# ============================================================================
# Exceptions
# ============================================================================


class AsofManifestError(Exception):
    """Base for all as-of manifest errors."""


class AsofManifestMissingEntryError(AsofManifestError):
    """Raised when a (vendor, source, field) lookup has no matching entry."""


class AsofManifestRejectError(AsofManifestError):
    """Raised when the manifest classification is 'reject' (e.g., Pattern B forward-fill-backwards field)."""


class AsofResolverNotRegisteredError(AsofManifestError):
    """Raised when shift_recipe='external_lookup' but no resolver is registered."""


class SchemaVersionMismatchError(AsofManifestError):
    """Raised when the vendored manifest's schema_version is not in SUPPORTED_SCHEMA_VERSIONS.

    This is a breaking-change signal — the asof.py code may not understand the new manifest
    structure. Resolution: re-bootstrap the vendored copy (which updates both asof.py and
    the manifest atomically) via meta-harness/scripts/asof-vendored/sync.py.
    """


# ============================================================================
# Manifest loading + caching
# ============================================================================

_MANIFEST_CACHE: Dict[str, dict] = {}


def load_manifest(vendor: str, manifest_root: Optional[Path] = None) -> dict:
    """Load <vendor>.json manifest. Cached per-process."""
    root = manifest_root or _DEFAULT_MANIFEST_ROOT
    cache_key = f"{root}::{vendor}"
    if cache_key in _MANIFEST_CACHE:
        return _MANIFEST_CACHE[cache_key]
    path = root / f"{vendor}.json"
    if not path.exists():
        raise AsofManifestError(f"manifest not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    _MANIFEST_CACHE[cache_key] = manifest
    return manifest


def invalidate_cache(vendor: Optional[str] = None) -> None:
    """Clear cached manifest(s). Call after scanner re-run if running in same process."""
    if vendor is None:
        _MANIFEST_CACHE.clear()
    else:
        for k in list(_MANIFEST_CACHE.keys()):
            if k.endswith(f"::{vendor}"):
                del _MANIFEST_CACHE[k]


# ============================================================================
# Entry lookup with wildcard support
# ============================================================================


def _entry_key(vendor: str, source: str, field: str) -> str:
    return f"{vendor}.{source}.{field}"


def _glob_to_regex(pattern: str) -> re.Pattern:
    """Convert manifest wildcard key (with '*' and '<placeholder>') to a regex."""
    # Replace '<...>' placeholders with .* and unescaped '*' with [^.]*
    # (we keep dots literal to respect the segmenting of the key)
    pat = re.escape(pattern)
    pat = pat.replace(r"\<", "<").replace(r"\>", ">")
    pat = re.sub(r"<[^>]+>", ".*", pat)
    pat = pat.replace(r"\*", ".*")
    return re.compile(f"^{pat}$")


def classify(vendor: str, source: str, field: str) -> dict:
    """Find the best-matching manifest entry for (vendor, source, field).

    Returns the entry value dict. Raises AsofManifestMissingEntryError if no match.

    Matching order:
      1. Exact key match.
      2. Wildcard glob (entries with '*' or '<...>' in key).
    """
    manifest = load_manifest(vendor)
    entries = manifest.get("entries", {})
    query = _entry_key(vendor, source, field)

    if query in entries:
        return entries[query]

    # Wildcard fallback
    candidates = []
    for key, entry in entries.items():
        if "*" in key or "<" in key:
            pattern = _glob_to_regex(key)
            if pattern.match(query):
                candidates.append((key, entry))
    if len(candidates) == 1:
        return candidates[0][1]
    if len(candidates) > 1:
        # Prefer the most specific (longest non-wildcard prefix)
        candidates.sort(key=lambda kv: len(kv[0].replace("*", "").replace("<", "")), reverse=True)
        return candidates[0][1]

    raise AsofManifestMissingEntryError(
        f"No manifest entry for {query!r}. "
        f"Add an entry to {vendor}.json or use a wildcard pattern. "
        f"Available top-level keys (first 5): {list(entries)[:5]}"
    )


# ============================================================================
# Resolver registry (for external_lookup)
# ============================================================================

_RESOLVERS: Dict[str, Callable[..., pd.Timestamp]] = {}


def register_resolver(name: str, fn: Callable[..., pd.Timestamp]) -> None:
    """Register a resolver for shift_recipe='external_lookup'.

    Signature: fn(symbol, raw_date, **kwargs) -> pd.Timestamp (the knowable date)
    """
    _RESOLVERS[name] = fn


def _get_resolver(name: str) -> Callable[..., pd.Timestamp]:
    if name not in _RESOLVERS:
        raise AsofResolverNotRegisteredError(
            f"No resolver registered for {name!r}. "
            f"Call register_resolver({name!r}, your_fn) before asof_shift."
        )
    return _RESOLVERS[name]


# ============================================================================
# Shift computation
# ============================================================================


def asof_shift(
    vendor: str,
    source: str,
    field: str,
    raw_date,
    *,
    fallback: bool = False,
    **lookup_kwargs,
) -> pd.Timestamp:
    """Shift raw column-date to the actual knowable-by date per manifest.

    Parameters:
        vendor, source, field: manifest lookup key.
        raw_date: the column date as stored by the vendor.
        fallback: if True and shift_recipe='external_lookup' but no resolver,
                  use shift_recipe_fallback_days (calendar days). Default False
                  raises so unresolved external lookups fail loudly.
        **lookup_kwargs: passed through to the resolver (e.g., symbol).

    Returns:
        pd.Timestamp of the knowable-by date.
    """
    entry = classify(vendor, source, field)
    recipe = entry.get("shift_recipe", "none")
    raw_ts = pd.Timestamp(raw_date)

    if recipe == "none":
        return raw_ts

    if recipe == "reject":
        raise AsofManifestRejectError(
            f"Field {vendor}.{source}.{field} is classified as reject (e.g., Pattern B "
            f"forward-fill-backwards). Per manifest entry, this field cannot be used as "
            f"an as-of anchor. Source ref: {entry.get('provenance', {}).get('evidence_audit')}"
        )

    if recipe == "shift_calendar_days":
        days = int(entry.get("shift_recipe_fallback_days", 0))
        return raw_ts + pd.Timedelta(days=days)

    if recipe == "shift_business_days":
        days = int(entry.get("shift_recipe_fallback_days", 0))
        return raw_ts + pd.tseries.offsets.BDay(days)

    if recipe == "use_intrinsic_anchor":
        # Caller must provide the anchor value via lookup_kwargs[entry["safe_as_of_field"]]
        anchor_field = entry["safe_as_of_field"]
        if anchor_field not in lookup_kwargs:
            raise AsofManifestError(
                f"shift_recipe='use_intrinsic_anchor' requires the caller to pass "
                f"{anchor_field}=<value> as a keyword argument."
            )
        anchor_val = lookup_kwargs[anchor_field]
        if pd.isna(anchor_val):
            # Fall back to shift_recipe_fallback_days if available
            fb_days = entry.get("shift_recipe_fallback_days")
            if fb_days is not None:
                return raw_ts + pd.Timedelta(days=int(fb_days))
            raise AsofManifestError(
                f"Intrinsic anchor field {anchor_field} is NULL and no fallback days. "
                f"Cannot shift {raw_date}."
            )
        return pd.Timestamp(anchor_val)

    if recipe == "external_lookup":
        # Resolver name follows pattern: 'use_dart_rcept_dt' -> 'dart' resolver,
        # 'use_krx_kind_announcement' -> 'krx_kind', etc.
        # If we have a resolver, call it.
        resolver_hint = entry.get("safe_as_of_field") or entry.get("notes", "")
        resolver_name = None
        if "dart" in resolver_hint.lower() or "rcept" in resolver_hint.lower():
            resolver_name = "dart"
        elif "kind" in resolver_hint.lower():
            resolver_name = "krx_kind"
        elif "sec_edgar" in resolver_hint.lower() or "acceptance" in resolver_hint.lower():
            resolver_name = "sec_edgar"

        if resolver_name and resolver_name in _RESOLVERS:
            try:
                return _get_resolver(resolver_name)(raw_date=raw_ts, **lookup_kwargs)
            except Exception as e:
                if fallback:
                    fb = entry.get("shift_recipe_fallback_days", 0)
                    return raw_ts + pd.Timedelta(days=int(fb))
                raise

        if fallback:
            fb = entry.get("shift_recipe_fallback_days", 0)
            return raw_ts + pd.Timedelta(days=int(fb))

        raise AsofResolverNotRegisteredError(
            f"shift_recipe='external_lookup' for {vendor}.{source}.{field} "
            f"requires resolver '{resolver_name or '(undetermined)'}'. "
            f"Either register_resolver(...) or pass fallback=True to use "
            f"shift_recipe_fallback_days={entry.get('shift_recipe_fallback_days')}."
        )

    raise AsofManifestError(f"Unknown shift_recipe: {recipe!r}")


# ============================================================================
# Vendor-specific panel loaders (subset; extend as needed)
# ============================================================================


def load_panel_with_asof(path: str, vendor: str, **kwargs) -> pd.DataFrame:
    """Vendor-aware panel loader that returns a DataFrame with an 'as_of_date' column
    that has been shifted per the manifest.

    Currently implemented:
        - fnguide xlsx (single-Item file, melted to long-form per stock-date)
        - fnguide csv (KR §A daily multi-stock + §B daily multi-item)
        - wrds csv.gz (Compustat fundq / IBES with intrinsic anchors)
        - yfinance daily price

    Extend by adding new branches as new vendors are onboarded.
    """
    if vendor == "fnguide":
        ext = Path(path).suffix.lower()
        if ext == ".csv":
            return _load_fnguide_csv(path, **kwargs)
        if ext in (".xlsx", ".xls"):
            return _load_fnguide_xlsx(path, **kwargs)
        raise ValueError(
            f"Unsupported FnGuide file extension {ext!r}: {path}. "
            f"Expected .csv, .xlsx, or .xls."
        )
    if vendor == "wrds":
        return _load_wrds_csv_gz(path, **kwargs)
    if vendor == "yfinance":
        return _load_yfinance_daily(path, **kwargs)
    raise NotImplementedError(
        f"load_panel_with_asof not yet implemented for vendor={vendor!r}. "
        f"Add a branch in shared_utils.asof or call classify() + asof_shift() manually."
    )


# ---- FnGuide layout helpers -------------------------------------------------

_FNGUIDE_TICKER_RE = re.compile(r"^A\d{6}$")


def _find_term_row(df: pd.DataFrame, *, max_rows: int = 20) -> int:
    """FnGuide convention: Term row carries the frequency marker — 'D' / 'M' / 'Y'
    in one of the columns. Heuristic returns the first matching row index.
    """
    limit = min(max_rows, len(df))
    for i in range(limit):
        row = df.iloc[i].dropna().astype(str)
        if any(v.strip() in {"D", "M", "Y"} for v in row):
            return i
    raise ValueError("FnGuide Term row not located in first 20 rows")


def _find_symbol_row(df: pd.DataFrame, *, after: int = 0, lookahead: int = 10) -> int:
    """Symbol header row holds at least 3 KRX A###### tickers."""
    limit = min(after + lookahead, len(df))
    for i in range(after, limit):
        row = df.iloc[i].dropna().astype(str)
        if sum(1 for v in row if _FNGUIDE_TICKER_RE.match(v.strip())) >= 3:
            return i
    raise ValueError(f"FnGuide Symbol header row not located within {lookahead} rows of {after}")


def _find_data_start_row(df: pd.DataFrame, *, after: int = 0, lookahead: int = 10) -> int:
    """Data starts at the first row after `after` whose column-0 cell parses as a date."""
    limit = min(after + 1 + lookahead, len(df))
    for i in range(after + 1, limit):
        cell = df.iat[i, 0]
        if pd.isna(cell):
            continue
        try:
            ts = pd.to_datetime(cell, errors="raise")
            if pd.notna(ts):
                return i
        except (ValueError, TypeError):
            continue
    raise ValueError(f"FnGuide data start row not located within {lookahead} rows of {after}")


def _vectorized_asof_shift(
    raw_dates: pd.Series,
    *,
    vendor: str,
    source: str,
    field: str,
    fallback: bool = True,
    symbol_series: Optional[pd.Series] = None,
) -> pd.Series:
    """Apply asof_shift to a date series, vectorising recipes that don't depend
    on per-row state. Returns a pd.Series of pd.Timestamp aligned to raw_dates.
    """
    entry = classify(vendor=vendor, source=source, field=field)
    recipe = entry.get("shift_recipe", "none")
    raw = pd.to_datetime(raw_dates, errors="coerce")

    if recipe == "none":
        return raw
    if recipe == "reject":
        raise AsofManifestRejectError(
            f"Field {vendor}.{source}.{field} classified reject — cannot use as as-of anchor. "
            f"Source ref: {entry.get('provenance', {}).get('evidence_audit')}"
        )
    if recipe == "shift_calendar_days":
        days = int(entry.get("shift_recipe_fallback_days", 0))
        return raw + pd.Timedelta(days=days)
    if recipe == "shift_business_days":
        days = int(entry.get("shift_recipe_fallback_days", 0))
        return raw.map(lambda d: d + pd.tseries.offsets.BDay(days) if pd.notna(d) else d)

    # Per-row recipes (use_intrinsic_anchor / external_lookup)
    if symbol_series is None:
        def _shift_one(d):
            if pd.isna(d):
                return d
            return asof_shift(vendor, source, field, d, fallback=fallback)
        return raw.map(_shift_one)

    out = []
    for d, sym in zip(raw, symbol_series):
        if pd.isna(d):
            out.append(d)
            continue
        out.append(asof_shift(vendor, source, field, d, fallback=fallback, symbol=sym))
    return pd.Series(out, index=raw.index)


# ---- FnGuide loaders --------------------------------------------------------


def _load_fnguide_xlsx(
    path: str,
    *,
    drop_na_values: bool = False,
    fallback: bool = True,
    **kwargs,
) -> pd.DataFrame:
    """Load a single-Item FnGuide xlsx file (rows=dates, columns=stock symbols).

    FnGuide §A layout (heuristic auto-detect, see KR23 §6.3 snapshot):
      Row ~3   Term row     — frequency marker ('D' / 'M' / 'Y') in some column
      Row ~7-8 Symbol row   — A###### KRX tickers across columns 1+
      Row ~11+ Data rows    — column 0 = date axis, columns 1+ = per-stock values

    Parameters:
        path: xlsx file path. Must be present in the FnGuide manifest as
              `fnguide.<path>.default` (otherwise AsofManifestMissingEntryError).
        drop_na_values: if True drop rows whose value is NaN. Default False
                        preserves missing values (관리종목 / 거래정지 information).
        fallback: passed to asof_shift; if True use shift_recipe_fallback_days
                  when external resolver is unregistered.

    Returns:
        Long-form pd.DataFrame with columns [symbol, raw_date, value, as_of_date].
    """
    # Verify the file is registered before incurring xlsx read cost
    classify(vendor="fnguide", source=path, field="default")

    df_raw = pd.read_excel(path, header=None, engine="openpyxl")

    term_row = _find_term_row(df_raw)
    symbol_row = _find_symbol_row(df_raw, after=term_row)
    data_start_row = _find_data_start_row(df_raw, after=symbol_row)

    # Extract symbol header — column 0 is the date axis, columns 1+ are tickers
    raw_symbols = df_raw.iloc[symbol_row].astype(str).tolist()
    symbol_cols: List[int] = []
    symbols: List[str] = []
    seen: set = set()
    for col_idx, raw_sym in enumerate(raw_symbols):
        if col_idx == 0:
            continue
        sym = raw_sym.strip()
        if not _FNGUIDE_TICKER_RE.match(sym):
            continue
        if sym in seen:
            # Edge case §2.5.3: duplicate ticker — keep first match.
            continue
        seen.add(sym)
        symbol_cols.append(col_idx)
        symbols.append(sym)

    if not symbols:
        raise ValueError(
            f"FnGuide xlsx {path}: no A###### tickers found in row {symbol_row}. "
            f"Header may have non-standard format."
        )

    # Slice the data block: column 0 (dates) + selected symbol columns
    cols_to_keep = [0] + symbol_cols
    data_block = df_raw.iloc[data_start_row:, cols_to_keep].copy()
    data_block.columns = ["raw_date"] + symbols
    data_block = data_block.reset_index(drop=True)

    long = data_block.melt(
        id_vars=["raw_date"],
        var_name="symbol",
        value_name="value",
    )
    long["raw_date"] = pd.to_datetime(long["raw_date"], errors="coerce")
    long = long.dropna(subset=["raw_date"]).reset_index(drop=True)

    if drop_na_values:
        long = long.dropna(subset=["value"]).reset_index(drop=True)

    long["as_of_date"] = _vectorized_asof_shift(
        long["raw_date"],
        vendor="fnguide",
        source=path,
        field="default",
        fallback=fallback,
        symbol_series=long["symbol"],
    )

    return long


def _load_fnguide_csv(
    path: str,
    *,
    drop_na_values: bool = False,
    fallback: bool = True,
    encoding: Optional[str] = None,
    **kwargs,
) -> pd.DataFrame:
    """Load a FnGuide CSV file (e.g., E:/Fnguide/daily_price.csv).

    Layout differs from xlsx: column headers are already symbols and the first
    column is the date axis. Auto-detects the date column via a small regex set.

    Parameters:
        path: csv file path. Must be registered under `fnguide.<path>.default`.
        drop_na_values: if True drop rows whose value is NaN.
        fallback: passed to asof_shift.
        encoding: explicit encoding override. Default tries utf-8 then cp949
                  (§2.5.1 edge case — KR vendors frequently ship cp949).

    Returns:
        Long-form pd.DataFrame with columns [symbol, raw_date, value, as_of_date].
    """
    classify(vendor="fnguide", source=path, field="default")

    if encoding is None:
        try:
            df_raw = pd.read_csv(path, low_memory=False, encoding="utf-8")
        except UnicodeDecodeError:
            df_raw = pd.read_csv(path, low_memory=False, encoding="cp949")
    else:
        df_raw = pd.read_csv(path, low_memory=False, encoding=encoding)

    date_pattern = re.compile(r"^(date|raw_date|trade_date|일자|날짜|Date)$", re.IGNORECASE)
    date_col = next(
        (c for c in df_raw.columns if isinstance(c, str) and date_pattern.match(c)),
        df_raw.columns[0],
    )

    # Deduplicate symbol columns (edge §2.5.3) and drop non-ticker metadata columns.
    seen_cols: set = set()
    keep_cols: List[str] = [date_col]
    for c in df_raw.columns:
        if c == date_col:
            continue
        c_str = str(c).strip()
        if c_str in seen_cols:
            continue
        seen_cols.add(c_str)
        keep_cols.append(c)
    df_raw = df_raw[keep_cols]

    long = df_raw.melt(
        id_vars=[date_col],
        var_name="symbol",
        value_name="value",
    )
    long = long.rename(columns={date_col: "raw_date"})
    long["raw_date"] = pd.to_datetime(long["raw_date"], errors="coerce")
    long = long.dropna(subset=["raw_date"]).reset_index(drop=True)
    long["symbol"] = long["symbol"].astype(str)

    if drop_na_values:
        long = long.dropna(subset=["value"]).reset_index(drop=True)

    long["as_of_date"] = _vectorized_asof_shift(
        long["raw_date"],
        vendor="fnguide",
        source=path,
        field="default",
        fallback=fallback,
        symbol_series=long["symbol"],
    )

    return long


def _load_wrds_csv_gz(path: str, **kwargs) -> pd.DataFrame:
    """Load a WRDS dump csv.gz file. Auto-detect schema.table from filename and
    apply intrinsic-anchor shift if applicable.

    Convention: filename = '<schema>.<table>.csv.gz'.
    """
    p = Path(path)
    name = p.name
    if not name.endswith(".csv.gz"):
        raise ValueError(f"expected <schema>.<table>.csv.gz, got {name}")
    schema_table = name[:-7]  # strip .csv.gz
    parts = schema_table.split(".")
    if len(parts) != 2:
        raise ValueError(f"expected '<schema>.<table>' in filename, got {schema_table!r}")
    schema, table = parts

    df = pd.read_csv(path, compression="gzip", low_memory=False)

    # Look up manifest for any field
    entry = classify(vendor="wrds", source=f"{schema}.{table}", field="<value_fields>")
    safe_field = entry.get("safe_as_of_field")
    raw_field = entry.get("raw_as_of_field")

    if safe_field and safe_field in df.columns:
        df["as_of_date"] = pd.to_datetime(df[safe_field], errors="coerce")
    elif raw_field and raw_field in df.columns:
        # Apply shift_calendar_days / shift_business_days
        df["as_of_date"] = pd.to_datetime(df[raw_field], errors="coerce")
        fb = entry.get("shift_recipe_fallback_days")
        if entry.get("shift_recipe") == "shift_calendar_days" and fb:
            df["as_of_date"] = df["as_of_date"] + pd.Timedelta(days=int(fb))
        elif entry.get("shift_recipe") == "shift_business_days" and fb:
            df["as_of_date"] = df["as_of_date"] + pd.tseries.offsets.BDay(int(fb))
    else:
        raise AsofManifestError(
            f"Neither safe_as_of_field={safe_field} nor raw_as_of_field={raw_field} "
            f"found as a column in {schema}.{table}. Manifest entry may need update."
        )

    return df


def _load_yfinance_daily(path: str, **kwargs) -> pd.DataFrame:
    """yfinance daily price is SAFE — pass through with as_of_date=date column."""
    df = pd.read_parquet(path) if path.endswith(".parquet") else pd.read_csv(path)
    date_col = next((c for c in ["date", "Date", "trade_date"] if c in df.columns), None)
    if date_col is None:
        raise ValueError(f"no date column found in {path}; columns: {list(df.columns)}")
    df["as_of_date"] = pd.to_datetime(df[date_col])
    return df


# ============================================================================
# Look-ahead guard
# ============================================================================


def assert_no_lookahead(
    panel: pd.DataFrame,
    *,
    value_cols: Optional[list] = None,
    as_of_col: str = "as_of_date",
    disclosure_col: str = "disclosure_date",
) -> None:
    """Pytest-friendly guard: assert no row has disclosure > as_of (with non-null value).

    Requires the panel to have both an 'as_of_date' column (already shifted via asof_shift
    or load_panel_with_asof) and a 'disclosure_date' column (the verified knowable date).

    For panels built purely from manifest-shifted data, as_of_date IS the knowable date,
    so no separate disclosure_date is needed; just verify monotonicity.
    """
    if as_of_col not in panel.columns:
        raise ValueError(f"panel missing {as_of_col!r} column. Was the loader applied?")

    # If panel doesn't have a separate disclosure_col, just verify as_of monotonicity per symbol
    if disclosure_col not in panel.columns:
        # No cross-reference available; only check that as_of is non-null where value is non-null
        if value_cols:
            for col in value_cols:
                if col not in panel.columns:
                    continue
                null_asof = panel[panel[col].notna() & panel[as_of_col].isna()]
                if not null_asof.empty:
                    raise AssertionError(
                        f"{len(null_asof)} rows have non-null {col!r} but NULL {as_of_col!r}. "
                        f"Cannot verify look-ahead without an as-of anchor. Sample:\n"
                        f"{null_asof[[as_of_col, col]].head().to_string()}"
                    )
        return

    # Cross-reference check
    if value_cols is None:
        value_cols = [c for c in panel.columns if c not in (as_of_col, disclosure_col)]

    for col in value_cols:
        if col not in panel.columns:
            continue
        mask = (panel[disclosure_col] > panel[as_of_col]) & panel[col].notna()
        leaked = panel[mask]
        if not leaked.empty:
            n = len(leaked)
            total = panel[col].notna().sum()
            pct = 100.0 * n / max(total, 1)
            sample = leaked[[as_of_col, disclosure_col, col]].head(5).to_string()
            raise AssertionError(
                f"Look-ahead detected in {col!r}: {n}/{total} ({pct:.2f}%) rows have "
                f"{disclosure_col} > {as_of_col}. Sample:\n{sample}"
            )


# ============================================================================
# Drift detection
# ============================================================================


@dataclass
class DriftResult:
    """Result of comparing vendored manifest snapshot against meta-harness SoT.

    Attributes:
        in_sync: True iff all files have matching SHA256 AND schema versions match.
        drifted_files: list of manifest filenames whose SHA256 differs.
        schema_breaking: True iff any vendored file's _meta.schema_version is not in
            SUPPORTED_SCHEMA_VERSIONS, OR if the SoT file's schema_version differs.
        missing_lock: True if no _manifest.lock found (vendored layout not initialized).
        sot_path_checked: meta-harness SoT path that was compared against, or None.
        vendored_path: vendored manifest root path.
        lock_age_days: days since the vendored snapshot was last synced (None if no lock).
    """
    in_sync: bool
    drifted_files: List[str] = field(default_factory=list)
    schema_breaking: bool = False
    missing_lock: bool = False
    sot_path_checked: Optional[str] = None
    vendored_path: Optional[str] = None
    lock_age_days: Optional[int] = None

    def report(self) -> str:
        """Human-readable one-paragraph summary for printing at session start."""
        if self.missing_lock:
            return (
                f"asof: vendored layout NOT initialized (no _manifest.lock at "
                f"{self.vendored_path}). Run sync.py to bootstrap."
            )
        if self.schema_breaking:
            return (
                f"asof: ⚠ SCHEMA BREAKING — vendored schema_version not in "
                f"{SUPPORTED_SCHEMA_VERSIONS}. Re-bootstrap required: "
                f"python D:/vscode/meta-harness/scripts/asof-vendored/sync.py <this-repo>"
            )
        if self.in_sync:
            age = f" (sync age {self.lock_age_days}d)" if self.lock_age_days is not None else ""
            return f"asof: vendored manifest in sync with meta-harness{age}"
        return (
            f"asof: ⚠ drift detected in {len(self.drifted_files)} files: "
            f"{', '.join(self.drifted_files[:3])}{'...' if len(self.drifted_files) > 3 else ''}. "
            f"Run: python D:/vscode/meta-harness/scripts/asof-vendored/sync.py <this-repo>"
        )


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def check_drift(
    *,
    vendored_root: Optional[Path] = None,
    sot_root: Optional[Path] = None,
    strict_schema: bool = True,
) -> DriftResult:
    """Compare vendored manifest snapshot against meta-harness SoT.

    Parameters:
        vendored_root: vendored manifest folder. Default: auto-detected per `_default_manifest_root`.
        sot_root: meta-harness SoT folder. Default: `D:/vscode/meta-harness/data/asof-manifest`.
        strict_schema: if True, raise `SchemaVersionMismatchError` immediately on schema breaking.

    Returns:
        DriftResult.

    Raises:
        SchemaVersionMismatchError: if strict_schema=True and breaking schema detected.
    """
    if vendored_root is None:
        vendored_root = _DEFAULT_MANIFEST_ROOT
    if sot_root is None:
        sot_root = Path("D:/vscode/meta-harness/data/asof-manifest")

    lock_path = Path(vendored_root) / "_manifest.lock"
    if not lock_path.exists():
        return DriftResult(
            in_sync=False,
            missing_lock=True,
            vendored_path=str(vendored_root),
            sot_path_checked=str(sot_root),
        )

    with open(lock_path, "r", encoding="utf-8") as f:
        lock = json.load(f)

    # Schema version check
    vendored_schema = lock.get("schema_version")
    breaking = vendored_schema not in SUPPORTED_SCHEMA_VERSIONS

    # Hash drift
    drifted = []
    if sot_root.exists():
        for filename, expected_hash in lock.get("files", {}).items():
            sot_file = Path(sot_root) / filename
            if not sot_file.exists():
                continue
            live_hash = _sha256_file(sot_file)
            if live_hash != expected_hash:
                drifted.append(filename)
            # Also check SoT schema version against supported set
            try:
                with open(sot_file, "r", encoding="utf-8") as f:
                    live_meta = json.load(f).get("_meta", {})
                live_schema = live_meta.get("schema_version")
                if live_schema and live_schema != vendored_schema:
                    breaking = True
            except Exception:
                pass

    # Age in days
    age_days = None
    try:
        synced_at = lock.get("synced_at") or lock.get("bootstrapped_at")
        if synced_at:
            synced_dt = datetime.fromisoformat(synced_at.replace("Z", "+00:00"))
            age_days = (datetime.now(synced_dt.tzinfo) - synced_dt).days
    except Exception:
        pass

    if breaking and strict_schema:
        raise SchemaVersionMismatchError(
            f"vendored schema_version={vendored_schema!r} not in supported "
            f"{SUPPORTED_SCHEMA_VERSIONS}. Re-bootstrap required."
        )

    return DriftResult(
        in_sync=(not drifted and not breaking),
        drifted_files=drifted,
        schema_breaking=breaking,
        missing_lock=False,
        sot_path_checked=str(sot_root),
        vendored_path=str(vendored_root),
        lock_age_days=age_days,
    )


# ============================================================================
# Built-in resolver stubs (override these with real implementations)
# ============================================================================


def _stub_dart_resolver(raw_date, symbol: Optional[str] = None, **kwargs):
    """Stub DART resolver. Real implementation should call DART OpenAPI to find
    the actual rcept_dt for (corp_code, period_around_raw_date).

    For now, applies a conservative +90 calendar day shift as a fallback.
    """
    return pd.Timestamp(raw_date) + pd.Timedelta(days=90)


def _stub_sec_edgar_resolver(raw_date, symbol: Optional[str] = None, **kwargs):
    """Stub SEC EDGAR resolver. Real implementation should call EDGAR full-text-search
    to find acceptance_datetime for (cik, filing_type, period_around_raw_date).

    For now, +60 calendar day shift fallback (typical 10-K filing deadline).
    """
    return pd.Timestamp(raw_date) + pd.Timedelta(days=60)


def _stub_krx_kind_resolver(raw_date, symbol: Optional[str] = None, **kwargs):
    """Stub KRX KIND resolver for 관리종목 / KOSPI200 rebalance announcements.

    Real implementation should query KIND public posting timestamps.

    For now, no shift (assume FnGuide column-date is on-or-after KIND announcement).
    Conservative behavior: subtract 15 trading days if entry shift_recipe_fallback_days is set.
    """
    # Until empirical KIND cross-ref is built, return raw_date (no shift).
    return pd.Timestamp(raw_date)


# Register stub resolvers by default; production deployment should override these.
register_resolver("dart", _stub_dart_resolver)
register_resolver("sec_edgar", _stub_sec_edgar_resolver)
register_resolver("krx_kind", _stub_krx_kind_resolver)


# ============================================================================
# CLI entry-point for ad-hoc lookup
# ============================================================================


def _cli():
    """python -m shared_utils.asof <vendor> <source> <field> [raw_date]"""
    import sys

    args = sys.argv[1:]
    if len(args) < 3:
        print("usage: python -m shared_utils.asof <vendor> <source> <field> [raw_date]")
        sys.exit(2)
    vendor, source, field = args[:3]
    entry = classify(vendor, source, field)
    print(json.dumps(entry, indent=2, ensure_ascii=False))
    if len(args) >= 4:
        raw_date = args[3]
        try:
            shifted = asof_shift(vendor, source, field, raw_date, fallback=True)
            print(f"\nraw_date={raw_date} -> as_of_date={shifted.date()}")
        except Exception as e:
            print(f"\nshift failed: {e}")


if __name__ == "__main__":
    _cli()
