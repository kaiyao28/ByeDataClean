#!/usr/bin/env python3
"""
run_cleaner.py
--------------
Entry point for the config-driven cleaning executor.

Usage examples
--------------
  # Dry run — see what would happen without writing output
  python python/run_cleaner.py \\
    --input data/raw/my_data.csv \\
    --rules config/cleaning_rules.example.yaml \\
    --dry-run

  # Full clean run
  python python/run_cleaner.py \\
    --input data/raw/my_data.csv \\
    --rules config/cleaning_rules.example.yaml \\
    --output data/processed/my_data_cleaned.csv

  # Full clean + auto QC report + Mermaid flowchart
  python python/run_cleaner.py \\
    --input data/raw/my_data.csv \\
    --rules config/cleaning_rules.example.yaml \\
    --output data/processed/my_data_cleaned.csv \\
    --after-report \\
    --flowchart

  # Cleaning profile
  python python/run_cleaner.py \\
    --input data/raw/my_data.csv \\
    --rules config/cleaning_profiles/descriptive_analysis.yaml \\
    --output data/processed/my_data_descriptive.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from repo root without installing the package
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from toolkit.cleaning import run_cleaning_pipeline
from toolkit.config import has_destructive_rules, load_rules
from toolkit.io import default_output_path, read_file, write_file
from toolkit.utils import abort, print_banner, safety_check_output


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run_cleaner.py",
        description="Config-driven data cleaning executor.",
    )
    p.add_argument("--input",   required=True, metavar="PATH",
                   help="Path to the raw input file (CSV, TSV, Excel, Parquet).")
    p.add_argument("--rules",   required=True, metavar="PATH",
                   help="Path to the YAML cleaning rules file.")
    p.add_argument("--output",  metavar="PATH",
                   help="Where to write the cleaned file. Defaults to data/processed/<stem>_cleaned.csv.")
    p.add_argument("--dry-run", action="store_true", dest="dry_run",
                   help="Simulate cleaning without writing output.")
    p.add_argument("--confirm-destructive", action="store_true", dest="confirm_destructive",
                   help="Required when rules contain row/column drops and --dry-run is not set.")
    p.add_argument("--log-dir",  metavar="DIR", dest="log_dir",
                   default="reports/cleaning_logs",
                   help="Directory to write cleaning logs and run manifests.")
    p.add_argument("--validation-dir", metavar="DIR", dest="validation_dir",
                   default="reports/validation_reports",
                   help="Directory to write validation reports.")
    p.add_argument("--after-report", action="store_true", dest="after_report",
                   help="Run the QC reporter on the cleaned data immediately after cleaning.")
    p.add_argument("--flowchart", action="store_true",
                   help="Generate a Mermaid flowchart of the cleaning steps in the log directory.")
    return p


def main() -> None:
    parser = _build_parser()
    args   = parser.parse_args()

    print_banner(dry_run=args.dry_run)

    # ── Load data ──────────────────────────────────────────────────────────────
    print(f"\nLoading input:  {args.input}")
    try:
        df = read_file(args.input)
    except FileNotFoundError as exc:
        abort(str(exc))

    print(f"  → {len(df):,} rows × {len(df.columns)} columns")

    # ── Load rules ─────────────────────────────────────────────────────────────
    print(f"Loading rules:  {args.rules}")
    try:
        rules = load_rules(args.rules)
    except FileNotFoundError as exc:
        abort(str(exc))

    rule_name = rules.get("name", Path(args.rules).stem)
    n_steps   = len(rules.get("rules", []))
    print(f"  → '{rule_name}' — {n_steps} cleaning step(s)")

    # ── Destructive-action guard ───────────────────────────────────────────────
    if has_destructive_rules(rules) and not args.dry_run and not args.confirm_destructive:
        abort(
            "This rules file contains row or column drops.\n"
            "  Re-run with --dry-run to preview changes first, then add\n"
            "  --confirm-destructive to proceed with the full clean run.\n"
            "  This guard ensures destructive steps are always intentional."
        )

    # ── Resolve output path ────────────────────────────────────────────────────
    if args.dry_run:
        output_path = None
    else:
        out = args.output or str(default_output_path(args.input))
        safety_check_output(args.input, out)
        output_path = out

    # ── Run pipeline ───────────────────────────────────────────────────────────
    print(f"\nApplying {n_steps} cleaning step(s)…\n")
    cleaned_df, _cleaning_log, _val_report = run_cleaning_pipeline(
        df,
        rules,
        input_path=args.input,
        output_path=output_path,
        rules_path=args.rules,
        dry_run=args.dry_run,
        log_dir=args.log_dir,
        validation_dir=args.validation_dir,
        flowchart=args.flowchart,
    )

    # ── Save cleaned data ──────────────────────────────────────────────────────
    if not args.dry_run and output_path:
        write_file(cleaned_df, output_path)
        print(f"  ✓ Cleaned data  → {output_path}")

    # ── Optional: run QC reporter on cleaned data ──────────────────────────────
    if args.after_report and not args.dry_run and output_path:
        print("\nRunning QC reporter on cleaned data…")
        try:
            import copy
            from toolkit.config import DEFAULTS
            from toolkit.profiling import (
                binary_summary, categorical_summary, collect_all_prompts,
                collect_all_warnings, column_inventory, continuous_summary,
                dataset_overview, date_summary, duplication_summary, missingness_summary,
            )
            from toolkit.report_writer import build_quick_report, write_quick_report
            from toolkit.type_detection import infer_types
            from toolkit.utils import check_optional_packages

            cfg = copy.deepcopy(DEFAULTS)
            cfg["input_path"]     = output_path
            cfg["report_basename"] = f"{Path(output_path).stem}_after_cleaning_qc"

            types      = infer_types(cleaned_df)
            thresholds = cfg["thresholds"]
            privacy    = cfg["privacy"]

            miss   = missingness_summary(cleaned_df, thresholds)
            dups   = duplication_summary(cleaned_df, id_cols=None)
            cont   = continuous_summary(cleaned_df, types, thresholds)
            binr   = binary_summary(cleaned_df, types, thresholds)
            cat    = categorical_summary(cleaned_df, types, thresholds, privacy)
            date   = date_summary(cleaned_df, types, [])
            warns  = collect_all_warnings(cleaned_df, types, thresholds, dups, binr, cat, date)
            prompts = collect_all_prompts(miss, dups, cont, binr, cat, date, None, thresholds)
            pkg_status = check_optional_packages("skimpy", "ydata_profiling", "seaborn")

            report_str = build_quick_report(
                cfg=cfg, source_label=f"cleaned:{output_path}",
                overview=dataset_overview(cleaned_df, types), inventory=column_inventory(cleaned_df, types),
                miss_summary=miss, dup_summary=dups,
                cont_df=cont, bin_df=binr, cat_df=cat, date_df=date,
                schema_issues=None, warnings=warns,
                optional_pkg_status=pkg_status, decision_prompts=prompts,
            )
            qc_path = write_quick_report(report_str, cfg)
            print(f"  ✓ After-cleaning QC report → {qc_path}")
        except Exception as exc:
            print(f"  ⚠️  After-cleaning QC report failed: {exc}", file=sys.stderr)

    # ── Final summary ──────────────────────────────────────────────────────────
    if args.dry_run:
        print("\n─────────────────────────────────────────────────────────")
        print("  Dry run complete. No data was written.")
        print("  Review the log above, then re-run without --dry-run.")
        print("  If rules include row/column drops, also add --confirm-destructive.")
    else:
        print("\n─────────────────────────────────────────────────────────")
        print("  Cleaning complete.")


if __name__ == "__main__":
    main()
