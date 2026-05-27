"""
cleaning_actions.py
-------------------
All supported cleaning action functions.

Each function signature:
    action_*(df, rule, dry_run=False) -> (pd.DataFrame, dict)

The returned dict is a step-level log entry with:
    rows_before, rows_after, rows_delta, cells_changed, warnings, details (str)

Actions
-------
 1  standardise_column_names   — snake_case column names
 2  rename_columns             — explicit mapping
 3  keep_columns               — drop all except listed (allow_drop: true)
 4  drop_columns               — drop listed columns (allow_drop: true)
 5  replace_missing_codes      — sentinel values → NaN
 6  trim_whitespace            — strip leading/trailing whitespace from strings
 7  standardise_case           — lower / upper / title
 8  map_categories             — remap categorical values
 9  set_invalid_to_missing     — out-of-range numeric → NaN
10  flag_outliers_iqr          — add outlier flag column; optionally remove rows
11  parse_dates                — convert strings to datetime (errors=coerce)
12  remove_exact_duplicates    — drop exact duplicate rows (allow_row_drop: true)
13  filter_rows_explicit       — drop rows by expression (allow_row_drop + reason)
14  create_missingness_flags   — add binary flag columns for missing values
"""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd


# ── Helpers ───────────────────────────────────────────────────────────────────

def _step_log(
    rows_before: int,
    rows_after: int,
    cells_changed: int,
    warnings: list[str] | None = None,
    details: str = "",
) -> dict[str, Any]:
    return {
        "rows_before": rows_before,
        "rows_after": rows_after,
        "rows_delta": rows_after - rows_before,
        "cells_changed": cells_changed,
        "warnings": warnings or [],
        "details": details,
    }


def _to_snake(name: str) -> str:
    """Convert a column name to snake_case."""
    name = str(name).strip()
    name = re.sub(r"[\s\-/]+", "_", name)
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    name = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", name)
    name = re.sub(r"[^\w]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_").lower()
    return name


def _string_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if pd.api.types.is_object_dtype(df[c])]


def _resolve_columns(df: pd.DataFrame, col_spec: Any) -> list[str]:
    if col_spec == "all" or col_spec is None:
        return list(df.columns)
    if col_spec == "string":
        return _string_cols(df)
    if isinstance(col_spec, list):
        return col_spec
    return [col_spec]


# ── 1. standardise_column_names ───────────────────────────────────────────────

def action_standardise_column_names(
    df: pd.DataFrame, rule: dict, dry_run: bool = False
) -> tuple[pd.DataFrame, dict]:
    old_cols = list(df.columns)
    new_cols = [_to_snake(c) for c in old_cols]
    changed  = [(o, n) for o, n in zip(old_cols, new_cols) if o != n]
    details  = "\n".join(f"  {o!r} → {n!r}" for o, n in changed) or "No column names changed."
    if not dry_run:
        df = df.copy()
        df.columns = new_cols
    return df, _step_log(len(df), len(df), len(changed), details=details)


# ── 2. rename_columns ─────────────────────────────────────────────────────────

def action_rename_columns(
    df: pd.DataFrame, rule: dict, dry_run: bool = False
) -> tuple[pd.DataFrame, dict]:
    mapping: dict = rule.get("mapping", {})
    warnings: list[str] = []
    valid = {}
    for old, new in mapping.items():
        if old not in df.columns:
            warnings.append(f"Column '{old}' not found; rename skipped.")
        else:
            valid[old] = new
    details = "\n".join(f"  {o!r} → {n!r}" for o, n in valid.items()) or "No renames applied."
    if not dry_run and valid:
        df = df.rename(columns=valid)
    return df, _step_log(len(df), len(df), len(valid), warnings, details)


# ── 3. keep_columns ───────────────────────────────────────────────────────────

