"""
test_full_loop.py
-----------------
End-to-end integration test for the full analyst loop:

  1. Create a small messy CSV in tmp_path
  2. Run the QC reporter
  3. Run the cleaner (dry-run first, then full run)
  4. Run the QC reporter again on the cleaned data
  5. Assert all outputs exist and are non-empty
  6. Assert the raw input file is unchanged
"""

from __future__ import annotations

import copy

import pandas as pd
import pytest

from toolkit.cleaning import run_cleaning_pipeline
from toolkit.config import DEFAULTS, load_config
from toolkit.io import read_file, write_file
from toolkit.profiling import (
    binary_summary,
    categorical_summary,
    collect_all_prompts,
    collect_all_warnings,
    column_inventory,
    continuous_summary,
    dataset_overview,
    date_summary,
    duplication_summary,
    missingness_summary,
)
from toolkit.report_writer import build_quick_report, write_quick_report
from toolkit.type_detection import infer_types
from toolkit.utils import check_optional_packages, safety_check_output


# ── Helper: run reporter pipeline ─────────────────────────────────────────────

def run_reporter_pipeline(df: pd.DataFrame, cfg: dict, source_label: str = "test") -> tuple[str, object]:
    """Run the full reporter pipeline and return (report_str, out_path)."""
    types = infer_types(
        df,
        id_cols=cfg.get("id_cols"),
        date_columns=cfg.get("date_columns", []),
        type_overrides=cfg.get("type_overrides", {}),
        thresholds=cfg.get("thresholds", {}),
    )
    thresholds = cfg["thresholds"]
    privacy    = cfg["privacy"]

    overview     = dataset_overview(df, types)
    inventory    = column_inventory(df, types)
    miss_summary = missingness_summary(df, thresholds)
    dup_summary  = duplication_summary(df, cfg.get("id_cols"))
    cont_df      = continuous_summary(df, types, thresholds)
    bin_df       = binary_summary(df, types, thresholds)
    cat_df       = categorical_summary(df, types, thresholds, privacy)
    date_df      = date_summary(df, types, cfg.get("date_columns", []))
    warnings     = collect_all_warnings(df, types, thresholds, dup_summary, bin_df, cat_df, date_df)
    prompts      = collect_all_prompts(
        miss_summary=miss_summary, dup_summary=dup_summary,
        cont_df=cont_df, bin_df=bin_df, cat_df=cat_df, date_df=date_df,
        schema_issues=None, thresholds=thresholds,
    )
    pkg_status = check_optional_packages("skimpy", "ydata_profiling", "seaborn")
    report_str = build_quick_report(
        cfg=cfg, source_label=source_label,
        overview=overview, inventory=inventory,
        miss_summary=miss_summary, dup_summary=dup_summary,
        cont_df=cont_df, bin_df=bin_df, cat_df=cat_df, date_df=date_df,
        schema_issues=None, warnings=warnings,
        optional_pkg_status=pkg_status, decision_prompts=prompts,
    )
    out_path = write_quick_report(report_str, cfg)
    return report_str, out_path


# ── Fixture: messy toy dataset ────────────────────────────────────────────────

@pytest.fixture
def toy_csv(tmp_path) -> tuple[object, pd.DataFrame]:
    """Write a small messy CSV to tmp_path and return (path, original_df)."""
    df = pd.DataFrame({
        "ParticipantID": [1, 2, 3, 4, 5, 1],     # row 0 and 5 are duplicates
        "Age":           [25.0, 200.0, 30.0, -5.0, 35.0, 25.0],
        "Sex":           ["Male", " Female ", "male", "F", "Female", "Male"],
        "Diagnosis":     ["Control", "SCZ", "NA", "BD", "Unknown", "Control"],
        "Score":         [10.0, 20.0, -9.0, 30.0, 25.0, 10.0],
    })
    csv_path = tmp_path / "raw" / "toy_data.csv"
    csv_path.parent.mkdir(parents=True)
    df.to_csv(csv_path, index=False)
    return csv_path, df


