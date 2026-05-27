"""
flowchart.py
------------
Generate a Mermaid flowchart from a cleaning run audit.

The main output is Mermaid's ``flowchart LR`` syntax, which can be:

  * Embedded directly in a Markdown file — GitHub, GitLab, Quarto, MkDocs,
    and Obsidian all render it natively without any extra tooling.
  * Saved as a ``.mmd`` file for use with the mermaid-cli or the online
    Mermaid Live Editor (https://mermaid.live/).

No mandatory external dependencies are required for Mermaid output.

Public API
----------
build_mermaid_flowchart(before_snap, step_audits, after_snap,
                        validation_summary=None) -> str
write_flowchart_files(mermaid_text, output_dir, basename) -> dict[str, Path]
escape_mermaid_label(text) -> str          (exported for testing / custom use)
format_dataset_node(label, summary) -> str
format_step_node(step_audit) -> str
format_validation_node(validation_summary) -> str
"""

from __future__ import annotations

import datetime
import re
from pathlib import Path
from typing import Any


# ── Text helpers ──────────────────────────────────────────────────────────────

def escape_mermaid_label(text: str) -> str:
    """Escape / clean characters that break Mermaid node labels.

    Mermaid node labels must not contain unescaped double-quotes, angle
    brackets, or raw newlines.  This function converts them to safe
    equivalents so the resulting diagram text is always valid.
    """
    text = str(text)
    text = text.replace('"', "'")           # double-quotes break node syntax
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace("\n", "<br/>")
    text = re.sub(r"\s{2,}", " ", text)     # collapse internal whitespace
    return text.strip()


def _fmt(n: int | float | None) -> str:
    """Format a number with thousands separator; return '?' for None."""
    if n is None:
        return "?"
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return str(n)


# ── Node label builders ───────────────────────────────────────────────────────

def format_dataset_node(label: str, summary: dict[str, Any]) -> str:
    """Return the multi-line label for a raw / cleaned dataset node.

    Parameters
    ----------
    label   : Display heading, e.g. ``"Raw data"`` or ``"Cleaned data"``.
    summary : A snapshot dict as returned by ``toolkit.audit.snapshot()``.
              Expected keys: n_rows, n_cols, n_missing_cells, n_exact_duplicates.
    """
    rows    = _fmt(summary.get("n_rows"))
    cols    = summary.get("n_cols", "?")
    missing = _fmt(summary.get("n_missing_cells"))
    dups    = _fmt(summary.get("n_exact_duplicates"))
    return (
        f"{label}<br/>"
        f"Rows: {rows}<br/>"
        f"Columns: {cols}<br/>"
        f"Missing cells: {missing}<br/>"
        f"Duplicate rows: {dups}"
    )


def format_step_node(step_audit: dict[str, Any]) -> str:
    """Return the multi-line label for a single cleaning-step node.

    Parameters
    ----------
    step_audit : A per-step audit dict with keys:
        step, rule_name, action, cells_changed, rows_removed,
        columns_added, columns_removed, warnings, destructive,
        outliers_flagged.
    """
    step   = step_audit.get("step", "?")
    name   = escape_mermaid_label(str(step_audit.get("rule_name", "?")))
    action = step_audit.get("action", "?")

    parts = [f"Step {step}: {name}"]

    # Show action in parentheses only when it differs from the rule name
    if name.lower() != action.replace("_", " ").lower():
        parts.append(f"({action})")

    outliers_flagged = step_audit.get("outliers_flagged")
    cells_changed    = step_audit.get("cells_changed", 0)
    rows_removed     = step_audit.get("rows_removed", 0)
    cols_added       = step_audit.get("columns_added", [])
    cols_removed     = step_audit.get("columns_removed", [])

    if outliers_flagged is not None:
        parts.append(f"Outliers flagged: {_fmt(outliers_flagged)}")
    elif cells_changed:
        parts.append(f"Cells changed: {_fmt(cells_changed)}")

    if rows_removed:
        parts.append(f"Rows removed: {_fmt(rows_removed)}")

    if cols_added:
        parts.append(f"Columns added: {len(cols_added)}")
    if cols_removed:
        parts.append(f"Columns removed: {len(cols_removed)}")

    n_warn = len(step_audit.get("warnings", []))
    if n_warn:
        parts.append(f"Warnings: {n_warn}")

    if step_audit.get("destructive"):
        parts.append("⚠ DESTRUCTIVE")

    return "<br/>".join(parts)


def format_validation_node(validation_summary: dict[str, Any]) -> str:
    """Return the multi-line label for the validation node.

    Parameters
    ----------
    validation_summary : dict with keys ``passed`` (int) and ``failed`` (int).
    """
    n_passed = int(validation_summary.get("passed", 0))
    n_failed = int(validation_summary.get("failed", 0))
    n_total  = n_passed + n_failed

    if n_total == 0:
        return "Validation<br/>No checks configured"

    lines = ["Validation"]
    if n_failed == 0:
        lines.append(f"All {n_total} checks passed")
    else:
        lines.append(f"Passed: {n_passed}")
        lines.append(f"Failed: {n_failed}")
    return "<br/>".join(lines)


# ── Main builder ──────────────────────────────────────────────────────────────

