"""
test_cleaner_actions.py
-----------------------
Unit tests for each cleaning action function.

No files are read or written. All DataFrames are built in-memory.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from toolkit.cleaning_actions import (
    action_flag_outliers_iqr,
    action_map_categories,
    action_remove_exact_duplicates,
    action_replace_missing_codes,
    action_set_invalid_to_missing,
    action_standardise_column_names,
    action_trim_whitespace,
    action_parse_dates,
    action_standardise_case,
    action_create_missingness_flags,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def simple_df() -> pd.DataFrame:
    return pd.DataFrame({
        "ParticipantID": [1, 2, 3, 4, 5],
        "Age":  [25.0, 30.0, -5.0, 200.0, 35.0],
        "Sex":  ["Male", " Female ", "male", "F", "Female"],
        "Dx":   ["Control", "SCZ", "NA", "BD", "Unknown"],
        "BMI":  [22.0, 25.0, 30.0, 75.0, 24.0],
    })


@pytest.fixture
def dup_df() -> pd.DataFrame:
    base = pd.DataFrame({"id": [1, 2, 3], "val": [10, 20, 30]})
    return pd.concat([base, base.iloc[[0]]], ignore_index=True)


# ── 1. standardise_column_names ───────────────────────────────────────────────

def test_standardise_column_names_converts_to_snake(simple_df):
    result, log = action_standardise_column_names(simple_df, {})
    assert "participant_id" in result.columns
    assert "age" in result.columns
    assert "sex" in result.columns
    assert log["cells_changed"] > 0


def test_standardise_column_names_dry_run_does_not_modify(simple_df):
    original_cols = list(simple_df.columns)
    result, log = action_standardise_column_names(simple_df, {}, dry_run=True)
    assert list(result.columns) == original_cols  # unchanged


# ── 5. replace_missing_codes ──────────────────────────────────────────────────

def test_replace_missing_codes_converts_strings(simple_df):
    rule = {"columns": "all", "missing_codes": ["NA", "Unknown"]}
    result, log = action_replace_missing_codes(simple_df, rule)
    assert result["Dx"].isna().sum() == 2  # "NA" and "Unknown"
    assert log["cells_changed"] == 2


def test_replace_missing_codes_dry_run_no_change(simple_df):
    rule = {"columns": "all", "missing_codes": ["NA", "Unknown"]}
    result, log = action_replace_missing_codes(simple_df, rule, dry_run=True)
    assert result["Dx"].isna().sum() == 0  # original had 0 NaN
    assert log["cells_changed"] == 2  # still counts what would change


def test_replace_missing_codes_numeric():
    df = pd.DataFrame({"score": [1.0, -9.0, 3.0, -99.0]})
    rule = {"columns": "all", "missing_codes": [-9, -99]}
    result, log = action_replace_missing_codes(df, rule)
    assert result["score"].isna().sum() == 2
    assert log["cells_changed"] == 2


# ── 6. trim_whitespace ────────────────────────────────────────────────────────

def test_trim_whitespace_removes_spaces(simple_df):
    rule = {"columns": "string"}
    result, log = action_trim_whitespace(simple_df, rule)
    assert " Female " not in result["Sex"].values
    assert "Female" in result["Sex"].values
    assert log["cells_changed"] >= 1


def test_trim_whitespace_dry_run(simple_df):
    rule = {"columns": "string"}
    result, log = action_trim_whitespace(simple_df, rule, dry_run=True)
    assert " Female " in result["Sex"].values  # unchanged in dry run


# ── 7. standardise_case ───────────────────────────────────────────────────────

def test_standardise_case_lower():
    df = pd.DataFrame({"label": ["Yes", "NO", "Maybe"]})
    result, log = action_standardise_case(df, {"case": "lower", "columns": ["label"]})
    assert list(result["label"]) == ["yes", "no", "maybe"]
    assert log["cells_changed"] == 3


def test_standardise_case_title():
    df = pd.DataFrame({"label": ["yes", "no"]})
    result, log = action_standardise_case(df, {"case": "title", "columns": ["label"]})
    assert list(result["label"]) == ["Yes", "No"]


# ── 8. map_categories ────────────────────────────────────────────────────────

def test_map_categories_applies_mapping(simple_df):
    rule = {
        "column": "Sex",
        "mapping": {"M": "Male", "male": "Male", "F": "Female", "female": "Female"},
        "unmatched_action": "warn",
    }
    result, log = action_map_categories(simple_df, rule)
    assert log["rows_before"] == len(simple_df)


def test_map_categories_set_missing_on_unmatched():
    df = pd.DataFrame({"cat": ["A", "B", "C", "unexpected"]})
    rule = {
        "column": "cat",
        "mapping": {"A": "Alpha", "B": "Beta", "C": "Gamma"},
        "unmatched_action": "set_missing",
    }
    result, log = action_map_categories(df, rule)
    assert result["cat"].isna().sum() == 1
    assert any("unmatched" in w for w in log["warnings"])


def test_map_categories_missing_column():
    df = pd.DataFrame({"other": [1, 2]})
    rule = {"column": "nonexistent", "mapping": {}, "unmatched_action": "warn"}
    result, log = action_map_categories(df, rule)
    assert result is df  # unchanged
    assert len(log["warnings"]) > 0


# ── 9. set_invalid_to_missing ─────────────────────────────────────────────────

def test_set_invalid_to_missing_range(simple_df):
    rule = {"column": "Age", "min": 18, "max": 100}
    result, log = action_set_invalid_to_missing(simple_df, rule)
    assert result["Age"].isna().sum() == 2  # -5 and 200
    assert log["cells_changed"] == 2


def test_set_invalid_to_missing_dry_run(simple_df):
    rule = {"column": "Age", "min": 18, "max": 100}
    result, log = action_set_invalid_to_missing(simple_df, rule, dry_run=True)
    assert result["Age"].isna().sum() == 0  # original df has no NaN in Age
    assert log["cells_changed"] == 2


def test_set_invalid_to_missing_no_invalids():
    df = pd.DataFrame({"age": [25.0, 30.0, 35.0]})
    rule = {"column": "age", "min": 18, "max": 100}
    result, log = action_set_invalid_to_missing(df, rule)
    assert log["cells_changed"] == 0
    assert result["age"].isna().sum() == 0


# ── 10. flag_outliers_iqr ─────────────────────────────────────────────────────

def test_flag_outliers_iqr_flags_correctly(simple_df):
    rule = {"column": "BMI", "output_column": "bmi_flag", "remove": False}
    result, log = action_flag_outliers_iqr(simple_df, rule)
    assert "bmi_flag" in result.columns
    assert result["bmi_flag"].sum() >= 1  # BMI=75 should be flagged
    assert len(result) == len(simple_df)  # no rows removed


def test_flag_outliers_iqr_no_removal_by_default(simple_df):
    rule = {"column": "BMI", "output_column": "bmi_flag", "remove": False}
    result, _ = action_flag_outliers_iqr(simple_df, rule)
    assert len(result) == len(simple_df)


def test_flag_outliers_iqr_dry_run(simple_df):
    rule = {"column": "BMI", "output_column": "bmi_flag", "remove": False}
    result, log = action_flag_outliers_iqr(simple_df, rule, dry_run=True)
    assert "bmi_flag" not in result.columns
    assert log["cells_changed"] >= 1


# ── 12. remove_exact_duplicates ───────────────────────────────────────────────

def test_remove_exact_duplicates_removes_dups(dup_df):
    rule = {"allow_row_drop": True}
    result, log = action_remove_exact_duplicates(dup_df, rule)
    assert len(result) == 3  # original 3 rows
    assert log["rows_delta"] == -1


def test_remove_exact_duplicates_dry_run(dup_df):
    rule = {"allow_row_drop": True}
    result, log = action_remove_exact_duplicates(dup_df, rule, dry_run=True)
    assert len(result) == len(dup_df)  # unchanged


def test_remove_exact_duplicates_no_dups():
    df = pd.DataFrame({"id": [1, 2, 3], "val": [10, 20, 30]})
    rule = {"allow_row_drop": True}
    result, log = action_remove_exact_duplicates(df, rule)
    assert len(result) == 3
    assert log["rows_delta"] == 0


# ── 11. parse_dates ───────────────────────────────────────────────────────────

def test_parse_dates_converts_strings():
    df = pd.DataFrame({"date_str": ["2024-01-01", "2024-06-15", "not_a_date"]})
    rule = {"columns": ["date_str"], "format": None}
    result, log = action_parse_dates(df, rule)
    assert pd.api.types.is_datetime64_any_dtype(result["date_str"])
    assert result["date_str"].isna().sum() == 1  # "not_a_date" → NaT
    assert len(log["warnings"]) > 0  # parse failure warned


# ── 14. create_missingness_flags ──────────────────────────────────────────────

def test_create_missingness_flags_adds_columns():
    df = pd.DataFrame({"a": [1.0, None, 3.0], "b": ["x", None, "z"]})
    rule = {"columns": "all", "only_if_any_missing": True}
    result, log = action_create_missingness_flags(df, rule)
    assert "a_missing_flag" in result.columns
    assert "b_missing_flag" in result.columns
    assert result["a_missing_flag"].sum() == 1
    assert result["b_missing_flag"].sum() == 1
    assert log["cells_changed"] == 2  # two flag columns created


def test_create_missingness_flags_dry_run():
    df = pd.DataFrame({"score": [1.0, None, 3.0]})
    rule = {"columns": "all"}
    result, log = action_create_missingness_flags(df, rule, dry_run=True)
    assert "score_missing_flag" not in result.columns  # dry run — not added
    assert log["cells_changed"] == 1  # would create 1 flag


def test_create_missingness_flags_only_missing():
    df = pd.DataFrame({"complete": [1.0, 2.0], "with_na": [1.0, None]})
    rule = {"columns": "all", "only_if_any_missing": True}
    result, log = action_create_missingness_flags(df, rule)
    assert "with_na_missing_flag" in result.columns
    assert "complete_missing_flag" not in result.columns  # no missing → skipped


def test_create_missingness_flags_custom_suffix():
    df = pd.DataFrame({"x": [None, 2.0]})
    rule = {"columns": ["x"], "suffix": "_flag", "only_if_any_missing": False}
    result, log = action_create_missingness_flags(df, rule)
    assert "x_flag" in result.columns
