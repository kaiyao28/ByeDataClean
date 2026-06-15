"""
decision_memo.py
----------------
Generate a pre-filled decision memo from cleaning pipeline results.

The memo answers: "Can this dataset be used for [purpose]?"

Sections that require human input are marked with [FILL IN].
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

from toolkit.scorecard import _overall_status, _recommended_use
from toolkit.validation import ValidationResult


def build_decision_memo(
    dataset_name: str,
    step_results: list[dict[str, Any]],
    validation_results: list[ValidationResult],
    before_snap: dict[str, Any],
    after_snap: dict[str, Any],
    rules_name: str = "",
    log_path: str | Path | None = None,
    val_path: str | Path | None = None,
    scorecard_path: str | Path | None = None,
) -> str:
    """Build a pre-filled decision memo from cleaning pipeline results.

    Sections that cannot be inferred automatically are marked [FILL IN].
    """
    ts = datetime.datetime.now().strftime("%Y-%m-%d")
    status = _overall_status(step_results, validation_results)
    rec_use = _recommended_use(status, step_results, validation_results)

    lines: list[str] = []
    a = lines.append

    a("# Data Quality Decision Memo\n")
    a(f"**Dataset:** `{dataset_name}`  ")
    a(f"**Rules:** `{rules_name}`  ")
    a(f"**Prepared by:** [FILL IN: analyst name]  ")
    a(f"**Date:** {ts}  ")
    a(f"**Review requested from:** [FILL IN: data owner / product owner / finance]\n")

    a("---\n")
    a("## Question\n")
    a(f"> Can the dataset `{dataset_name}` be used for "
      "`[FILL IN: e.g. the Q1 retention analysis / the revenue dashboard]`?\n")

    # ── Recommendation ────────────────────────────────────────────────────────
    a("---\n")
    a("## Recommendation\n")
    if status == "PASS":
        a("**✓ Use** — this dataset passes all automated quality checks.")
        a("")
        a("> _Automated recommendation based on PASS status. Confirm with the data owner._")
    elif status == "WARNING":
        a("**⚠ Use with caveats** — known issues exist. See unresolved issues section.")
        a("")
        a("> _Automated recommendation based on WARNING status. Review open issues before publishing._")
    else:
        a("**✗ Do not use yet** — blocking data quality issues must be resolved.")
        a("")
        a("> _Automated recommendation based on BLOCKER status. See unresolved issues below._")
    a("")

    # ── Main data quality risks ───────────────────────────────────────────────
    a("---\n")
    a("## Main data-quality risks\n")
    severity_order = ["critical", "high", "medium", "low"]
    risk_steps = [
        sr for sr in step_results
        if (sr.get("severity") or "").lower() in severity_order
    ]
    if risk_steps:
        a("| Issue | Severity | Business metric affected |")
        a("|---|---|---|")
        for sr in sorted(risk_steps,
                         key=lambda s: severity_order.index((s.get("severity") or "low").lower())):
            note = sr.get("stakeholder_note") or sr.get("rationale") or sr.get("name", "")
            if note and len(note) > 80:
                note = note[:77].rstrip() + "…"
            bm = sr.get("business_metric") or "—"
            if isinstance(bm, list):
                bm = ", ".join(bm)
            sev = (sr.get("severity") or "").capitalize()
            a(f"| {note} | {sev} | {bm} |")
    else:
        a("| Issue | Severity | Business metric affected |")
        a("|---|---|---|")
        a("| [FILL IN] | | |")
    a("")

    # ── Business metrics affected ─────────────────────────────────────────────
    a("---\n")
    a("## Business metrics affected\n")
    all_metrics: set[str] = set()
    for sr in step_results:
        bm = sr.get("business_metric") or ""
        if isinstance(bm, list):
            all_metrics.update(bm)
        elif bm:
            all_metrics.add(bm)
    if all_metrics:
        for m in sorted(all_metrics):
            a(f"- `{m}` — [FILL IN: describe the specific impact]")
    else:
        a("- [FILL IN: e.g. Monthly GMV figure]")
        a("- [FILL IN: e.g. Retention cohort]")
    a("")

    # ── Cleaning actions applied ──────────────────────────────────────────────
    a("---\n")
    a("## Cleaning actions applied\n")
    a("| Step | Action | Decision status | Rows affected |")
    a("|---|---|---|---|")
    for sr in step_results:
        rows_removed = sr.get("rows_removed", 0)
        cells_changed = (sr.get("log") or {}).get("cells_changed", 0)
        if rows_removed:
            effect = f"{rows_removed} row(s) removed"
        elif cells_changed:
            effect = f"{cells_changed} cell(s) changed"
        else:
            effect = "—"
        status_str = sr.get("decision_status") or "—"
        a(f"| {sr['step']} | `{sr['action']}` | {status_str} | {effect} |")
    a("")
    if log_path:
        a(f"Full cleaning log: `{log_path}`\n")

    # ── Unresolved issues ─────────────────────────────────────────────────────
    a("---\n")
    a("## Remaining unresolved issues\n")
    unresolved = [
        sr for sr in step_results
        if (sr.get("action_required") or "").lower() in ("investigate", "block_report")
    ]
    if unresolved:
        a("| Issue | Action required | Owner |")
        a("|---|---|---|")
        for sr in unresolved:
            note = sr.get("stakeholder_note") or sr.get("name", sr.get("action", ""))
            if note and len(note) > 80:
                note = note[:77].rstrip() + "…"
            ar = sr.get("action_required", "investigate")
            owner = sr.get("owner") or "[FILL IN]"
            a(f"| {note} | `{ar}` | {owner} |")
    else:
        a("_No unresolved issues — all identified problems were addressed by cleaning rules._")
    a("")

    # ── Safe / unsafe decisions ───────────────────────────────────────────────
    a("---\n")
    a("## What decisions are safe after cleaning\n")
    safe = [use for use, is_safe in rec_use if is_safe and use != "Not safe without investigation"]
    if safe:
        for s in safe:
            a(f"- {s}")
    else:
        a("- [FILL IN: list analyses that are safe to proceed with]")
    a("")

    a("## What decisions are NOT safe without further investigation\n")
    not_safe = [use for use, is_safe in rec_use
                if not is_safe and use != "Not safe without investigation"]
    if unresolved:
        for sr in unresolved:
            note = sr.get("stakeholder_note") or sr.get("name", "")
            if note and len(note) > 100:
                note = note[:97].rstrip() + "…"
            a(f"- {note}")
    elif not_safe:
        for s in not_safe:
            a(f"- {s}")
    else:
        a("- [FILL IN: list analyses that require further investigation]")
    a("")

    # ── Next actions ──────────────────────────────────────────────────────────
    a("---\n")
    a("## Next actions\n")
    a("| Action | Owner | By when |")
    a("|---|---|---|")
    if unresolved:
        for sr in unresolved:
            name = sr.get("name", sr.get("action", ""))
            owner = sr.get("owner") or "[FILL IN]"
            a(f"| Resolve: {name} | {owner} | [FILL IN: date] |")
    else:
        a("| [FILL IN] | [FILL IN] | [FILL IN] |")
    a("")

    # ── Supporting documents ──────────────────────────────────────────────────
    a("---\n")
    a("## Supporting documents\n")
    if log_path:
        a(f"- Cleaning log: `{log_path}`")
    if val_path:
        a(f"- Validation report: `{val_path}`")
    if scorecard_path:
        a(f"- Data quality scorecard: `{scorecard_path}`")
    a("- Business impact report: `[FILL IN]`")
    a("")
    a("---\n")
    a("_Generated by [ByeDataClean](https://github.com/kaiyao28/ByeDataClean)._")
    a(f"_Template: `docs/templates/decision_memo_template.md`_")

    return "\n".join(lines)


def write_decision_memo(content: str, directory: str | Path, basename: str) -> Path:
    """Write the decision memo to a timestamped file and return the path."""
    out_dir = Path(directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"{basename}_{ts}_decision_memo.md"
    out_path.write_text(content, encoding="utf-8")
    return out_path
