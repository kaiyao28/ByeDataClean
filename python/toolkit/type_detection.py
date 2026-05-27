"""
type_detection.py
-----------------
Infer a semantic variable type for each column.

Returned type labels
--------------------
  empty                  All values missing
  constant               One unique non-missing value
  date                   Datetime dtype or listed in date_columns override
  binary                 Exactly 2 unique non-missing values (numeric or string)
  continuous             Numeric with > 10 unique non-missing values
  categorical_or_ordinal Numeric with 3–10 unique non-missing values
  categorical            String / object with <= high_cardinality_cutoff unique values
  text_high_cardinality  String / object with > high_cardinality_cutoff unique values
  id                     Marked as ID column by the caller
"""

from __future__ import annotations

from typing import Any

import pandas as pd


_DEFAULTS = {"high_cardinality_cutoff": 50}


def infer_types(
    df: pd.DataFrame,
    id_cols: list[str] | None = None,
    date_columns: list[str] | None = None,
    type_overrides: dict[str, str] | None = None,
    thresholds: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Return a dict mapping column name → inferred type label.

    Parameters
    ----------
    df:
        The DataFrame to analyse.
    id_cols:
        Columns to label as ``id`` before other inference.
    date_columns:
        Columns to label as ``date`` before other inference.
    type_overrides:
        Config-level overrides; applied last and take priority over everything.
    thresholds:
        Dict with threshold values.
    """
    thresholds = {**_DEFAULTS, **(thresholds or {})}
    hcc = int(thresholds["high_cardinality_cutoff"])

    id_cols        = set(id_cols or [])
    date_columns   = set(date_columns or [])
    type_overrides = type_overrides or {}

    types: dict[str, str] = {}

    for col in df.columns:
        if col in type_overrides:
            types[col] = type_overrides[col]
            continue
        if col in id_cols:
            types[col] = "id"
            continue

        series   = df[col]
        n_missing = series.isna().sum()
        n_total   = len(series)

        if n_missing == n_total:
            types[col] = "empty"
            continue

        non_null = series.dropna()
        n_unique = non_null.nunique()

        if n_unique == 1:
            types[col] = "constant"
            continue

        if col in date_columns or pd.api.types.is_datetime64_any_dtype(series):
            types[col] = "date"
            continue

        if pd.api.types.is_numeric_dtype(series):
            if n_unique == 2:
                types[col] = "binary"
            elif n_unique <= 10:
                types[col] = "categorical_or_ordinal"
            else:
                types[col] = "continuous"
            continue

        # Object / string
        if n_unique == 2:
            types[col] = "binary"
        elif n_unique <= hcc:
            types[col] = "categorical"
        else:
            types[col] = "text_high_cardinality"

    return types
