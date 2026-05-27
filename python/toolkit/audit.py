"""
audit.py
--------
Compute before/after dataset statistics for the cleaning log.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


def snapshot(df: pd.DataFrame, label: str = "") -> dict[str, Any]:
    """Capture a concise statistical snapshot of a DataFrame."""
    miss = df.isna().mean().round(4)
    return {
        "label": label,
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "n_exact_duplicates": int(df.duplicated().sum()),
        "n_missing_cells": int(df.isna().sum().sum()),
        "columns": list(df.columns),
        "missingness_pct": {
            col: round(float(v) * 100, 1)
            for col, v in miss.items()
            if v > 0
        },
    }


def before_after_summary(
    before: dict[str, Any],
    after: dict[str, Any],
) -> str:
    """Format a before/after comparison as a markdown table."""
    rows_delta = after["n_rows"] - before["n_rows"]
    cols_delta = after["n_cols"] - before["n_cols"]
    dup_delta  = after["n_exact_duplicates"] - before["n_exact_duplicates"]
    miss_delta = after["n_missing_cells"] - before["n_missing_cells"]

    lines = [
        "| Metric | Before | After | Change |",
        "|---|---|---|---|",
        f"| Rows | {before['n_rows']:,} | {after['n_rows']:,} | {rows_delta:+,} |",
        f"| Columns | {before['n_cols']} | {after['n_cols']} | {cols_delta:+} |",
        f"| Exact duplicate rows | {before['n_exact_duplicates']:,} | {after['n_exact_duplicates']:,} | {dup_delta:+,} |",
        f"| Total missing cells | {before['n_missing_cells']:,} | {after['n_missing_cells']:,} | {miss_delta:+,} |",
    ]

    added   = [c for c in after["columns"]  if c not in before["columns"]]
    removed = [c for c in before["columns"] if c not in after["columns"]]
    if added:
        lines.append(f"\n**Columns added:** `{added}`")
    if removed:
        lines.append(f"\n**Columns removed:** `{removed}`")

    before_miss = before.get("missingness_pct", {})
    after_miss  = after.get("missingness_pct", {})
    all_miss_cols = set(before_miss) | set(after_miss)
    changed_miss = [
        (c, before_miss.get(c, 0.0), after_miss.get(c, 0.0))
        for c in sorted(all_miss_cols)
        if before_miss.get(c, 0.0) != after_miss.get(c, 0.0)
    ]
    if changed_miss:
        lines.append("\n**Missingness changes:**")
        for col, b, a in changed_miss:
            lines.append(f"- `{col}`: {b}% → {a}%")

    return "\n".join(lines) + "\n"
