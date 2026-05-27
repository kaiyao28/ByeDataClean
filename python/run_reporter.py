#!/usr/bin/env python3
"""
run_reporter.py
---------------
Entry point for the descriptive QC reporter.

Usage examples
--------------
  python python/run_reporter.py --example-dataset penguins
  python python/run_reporter.py --input data/raw/my_data.csv
  python python/run_reporter.py --input data/raw/my_data.csv --mode both
  python python/run_reporter.py --config config/reporter_config.example.yaml
  python python/run_reporter.py --input data/raw/my_data.csv \\
      --columns age sex bmi --id-cols participant_id
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from repo root without installing the package
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from toolkit.config import apply_cli_overrides, load_config, validate_config
from toolkit.profiling import (
    binary_summary, categorical_summary, collect_all_prompts,
    collect_all_warnings, column_inventory, continuous_summary,
    dataset_overview, date_summary, duplication_summary, missingness_summary,
)
from toolkit.example_datasets import load_example_dataset
from toolkit.io import read_file, select_columns
from toolkit.report_writer import build_quick_report, run_full_profile, write_quick_report
from toolkit.type_detection import infer_types
from toolkit.utils import check_optional_packages
from toolkit.validation import load_schema, run_schema_checks


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run_reporter.py",
        description="Descriptive QC reporter — profile a dataset without writing any code.",
    )
    input_grp = p.add_mutually_exclusive_group()
    input_grp.add_argument("--input", metavar="PATH", help="Path to CSV, TSV, Excel, or Parquet file.")
    input_grp.add_argument("--example-dataset", metavar="NAME",
                           help="Load a built-in example dataset: penguins, tips, iris.")
    p.add_argument("--config", metavar="PATH", help="Path to a YAML reporter config file.")
    p.add_argument("--schema", metavar="PATH", help="Path to a YAML schema file for validation checks.")
    p.add_argument("--columns", nargs="+", metavar="COL", help="Analyse only these columns.")
    p.add_argument("--id-cols", nargs="+", metavar="COL", dest="id_cols",
                   help="Mark these columns as ID columns (enables duplicate ID checks).")
    p.add_argument("--mode", choices=["quick", "full", "both"], default=None,
                   help="Report mode: quick (markdown), full (HTML), or both.")
    p.add_argument("--output-dir", metavar="DIR", dest="output_dir",
                   help="Directory to write the markdown report.")
    return p


def main() -> None:
    parser = _build_parser()
    args   = parser.parse_args()

    cfg = load_config(args.config)
    cfg = apply_cli_overrides(cfg, args)

    try:
        validate_config(cfg)
    except ValueError as exc:
        parser.error(str(exc))

    pkg_status = check_optional_packages("skimpy", "ydata_profiling", "seaborn")

    # ── Load data ──────────────────────────────────────────────────────────────
    if cfg.get("example_dataset"):
        df = load_example_dataset(cfg["example_dataset"])
        if df is None:
            sys.exit(1)
        source_label = f"example:{cfg['example_dataset']}"
    else:
        try:
            df = read_file(cfg["input_path"])
        except FileNotFoundError as exc:
            parser.error(str(exc))
        source_label = str(cfg["input_path"])

    try:
        df = select_columns(df, cfg.get("columns"))
    except ValueError as exc:
        parser.error(str(exc))

    # ── Type inference ─────────────────────────────────────────────────────────
    types = infer_types(
        df,
        id_cols=cfg.get("id_cols"),
        date_columns=cfg.get("date_columns", []),
        type_overrides=cfg.get("type_overrides", {}),
        thresholds=cfg.get("thresholds", {}),
    )

    thresholds = cfg.get("thresholds", {})
    privacy    = cfg.get("privacy", {})

    # ── Profile ────────────────────────────────────────────────────────────────
    overview     = dataset_overview(df, types)
    inventory    = column_inventory(df, types)
    miss_summary = missingness_summary(df, thresholds)
    dup_summary  = duplication_summary(df, cfg.get("id_cols"))
    cont_df      = continuous_summary(df, types, thresholds)
    bin_df       = binary_summary(df, types, thresholds)
    cat_df       = categorical_summary(df, types, thresholds, privacy)
    date_df      = date_summary(df, types, cfg.get("date_columns", []))

    # ── Schema validation ──────────────────────────────────────────────────────
    schema_issues = None
    if cfg.get("schema_path"):
        try:
            schema        = load_schema(cfg["schema_path"])
            schema_issues = run_schema_checks(df, schema)
        except FileNotFoundError as exc:
            print(f"[WARNING] {exc} — skipping schema checks.", file=sys.stderr)

    # ── Warnings and prompts ───────────────────────────────────────────────────
    warnings = collect_all_warnings(df, types, thresholds, dup_summary, bin_df, cat_df, date_df)
    prompts  = collect_all_prompts(
        miss_summary=miss_summary, dup_summary=dup_summary,
        cont_df=cont_df, bin_df=bin_df, cat_df=cat_df, date_df=date_df,
        schema_issues=schema_issues, thresholds=thresholds,
    )

    # ── Render ─────────────────────────────────────────────────────────────────
    mode = cfg.get("mode", "quick")

    if mode in ("quick", "both"):
        report_str = build_quick_report(
            cfg=cfg, source_label=source_label,
            overview=overview, inventory=inventory,
            miss_summary=miss_summary, dup_summary=dup_summary,
            cont_df=cont_df, bin_df=bin_df, cat_df=cat_df, date_df=date_df,
            schema_issues=schema_issues, warnings=warnings,
            optional_pkg_status=pkg_status, decision_prompts=prompts,
        )
        print(report_str)
        out_path = write_quick_report(report_str, cfg)
        print(f"\n✓ Quick report saved → {out_path}")

        if pkg_status.get("skimpy"):
            try:
                from skimpy import skim  # type: ignore
                print("\n── skimpy skim ──────────────────────────────────────")
                skim(df)
            except Exception as exc:
                print(f"[WARNING] skimpy.skim failed: {exc}", file=sys.stderr)
        else:
            print("[INFO] Install 'skimpy' (pip install skimpy) for a richer console summary.")

    if mode in ("full", "both"):
        html_path = run_full_profile(df, cfg)
        if html_path:
            print(f"✓ Full HTML profile saved → {html_path}")


if __name__ == "__main__":
    main()