def action_keep_columns(
    df: pd.DataFrame, rule: dict, dry_run: bool = False
) -> tuple[pd.DataFrame, dict]:
    keep: list[str] = rule.get("columns", [])
    missing  = [c for c in keep if c not in df.columns]
    warnings: list[str] = []
    if missing:
        warnings.append(f"Columns not found (cannot keep): {missing}")
    dropped  = [c for c in df.columns if c not in keep]
    details  = f"Keeping {len(keep)} columns; dropping {len(dropped)}: {dropped}"
    n_before = len(df)
    if not dry_run:
        keep_valid = [c for c in keep if c in df.columns]
        df = df[keep_valid].copy()
    return df, _step_log(n_before, len(df), 0, warnings, details)


# ── 4. drop_columns ───────────────────────────────────────────────────────────

def action_drop_columns(
    df: pd.DataFrame, rule: dict, dry_run: bool = False
) -> tuple[pd.DataFrame, dict]:
    drop: list[str] = rule.get("columns", [])
    missing  = [c for c in drop if c not in df.columns]
    warnings: list[str] = []
    if missing:
        warnings.append(f"Columns not found (cannot drop): {missing}")
    to_drop  = [c for c in drop if c in df.columns]
    details  = f"Dropping {len(to_drop)} columns: {to_drop}"
    n_before = len(df)
    if not dry_run and to_drop:
        df = df.drop(columns=to_drop)
    return df, _step_log(n_before, len(df), 0, warnings, details)


# ── 5. replace_missing_codes ──────────────────────────────────────────────────

def action_replace_missing_codes(
    df: pd.DataFrame, rule: dict, dry_run: bool = False
) -> tuple[pd.DataFrame, dict]:
    codes: list = rule.get("missing_codes", [])
    col_spec = rule.get("columns", "all")
    cols = [c for c in _resolve_columns(df, col_spec) if c in df.columns]

    str_codes = [c for c in codes if isinstance(c, str)]
    num_codes = [c for c in codes if not isinstance(c, str)]

    total_changed = 0
    col_details: list[str] = []

    df_out = df.copy()
    for col in cols:
        before = df_out[col].isna().sum()
        if pd.api.types.is_object_dtype(df_out[col]):
            df_out[col] = df_out[col].replace(str_codes + [str(n) for n in num_codes], np.nan)
            df_out[col] = df_out[col].replace(num_codes, np.nan)
        else:
            df_out[col] = df_out[col].replace(num_codes, np.nan)
        n_changed = int(df_out[col].isna().sum() - before)
        if n_changed > 0:
            total_changed += n_changed
            col_details.append(f"  {col}: {n_changed} value(s) → NaN")

    details = "\n".join(col_details) if col_details else "No matching missing codes found."
    result_df = df_out if not dry_run else df
    return result_df, _step_log(len(df), len(result_df), total_changed, details=details)


# ── 6. trim_whitespace ────────────────────────────────────────────────────────

def action_trim_whitespace(
    df: pd.DataFrame, rule: dict, dry_run: bool = False
) -> tuple[pd.DataFrame, dict]:
    col_spec = rule.get("columns", "string")
    cols = [c for c in _resolve_columns(df, col_spec) if c in df.columns]
    cols = [c for c in cols if pd.api.types.is_object_dtype(df[c])]

    total_changed = 0
    df_out = df.copy()
    for col in cols:
        stripped  = df_out[col].str.strip()
        n         = int((df_out[col] != stripped).sum())
        total_changed += n
        if not dry_run:
            df_out[col] = stripped

    details = f"Trimmed whitespace in {len(cols)} string column(s); {total_changed} cell(s) changed."
    result_df = df_out if not dry_run else df
    return result_df, _step_log(len(df), len(result_df), total_changed, details=details)


# ── 7. standardise_case ───────────────────────────────────────────────────────

