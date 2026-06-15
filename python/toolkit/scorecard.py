"""
scorecard.py
------------
Build a stakeholder-facing data-quality scorecard.

Summarises whether a dataset is safe to use for analysis, dashboarding,
ML, or reporting. Called by run_cleaner.py when --scorecard is passed.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

from toolkit.validation import ValidationResult


SEVERITY_ORDER = ["critical", "high", "medium", "low"]


def _overall_status(
    step_results: list[dict[str, Any]],
    validation_results: list[ValidationResult],
) -> str:
    """Return 'BLOCKER', 'WARNING', or 'PASS'."""
    if any(not r.passed for r in validation_results):
        return "BLOCKER"

    for sr in step_results:
        sev = (sr.get("severity") or "").lower()
        ar = (sr.get("action_required") or "").lower()
        if sev == "critical" and ar in ("block_report", "investigate"):
            return "BLOCKER"
        if sev == "high" and ar == "block_report":
            return "BLOCKER"

    for sr in step_results:
        sev = (sr.get("severity") or "").lower()
        ar = (sr.get("action_required") or "").lower()
        if sev in ("high", "medium") and ar in ("investigate", "block_report"):
            return "WARNING"

    return "PASS"


def _severity_counts(step_results: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {s: 0 for s in SEVERITY_ORDER}
    for sr in step_results:
        sev = (sr.get("severity") or "").lower()
        if sev in counts:
            counts[sev] += 1
    return counts


def _recommended_use(
    status: str,
    step_results: list[dict[str, Any]],
    validation_results: list[ValidationResult],
) -> list[tuple[str, bool]]:
    val_failures = sum(1 for r in validation_results if not r.passed)
    has_investigate = any(
        (sr.get("action_required") or "").lower() in ("investigate", "block_report")
        for sr in step_results
    )
    return [
        ("Safe for exploratory analysis",  status != "BLOCKER"),
        ("Safe for dashboard refresh",     status == "PASS" and val_failures == 0),
        ("Safe for experiment readout",    status == "PASS" and val_failures == 0 and not has_investigate),
        ("Safe for executive reporting",   status == "PASS" and val_failures == 0 and not has_investigate),
        ("Not safe without investigation", status == "BLOCKER"),
    ]


def build_scorecard(
    dataset_name: str,
    before_snap: dict[str, Any],
    after_snap: dict[str, Any],
    step_results: list[dict[str, Any]],
    validation_results: list[ValidationResult],
    rules_name: str = "",
) -> str:
    """Assemble and return the scorecard as a markdown string."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    status = _overall_status(step_results, validation_results)
    sev_counts = _severity_counts(step_results)
    status_icon = {"PASS": "✓", "WARNING": "⚠", "BLOCKER": "✗"}[status]

    lines: list[str] = []
    a = lines.append

    a("# Data Quality Scorecard\n")
    a(f"**Dataset:** `{dataset_name}`  ")
    a(f"**Rules:** `{rules_name}`  ")
    a(f"**Generated:** {ts}\n")

    a("---\n")
    a(f"## Overall status: {status_icon} {status}\n")
    if status == "PASS":
        a("All checks passed. No blocking issues found.")
    elif status == "WARNING":
        a("One or more issues require investigation before this data is used for reporting.")
    else:
        a("This dataset has blocking issues. Do not use for reporting until resolved.")
    a("")

    a("---\n")
    a("## Issues by severity\n")
    a("| Severity | Steps flagged |")
    a("|---|---:|")
    for sev in SEVERITY_ORDER:
        a(f"| {sev.capitalize()} | {sev_counts[sev]} |")
    a("")

    val_passed = sum(1 for r in validation_results if r.passed)
    val_failed = sum(1 for r in validation_results if not r.passed)
    a("## Validation checks\n")
    a(f"- Passed: **{val_passed}**")
    a(f"- Failed: **{val_failed}**")
    if val_failed:
        a("\n**Failed checks:**")
        for r in (r for r in validation_results if not r.passed):
            a(f"  - `{r.check}` / `{r.column}`: {r.message}")
    a("")

    a("## Dataset counts\n")
    a("| | Before | After | Change |")
    a("|---|---:|---:|---:|")
    row_d = after_snap["n_rows"] - before_snap["n_rows"]
    col_d = after_snap["n_cols"] - before_snap["n_cols"]
    mis_d = after_snap["n_missing_cells"] - before_snap["n_missing_cells"]
    a(f"| Rows | {before_snap['n_rows']:,} | {after_snap['n_rows']:,} | {row_d:+} |")
    a(f"| Columns | {before_snap['n_cols']} | {after_snap['n_cols']} | {col_d:+} |")
    a(f"| Missing cells | {before_snap['n_missing_cells']:,} | {after_snap['n_missing_cells']:,} | {mis_d:+} |")
    a("")

    destructive = [sr for sr in step_results if sr.get("destructive")]
    a("## Destructive actions applied\n")
    if destructive:
        for sr in destructive:
            rows_rm = sr.get("rows_removed", 0)
            cols_rm = sr.get("columns_removed", [])
            parts = []
            if rows_rm:
                parts.append(f"{rows_rm} row(s) removed")
            if cols_rm:
                parts.append(f"{len(cols_rm)} column(s) removed")
            a(f"- **Step {sr['step']}: {sr['name']}** — {', '.join(parts) or 'modified'}")
    else:
        a("None — no rows or columns were removed.")
    a("")

    unresolved = [
        sr for sr in step_results
        if (sr.get("action_required") or "").lower() in ("investigate", "block_report")
    ]
    a("## Unresolved issues requiring action\n")
    if unresolved:
        for sr in unresolved:
            note = sr.get("stakeholder_note") or sr.get("rationale") or ""
            if note and len(note) > 150:
                note = note[:147].rstrip() + "…"
            ar = sr.get("action_required", "investigate")
            a(f"- **Step {sr['step']}: {sr['name']}** `[{ar}]`")
            if note:
                a(f"  _{note}_")
    else:
        a("None — all identified issues have been resolved by cleaning rules.")
    a("")

    a("## Recommended use\n")
    for use_case, is_safe in _recommended_use(status, step_results, validation_results):
        icon = "✓" if is_safe else "✗"
        a(f"- {icon} {use_case}")
    a("")

    return "\n".join(lines)


def write_scorecard(content: str, directory: str | Path, basename: str) -> Path:
    """Write the scorecard to a timestamped file and return the path."""
    out_dir = Path(directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"{basename}_{ts}_scorecard.md"
    out_path.write_text(content, encoding="utf-8")
    return out_path
