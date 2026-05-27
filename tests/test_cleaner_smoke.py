"""
test_cleaner_smoke.py
---------------------
Integration smoke tests for the cleaning pipeline.

All DataFrames are built in-memory. Real files are written only
to pytest's tmp_path — never to the project's data/ or reports/ dirs.
"""

from __future__ import annotations

import pandas as pd
import pytest

from toolkit.cleaning import run_cleaning_pipeline
from toolkit.utils import safety_check_output


# ── Shared rule dicts (no YAML files needed) ──────────────────────────────────

MINIMAL_RULES = {
    "version": 1,
    "name": "smoke_minimal",
    "rules": [
        {
            "step": 1,
            "name": "standardise_column_names",
            "action": "standardise_column_names",
        },
    ],
}

MULTI_STEP_RULES = {
    "version": 1,
    "name": "smoke_multi_step",
    "rules": [
        {
            "step": 1,
            "name": "standardise_column_names",
            "action": "standardise_column_names",
        },
        {
            "step": 2,
            "name": "trim_whitespace",
            "action": "trim_whitespace",
            "columns": "string",
        },
        {
            "step": 3,
            "name": "replace_missing_codes",
            "action": "replace_missing_codes",
            "columns": "all",
            "missing_codes": ["NA", "Unknown", -9],
        },
        {
            "step": 4,
            "name": "remove_duplicates",
            "action": "remove_exact_duplicates",
            "allow_row_drop": True,
        },
    ],
    "validation": {
        "required_columns": ["participant_id"],
        "unique_keys": [["participant_id"]],
    },
}

EMPTY_RULES = {
    "version": 1,
    "name": "smoke_empty",
    "rules": [],
}


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def raw_df() -> pd.DataFrame:
    """5 rows: 4 unique + 1 exact duplicate of row 0."""
    base = pd.DataFrame({
        "ParticipantID": [1, 2, 3, 4],
        "Age":           [25.0, 30.0, 35.0, 40.0],
        "Diagnosis":     ["Control", " SCZ ", "NA", "BD"],
        "Score":         [10.0, -9.0, 20.0, 30.0],
    })
    return pd.concat([base, base.iloc[[0]]], ignore_index=True)


# ── 1. Return types ───────────────────────────────────────────────────────────

def test_pipeline_returns_dataframe(raw_df, tmp_path):
    cleaned, log, val = run_cleaning_pipeline(
        raw_df, MINIMAL_RULES,
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )
    assert isinstance(cleaned, pd.DataFrame)
    assert len(cleaned) > 0


def test_pipeline_returns_three_values(raw_df, tmp_path):
    cleaned, log, val = run_cleaning_pipeline(
        raw_df, MINIMAL_RULES,
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )
    assert isinstance(log, str)
    assert isinstance(val, str)


# ── 2. Cleaning steps are applied ────────────────────────────────────────────

def test_snake_case_applied(raw_df, tmp_path):
    cleaned, _, _ = run_cleaning_pipeline(
        raw_df, MINIMAL_RULES,
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )
    assert "participant_id" in cleaned.columns
    assert "ParticipantID" not in cleaned.columns


def test_multi_step_removes_exact_duplicate(raw_df, tmp_path):
    assert len(raw_df) == 5
    cleaned, _, _ = run_cleaning_pipeline(
        raw_df, MULTI_STEP_RULES,
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )
    assert len(cleaned) == 4


def test_multi_step_trims_whitespace(raw_df, tmp_path):
    cleaned, _, _ = run_cleaning_pipeline(
        raw_df, MULTI_STEP_RULES,
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )
    diag_col = "diagnosis" if "diagnosis" in cleaned.columns else "Diagnosis"
    assert " SCZ " not in cleaned[diag_col].values
    assert "SCZ" in cleaned[diag_col].dropna().values


def test_multi_step_replaces_missing_codes(raw_df, tmp_path):
    cleaned, _, _ = run_cleaning_pipeline(
        raw_df, MULTI_STEP_RULES,
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )
    diag_col  = "diagnosis" if "diagnosis" in cleaned.columns else "Diagnosis"
    score_col = "score"     if "score"     in cleaned.columns else "Score"
    assert cleaned[diag_col].isna().sum() >= 1   # "NA" → NaN
    assert cleaned[score_col].isna().sum() >= 1  # -9 → NaN


# ── 3. Cleaning log is a well-formed markdown string ─────────────────────────

def test_cleaning_log_non_empty(raw_df, tmp_path):
    _, log, _ = run_cleaning_pipeline(
        raw_df, MINIMAL_RULES,
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )
    assert len(log) > 100


def test_cleaning_log_contains_required_sections(raw_df, tmp_path):
    _, log, _ = run_cleaning_pipeline(
        raw_df, MINIMAL_RULES,
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )
    for heading in (
        "# Cleaning Log",
        "## Run Metadata",
        "## Step Summary",
        "## Detailed Step Notes",
        "## Before / After Summary",
    ):
        assert heading in log, f"Missing heading: {heading!r}"


