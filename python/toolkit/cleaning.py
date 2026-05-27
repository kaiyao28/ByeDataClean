"""
cleaning.py
-----------
Orchestrate the cleaning pipeline:
  validate rules → snapshot → apply steps → snapshot → validate → log/manifest
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd

from toolkit.cleaning_actions import apply_action
from toolkit.audit import before_after_summary, snapshot
from toolkit.config import validate_rules
from toolkit.log_writer import (
    build_cleaning_log,
    build_run_manifest,
    build_validation_report,
    write_log,
    write_manifest,
)
from toolkit.validation import run_validation


def run_cleaning_pipeline(
    df: pd.DataFrame,
    rules: dict[str, Any],
    *,
    input_path: str = "unknown",
    output_path: str | None = None,
    rules_path: str = "unknown",
    dry_run: bool = False,
    log_dir: str = "reports/cleaning_logs",
    validation_dir: str = "reports/validation_reports",
    flowchart: bool = False,
) -> tuple[pd.DataFrame, str, str]:
    """Apply all rules in step order. Return (cleaned_df, cleaning_log_str, validation_report_str).

    Parameters
    ----------
    df             : Input DataFrame (not modified in place).
    rules          : Parsed YAML rules dict.
    input_path     : Display path for the log (original file location).
    output_path    : Where cleaned data will be written (used in log only).
    rules_path     : Display path of the rules YAML.
    dry_run        : If True, no data is modified; simulate only.
    log_dir        : Directory to write the cleaning log and run manifest.
    validation_dir : Directory to write the validation report.
    flowchart      : If True, generate and write a Mermaid flowchart alongside
                     the cleaning log.

    Returns
    -------
    (cleaned_df, cleaning_log_markdown, validation_report_markdown)
    """

    # ── 0. Validate rules ─────────────────────────────────────────────────────
    errors = validate_rules(rules)
    if errors:
        print("\n[run_cleaner] ✗ Rules file validation failed:\n", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    # ── 1. Pre-cleaning snapshot ──────────────────────────────────────────────
    before = snapshot(df, label="before cleaning")

    # ── 2. Apply rules ────────────────────────────────────────────────────────
    cleaned = df.copy()
    step_results: list[dict[str, Any]] = []

    steps = sorted(rules.get("rules", []), key=lambda r: r.get("step", 999))
    for rule in steps:
        action = rule.get("action", "unknown")
        name   = rule.get("name", action)
        step_n = rule.get("step", "?")

        print(f"  Step {step_n}: {name} [{action}] {'(DRY RUN)' if dry_run else ''}")

        # Track column state before the action
        cols_before_list = list(cleaned.columns)

        cleaned, log_entry = apply_action(cleaned, rule, dry_run=dry_run)

        # Track column state after the action
        cols_after_list = list(cleaned.columns)
        cols_before_set = set(cols_before_list)
        cols_after_set  = set(cols_after_list)
        columns_added   = [c for c in cols_after_list if c not in cols_before_set]
        columns_removed = [c for c in cols_before_list if c not in cols_after_set]

        rows_removed    = max(0, log_entry.get("rows_before", len(cleaned))
                              - log_entry.get("rows_after",  len(cleaned)))
        is_destructive  = rows_removed > 0 or bool(columns_removed)

        for w in log_entry.get("warnings", []):
            print(f"    ⚠️  {w}", file=sys.stderr)

        step_results.append({
            "step":            step_n,
            "name":            name,
            "action":          action,
            "decision_status": rule.get("decision_status", ""),
            "rationale":       rule.get("rationale", ""),
            "log":             log_entry,
            # ── Flowchart / impact-table fields ───────────────────────────────
            "cols_before":     len(cols_before_list),
            "cols_after":      len(cols_after_list),
            "columns_added":   columns_added,
            "columns_removed": columns_removed,
            "rows_removed":    rows_removed,
            "destructive":     is_destructive,
            # flag_outliers_iqr: cells_changed == outliers flagged; all others: None
            "outliers_flagged": (
                log_entry.get("cells_changed", 0)
                if action == "flag_outliers_iqr" else None
            ),
        })

    # ── 3. Post-cleaning snapshot ─────────────────────────────────────────────
    after      = snapshot(cleaned, label="after cleaning")
    ba_summary = before_after_summary(before, after)

    # ── 4. Validation ─────────────────────────────────────────────────────────
    validation_cfg = rules.get("validation", {}) or {}
    val_results    = run_validation(cleaned, validation_cfg)

    val_summary = {
        "passed": sum(1 for r in val_results if r.passed),
        "failed": sum(1 for r in val_results if not r.passed),
    }

    n_fail = val_summary["failed"]
    if n_fail > 0:
        print(f"\n  ⚠️  Validation: {n_fail} check(s) failed — see validation report.",
              file=sys.stderr)
    elif val_results:
        print(f"  ✓ Validation: all {len(val_results)} check(s) passed.")

    # ── 5. Optionally build Mermaid flowchart ─────────────────────────────────
    mermaid_text: str | None = None
    if flowchart:
        from toolkit.flowchart import build_mermaid_flowchart, write_flowchart_files

        step_audits = [
            {
                "step":             sr["step"],
                "rule_name":        sr["name"],
                "action":           sr["action"],
                "rows_before":      sr["log"].get("rows_before", before["n_rows"]),
                "rows_after":       sr["log"].get("rows_after",  after["n_rows"]),
                "rows_removed":     sr["rows_removed"],
                "columns_before":   sr["cols_before"],
                "columns_after":    sr["cols_after"],
                "columns_added":    sr["columns_added"],
                "columns_removed":  sr["columns_removed"],
                "cells_changed":    sr["log"].get("cells_changed", 0),
                "warnings":         sr["log"].get("warnings", []),
                "destructive":      sr["destructive"],
                "outliers_flagged": sr["outliers_flagged"],
            }
            for sr in step_results
        ]

        mermaid_text = build_mermaid_flowchart(before, step_audits, after, val_summary)
        rules_stem   = Path(rules_path).stem
        flow_paths   = write_flowchart_files(mermaid_text, log_dir, rules_stem)
        print(f"  ✓ Flow diagram  → {flow_paths['md']}")
        print(f"                    {flow_paths['mmd']}")

    # ── 6. Build reports ──────────────────────────────────────────────────────
    cleaning_log = build_cleaning_log(
        input_path=input_path,
        output_path=output_path,
        rules_path=rules_path,
        dry_run=dry_run,
        before_snap=before,
        after_snap=after,
        step_results=step_results,
        validation_results=val_results,
        before_after_md=ba_summary,
        mermaid_text=mermaid_text,
    )
    val_report = build_validation_report(
        input_path=input_path,
        output_path=output_path,
        validation_results=val_results,
    )
    manifest = build_run_manifest(
        input_path=input_path,
        output_path=output_path,
        rules_path=rules_path,
        dry_run=dry_run,
        before_snap=before,
        after_snap=after,
    )

    # ── 7. Write logs and manifest to disk ────────────────────────────────────
    rules_name = Path(rules_path).stem
    log_path = write_log(cleaning_log, log_dir, f"{rules_name}_cleaning_log")
    val_path = write_log(val_report,   validation_dir, f"{rules_name}_validation")
    man_path = write_manifest(manifest, log_dir, rules_name)

    print(f"\n  ✓ Cleaning log  → {log_path}")
    print(f"  ✓ Validation    → {val_path}")
    print(f"  ✓ Run manifest  → {man_path}")

    return cleaned, cleaning_log, val_report