@pytest.fixture
def cleaning_rules() -> dict:
    return {
        "version": 1,
        "name": "full_loop_test_rules",
        "metadata": {
            "analyst": "pytest",
            "analysis_purpose": "integration test",
            "expected_unit": "one row per participant",
        },
        "rules": [
            {
                "step": 1,
                "name": "standardise_column_names",
                "action": "standardise_column_names",
                "decision_status": "approved",
                "rationale": "Always normalise column names for consistency.",
            },
            {
                "step": 2,
                "name": "trim_whitespace",
                "action": "trim_whitespace",
                "columns": "string",
                "decision_status": "approved",
                "rationale": "Leading/trailing whitespace is never intentional.",
            },
            {
                "step": 3,
                "name": "replace_sentinel_codes",
                "action": "replace_missing_codes",
                "columns": "all",
                "missing_codes": ["NA", "Unknown", -9],
                "decision_status": "approved",
                "rationale": "NA and Unknown are missing-data codes, not real categories.",
            },
            {
                "step": 4,
                "name": "clip_age_range",
                "action": "set_invalid_to_missing",
                "column": "age",
                "min": 18,
                "max": 100,
                "decision_status": "approved",
                "rationale": "Age outside 18–100 is biologically implausible for this cohort.",
            },
            {
                "step": 5,
                "name": "flag_score_outliers",
                "action": "flag_outliers_iqr",
                "column": "score",
                "output_column": "score_outlier_flag",
                "remove": False,
                "decision_status": "approved",
                "rationale": "Flag only; analyst will review before any removal.",
            },
            {
                "step": 6,
                "name": "add_missingness_flags",
                "action": "create_missingness_flags",
                "columns": "all",
                "only_if_any_missing": True,
                "decision_status": "approved",
                "rationale": "Preserve missingness information for regression models.",
            },
            {
                "step": 7,
                "name": "remove_exact_duplicates",
                "action": "remove_exact_duplicates",
                "allow_row_drop": True,
                "decision_status": "approved",
                "rationale": "Rows 0 and 5 are confirmed accidental duplicates from the export.",
            },
        ],
        "validation": {
            "required_columns": ["participant_id", "age"],
            "unique_keys": [["participant_id"]],
            "ranges": {
                "age": {"min": 18, "max": 100},
            },
        },
    }


# ── Full-loop tests ───────────────────────────────────────────────────────────

def test_full_loop_raw_file_exists(toy_csv):
    csv_path, _ = toy_csv
    assert csv_path.exists()


def test_full_loop_reporter_on_raw_data(toy_csv, tmp_path):
    """Step 1: run the QC reporter on raw data."""
    csv_path, _ = toy_csv
    df = read_file(csv_path)

    cfg = copy.deepcopy(DEFAULTS)
    cfg["input_path"]     = str(csv_path)
    cfg["report_basename"] = "before_cleaning_qc"
    cfg["output_dir"]     = str(tmp_path / "reports" / "before")

    report_str, out_path = run_reporter_pipeline(df, cfg, source_label=str(csv_path))

    assert isinstance(report_str, str)
    assert len(report_str) > 100
    assert out_path.exists()
    assert out_path.stat().st_size > 0
    assert "# Descriptive QC Report" in report_str


def test_full_loop_dry_run_does_not_write_cleaned_file(toy_csv, cleaning_rules, tmp_path):
    """Step 2: dry-run — check what would change without writing."""
    csv_path, _ = toy_csv
    df = read_file(csv_path)

    cleaned, log, val = run_cleaning_pipeline(
        df, cleaning_rules,
        input_path=str(csv_path),
        dry_run=True,
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )

    # Cleaned data not written; raw file untouched
    cleaned_csv = tmp_path / "processed" / "toy_data_cleaned.csv"
    assert not cleaned_csv.exists()

    # But the log was written
    assert len(list((tmp_path / "logs").glob("*.md"))) == 1
    assert "DRY RUN" in log.upper() or "dry run" in log.lower()


