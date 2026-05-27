"""
report_writer.py
----------------
Render profiling results to a markdown string (quick report)
and optionally trigger ydata-profiling for the full HTML report.

Report sections (in order)
--------------------------
 1  Report metadata
 2  Dataset overview
 3  Column inventory
 4  Missingness summary
 5  Duplication summary
 6  Continuous variable summary
 7  Binary variable summary
 8  Categorical variable summary
 9  Date variable summary
10  Schema checks
11  Suggested cleaning actions   (brief bullet list)
12  Cleaning decision prompts    (structured analyst questions)
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from toolkit.profiling import DecisionPrompt


# ── Markdown helpers ──────────────────────────────────────────────────────────

def _h1(t: str) -> str: return f"\n# {t}\n"
def _h2(t: str) -> str: return f"\n## {t}\n"
def _h3(t: str) -> str: return f"\n### {t}\n"

def _bullet(items: list[str]) -> str:
    if not items:
        return "_None_\n"
    return "\n".join(f"- {i}" for i in items) + "\n"

def _kv(key: str, value: Any) -> str:
    return f"- **{key}:** {value}\n"

def _df_to_md(df: pd.DataFrame) -> str:
    """Render a DataFrame as a GitHub-flavoured markdown table.

    Uses ``tabulate`` when available for nicer alignment; falls back to a
    simple hand-rolled formatter so the reporter works with zero optional deps.
    """
    if df.empty:
        return "_No data._\n"
    try:
        return df.to_markdown(index=False) + "\n"
    except ImportError:
        pass
    cols = list(df.columns)
    rows = [[str(v) for v in row] for row in df.itertuples(index=False, name=None)]
    col_widths = [max(len(c), max((len(r[i]) for r in rows), default=0))
                  for i, c in enumerate(cols)]
    def fmt_row(cells: list[str]) -> str:
        return "| " + " | ".join(c.ljust(w) for c, w in zip(cells, col_widths)) + " |"
    sep   = "| " + " | ".join("-" * w for w in col_widths) + " |"
    lines = [fmt_row(cols), sep] + [fmt_row(r) for r in rows]
    return "\n".join(lines) + "\n"


# ── Quick report ──────────────────────────────────────────────────────────────

def build_quick_report(
    cfg: dict[str, Any],
    source_label: str,
    overview: dict[str, Any],
    inventory: pd.DataFrame,
    miss_summary: dict[str, Any],
    dup_summary: dict[str, Any],
    cont_df: pd.DataFrame,
    bin_df: pd.DataFrame,
    cat_df: pd.DataFrame,
    date_df: pd.DataFrame,
    schema_issues: dict[str, list[str]] | None,
    warnings: list[str],
    optional_pkg_status: dict[str, bool],
    decision_prompts: "list[DecisionPrompt] | None" = None,
) -> str:
    lines: list[str] = []

    # ── 1. Metadata ───────────────────────────────────────────────────────────
    lines.append(_h1("Descriptive QC Report"))
    lines.append(_kv("Timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    lines.append(_kv("Input source", source_label))
    lines.append(_kv("Selected columns", cfg.get("columns") or "all"))
    lines.append(_kv("ID columns", cfg.get("id_cols") or "none"))
    lines.append(_kv("Report mode", cfg.get("mode", "quick")))
    lines.append(_kv("Schema file", cfg.get("schema_path") or "none"))
    pkg_notes = ", ".join(
        f"{pkg}: {'✓' if avail else '✗ (not installed)'}"
        for pkg, avail in optional_pkg_status.items()
    )
    lines.append(_kv("Optional packages", pkg_notes))

    # ── 2. Dataset overview ───────────────────────────────────────────────────
    lines.append(_h2("Dataset Overview"))
    lines.append(_kv("Rows", f"{overview['n_rows']:,}"))
    lines.append(_kv("Columns", overview['n_cols']))
    lines.append(_kv("Memory (MB)", overview['memory_mb']))
    lines.append(_kv("Inferred type counts", overview['type_counts']))

    # ── 3. Column inventory ───────────────────────────────────────────────────
    lines.append(_h2("Column Inventory"))
    lines.append(_df_to_md(inventory))

    # ── 4. Missingness summary ────────────────────────────────────────────────
    lines.append(_h2("Missingness Summary"))
    if miss_summary.get("top_missing"):
        lines.append(_h3("Top missing columns (%)"))
        for col, pct in miss_summary["top_missing"].items():
            lines.append(f"- {col}: {pct}%\n")
    else:
        lines.append("No missing values detected.\n")
    if miss_summary.get("fully_missing"):
        lines.append(_kv("Fully missing columns", miss_summary["fully_missing"]))
    if miss_summary.get("very_high_missing"):
        lines.append(_kv("Very-high missingness (>50%)", miss_summary["very_high_missing"]))
    if miss_summary.get("high_missing"):
        lines.append(_kv("High missingness (>20%)", miss_summary["high_missing"]))

    # ── 5. Duplication summary ────────────────────────────────────────────────
    lines.append(_h2("Duplication Summary"))
    lines.append(_kv("Exact duplicate rows", dup_summary.get("exact_duplicate_rows", 0)))
    if "duplicate_id_rows" in dup_summary:
        lines.append(_kv(
            f"Rows with duplicate ID ({dup_summary.get('id_cols_checked')})",
            dup_summary["duplicate_id_rows"],
        ))
    if "id_cols_not_found" in dup_summary:
        lines.append(_kv("ID columns not found in data", dup_summary["id_cols_not_found"]))

    # ── 6–9. Variable summaries ───────────────────────────────────────────────
    lines.append(_h2("Continuous Variable Summary"))
    lines.append(_df_to_md(cont_df))

    lines.append(_h2("Binary Variable Summary"))
    lines.append(_df_to_md(bin_df))

    lines.append(_h2("Categorical Variable Summary"))
    if not cat_df.empty:
        display_cols = [c for c in [
            "column", "n_categories", "high_cardinality",
            "n_rare", "possible_whitespace", "possible_case_inconsistency", "missing"
        ] if c in cat_df.columns]
        lines.append(_df_to_md(cat_df[display_cols]))
    else:
        lines.append("_No categorical columns detected._\n")

    lines.append(_h2("Date Variable Summary"))
    lines.append(_df_to_md(date_df))

    # ── 10. Schema checks ─────────────────────────────────────────────────────
    lines.append(_h2("Schema Checks"))
    if schema_issues is None:
        lines.append("_No schema provided. Pass --schema to enable validation checks._\n")
    else:
        any_issues = False
        for issue_type, msgs in schema_issues.items():
            if msgs:
                any_issues = True
                lines.append(_h3(issue_type.replace("_", " ").title()))
                lines.append(_bullet(msgs))
        if not any_issues:
            lines.append("✓ No schema violations detected.\n")

    # ── 11. Suggested cleaning actions ────────────────────────────────────────
    lines.append(_h2("Suggested Cleaning Actions"))
    if warnings:
        lines.append(_bullet(warnings))
    else:
        lines.append("✓ No obvious issues detected.\n")

    # ── 12. Cleaning decision prompts ─────────────────────────────────────────
    lines.append(_h2("Cleaning Decision Prompts"))
    lines.append(
        "> These prompts help you decide **how** to respond to each issue. "
        "They are questions, not instructions — the right action depends on your analysis purpose.\n"
        "> See `docs/cleaning_decision_guides/` for detailed guidance.\n"
    )
    if not decision_prompts:
        lines.append("✓ No issues requiring a cleaning decision were detected.\n")
    else:
        for i, p in enumerate(decision_prompts, 1):
            lines.append(f"\n### Prompt {i} — [{p.dimension}] {p.variable}\n")
            lines.append(f"**Detected:** {p.issue}\n")
            lines.append(f"**Question:** {p.question}\n")
            lines.append("**Options:**\n")
            lines.append(_bullet(p.options))
            lines.append(f"**Document:** {p.document}\n")

    return "".join(lines)


def write_quick_report(report_str: str, cfg: dict[str, Any]) -> Path:
    """Write the markdown report to disk and return the output path."""
    out_dir   = Path(cfg.get("output_dir", "reports/descriptive_summary"))
    out_dir.mkdir(parents=True, exist_ok=True)
    basename  = cfg.get("report_basename", "descriptive_qc_report")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path  = out_dir / f"{basename}_{timestamp}.md"
    out_path.write_text(report_str, encoding="utf-8")
    return out_path


def run_full_profile(df: pd.DataFrame, cfg: dict[str, Any]) -> Path | None:
    """Generate a full HTML profile using ydata-profiling.

    Returns the output path, or None if ydata-profiling is not installed.
    """
    try:
        from ydata_profiling import ProfileReport  # type: ignore
    except ImportError:
        print(
            "[report_writer] ydata-profiling is not installed — skipping full HTML report.\n"
            "  Install with: pip install ydata-profiling"
        )
        return None

    out_dir   = Path(cfg.get("full_profile_dir", "reports/full_profiles"))
    out_dir.mkdir(parents=True, exist_ok=True)
    basename  = cfg.get("report_basename", "descriptive_qc_report")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path  = out_dir / f"{basename}_{timestamp}.html"

    print("[report_writer] Generating full HTML profile (this may take a moment)…")
    profile = ProfileReport(df, title=basename, explorative=True)
    profile.to_file(out_path)
    return out_path