def action_standardise_case(
    df: pd.DataFrame, rule: dict, dry_run: bool = False
) -> tuple[pd.DataFrame, dict]:
    case: str = rule.get("case", "lower")
    col_spec  = rule.get("columns", "string")
    cols = [c for c in _resolve_columns(df, col_spec) if c in df.columns]
    cols = [c for c in cols if pd.api.types.is_object_dtype(df[c])]

    total_changed = 0
    df_out = df.copy()
    for col in cols:
        if case == "lower":
            new = df_out[col].str.lower()
        elif case == "upper":
            new = df_out[col].str.upper()
        elif case == "title":
            new = df_out[col].str.title()
        else:
            new = df_out[col]
        n = int((df_out[col] != new).sum())
        total_changed += n
        if not dry_run:
            df_out[col] = new

    details = f"Applied '{case}' case to {len(cols)} column(s); {total_changed} cell(s) changed."
    result_df = df_out if not dry_run else df
    return result_df, _step_log(len(df), len(result_df), total_changed, details=details)


# ── 8. map_categories ────────────────────────────────────────────────────────

def action_map_categories(
    df: pd.DataFrame, rule: dict, dry_run: bool = False
) -> tuple[pd.DataFrame, dict]:
    col: str       = rule.get("column", "")
    mapping: dict  = rule.get("mapping", {})
    unmatched: str = rule.get("unmatched_action", "warn")
    warnings: list[str] = []

    if col not in df.columns:
        return df, _step_log(len(df), len(df), 0, [f"Column '{col}' not found."])

    before_vc = df[col].value_counts(dropna=False).to_dict()
    df_out = df.copy()
    mapped      = df_out[col].map(mapping)
    was_mapped  = df_out[col].isin(mapping.keys())
    n_mapped    = int(was_mapped.sum())

    if not dry_run:
        df_out[col] = df_out[col].where(~was_mapped, other=mapped)

    after_valid = df_out[col].isin(list(mapping.values())) | df_out[col].isna()
    n_unmatched = int((~after_valid & ~df_out[col].isna()).sum())
    if n_unmatched > 0:
        unmatched_vals = df_out.loc[~after_valid & ~df_out[col].isna(), col].unique()[:5]
        if unmatched == "warn":
            warnings.append(f"{n_unmatched} unmatched value(s) in '{col}' (examples: {list(unmatched_vals)}).")
        elif unmatched == "set_missing" and not dry_run:
            df_out.loc[~after_valid & ~df_out[col].isna(), col] = np.nan
            warnings.append(f"{n_unmatched} unmatched value(s) in '{col}' set to NaN.")

    after_vc = df_out[col].value_counts(dropna=False).to_dict() if not dry_run else before_vc
    details = (
        f"Mapped {n_mapped} value(s) in '{col}'.\n"
        f"  Before unique values: {len(before_vc)}\n"
        f"  After unique values: {len(after_vc)}"
    )
    result_df = df_out if not dry_run else df
    return result_df, _step_log(len(df), len(result_df), n_mapped, warnings, details)


# ── 9. set_invalid_to_missing ─────────────────────────────────────────────────

def action_set_invalid_to_missing(
    df: pd.DataFrame, rule: dict, dry_run: bool = False
) -> tuple[pd.DataFrame, dict]:
    col: str  = rule.get("column", "")
    col_min   = rule.get("min")
    col_max   = rule.get("max")

    if col not in df.columns:
        return df, _step_log(len(df), len(df), 0, [f"Column '{col}' not found."])

    series = df[col]
    mask   = pd.Series(False, index=series.index)
    if col_min is not None:
        mask |= (series.notna() & (series < col_min))
    if col_max is not None:
        mask |= (series.notna() & (series > col_max))

    n_invalid = int(mask.sum())
    details = (
        f"'{col}': {n_invalid} value(s) outside [{col_min}, {col_max}] set to NaN."
        if n_invalid > 0 else f"'{col}': no values outside [{col_min}, {col_max}]."
    )
    df_out = df.copy()
    if not dry_run and n_invalid > 0:
        df_out.loc[mask, col] = np.nan

    result_df = df_out if not dry_run else df
    return result_df, _step_log(len(df), len(result_df), n_invalid, details=details)


