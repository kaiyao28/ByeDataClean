"""
business_impact.py
------------------
Compare before/after datasets and estimate how data-quality issues
affected key business metrics.

Usage via CLI:
    python python/run_business_impact.py \\
      --before data/examples/dirty_orders.csv \\
      --after  data/processed/orders_cleaned.csv \\
      --id-column order_id \\
      --value-column order_value \\
      --date-column order_date \\
      --customer-column customer_id \\
      --channel-column acquisition_channel \\
      --output reports/business_impact/orders_impact.md
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

import pandas as pd


def _safe_col(df: pd.DataFrame, col: str | None) -> pd.Series | None:
    """Return the series if the column exists, else None."""
    if col and col in df.columns:
        return df[col]
    return None


def compute_impact(
    before_df: pd.DataFrame,
    after_df: pd.DataFrame,
    *,
    id_column: str | None = None,
    value_column: str | None = None,
    date_column: str | None = None,
    customer_column: str | None = None,
    channel_column: str | None = None,
) -> dict[str, Any]:
    """Compute business impact metrics comparing before and after DataFrames.

    All optional column parameters are silently skipped if the column is absent
    from the before_df. This makes the function safe to call with any dataset.
    """
    now = datetime.date.today()
    result: dict[str, Any] = {
        "rows_before": len(before_df),
        "rows_after": len(after_df),
        "rows_removed": len(before_df) - len(after_df),
        "cols_before": len(before_df.columns),
        "cols_after": len(after_df.columns),
        # Optional metrics — set to None when column is unavailable
        "value_sum_before": None,
        "value_sum_after": None,
        "value_delta": None,
        "value_delta_pct": None,
        "duplicate_id_count": None,
        "duplicate_value_overcount": None,
        "missing_customer_count": None,
        "missing_customer_rate": None,
        "missing_channel_count": None,
        "missing_channel_rate": None,
        "negative_value_count": None,
        "zero_value_count": None,
        "invalid_date_count": None,
        "future_date_count": None,
        # Columns checked (for display in report)
        "id_column": id_column,
        "value_column": value_column,
        "date_column": date_column,
        "customer_column": customer_column,
        "channel_column": channel_column,
    }

    # ── Value column ──────────────────────────────────────────────────────────
    val_before = _safe_col(before_df, value_column)
    val_after  = _safe_col(after_df,  value_column)

    if val_before is not None:
        num_before = pd.to_numeric(val_before, errors="coerce")
        result["value_sum_before"] = float(num_before.sum())
        result["negative_value_count"] = int((num_before < 0).sum())
        result["zero_value_count"] = int((num_before == 0).sum())

    if val_after is not None:
        num_after = pd.to_numeric(val_after, errors="coerce")
        result["value_sum_after"] = float(num_after.sum())

    if result["value_sum_before"] is not None and result["value_sum_after"] is not None:
        delta = result["value_sum_before"] - result["value_sum_after"]
        result["value_delta"] = round(delta, 2)
        if result["value_sum_before"] != 0:
            result["value_delta_pct"] = round(100 * delta / abs(result["value_sum_before"]), 2)

    # ── ID column (duplicates) ─────────────────────────────────────────────────
    id_before = _safe_col(before_df, id_column)
    if id_before is not None:
        dup_extra_mask = before_df[id_column].duplicated(keep="first")
        result["duplicate_id_count"] = int(dup_extra_mask.sum())
        if val_before is not None and result["duplicate_id_count"] > 0:
            result["duplicate_value_overcount"] = round(
                float(pd.to_numeric(before_df.loc[dup_extra_mask, value_column], errors="coerce").sum()), 2
            )

    # ── Customer column ───────────────────────────────────────────────────────
    cust = _safe_col(before_df, customer_column)
    if cust is not None:
        missing_n = int(cust.isna().sum())
        result["missing_customer_count"] = missing_n
        result["missing_customer_rate"] = round(missing_n / len(before_df), 4) if len(before_df) else 0.0

    # ── Channel column ────────────────────────────────────────────────────────
    chan = _safe_col(before_df, channel_column)
    if chan is not None:
        missing_n = int(chan.isna().sum())
        result["missing_channel_count"] = missing_n
        result["missing_channel_rate"] = round(missing_n / len(before_df), 4) if len(before_df) else 0.0

    # ── Date column ───────────────────────────────────────────────────────────
    date_col = _safe_col(before_df, date_column)
    if date_col is not None:
        parsed = pd.to_datetime(date_col, errors="coerce")
        n_invalid = int(parsed.isna().sum() - date_col.isna().sum())
        result["invalid_date_count"] = max(0, n_invalid)
        result["future_date_count"] = int((parsed.dt.date > now).sum())

    return result


def _status(impact: dict[str, Any]) -> str:
    """Derive overall status from impact metrics."""
    if impact.get("duplicate_id_count") or 0 > 0:
        return "BLOCKER"
    if (
        (impact.get("negative_value_count") or 0) > 0
        or (impact.get("future_date_count") or 0) > 0
        or (impact.get("missing_customer_rate") or 0.0) > 0.10
        or (impact.get("missing_channel_rate") or 0.0) > 0.10
    ):
        return "WARNING"
    return "PASS"


def build_impact_report(
    impact: dict[str, Any],
    dataset_name: str = "",
    caveats: list[str] | None = None,
) -> str:
    """Format the impact dict as a markdown report."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    status = _status(impact)
    status_icon = {"PASS": "✓", "WARNING": "⚠", "BLOCKER": "✗"}[status]

    lines: list[str] = []
    a = lines.append

    a("# Business Impact Report\n")
    a(f"**Dataset:** `{dataset_name}`  ")
    a(f"**Generated:** {ts}\n")

    a("---\n")
    a(f"## Overall status: {status_icon} {status}\n")
    if status == "PASS":
        a("No significant data-quality issues detected that affect business metrics.")
    elif status == "WARNING":
        a("Issues detected that may affect metric accuracy. Review before publishing.")
    else:
        a("Blocking issues detected. Do not use this dataset for reporting without investigation.")
    a("")

    # ── Row counts ────────────────────────────────────────────────────────────
    a("## Row and column counts\n")
    a("| | Before cleaning | After cleaning | Change |")
    a("|---|---:|---:|---:|")
    a(f"| Rows | {impact['rows_before']:,} | {impact['rows_after']:,} | {impact['rows_removed']:+,} |")
    a(f"| Columns | {impact['cols_before']} | {impact['cols_after']} | {impact['cols_after'] - impact['cols_before']:+} |")
    a("")

    # ── Value metric ──────────────────────────────────────────────────────────
    if impact["value_sum_before"] is not None:
        a(f"## Revenue / value metric (`{impact['value_column']}`)\n")
        a(f"| | Value |")
        a("|---|---:|")
        a(f"| Sum before cleaning | {impact['value_sum_before']:,.2f} |")
        if impact["value_sum_after"] is not None:
            a(f"| Sum after cleaning  | {impact['value_sum_after']:,.2f} |")
        if impact["value_delta"] is not None:
            sign = "+" if impact["value_delta"] < 0 else "−"
            a(f"| Difference | {sign}{abs(impact['value_delta']):,.2f} "
              f"({impact['value_delta_pct']:+.2f}%) |")
        if impact.get("negative_value_count"):
            a(f"| Negative values found | {impact['negative_value_count']} (set to NaN during cleaning) |")
        if impact.get("zero_value_count"):
            a(f"| Zero values found | {impact['zero_value_count']} (investigate: cancelled or error?) |")
        a("")

    # ── Duplicate IDs ─────────────────────────────────────────────────────────
    if impact["duplicate_id_count"] is not None:
        a(f"## Duplicate IDs (`{impact['id_column']}`)\n")
        n = impact["duplicate_id_count"]
        if n:
            a(f"- **{n} duplicate row(s) found** — the raw data contains extra copies of {n} ID(s).")
            if impact.get("duplicate_value_overcount") is not None:
                a(f"- **Estimated revenue overcount: {impact['duplicate_value_overcount']:,.2f}** "
                  f"— this amount is counted more than once in the raw `{impact['value_column']}` sum.")
        else:
            a(f"- No duplicate `{impact['id_column']}` values found.")
        a("")

    # ── Missing customer IDs ──────────────────────────────────────────────────
    if impact["missing_customer_count"] is not None:
        a(f"## Missing customer IDs (`{impact['customer_column']}`)\n")
        n = impact["missing_customer_count"]
        rate = impact["missing_customer_rate"] * 100
        if n:
            a(f"- **{n} orders ({rate:.1f}%) have no customer ID.**")
            a("- These orders cannot be joined to the CRM, user table, or cohort model.")
            a("- Retention and LTV analysis based on this data will be biased.")
        else:
            a(f"- All orders have a `{impact['customer_column']}`. No impact on retention analysis.")
        a("")

    # ── Missing acquisition channel ───────────────────────────────────────────
    if impact["missing_channel_count"] is not None:
        a(f"## Missing acquisition channel (`{impact['channel_column']}`)\n")
        n = impact["missing_channel_count"]
        rate = impact["missing_channel_rate"] * 100
        if n:
            a(f"- **{n} orders ({rate:.1f}%) have no acquisition channel.**")
            a("- Channel attribution model will overstate each channel's true share.")
            a("- Investigate source system to understand why these are missing.")
        else:
            a(f"- All orders have a `{impact['channel_column']}`. Channel attribution is unaffected.")
        a("")

    # ── Date quality ──────────────────────────────────────────────────────────
    if impact["invalid_date_count"] is not None or impact["future_date_count"] is not None:
        a(f"## Date quality (`{impact['date_column']}`)\n")
        n_inv = impact.get("invalid_date_count") or 0
        n_fut = impact.get("future_date_count") or 0
        if n_inv:
            a(f"- **{n_inv} unparseable date(s)** — these rows have been excluded from time-series analysis.")
        if n_fut:
            a(f"- **{n_fut} future-dated row(s)** — these will appear in 'current period' metrics unless filtered.")
        if not n_inv and not n_fut:
            a(f"- All `{impact['date_column']}` values are valid and in the past.")
        a("")

    # ── Recommended action ────────────────────────────────────────────────────
    a("## Recommended action\n")
    if status == "PASS":
        a("- Data is ready for analysis and reporting.")
        a("- Re-run the QC reporter on the cleaned file to confirm all issues resolved.")
    elif status == "WARNING":
        a("- **Review unresolved issues before publishing metrics.**")
        if (impact.get("missing_customer_rate") or 0) > 0.10:
            a("- Investigate why customer IDs are missing in the source system.")
        if (impact.get("missing_channel_rate") or 0) > 0.10:
            a("- Investigate missing acquisition channels before running attribution analysis.")
        if (impact.get("future_date_count") or 0) > 0:
            a("- Confirm whether future-dated orders are valid pre-orders or data entry errors.")
        if (impact.get("negative_value_count") or 0) > 0:
            a("- Determine whether negative values are refunds or data errors; adjust accordingly.")
    else:
        a("- **Do not use the raw dataset for revenue or metric reporting.**")
        if impact.get("duplicate_id_count"):
            a(f"- Remove {impact['duplicate_id_count']} duplicate row(s) before aggregating.")
        a("- Use the cleaned dataset at `after` path for all reporting.")
        a("- Update any previously published figures from the raw export.")
    a("")

    # ── Caveats ───────────────────────────────────────────────────────────────
    default_caveats = [
        "This report compares row/column counts and column statistics. "
        "It does not validate business logic or data relationships.",
        "Impact estimates assume all removed rows were counted in the original metric. "
        "Confirm with the data owner before adjusting published figures.",
        "Missing-value rates are computed from the *before* dataset only.",
    ]
    all_caveats = (caveats or []) + default_caveats
    a("## Caveats\n")
    for c in all_caveats:
        a(f"- {c}")
    a("")

    return "\n".join(lines)


def write_impact_report(content: str, output_path: str | Path) -> Path:
    """Write the report to the given path, creating parent directories as needed."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    return out
