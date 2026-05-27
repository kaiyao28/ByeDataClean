"""
validation.py
-------------
Two complementary validation layers:

  1. Schema validation (reporter) — check a dataset against a YAML schema
     (required columns, allowed values, numeric ranges, unique IDs).

  2. Post-cleaning validation (cleaner) — run declared checks after all
     cleaning steps and produce a structured pass/fail report.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


# ─────────────────────────────────────────────────────────────────────────────
# Schema validation (reporter layer)
# ─────────────────────────────────────────────────────────────────────────────

def load_schema(schema_path: str | Path) -> dict[str, Any]:
    """Load and return the YAML schema dict."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    with path.open() as fh:
        return yaml.safe_load(fh) or {}


def run_schema_checks(
    df: pd.DataFrame,
    schema: dict[str, Any],
) -> dict[str, list[str]]:
    """Return a dict of issue-type → list of human-readable messages."""
    col_schema: dict[str, Any] = schema.get("columns", {})
    issues: dict[str, list[str]] = {
        "missing_required": [],
        "unexpected_columns": [],
        "allowed_value_violations": [],
        "range_violations": [],
        "uniqueness_violations": [],
    }

    df_cols = set(df.columns)

    for col, spec in col_schema.items():
        if spec.get("required", False) and col not in df_cols:
            issues["missing_required"].append(
                f"Required column '{col}' is missing from the dataset."
            )

    for col, spec in col_schema.items():
        if col not in df_cols:
            continue
        allowed = spec.get("allowed_values")
        if allowed is not None:
            bad = df[col].dropna()[~df[col].dropna().isin(allowed)]
            if len(bad) > 0:
                uniq_bad = list(bad.unique()[:5])
                issues["allowed_value_violations"].append(
                    f"'{col}': {len(bad)} rows with disallowed values "
                    f"(examples: {uniq_bad}).  Allowed: {allowed}"
                )

    for col, spec in col_schema.items():
        if col not in df_cols:
            continue
        col_min = spec.get("min")
        col_max = spec.get("max")
        if col_min is not None:
            n_below = int((df[col].dropna() < col_min).sum())
            if n_below > 0:
                issues["range_violations"].append(
                    f"'{col}': {n_below} rows below minimum ({col_min})."
                )
        if col_max is not None:
            n_above = int((df[col].dropna() > col_max).sum())
            if n_above > 0:
                issues["range_violations"].append(
                    f"'{col}': {n_above} rows above maximum ({col_max})."
                )

    for col, spec in col_schema.items():
        if col not in df_cols:
            continue
        if spec.get("unique", False) or spec.get("role") == "id":
            n_dup = int(df[col].dropna().duplicated().sum())
            if n_dup > 0:
                issues["uniqueness_violations"].append(
                    f"'{col}' has {n_dup} duplicate non-null values (expected unique)."
                )

    return issues


# ─────────────────────────────────────────────────────────────────────────────
# Post-cleaning validation (cleaner layer)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    check: str
    column: str
    passed: bool
    message: str


def run_validation(
    df: pd.DataFrame,
    validation_cfg: dict[str, Any],
) -> list[ValidationResult]:
    """Run all configured validation checks. Returns a list of ValidationResult."""
    results: list[ValidationResult] = []
    if not validation_cfg:
        return results

    # Required columns
    for col in validation_cfg.get("required_columns", []):
        if col not in df.columns:
            results.append(ValidationResult(
                check="required_column", column=col, passed=False,
                message=f"Required column '{col}' is missing from the dataset.",
            ))
        else:
            results.append(ValidationResult(
                check="required_column", column=col, passed=True,
                message=f"'{col}' is present.",
            ))

    # Unique keys
    for key_spec in validation_cfg.get("unique_keys", []):
        cols = key_spec if isinstance(key_spec, list) else [key_spec]
        valid_cols = [c for c in cols if c in df.columns]
        if not valid_cols:
            results.append(ValidationResult(
                check="unique_key", column=str(cols), passed=False,
                message=f"Key columns {cols} not found in dataset.",
            ))
            continue
        n_dup     = int(df.duplicated(subset=valid_cols, keep=False).sum())
        key_label = " + ".join(valid_cols)
        if n_dup > 0:
            results.append(ValidationResult(
                check="unique_key", column=key_label, passed=False,
                message=f"Key ({key_label}) has {n_dup} non-unique row(s).",
            ))
        else:
            results.append(ValidationResult(
                check="unique_key", column=key_label, passed=True,
                message=f"Key ({key_label}) is unique.",
            ))

    # Accepted values
    for col, allowed in validation_cfg.get("accepted_values", {}).items():
        if col not in df.columns:
            results.append(ValidationResult(
                check="accepted_values", column=col, passed=False,
                message=f"Column '{col}' not found; accepted_values check skipped.",
            ))
            continue
        non_null = df[col].dropna()
        bad = non_null[~non_null.isin(allowed)]
        if len(bad) > 0:
            examples = list(bad.unique()[:5])
            results.append(ValidationResult(
                check="accepted_values", column=col, passed=False,
                message=f"'{col}': {len(bad)} value(s) not in allowed list {allowed}. Examples: {examples}",
            ))
        else:
            results.append(ValidationResult(
                check="accepted_values", column=col, passed=True,
                message=f"'{col}': all non-null values are in {allowed}.",
            ))

    # Numeric ranges
    for col, spec in validation_cfg.get("ranges", {}).items():
        if col not in df.columns:
            results.append(ValidationResult(
                check="range", column=col, passed=False,
                message=f"Column '{col}' not found; range check skipped.",
            ))
            continue
        col_min = spec.get("min")
        col_max = spec.get("max")
        non_null = df[col].dropna()
        n_below = int((non_null < col_min).sum()) if col_min is not None else 0
        n_above = int((non_null > col_max).sum()) if col_max is not None else 0

        if n_below > 0 or n_above > 0:
            parts = []
            if n_below:
                parts.append(f"{n_below} value(s) below min ({col_min})")
            if n_above:
                parts.append(f"{n_above} value(s) above max ({col_max})")
            results.append(ValidationResult(
                check="range", column=col, passed=False,
                message=f"'{col}': " + "; ".join(parts) + ".",
            ))
        else:
            results.append(ValidationResult(
                check="range", column=col, passed=True,
                message=f"'{col}': all values within [{col_min}, {col_max}].",
            ))

    return results