# ── 10. flag_outliers_iqr ────────────────────────────────────────────────────

def action_flag_outliers_iqr(
    df: pd.DataFrame, rule: dict, dry_run: bool = False
) -> tuple[pd.DataFrame, dict]:
    col: str      = rule.get("column", "")
    out_col: str  = rule.get("output_column", f"{col}_outlier_flag")
    do_remove     = rule.get("remove", False)
    warnings: list[str] = []

    if col not in df.columns:
        return df, _step_log(len(df), len(df), 0, [f"Column '{col}' not found."])

    s = df[col].dropna()
    if len(s) == 0:
        return df, _step_log(len(df), len(df), 0, [f"'{col}' has no non-null values."])

    q1, q3  = float(s.quantile(0.25)), float(s.quantile(0.75))
    iqr     = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    flag    = ((df[col] < lower) | (df[col] > upper)).astype("Int8")
    n_flagged = int(flag.sum())

    df_out = df.copy()
    if not dry_run:
        df_out[out_col] = flag

    rows_after = len(df)
    if do_remove and not dry_run:
        df_out = df_out[flag == 0].copy()
        warnings.append(f"Removed {n_flagged} outlier row(s) from '{col}' (IQR method).")
        rows_after = len(df_out)

    details = (
        f"'{col}': IQR=[{lower:.3f}, {upper:.3f}]; {n_flagged} outlier(s) flagged in '{out_col}'."
        + (f" {n_flagged} rows removed." if do_remove and not dry_run else "")
    )
    result_df = df_out if not dry_run else df
    return result_df, _step_log(len(df), rows_after, n_flagged, warnings, details)


# ── 11. parse_dates ───────────────────────────────────────────────────────────

def action_parse_dates(
    df: pd.DataFrame, rule: dict, dry_run: bool = False
) -> tuple[pd.DataFrame, dict]:
    cols: list[str] = rule.get("columns", [])
    fmt: str | None = rule.get("format", None)
    warnings: list[str] = []
    total_failed = 0

    df_out = df.copy()
    for col in cols:
        if col not in df_out.columns:
            warnings.append(f"Column '{col}' not found; skipped.")
            continue
        before_nulls = df_out[col].isna().sum()
        parsed = pd.to_datetime(df_out[col], format=fmt, errors="coerce")
        n_failed = int(parsed.isna().sum() - before_nulls)
        if n_failed > 0:
            warnings.append(f"'{col}': {n_failed} value(s) could not be parsed as dates (set to NaT).")
            total_failed += n_failed
        if not dry_run:
            df_out[col] = parsed

    details = (
        f"Parsed {len(cols)} date column(s). {total_failed} total parse failure(s) set to NaT."
    )
    result_df = df_out if not dry_run else df
    return result_df, _step_log(len(df), len(result_df), total_failed, warnings, details)


# ── 12. remove_exact_duplicates ───────────────────────────────────────────────

def action_remove_exact_duplicates(
    df: pd.DataFrame, rule: dict, dry_run: bool = False
) -> tuple[pd.DataFrame, dict]:
    n_dups  = int(df.duplicated().sum())
    details = f"Found {n_dups} exact duplicate row(s)."

    if n_dups > 0 and not dry_run:
        df_out = df.drop_duplicates(keep="first").copy()
        details += f" Removed {n_dups}; kept first occurrence."
    else:
        df_out = df

    result_df = df_out if not dry_run else df
    return result_df, _step_log(len(df), len(result_df), 0, [], details)


# ── 13. filter_rows_explicit ──────────────────────────────────────────────────

