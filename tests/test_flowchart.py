"""
test_flowchart.py
-----------------
Unit tests for toolkit.flowchart.

All tests are fully in-memory — no data files, no optional packages.
"""

from __future__ import annotations

import pytest

from toolkit.flowchart import (
    build_mermaid_flowchart,
    escape_mermaid_label,
    format_dataset_node,
    format_step_node,
    format_validation_node,
    write_flowchart_files,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def before_snap() -> dict:
    return {
        "n_rows": 10_000,
        "n_cols": 45,
        "n_missing_cells": 1_230,
        "n_exact_duplicates": 30,
    }


@pytest.fixture
def after_snap() -> dict:
    return {
        "n_rows": 9_970,
        "n_cols": 46,
        "n_missing_cells": 1_206,
        "n_exact_duplicates": 0,
    }


@pytest.fixture
def step_audits() -> list[dict]:
    return [
        {
            "step": 1,
            "rule_name": "replace_common_missing_codes",
            "action": "replace_missing_codes",
            "rows_before": 10_000,
            "rows_after":  10_000,
            "rows_removed": 0,
            "columns_before": 45,
            "columns_after":  45,
            "columns_added":   [],
            "columns_removed": [],
            "cells_changed": 530,
            "warnings": [],
            "destructive": False,
            "outliers_flagged": None,
        },
        {
            "step": 2,
            "rule_name": "map_sex_labels",
            "action": "map_categories",
            "rows_before": 10_000,
            "rows_after":  10_000,
            "rows_removed": 0,
            "columns_before": 45,
            "columns_after":  45,
            "columns_added":   [],
            "columns_removed": [],
            "cells_changed": 86,
            "warnings": ["2 unmatched values found"],
            "destructive": False,
            "outliers_flagged": None,
        },
        {
            "step": 3,
            "rule_name": "flag_bmi_outliers",
            "action": "flag_outliers_iqr",
            "rows_before": 10_000,
            "rows_after":  10_000,
            "rows_removed": 0,
            "columns_before": 45,
            "columns_after":  46,
            "columns_added":   ["bmi_outlier_flag"],
            "columns_removed": [],
            "cells_changed": 19,
            "warnings": [],
            "destructive": False,
            "outliers_flagged": 19,
        },
        {
            "step": 4,
            "rule_name": "remove_exact_duplicate_rows",
            "action": "remove_exact_duplicates",
            "rows_before": 10_000,
            "rows_after":  9_970,
            "rows_removed": 30,
            "columns_before": 46,
            "columns_after":  46,
            "columns_added":   [],
            "columns_removed": [],
            "cells_changed": 0,
            "warnings": [],
            "destructive": True,
            "outliers_flagged": None,
        },
    ]


@pytest.fixture
def val_summary() -> dict:
    return {"passed": 9, "failed": 1}


# ── 1. escape_mermaid_label ───────────────────────────────────────────────────

def test_escape_double_quotes():
    assert '"' not in escape_mermaid_label('say "hello"')


def test_escape_angle_brackets():
    result = escape_mermaid_label("<b>bold</b>")
    assert "<b>" not in result
    assert "&lt;b&gt;" in result


def test_escape_newlines():
    result = escape_mermaid_label("line1\nline2")
    assert "\n" not in result
    assert "<br/>" in result


# ── 2. format_dataset_node ────────────────────────────────────────────────────

def test_dataset_node_contains_label(before_snap):
    result = format_dataset_node("Raw data", before_snap)
    assert "Raw data" in result


def test_dataset_node_contains_row_count(before_snap):
    result = format_dataset_node("Raw data", before_snap)
    assert "10,000" in result


def test_dataset_node_contains_missing_cells(before_snap):
    result = format_dataset_node("Raw data", before_snap)
    assert "1,230" in result


def test_dataset_node_contains_duplicates(before_snap):
    result = format_dataset_node("Raw data", before_snap)
    assert "30" in result


# ── 3. format_step_node ───────────────────────────────────────────────────────

def test_step_node_contains_step_number(step_audits):
    result = format_step_node(step_audits[0])
    assert "Step 1" in result


def test_step_node_shows_cells_changed(step_audits):
    result = format_step_node(step_audits[0])
    assert "530" in result


def test_step_node_outliers_flagged_label(step_audits):
    """flag_outliers_iqr steps should say 'Outliers flagged', not 'Cells changed'."""
    result = format_step_node(step_audits[2])
    assert "Outliers flagged" in result
    assert "19" in result


def test_step_node_shows_rows_removed(step_audits):
    result = format_step_node(step_audits[3])
    assert "Rows removed" in result
    assert "30" in result


def test_step_node_shows_columns_added(step_audits):
    result = format_step_node(step_audits[2])
    assert "Columns added" in result


def test_step_node_destructive_label(step_audits):
    result = format_step_node(step_audits[3])
    assert "DESTRUCTIVE" in result


def test_step_node_warning_count(step_audits):
    """Step with warnings should show the warning count."""
    result = format_step_node(step_audits[1])
    assert "Warnings" in result


# ── 4. format_validation_node ─────────────────────────────────────────────────

def test_validation_node_shows_passed():
    result = format_validation_node({"passed": 9, "failed": 0})
    assert "9" in result


def test_validation_node_shows_failed():
    result = format_validation_node({"passed": 9, "failed": 1})
    assert "Failed" in result
    assert "1" in result


def test_validation_node_no_checks():
    result = format_validation_node({"passed": 0, "failed": 0})
    assert "no checks" in result.lower()


# ── 5. build_mermaid_flowchart ────────────────────────────────────────────────

def test_build_mermaid_returns_string(before_snap, step_audits, after_snap):
    result = build_mermaid_flowchart(before_snap, step_audits, after_snap)
    assert isinstance(result, str)
    assert len(result) > 50


def test_mermaid_contains_flowchart_lr(before_snap, step_audits, after_snap):
    result = build_mermaid_flowchart(before_snap, step_audits, after_snap)
    assert "flowchart LR" in result


def test_mermaid_contains_raw_data_node(before_snap, step_audits, after_snap):
    result = build_mermaid_flowchart(before_snap, step_audits, after_snap)
    assert "Raw data" in result


def test_mermaid_contains_cleaned_data_node(before_snap, step_audits, after_snap):
    result = build_mermaid_flowchart(before_snap, step_audits, after_snap)
    assert "Cleaned data" in result


def test_mermaid_contains_all_step_nodes(before_snap, step_audits, after_snap):
    result = build_mermaid_flowchart(before_snap, step_audits, after_snap)
    for i in range(1, len(step_audits) + 1):
        assert f"N{i}[" in result


def test_mermaid_linear_edges(before_snap, step_audits, after_snap):
    """All nodes must be connected in a single --> chain."""
    result = build_mermaid_flowchart(before_snap, step_audits, after_snap)
    assert "-->" in result
    # The chain connects N0 through to the last node
    assert "N0 -->" in result


def test_mermaid_destructive_step_gets_destructive_class(before_snap, step_audits, after_snap):
    result = build_mermaid_flowchart(before_snap, step_audits, after_snap)
    # Step 4 is destructive (index 3 → node N4)
    assert "class N4 destructive_step" in result


def test_mermaid_warning_step_gets_warning_class(before_snap, step_audits, after_snap):
    result = build_mermaid_flowchart(before_snap, step_audits, after_snap)
    # Step 2 has warnings (index 1 → node N2)
    assert "class N2 warning_step" in result


def test_mermaid_safe_step_gets_clean_class(before_snap, step_audits, after_snap):
    result = build_mermaid_flowchart(before_snap, step_audits, after_snap)
    # Step 1 is safe, no warnings (node N1)
    assert "class N1 clean_step" in result


def test_mermaid_raw_node_class(before_snap, step_audits, after_snap):
    result = build_mermaid_flowchart(before_snap, step_audits, after_snap)
    assert "class N0 input_node" in result


def test_mermaid_cleaned_node_class(before_snap, step_audits, after_snap):
    result = build_mermaid_flowchart(before_snap, step_audits, after_snap)
    assert "output_node" in result


def test_mermaid_contains_validation_node(before_snap, step_audits, after_snap, val_summary):
    result = build_mermaid_flowchart(before_snap, step_audits, after_snap, val_summary)
    assert "Validation" in result


def test_mermaid_validation_failure_gets_warning_class(before_snap, step_audits, after_snap):
    result = build_mermaid_flowchart(
        before_snap, step_audits, after_snap, {"passed": 9, "failed": 1}
    )
    # Validation node should be warning-styled when there are failures
    assert "warning_step" in result


def test_mermaid_validation_pass_gets_validation_class(before_snap, step_audits, after_snap):
    result = build_mermaid_flowchart(
        before_snap, step_audits, after_snap, {"passed": 9, "failed": 0}
    )
    assert "validation_node" in result


def test_mermaid_no_validation_node_when_none(before_snap, step_audits, after_snap):
    result = build_mermaid_flowchart(before_snap, step_audits, after_snap, None)
    assert "Validation" not in result


def test_mermaid_contains_css_classes(before_snap, step_audits, after_snap):
    result = build_mermaid_flowchart(before_snap, step_audits, after_snap)
    assert "classDef" in result


def test_mermaid_empty_steps(before_snap, after_snap):
    """Pipeline with no cleaning steps should still produce a valid diagram."""
    result = build_mermaid_flowchart(before_snap, [], after_snap)
    assert "flowchart LR" in result
    assert "Raw data" in result
    assert "Cleaned data" in result


# ── 6. write_flowchart_files ──────────────────────────────────────────────────

def test_write_flowchart_creates_mmd_file(tmp_path, before_snap, step_audits, after_snap):
    mermaid_text = build_mermaid_flowchart(before_snap, step_audits, after_snap)
    paths = write_flowchart_files(mermaid_text, tmp_path / "logs", "test_rules")
    assert paths["mmd"].exists()
    assert paths["mmd"].suffix == ".mmd"


def test_write_flowchart_creates_md_file(tmp_path, before_snap, step_audits, after_snap):
    mermaid_text = build_mermaid_flowchart(before_snap, step_audits, after_snap)
    paths = write_flowchart_files(mermaid_text, tmp_path / "logs", "test_rules")
    assert paths["md"].exists()
    assert paths["md"].suffix == ".md"


def test_write_flowchart_md_embeds_mermaid_fence(tmp_path, before_snap, step_audits, after_snap):
    mermaid_text = build_mermaid_flowchart(before_snap, step_audits, after_snap)
    paths = write_flowchart_files(mermaid_text, tmp_path / "logs", "test_rules")
    content = paths["md"].read_text(encoding="utf-8")
    assert "```mermaid" in content
    assert "flowchart LR" in content


def test_write_flowchart_mmd_content_matches(tmp_path, before_snap, step_audits, after_snap):
    mermaid_text = build_mermaid_flowchart(before_snap, step_audits, after_snap)
    paths = write_flowchart_files(mermaid_text, tmp_path / "logs", "test_rules")
    mmd_content = paths["mmd"].read_text(encoding="utf-8").strip()
    assert mmd_content == mermaid_text


def test_write_flowchart_creates_dir_if_absent(tmp_path, before_snap, step_audits, after_snap):
    mermaid_text = build_mermaid_flowchart(before_snap, step_audits, after_snap)
    new_dir = tmp_path / "deep" / "nested" / "logs"
    assert not new_dir.exists()
    write_flowchart_files(mermaid_text, new_dir, "rules")
    assert new_dir.exists()


# ── 7. Pipeline integration — flowchart=True ─────────────────────────────────

def test_pipeline_flowchart_writes_mmd_and_md(tmp_path):
    """run_cleaning_pipeline with flowchart=True must write .mmd and .md files."""
    import pandas as pd
    from toolkit.cleaning import run_cleaning_pipeline

    df = pd.DataFrame({
        "ParticipantID": [1, 2, 3],
        "Age": [25.0, -9.0, 30.0],
        "Dx": ["Control", "NA", "SCZ"],
    })
    rules = {
        "version": 1,
        "name": "flowchart_test_rules",
        "rules": [
            {"step": 1, "name": "standardise_column_names",
             "action": "standardise_column_names"},
            {"step": 2, "name": "replace_missing_codes",
             "action": "replace_missing_codes",
             "columns": "all", "missing_codes": ["NA", -9]},
        ],
    }

    log_dir = tmp_path / "logs"
    run_cleaning_pipeline(
        df, rules,
        log_dir=str(log_dir),
        validation_dir=str(tmp_path / "val"),
        flowchart=True,
    )

    mmd_files = list(log_dir.glob("*_flow.mmd"))
    md_files  = list(log_dir.glob("*_flow.md"))
    assert len(mmd_files) == 1, "Expected exactly one .mmd flowchart file"
    assert len(md_files)  == 1, "Expected exactly one .md flowchart file"


def test_pipeline_no_flowchart_by_default(tmp_path):
    """Without flowchart=True, no .mmd / .md flow files should be written."""
    import pandas as pd
    from toolkit.cleaning import run_cleaning_pipeline

    df = pd.DataFrame({"id": [1, 2, 3], "val": [10, 20, 30]})
    rules = {"version": 1, "name": "no_flow_rules", "rules": [
        {"step": 1, "action": "standardise_column_names",
         "name": "standardise_column_names"},
    ]}
    log_dir = tmp_path / "logs"
    run_cleaning_pipeline(
        df, rules,
        log_dir=str(log_dir),
        validation_dir=str(tmp_path / "val"),
    )
    assert list(log_dir.glob("*_flow.mmd")) == []
    assert list(log_dir.glob("*_flow.md"))  == []


def test_cleaning_log_embeds_mermaid_when_flowchart_enabled(tmp_path):
    """The cleaning log .md file should contain a mermaid code fence when flowchart=True."""
    import pandas as pd
    from toolkit.cleaning import run_cleaning_pipeline

    df = pd.DataFrame({"Score": [10.0, 20.0, 30.0]})
    rules = {"version": 1, "name": "embed_test", "rules": [
        {"step": 1, "action": "standardise_column_names",
         "name": "standardise_column_names"},
    ]}
    log_dir = tmp_path / "logs"
    _, cleaning_log, _ = run_cleaning_pipeline(
        df, rules,
        log_dir=str(log_dir),
        validation_dir=str(tmp_path / "val"),
        flowchart=True,
    )
    assert "```mermaid" in cleaning_log
    assert "## Cleaning Flowchart" in cleaning_log


def test_cleaning_log_always_has_step_impact_table(tmp_path):
    """## Step Impact Summary must appear in the log even without flowchart."""
    import pandas as pd
    from toolkit.cleaning import run_cleaning_pipeline

    df = pd.DataFrame({"val": [1, 2, 3]})
    rules = {"version": 1, "name": "impact_table_test", "rules": [
        {"step": 1, "action": "standardise_column_names",
         "name": "standardise_column_names"},
    ]}
    _, cleaning_log, _ = run_cleaning_pipeline(
        df, rules,
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )
    assert "## Step Impact Summary" in cleaning_log