def test_full_loop_full_clean_run(toy_csv, cleaning_rules, tmp_path):
    """Step 3: full clean run — cleaned file is written."""
    csv_path, original_df = toy_csv
    df = read_file(csv_path)

    output_path = tmp_path / "processed" / "toy_data_cleaned.csv"
    output_path.parent.mkdir(parents=True)

    cleaned, log, val = run_cleaning_pipeline(
        df, cleaning_rules,
        input_path=str(csv_path),
        output_path=str(output_path),
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )

    write_file(cleaned, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0

    # Fewer rows (duplicate removed)
    cleaned_from_disk = pd.read_csv(output_path)
    assert len(cleaned_from_disk) < len(original_df)

    # Columns are snake_case
    assert "participant_id" in cleaned_from_disk.columns
    assert "ParticipantID" not in cleaned_from_disk.columns

    # Raw file is unchanged
    raw_from_disk = pd.read_csv(csv_path)
    assert list(raw_from_disk.columns) == list(original_df.columns)
    assert len(raw_from_disk) == len(original_df)


def test_full_loop_cleaning_log_written(toy_csv, cleaning_rules, tmp_path):
    """Cleaning log file must exist and contain the expected sections."""
    csv_path, _ = toy_csv
    df = read_file(csv_path)
    log_dir = tmp_path / "logs"

    _, log, _ = run_cleaning_pipeline(
        df, cleaning_rules,
        input_path=str(csv_path),
        log_dir=str(log_dir),
        validation_dir=str(tmp_path / "val"),
    )

    log_files = list(log_dir.glob("*.md"))
    assert len(log_files) == 1
    content = log_files[0].read_text(encoding="utf-8")
    for section in ("# Cleaning Log", "## Run Metadata", "## Step Summary",
                    "## Detailed Step Notes", "## Before / After Summary"):
        assert section in content


def test_full_loop_run_manifest_written(toy_csv, cleaning_rules, tmp_path):
    """Run manifest YAML must exist alongside the cleaning log."""
    csv_path, _ = toy_csv
    df = read_file(csv_path)
    log_dir = tmp_path / "logs"

    run_cleaning_pipeline(
        df, cleaning_rules,
        input_path=str(csv_path),
        log_dir=str(log_dir),
        validation_dir=str(tmp_path / "val"),
    )

    manifest_files = list(log_dir.glob("*.yaml"))
    assert len(manifest_files) == 1
    content = manifest_files[0].read_text(encoding="utf-8")
    for key in ("timestamp", "input_file", "rows_before", "rows_after", "git_commit"):
        assert key in content


def test_full_loop_validation_report_written(toy_csv, cleaning_rules, tmp_path):
    """Validation report must exist and mention required columns."""
    csv_path, _ = toy_csv
    df = read_file(csv_path)
    val_dir = tmp_path / "val"

    _, _, val = run_cleaning_pipeline(
        df, cleaning_rules,
        input_path=str(csv_path),
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(val_dir),
    )

    val_files = list(val_dir.glob("*.md"))
    assert len(val_files) == 1
    assert "# Validation Report" in val
    assert "participant_id" in val


def test_full_loop_raw_file_unchanged_after_cleaning(toy_csv, cleaning_rules, tmp_path):
    """The raw CSV must be byte-for-byte identical before and after the pipeline."""
    csv_path, _ = toy_csv
    raw_bytes_before = csv_path.read_bytes()

    df = read_file(csv_path)
    run_cleaning_pipeline(
        df, cleaning_rules,
        input_path=str(csv_path),
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )

    raw_bytes_after = csv_path.read_bytes()
    assert raw_bytes_before == raw_bytes_after


def test_full_loop_reporter_on_cleaned_data(toy_csv, cleaning_rules, tmp_path):
    """Step 4: QC reporter on cleaned data — fewer issues should be detected."""
    csv_path, _ = toy_csv
    df = read_file(csv_path)

    output_path = tmp_path / "processed" / "cleaned.csv"
    output_path.parent.mkdir(parents=True)

    cleaned, _, _ = run_cleaning_pipeline(
        df, cleaning_rules,
        input_path=str(csv_path),
        output_path=str(output_path),
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )
    write_file(cleaned, output_path)

    cfg = copy.deepcopy(DEFAULTS)
    cfg["input_path"]     = str(output_path)
    cfg["report_basename"] = "after_cleaning_qc"
    cfg["output_dir"]     = str(tmp_path / "reports" / "after")

    after_report, after_path = run_reporter_pipeline(
        cleaned, cfg, source_label=f"cleaned:{output_path}"
    )

    assert after_path.exists()
    assert "# Descriptive QC Report" in after_report

    # Duplicate section should show zero duplicates (they were removed)
    dup_sum = duplication_summary(cleaned, id_cols=None)
    assert dup_sum["exact_duplicate_rows"] == 0


def test_full_loop_decision_status_in_cleaning_log(toy_csv, cleaning_rules, tmp_path):
    """Rules with decision_status fields should appear in the cleaning log."""
    csv_path, _ = toy_csv
    df = read_file(csv_path)

    _, log, _ = run_cleaning_pipeline(
        df, cleaning_rules,
        input_path=str(csv_path),
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )

    assert "approved" in log
    assert "Rationale:" in log or "rationale" in log.lower()


def test_full_loop_safety_check_output_guard(toy_csv, tmp_path):
    """Writing cleaned output to the same path as raw input must abort."""
    csv_path, _ = toy_csv
    with pytest.raises(SystemExit):
        safety_check_output(str(csv_path), str(csv_path))


def test_full_loop_flowchart_files_written(toy_csv, cleaning_rules, tmp_path):
    """Running with flowchart=True must produce .mmd and .md flow files."""
    csv_path, _ = toy_csv
    df = read_file(csv_path)
    log_dir = tmp_path / "logs"

    run_cleaning_pipeline(
        df, cleaning_rules,
        input_path=str(csv_path),
        log_dir=str(log_dir),
        validation_dir=str(tmp_path / "val"),
        flowchart=True,
    )

    mmd_files = list(log_dir.glob("*_flow.mmd"))
    md_files  = list(log_dir.glob("*_flow.md"))
    assert len(mmd_files) == 1
    assert len(md_files)  == 1

    # .mmd must start with the Mermaid keyword
    mmd_content = mmd_files[0].read_text(encoding="utf-8")
    assert "flowchart LR" in mmd_content

    # .md must embed the Mermaid code fence
    md_content = md_files[0].read_text(encoding="utf-8")
    assert "```mermaid" in md_content
    assert "Raw data" in md_content
    assert "Cleaned data" in md_content


def test_full_loop_cleaning_log_embeds_flowchart(toy_csv, cleaning_rules, tmp_path):
    """When flowchart=True the cleaning log text must include the Mermaid section."""
    csv_path, _ = toy_csv
    df = read_file(csv_path)

    _, log, _ = run_cleaning_pipeline(
        df, cleaning_rules,
        input_path=str(csv_path),
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
        flowchart=True,
    )

    assert "## Cleaning Flowchart" in log
    assert "```mermaid" in log
    assert "flowchart LR" in log


def test_full_loop_cleaning_log_has_step_impact_table(toy_csv, cleaning_rules, tmp_path):
    """Step Impact Summary table must appear in every log, with or without flowchart."""
    csv_path, _ = toy_csv
    df = read_file(csv_path)

    _, log, _ = run_cleaning_pipeline(
        df, cleaning_rules,
        input_path=str(csv_path),
        log_dir=str(tmp_path / "logs"),
        validation_dir=str(tmp_path / "val"),
    )

    assert "## Step Impact Summary" in log
    # Table must include impact columns
    assert "Rows before" in log
    assert "Rows removed" in log
