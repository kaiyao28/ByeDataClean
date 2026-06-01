"""
log_writer.py
-------------
Build the markdown cleaning log, validation report, and run manifest.

Run manifest
------------
A YAML file written alongside each cleaning log containing machine-readable
metadata: input/output paths, rules file, timestamp, git commit, Python
version, package versions, and row/column counts.  Useful for reproducibility
audits.
"""

from __future__ import annotations

import datetime
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from toolkit.validation import ValidationResult


def _git_commit() -> str:
    """Return current git commit hash or 'unavailable'."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=3,
        )
        return result.stdout.strip() or "unavailable"
    except Exception:
        return "unavailable"


def _package_version(name: str) -> str:
    try:
        import importlib.metadata
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


# ── Cleaning log ──────────────────────────────────────────────────────────────

def build_cleaning_log(
    input_path: str,
    output_path: str | None,
    rules_path: str,
    dry_run: bool,
    before_snap: dict[str, Any],
    after_snap: dict[str, Any],
    step_results: list[dict[str, Any]],
    validation_results: list[ValidationResult],
    before_after_md: str,
    mermaid_text: str | None = None,
) -> str:
    """Assemble and return the full markdown cleaning log.

    Parameters
    ----------
    mermaid_text : Optional Mermaid flowchart string. When provided, a
                   ``## Cleaning Flowchart`` section is embedded at the top
                   of the log using a fenced Mermaid code block.
    """
    ts       = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    git_hash = _git_commit()

    lines: list[str] = []
    a = lines.append

    a("# Cleaning Log\n")

    # ── Metadata ──────────────────────────────────────────────────────────────
    a("## Run Metadata\n")
    a(f"- **Timestamp:** {ts}")
    a(f"- **Dry run:** {'Yes — no output was written' if dry_run else 'No'}")
    a(f"- **Input file:** `{input_path}`")
    a(f"- **Output file:** `{output_path or 'not written (dry run)'}`")
    a(f"- **Rules file:** `{rules_path}`")
    a(f"- **Git commit:** `{git_hash}`")
    a(f"- **Rows before:** {before_snap['n_rows']:,}")
    a(f"- **Rows after:** {after_snap['n_rows']:,} "
      f"({'−' if after_snap['n_rows'] < before_snap['n_rows'] else '+'}"
      f"{abs(after_snap['n_rows'] - before_snap['n_rows'])})")
    a(f"- **Columns before:** {before_snap['n_cols']}")
    a(f"- **Columns after:** {after_snap['n_cols']}")
    a("")

    # ── Embedded Mermaid flowchart (optional) ─────────────────────────────────
    if mermaid_text:
        a("## Cleaning Flowchart\n")
        a("_Rendered in GitHub, GitLab, Quarto, MkDocs, and Obsidian._\n")
        a("```mermaid")
        a(mermaid_text)
        a("```")
        a("")

    # ── Step summary table ────────────────────────────────────────────────────
    a("## Step Summary\n")
    a("| Step | Name | Action | Decision Status | Rows Δ | Cells changed | Warnings |")
    a("|---|---|---|---|---|---|---|")
    for sr in step_results:
        log    = sr.get("log", {})
        n_warn = len(log.get("warnings", []))
        status = sr.get("decision_status") or "—"
        a(
            f"| {sr['step']} | {sr['name']} | `{sr['action']}` "
            f"| {status} "
            f"| {log.get('rows_delta', 0):+} "
            f"| {log.get('cells_changed', 0)} "
            f"| {n_warn} |"
        )
    a("")

    # ── Step impact summary (always shown) ────────────────────────────────────
    a("## Step Impact Summary\n")
    a("| Step | Action | Rows before | Rows after | Rows removed "
      "| Cols before | Cols after | Cells changed | Warnings |")
    a("|---|---|---:|---:|---:|---:|---:|---:|---|")
    for sr in step_results:
        log        = sr.get("log", {})
        n_warn     = len(log.get("warnings", []))
        warn_label = f"⚠ {n_warn}" if n_warn else "—"
        destr      = " 🔴" if sr.get("destructive") else ""
        a(
            f"| {sr['step']} | `{sr['action']}`{destr} "
            f"| {log.get('rows_before', '?'):,} "
            f"| {log.get('rows_after', '?'):,} "
            f"| {sr.get('rows_removed', 0)} "
            f"| {sr.get('cols_before', '?')} "
            f"| {sr.get('cols_after', '?')} "
            f"| {log.get('cells_changed', 0)} "
            f"| {warn_label} |"
        )
    a("")

    # ── Detailed step notes ───────────────────────────────────────────────────
    a("## Detailed Step Notes\n")
    for sr in step_results:
        log = sr.get("log", {})
        a(f"### Step {sr['step']}: {sr['name']}\n")
        a(f"- **Action:** `{sr['action']}`")

        # Decision metadata
        if sr.get("decision_status"):
            a(f"- **Decision status:** {sr['decision_status']}")
        if sr.get("rationale"):
            a(f"- **Rationale:** {sr['rationale']}")

        a(f"- **Rows before:** {log.get('rows_before', '?'):,}  |  "
          f"**Rows after:** {log.get('rows_after', '?'):,}  |  "
          f"**Cells changed:** {log.get('cells_changed', 0)}")

        # Columns added / removed
        cols_added   = sr.get("columns_added", [])
        cols_removed = sr.get("columns_removed", [])
        if cols_added:
            a(f"- **Columns added:** {', '.join(f'`{c}`' for c in cols_added)}")
        if cols_removed:
            a(f"- **Columns removed:** {', '.join(f'`{c}`' for c in cols_removed)}")

        details = log.get("details", "")
        if details:
            a(f"\n```\n{details}\n```")
        warns = log.get("warnings", [])
        if warns:
            a("\n**Warnings:**")
            for w in warns:
                a(f"- ⚠️  {w}")
        if dry_run:
            a("\n> _Dry run — no changes were written._")
        a("")

    # ── Validation summary ────────────────────────────────────────────────────
    a("## Validation Summary\n")
    if not validation_results:
        a("_No validation rules configured._\n")
    else:
        passed = [r for r in validation_results if r.passed]
        failed = [r for r in validation_results if not r.passed]
        a(f"**Passed:** {len(passed)}  |  **Failed:** {len(failed)}\n")
        if passed:
            a("### ✓ Passed\n")
            for r in passed:
                a(f"- `{r.check}` / `{r.column}`: {r.message}")
        if failed:
            a("\n### ✗ Failed\n")
            for r in failed:
                a(f"- `{r.check}` / `{r.column}`: {r.message}")
        a("")

    # ── Before/after summary ──────────────────────────────────────────────────
    a("## Before / After Summary\n")
    a(before_after_md)

    return "\n".join(lines)


# ── Validation report ─────────────────────────────────────────────────────────

def build_validation_report(
    input_path: str,
    output_path: str | None,
    validation_results: list[ValidationResult],
) -> str:
    """Build a concise standalone validation report."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: list[str] = []
    a = lines.append

    a("# Validation Report\n")
    a(f"- **Timestamp:** {ts}")
    a(f"- **Dataset:** `{output_path or input_path}`\n")

    passed = [r for r in validation_results if r.passed]
    failed = [r for r in validation_results if not r.passed]

    a(f"**Result:** {'✓ All checks passed.' if not failed else f'✗ {len(failed)} check(s) failed.'}")
    a(f"**Checks passed:** {len(passed)}  |  **Failed:** {len(failed)}\n")

    if failed:
        a("## Failed Checks\n")
        for r in failed:
            a(f"- **[{r.check}]** `{r.column}`: {r.message}")
        a("")
    if passed:
        a("## Passed Checks\n")
        for r in passed:
            a(f"- **[{r.check}]** `{r.column}`: {r.message}")

    return "\n".join(lines)