def build_mermaid_flowchart(
    before_snap: dict[str, Any],
    step_audits: list[dict[str, Any]],
    after_snap: dict[str, Any],
    validation_summary: dict[str, Any] | None = None,
) -> str:
    """Return a complete Mermaid ``flowchart LR`` diagram as a string.

    The layout is a simple left-to-right linear chain:

        Raw data → Step 1 → Step 2 → … → Validation → Cleaned data

    Node colours are driven by Mermaid CSS classes:

    * ``input_node``       — raw dataset (blue tint)
    * ``clean_step``       — non-destructive, no warnings (grey)
    * ``destructive_step`` — removed rows or columns (red tint)
    * ``warning_step``     — has warnings (yellow tint)
    * ``validation_node``  — validation passed (teal tint)
    * ``warning_step``     — validation has failures (yellow tint)
    * ``output_node``      — cleaned dataset (green tint)

    Parameters
    ----------
    before_snap        : Snapshot dict from ``toolkit.audit.snapshot()`` (before).
    step_audits        : List of per-step audit dicts (see ``format_step_node``).
    after_snap         : Snapshot dict from ``toolkit.audit.snapshot()`` (after).
    validation_summary : Optional dict with ``passed`` and ``failed`` counts.
    """
    lines: list[str] = []
    a = lines.append
    a("flowchart LR")
    a("")

    # ── Node definitions ──────────────────────────────────────────────────────
    node_ids: list[str] = []

    # N0 — raw dataset
    raw_label = format_dataset_node("Raw data", before_snap)
    a(f'  N0["{raw_label}"]')
    node_ids.append("N0")

    # N1…Nk — cleaning steps
    for i, audit in enumerate(step_audits, start=1):
        nid = f"N{i}"
        lbl = format_step_node(audit)
        a(f'  {nid}["{lbl}"]')
        node_ids.append(nid)

    n_steps = len(step_audits)

    # Optional validation node
    val_node_id: str | None = None
    if validation_summary is not None:
        val_node_id = f"N{n_steps + 1}"
        val_label   = format_validation_node(validation_summary)
        a(f'  {val_node_id}["{val_label}"]')
        node_ids.append(val_node_id)

    # Cleaned dataset node (always last)
    out_nid = f"N{n_steps + (2 if val_node_id else 1)}"
    clean_label = format_dataset_node("Cleaned data", after_snap)
    a(f'  {out_nid}["{clean_label}"]')
    node_ids.append(out_nid)

    # ── Edges — linear chain ──────────────────────────────────────────────────
    a("")
    a("  " + " --> ".join(node_ids))

    # ── CSS class definitions ─────────────────────────────────────────────────
    a("")
    a("  classDef input_node       fill:#e8f1ff,stroke:#2b6cb0,stroke-width:2px;")
    a("  classDef clean_step       fill:#f7fafc,stroke:#4a5568,stroke-width:1px;")
    a("  classDef destructive_step fill:#ffe8e8,stroke:#c53030,stroke-width:2px;")
    a("  classDef warning_step     fill:#fff8db,stroke:#d69e2e,stroke-width:2px;")
    a("  classDef validation_node  fill:#e6fffa,stroke:#319795,stroke-width:2px;")
    a("  classDef output_node      fill:#e9ffe8,stroke:#2f855a,stroke-width:2px;")

    # ── Class assignments ─────────────────────────────────────────────────────
    a(f"  class N0 input_node;")
    a(f"  class {out_nid} output_node;")

    if val_node_id:
        n_failed = int((validation_summary or {}).get("failed", 0))
        val_class = "warning_step" if n_failed else "validation_node"
        a(f"  class {val_node_id} {val_class};")

    for i, audit in enumerate(step_audits, start=1):
        nid = f"N{i}"
        if audit.get("destructive"):
            cls = "destructive_step"
        elif audit.get("warnings"):
            cls = "warning_step"
        else:
            cls = "clean_step"
        a(f"  class {nid} {cls};")

    return "\n".join(lines)


# ── File writers ──────────────────────────────────────────────────────────────

def write_flowchart_files(
    mermaid_text: str,
    output_dir: str | Path,
    basename: str,
) -> dict[str, Path]:
    """Write ``.mmd`` and ``.md`` flowchart files; return their ``Path``s.

    Parameters
    ----------
    mermaid_text : The Mermaid diagram string produced by
                   ``build_mermaid_flowchart``.
    output_dir   : Directory to write the files (created if absent).
    basename     : Base name without extension, e.g. ``"my_rules"``.

    Returns
    -------
    dict with keys ``"mmd"`` and ``"md"`` mapping to the written ``Path`` objects.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    mmd_path = out_dir / f"{basename}_{ts}_flow.mmd"
    md_path  = out_dir / f"{basename}_{ts}_flow.md"

    # Raw .mmd file — for mermaid-cli or online editors
    mmd_path.write_text(mermaid_text + "\n", encoding="utf-8")

    # .md file with an embedded Mermaid code fence
    md_content = (
        "# Cleaning Flow Diagram\n\n"
        "_Rendered automatically by the data-cleaning-toolkit. "
        "Open this file in GitHub, GitLab, Quarto, or MkDocs to see the diagram._\n\n"
        "```mermaid\n"
        + mermaid_text
        + "\n```\n"
    )
    md_path.write_text(md_content, encoding="utf-8")

    return {"mmd": mmd_path, "md": md_path}
