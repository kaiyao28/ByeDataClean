#!/usr/bin/env python3
"""
run_business_impact.py
----------------------
Compare a raw dataset against a cleaned version and produce a manager-friendly
Markdown report estimating how data-quality issues affected business metrics.

Usage example
-------------
  python python/run_business_impact.py \\
    --before data/examples/dirty_orders.csv \\
    --after  data/processed/orders_cleaned.csv \\
    --id-column order_id \\
    --value-column order_value \\
    --date-column order_date \\
    --customer-column customer_id \\
    --channel-column acquisition_channel \\
    --output reports/business_impact/orders_impact.md

All column flags are optional. If a column does not exist in the before file,
it is silently skipped.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from toolkit.business_impact import build_impact_report, compute_impact, write_impact_report
from toolkit.io import read_file


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run_business_impact.py",
        description="Generate a business impact report comparing raw vs. cleaned data.",
    )
    p.add_argument("--before",   required=True, metavar="PATH",
                   help="Path to the raw (before cleaning) file.")
    p.add_argument("--after",    required=True, metavar="PATH",
                   help="Path to the cleaned (after cleaning) file.")
    p.add_argument("--id-column",       metavar="COL", dest="id_column",
                   help="Column containing unique row identifiers (e.g. order_id).")
    p.add_argument("--value-column",    metavar="COL", dest="value_column",
                   help="Numeric column to compare (e.g. order_value, revenue).")
    p.add_argument("--date-column",     metavar="COL", dest="date_column",
                   help="Date column to check for invalid or future values.")
    p.add_argument("--customer-column", metavar="COL", dest="customer_column",
                   help="Customer identifier column to check for missingness.")
    p.add_argument("--channel-column",  metavar="COL", dest="channel_column",
                   help="Acquisition channel column to check for missingness.")
    p.add_argument("--output",  metavar="PATH",
                   default="reports/business_impact/impact_report.md",
                   help="Where to write the Markdown impact report.")
    return p


def main() -> None:
    args = _build_parser().parse_args()

    # ── Load files ────────────────────────────────────────────────────────────
    print(f"\nLoading before: {args.before}")
    try:
        before_df = read_file(args.before)
    except FileNotFoundError as exc:
        print(f"  Error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"  → {len(before_df):,} rows × {len(before_df.columns)} columns")

    print(f"Loading after:  {args.after}")
    try:
        after_df = read_file(args.after)
    except FileNotFoundError as exc:
        print(f"  Error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"  → {len(after_df):,} rows × {len(after_df.columns)} columns")

    # ── Compute impact ────────────────────────────────────────────────────────
    print("\nComputing business impact…")
    impact = compute_impact(
        before_df, after_df,
        id_column=args.id_column,
        value_column=args.value_column,
        date_column=args.date_column,
        customer_column=args.customer_column,
        channel_column=args.channel_column,
    )

    dataset_name = Path(args.before).name
    report = build_impact_report(impact, dataset_name=dataset_name)

    # ── Write report ──────────────────────────────────────────────────────────
    out_path = write_impact_report(report, args.output)
    print(f"\n  ✓ Impact report → {out_path}")

    # Print status to terminal
    from toolkit.business_impact import _status
    status = _status(impact)
    icon = {"PASS": "✓", "WARNING": "⚠", "BLOCKER": "✗"}[status]
    print(f"  {icon} Overall status: {status}")
    if impact["rows_removed"]:
        print(f"  − {impact['rows_removed']} rows removed by cleaning")
    if impact.get("value_delta") is not None:
        print(f"  Δ {impact['value_column']}: {impact['value_delta']:+,.2f} ({impact.get('value_delta_pct', 0):+.2f}%)")
    if impact.get("duplicate_id_count"):
        print(f"  ! {impact['duplicate_id_count']} duplicate ID(s) found")


if __name__ == "__main__":
    main()