def test_cleaning_log_records_dry_run_flag(raw_df, tmp_path):
    _, log, _ = run_cleaning_pipeline(
        raw_df, MINIMAL_RULES,
        dry_run=True,
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )
    assert "dry run" in log.lower() or "Dry run" in log


# ── 4. Validation report ──────────────────────────────────────────────────────

def test_validation_report_heading(raw_df, tmp_path):
    _, _, val = run_cleaning_pipeline(
        raw_df, MULTI_STEP_RULES,
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )
    assert "# Validation Report" in val


def test_validation_detects_missing_required_column(tmp_path):
    df = pd.DataFrame({"other_col": [1, 2, 3]})
    rules = {
        "version": 1, "name": "val_smoke", "rules": [],
        "validation": {"required_columns": ["participant_id"]},
    }
    _, _, val = run_cleaning_pipeline(
        df, rules,
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )
    assert "participant_id" in val
    assert "missing" in val.lower() or "Failed" in val


def test_validation_passes_when_data_is_clean(tmp_path):
    df = pd.DataFrame({"participant_id": [1, 2, 3], "score": [10, 20, 30]})
    rules = {
        "version": 1, "name": "val_pass", "rules": [],
        "validation": {
            "required_columns": ["participant_id"],
            "unique_keys": [["participant_id"]],
        },
    }
    _, _, val = run_cleaning_pipeline(
        df, rules,
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )
    assert "passed" in val.lower()


# ── 5. Log files written to disk ─────────────────────────────────────────────

def test_log_files_are_written(raw_df, tmp_path):
    log_dir = tmp_path / "logs"
    val_dir = tmp_path / "val"
    run_cleaning_pipeline(
        raw_df, MINIMAL_RULES,
        log_dir=str(log_dir),
        validation_dir=str(val_dir),
    )
    assert len(list(log_dir.glob("*.md")))   == 1
    assert len(list(val_dir.glob("*.md")))   == 1
    # Run manifest (.yaml) is also written alongside the log
    assert len(list(log_dir.glob("*.yaml"))) == 1


def test_log_file_content_matches_returned_string(raw_df, tmp_path):
    log_dir = tmp_path / "logs"
    _, log, _ = run_cleaning_pipeline(
        raw_df, MINIMAL_RULES,
        log_dir=str(log_dir),
        validation_dir=str(tmp_path / "val"),
    )
    written = next(log_dir.glob("*.md")).read_text(encoding="utf-8")
    assert written == log


def test_log_files_written_even_in_dry_run(raw_df, tmp_path):
    log_dir = tmp_path / "logs"
    run_cleaning_pipeline(
        raw_df, MINIMAL_RULES,
        dry_run=True,
        log_dir=str(log_dir),
        validation_dir=str(tmp_path / "val"),
    )
    assert len(list(log_dir.glob("*.md"))) == 1


# ── 6. Dry-run leaves the DataFrame unchanged ─────────────────────────────────

def test_dry_run_columns_unchanged(raw_df, tmp_path):
    original_cols = list(raw_df.columns)
    cleaned, _, _ = run_cleaning_pipeline(
        raw_df, MULTI_STEP_RULES,
        dry_run=True,
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )
    assert list(cleaned.columns) == original_cols


def test_dry_run_row_count_unchanged(raw_df, tmp_path):
    cleaned, _, _ = run_cleaning_pipeline(
        raw_df, MULTI_STEP_RULES,
        dry_run=True,
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )
    assert len(cleaned) == len(raw_df)


def test_dry_run_values_unchanged(raw_df, tmp_path):
    cleaned, _, _ = run_cleaning_pipeline(
        raw_df, MULTI_STEP_RULES,
        dry_run=True,
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )
    assert " SCZ " in cleaned["Diagnosis"].values
    assert "NA" in cleaned["Diagnosis"].values


# ── 7. Raw input is never overwritten ────────────────────────────────────────

def test_safety_check_raises_on_same_path(tmp_path):
    same = str(tmp_path / "data.csv")
    with pytest.raises(SystemExit):
        safety_check_output(same, same)


def test_safety_check_passes_on_different_paths(tmp_path):
    safety_check_output(
        str(tmp_path / "input.csv"),
        str(tmp_path / "output.csv"),
    )


def test_safety_check_catches_symlink(tmp_path):
    real = tmp_path / "raw.csv"
    real.write_text("id\n1\n", encoding="utf-8")
    link = tmp_path / "link_to_raw.csv"
    link.symlink_to(real)
    with pytest.raises(SystemExit):
        safety_check_output(str(real), str(link))


# ── 8. Empty rules list ───────────────────────────────────────────────────────

def test_empty_rules_passthrough(raw_df, tmp_path):
    cleaned, log, _ = run_cleaning_pipeline(
        raw_df, EMPTY_RULES,
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )
    assert list(cleaned.columns) == list(raw_df.columns)
    assert len(cleaned) == len(raw_df)
    assert "# Cleaning Log" in log
