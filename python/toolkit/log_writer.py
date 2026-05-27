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
