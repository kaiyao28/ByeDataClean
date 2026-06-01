#!/usr/bin/env python3
"""
run_demo.py
-----------
One-command demo for ByeDataClean.

Runs the full Profile → Dry-run → Clean → Validate → Re-profile loop on
the bundled example dataset. No internet connection or optional packages needed.

Usage:
    python python/run_demo.py

Expected outputs (printed at the end):
    reports/descriptive_summary/  ← before-cleaning QC report
    reports/cleaning_logs/        ← cleaning log, run manifest, flowchart
    reports/validation_reports/   ← validation report
    data/processed/               ← cleaned dataset
    reports/descriptive_summary/  ← after-cleaning QC report
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

# Allow running from the repo root
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Check working directory ────────────────────────────────────────────────────

_repo_root = Path(__file__).parent.parent
_cwd = Path.cwd()

if _cwd.name == "python":
    print(
        "\n  Problem: you appear to be inside the python/ directory.\n"
        "  Fix: run  cd ..  and then try again.\n"
    )
    sys.exit(1)

_EXAMPLE_INPUT   = _repo_root / "data" / "raw" / "example_dirty_data.csv"
_EXAMPLE_RULES   = _repo_root / "config" / "example_cleaning_rules.yaml"
_EXAMPLE_OUTPUT  = _repo_root / "data" / "processed" / "example_cleaned.csv"
_LOG_DIR         = _repo_root / "reports" / "cleaning_logs"
_VAL_DIR         = _repo_root / "reports" / "validation_reports"
_REPORT_DIR      = _repo_root / "reports" / "descriptive_summary"

if not _EXAMPLE_INPUT.exists():
    print(
        f"\n  Problem: example dataset not found at:\n"
        f"    {_EXAMPLE_INPUT}\n"
        f"  Make sure you are running from the repository root.\n"
    )
    sys.exit(1)

if not _EXAMPLE_RULES.exists():
    print(
        f"\n  Problem: example rules not found at:\n"
        f"    {_EXAMPLE_RULES}\n"
    )
    sys.exit(1)

# ── Imports ────────────────────────────────────────────────────────────────────

from toolkit.cleaning import run_cleaning_pipeline
from toolkit.config import DEFAULTS, load_rules
from toolkit.io import read_file, write_file
from toolkit.profiling import (
    binary_summary, categorical_summary, collect_all_prompts,
    collect_all_warnings, column_inventory, continuous_summary,
    dataset_overview, date_summary, duplication_summary, missingness_summary,
)
from toolkit.report_writer import build_quick_report, write_quick_report
from toolkit.type_detection import infer_types
from toolkit.utils import check_optional_packages


def _run_reporter(df, label: str, output_dir: str) -> Path:
    """Run the quick reporter on df and return the saved report path."""
    cfg = copy.deepcopy(DEFAULTS)
    cfg["output_dir"] = output_dir

    types      = infer_types(df)
    thresholds = cfg["thresholds"]
    privacy    = cfg["privacy"]

    overview = dataset_overview(df, types)
    inventory = column_inventory(df, types)
    miss  = missingness_summary(df, thresholds)
    dups  = duplication_summary(df, id_cols=None)
    cont  = continuous_summary(df, types, thresholds)
    binr  = binary_summary(df, types, thresholds)
    cat   = categorical_summary(df, types, thresholds, privacy)
    date  = date_summary(df, types, [])
    warns = collect_all_warnings(df, types, thresholds, dups, binr, cat, date)
    prompts = collect_all_prompts(miss, dups, cont, binr, cat, date, None, thresholds)
    pkg_status = check_optional_packages("skimpy", "ydata_profiling", "seaborn")

    report_str = build_quick_report(
        cfg=cfg, source_label=label,
        overview=overview, inventory=inventory,
        miss_summary=miss, dup_summary=dups,
        cont_df=cont, bin_df=binr, cat_df=cat, date_df=date,
        schema_issues=None, warnings=warns,
        optional_pkg_status=pkg_status, decision_prompts=prompts,
    )
    return write_quick_report(report_str, cfg)


def main() -> None:
    sep = "─" * 62

    print(f"\n{sep}")
    print("  ByeDataClean  │  DEMO")
    print(f"{sep}")
    print(f"\n  Input:  {_EXAMPLE_INPUT.relative_to(_repo_root)}")
    print(f"  Rules:  {_EXAMPLE_RULES.relative_to(_repo_root)}")

    # ── Step 1: Profile raw data ───────────────────────────────────────────────
    print(f"\n{sep}")
    print("  Step 1 of 5 — Profile raw data")
    print(f"{sep}\n")

    df_raw = read_file(_EXAMPLE_INPUT)
    print(f"  Loaded {len(df_raw):,} rows × {len(df_raw.columns)} columns")

    before_report = _run_reporter(
        df_raw,
        label=str(_EXAMPLE_INPUT.relative_to(_repo_root)),
        output_dir=str(_REPORT_DIR),
    )
    print(f"  ✓ Before-cleaning report  → {before_report.relative_to(_repo_root)}")

    # ── Step 2: Dry-run ────────────────────────────────────────────────────────
    print(f"\n{sep}")
    print("  Step 2 of 5 — Dry-run cleaning (nothing is written to data/)")
    print(f"{sep}\n")

    rules = load_rules(_EXAMPLE_RULES)
    n_steps = len(rules.get("rules", []))
    print(f"  Rules file: '{rules.get('name')}' — {n_steps} steps\n")

    run_cleaning_pipeline(
        df_raw, rules,
        input_path=str(_EXAMPLE_INPUT),
        output_path=None,
        rules_path=str(_EXAMPLE_RULES),
        dry_run=True,
        log_dir=str(_LOG_DIR),
        validation_dir=str(_VAL_DIR),
    )

    # ── Step 3: Apply cleaning ─────────────────────────────────────────────────
    print(f"\n{sep}")
    print("  Step 3 of 5 — Apply cleaning")
    print(f"{sep}\n")

    _EXAMPLE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    cleaned_df, _log, _val = run_cleaning_pipeline(
        df_raw, rules,
        input_path=str(_EXAMPLE_INPUT),
        output_path=str(_EXAMPLE_OUTPUT),
        rules_path=str(_EXAMPLE_RULES),
        dry_run=False,
        log_dir=str(_LOG_DIR),
        validation_dir=str(_VAL_DIR),
        flowchart=True,
    )
    write_file(cleaned_df, _EXAMPLE_OUTPUT)
    print(f"  ✓ Cleaned data            → {_EXAMPLE_OUTPUT.relative_to(_repo_root)}")

    # ── Step 4: Raw file unchanged ─────────────────────────────────────────────
    df_check = read_file(_EXAMPLE_INPUT)
    assert len(df_check) == len(df_raw), "Raw file was modified — this is a bug!"

    # ── Step 5: Profile cleaned data ───────────────────────────────────────────
    print(f"\n{sep}")
    print("  Step 5 of 5 — Profile cleaned data")
    print(f"{sep}\n")

    after_report = _run_reporter(
        cleaned_df,
        label=f"cleaned:{_EXAMPLE_OUTPUT.relative_to(_repo_root)}",
        output_dir=str(_REPORT_DIR),
    )
    print(f"  ✓ After-cleaning report   → {after_report.relative_to(_repo_root)}")

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\n{sep}")
    print("  Demo complete.")
    print(f"{sep}")
    print(f"\n  Raw data:       {len(df_raw):,} rows × {len(df_raw.columns)} columns")
    print(f"  Cleaned data:   {len(cleaned_df):,} rows × {len(cleaned_df.columns)} columns")
    print(f"\n  Reports and logs saved under reports/")
    print(f"  Cleaned file:  {_EXAMPLE_OUTPUT.relative_to(_repo_root)}")
    print(f"\n  Try your own data:")
    print(f"    python python/run_reporter.py --input data/raw/YOUR_FILE.csv")
    print()


if __name__ == "__main__":
    main()