def action_filter_rows_explicit(
    df: pd.DataFrame, rule: dict, dry_run: bool = False
) -> tuple[pd.DataFrame, dict]:
    condition: str = rule.get("condition", "")
    reason: str    = rule.get("reason", "")
    warnings: list[str] = []

    if not condition:
        return df, _step_log(len(df), len(df), 0, ["No condition specified; skipped."])

    try:
        mask = df.eval(condition)
    except Exception as exc:
        return df, _step_log(len(df), len(df), 0,
                             [f"Could not evaluate condition '{condition}': {exc}"])

    n_keep = int(mask.sum())
    n_drop = len(df) - n_keep
    details = (
        f"Condition: {condition!r}\n"
        f"Reason: {reason}\n"
        f"Rows kept: {n_keep}, rows dropped: {n_drop}"
    )
    if n_drop > 0:
        warnings.append(f"Dropping {n_drop} row(s). Reason: {reason}")

    df_out    = df[mask].copy() if not dry_run else df
    return df_out, _step_log(len(df), len(df_out), 0, warnings, details)


# ── 14. create_missingness_flags ──────────────────────────────────────────────

def action_create_missingness_flags(
    df: pd.DataFrame, rule: dict, dry_run: bool = False
) -> tuple[pd.DataFrame, dict]:
    """Add a binary (0/1) flag column for each specified column indicating whether
    the value was missing.  Flag column name: ``{col}_missing_flag``.

    This is a safe, non-destructive action that preserves all original values
    while surfacing potentially informative missingness for analysis.

    Rule keys
    ---------
    columns : list[str] | "all" | "string"
        Columns to create flags for.  Defaults to all columns with any missing.
    suffix : str
        Suffix for flag column names (default: ``_missing_flag``).
    only_if_any_missing : bool
        If True (default), only create a flag for columns that actually have
        missing values.  If False, create flags for all listed columns.
    """
    col_spec = rule.get("columns", "all")
    suffix   = rule.get("suffix", "_missing_flag")
    only_if_any_missing = rule.get("only_if_any_missing", True)

    cols = [c for c in _resolve_columns(df, col_spec) if c in df.columns]
    if only_if_any_missing:
        cols = [c for c in cols if df[c].isna().any()]

    n_flags  = len(cols)
    df_out   = df.copy()
    flag_cols: list[str] = []
    for col in cols:
        flag_col = f"{col}{suffix}"
        if not dry_run:
            df_out[flag_col] = df_out[col].isna().astype("Int8")
        flag_cols.append(flag_col)

    details = (
        f"Created {n_flags} missingness flag column(s): {flag_cols}"
        if flag_cols else "No columns with missing values found — no flags created."
    )
    result_df = df_out if not dry_run else df
    return result_df, _step_log(len(df), len(result_df), n_flags, details=details)


# ── Dispatch ──────────────────────────────────────────────────────────────────

ACTION_MAP: dict[str, Any] = {
    "standardise_column_names":  action_standardise_column_names,
    "rename_columns":            action_rename_columns,
    "keep_columns":              action_keep_columns,
    "drop_columns":              action_drop_columns,
    "replace_missing_codes":     action_replace_missing_codes,
    "trim_whitespace":           action_trim_whitespace,
    "standardise_case":          action_standardise_case,
    "map_categories":            action_map_categories,
    "set_invalid_to_missing":    action_set_invalid_to_missing,
    "flag_outliers_iqr":         action_flag_outliers_iqr,
    "parse_dates":               action_parse_dates,
    "remove_exact_duplicates":   action_remove_exact_duplicates,
    "filter_rows_explicit":      action_filter_rows_explicit,
    "create_missingness_flags":  action_create_missingness_flags,
}


def apply_action(
    df: pd.DataFrame,
    rule: dict,
    dry_run: bool = False,
) -> tuple[pd.DataFrame, dict]:
    """Dispatch to the correct action function."""
    action_name = rule.get("action", "")
    fn = ACTION_MAP.get(action_name)
    if fn is None:
        log = _step_log(len(df), len(df), 0,
                        [f"Unknown action '{action_name}'; skipped."])
        return df, log
    return fn(df, rule, dry_run=dry_run)