# ── Run manifest ──────────────────────────────────────────────────────────────

def build_run_manifest(
    input_path: str,
    output_path: str | None,
    rules_path: str,
    dry_run: bool,
    before_snap: dict[str, Any],
    after_snap: dict[str, Any],
) -> dict[str, Any]:
    """Build a machine-readable run manifest dict."""
    return {
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "dry_run": dry_run,
        "input_file": str(input_path),
        "output_file": str(output_path) if output_path else None,
        "rules_file": str(rules_path),
        "git_commit": _git_commit(),
        "python_version": sys.version.split()[0],
        "package_versions": {
            "pandas": _package_version("pandas"),
            "numpy":  _package_version("numpy"),
            "pyyaml": _package_version("pyyaml"),
        },
        "rows_before":    before_snap["n_rows"],
        "rows_after":     after_snap["n_rows"],
        "columns_before": before_snap["n_cols"],
        "columns_after":  after_snap["n_cols"],
        "missing_cells_before": before_snap["n_missing_cells"],
        "missing_cells_after":  after_snap["n_missing_cells"],
    }


# ── Manager summary ──────────────────────────────────────────────────────────

def build_manager_summary(
    input_path: str,
    output_path: str | None,
    before_snap: dict[str, Any],
    after_snap: dict[str, Any],
    step_results: list[dict[str, Any]],
    validation_results: list[ValidationResult],
    log_path: str | Path | None = None,
    flowchart_path: str | Path | None = None,
) -> str:
    """Build a short non-technical summary suitable for a manager or collaborator.

    Focuses on *what changed* and *whether the data is clean*, using plain language
    rather than technical terms.
    """
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines: list[str] = []
    a = lines.append

    a("# Cleaning Summary\n")
    a(f"_Generated {ts}_\n")
    a(f"- **Input:**  `{input_path}`")
    a(f"- **Output:** `{output_path or 'not written (dry run)'}`\n")

    # ── What changed ──────────────────────────────────────────────────────────
    a("## What changed\n")

    rows_before = before_snap["n_rows"]
    rows_after  = after_snap["n_rows"]
    cols_before = before_snap["n_cols"]
    cols_after  = after_snap["n_cols"]
    miss_before = before_snap["n_missing_cells"]
    miss_after  = after_snap["n_missing_cells"]

    a(f"- Started with **{rows_before:,} rows** and **{cols_before} columns**.")

    rows_removed = rows_before - rows_after
    if rows_removed > 0:
        a(f"- Removed **{rows_removed:,} duplicate row(s)**.")
    cols_added = cols_after - cols_before
    if cols_added > 0:
        a(f"- Added **{cols_added} new column(s)** (e.g. missingness flags, outlier flags).")

    # Summarise actions in plain language
    action_labels = {
        "replace_missing_codes":     "Replaced missing-data codes (e.g. NA, Unknown, -9) with blank.",
        "trim_whitespace":           "Removed leading and trailing spaces from text fields.",
        "standardise_column_names":  "Standardised column names to lowercase with underscores.",
        "map_categories":            "Standardised category labels (e.g. inconsistent capitalisation).",
        "standardise_case":          "Standardised text case in category columns.",
        "set_invalid_to_missing":    "Set impossible numeric values (e.g. age = -5) to blank.",
        "flag_outliers_iqr":         "Flagged statistical outliers for review.",
        "create_missingness_flags":  "Added indicator columns recording which values were originally missing.",
        "remove_exact_duplicates":   "Removed exact duplicate rows.",
        "parse_dates":               "Converted text columns to date format.",
    }
    seen_actions: set[str] = set()
    for sr in step_results:
        action = sr.get("action", "")
        if action not in seen_actions and action in action_labels:
            cells = sr["log"].get("cells_changed", 0)
            label = action_labels[action]
            if cells:
                a(f"- {label} ({cells:,} cells affected)")
            else:
                a(f"- {label}")
            seen_actions.add(action)

    a(f"\n- Ended with **{rows_after:,} rows** and **{cols_after} columns**.")

    miss_delta = miss_before - miss_after
    if miss_delta > 0:
        a(f"- Missing values reduced by **{miss_delta:,}** (from {miss_before:,} to {miss_after:,}).")
    elif miss_after > miss_before:
        a(f"- Missing values increased by **{miss_after - miss_before:,}** (intentional: impossible values set to blank).")

    # ── Data checks ───────────────────────────────────────────────────────────
    a("\n## Data checks after cleaning\n")
    if not validation_results:
        a("_No validation checks were configured._")
    else:
        passed = [r for r in validation_results if r.passed]
        failed = [r for r in validation_results if not r.passed]
        total  = len(validation_results)
        if not failed:
            a(f"✓ All {total} data checks passed.")
        else:
            a(f"⚠ {len(passed)} of {total} checks passed. {len(failed)} need review:")
            for r in failed:
                a(f"  - {r.message}")

    # ── Output paths ──────────────────────────────────────────────────────────
    a("\n## Where to find the full details\n")
    if log_path:
        a(f"- Full cleaning log: `{log_path}`")
    if flowchart_path:
        a(f"- Visual flowchart:  `{flowchart_path}`")
    a(f"- Cleaned data:      `{output_path or 'not written'}`")

    return "\n".join(lines)


# ── File writers ──────────────────────────────────────────────────────────────

def write_log(content: str, directory: str | Path, basename: str) -> Path:
    """Write a markdown string to a timestamped file and return the path."""
    out_dir = Path(directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"{basename}_{ts}.md"
    out_path.write_text(content, encoding="utf-8")
    return out_path


def write_manifest(manifest: dict[str, Any], directory: str | Path, basename: str) -> Path:
    """Write a run manifest to a timestamped YAML file and return the path."""
    out_dir = Path(directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"{basename}_{ts}_manifest.yaml"
    out_path.write_text(
        yaml.dump(manifest, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    return out_path
