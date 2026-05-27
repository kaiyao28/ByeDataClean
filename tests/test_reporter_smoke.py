"""
test_reporter_smoke.py
----------------------
Smoke tests: build a small DataFrame in memory, run the full pipeline,
and assert the report contains the expected sections.

No files are read from disk; no optional packages are required.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from toolkit.config import DEFAULTS
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
from toolkit.report_writer import build_quick_report
from toolkit.type_detection import infer_types


# ── Fixture: small edge-case DataFrame ────────────────────────────────────────

@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Intentionally messy DataFrame covering all variable types."""
    rng = np.random.default_rng(42)
    n = 50
    df = pd.DataFrame({
        "participant_id": list(range(1, n)) + [1],
        "age": np.concatenate([rng.integers(18, 80, n - 1).astype(float), [200.0]]),
        "sex": rng.choice(["Female", "Male"], n),
        "diagnosis": rng.choice(["Control", "SCZ", "BD", "MDD", "Rare_dx"], n,
                                 p=[0.40, 0.30, 0.15, 0.10, 0.05]),
        "bmi": np.where(rng.random(n) < 0.60, np.nan, rng.uniform(18, 40, n)),
        "assessment_date": pd.date_range("2020-01-01", periods=n, freq="7D"),
    })
    df = pd.concat([df, df.iloc[[0, 1]]], ignore_index=True)
    return df


@pytest.fixture
def cfg() -> dict:
    import copy
    return copy.deepcopy(DEFAULTS)


# ── Helper: run full pipeline ─────────────────────────────────────────────────

def run_pipeline(df: pd.DataFrame, cfg: dict) -> str:
    types = infer_types(
        df,
        id_cols=["participant_id"],
        date_columns=["assessment_date"],
        thresholds=cfg["thresholds"],
    )
    thresholds = cfg["thresholds"]
    privacy    = cfg["privacy"]

    overview     = dataset_overview(df, types)
    inventory    = column_inventory(df, types)
    miss_summary = missingness_summary(df, thresholds)
    dup_summary  = duplication_summary(df, id_cols=["participant_id"])
    cont_df      = continuous_summary(df, types, thresholds)
    bin_df       = binary_summary(df, types, thresholds)
    cat_df       = categorical_summary(df, types, thresholds, privacy)
    date_df      = date_summary(df, types, ["assessment_date"])
    warnings     = collect_all_warnings(df, types, thresholds, dup_summary,
                                        bin_df, cat_df, date_df)
    prompts      = collect_all_prompts(
        miss_summary=miss_summary, dup_summary=dup_summary,
        cont_df=cont_df, bin_df=bin_df, cat_df=cat_df, date_df=date_df,
        schema_issues=None, thresholds=thresholds,
    )
    return build_quick_report(
        cfg=cfg, source_label="test:in_memory",
        overview=overview, inventory=inventory,
        miss_summary=miss_summary, dup_summary=dup_summary,
        cont_df=cont_df, bin_df=bin_df, cat_df=cat_df, date_df=date_df,
        schema_issues=None, warnings=warnings,
        optional_pkg_status={"skimpy": False, "ydata_profiling": False, "seaborn": False},
        decision_prompts=prompts,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_report_is_string(sample_df, cfg):
    report = run_pipeline(sample_df, cfg)
    assert isinstance(report, str)
    assert len(report) > 100


def test_report_contains_missing_section(sample_df, cfg):
    assert "missing" in run_pipeline(sample_df, cfg).lower()


def test_report_contains_duplicate_section(sample_df, cfg):
    assert "duplicate" in run_pipeline(sample_df, cfg).lower()


def test_report_contains_continuous_section(sample_df, cfg):
    assert "continuous" in run_pipeline(sample_df, cfg).lower()


def test_report_contains_categorical_section(sample_df, cfg):
    assert "categorical" in run_pipeline(sample_df, cfg).lower()


def test_report_contains_suggested_cleaning_actions(sample_df, cfg):
    assert "suggested cleaning actions" in run_pipeline(sample_df, cfg).lower()


def test_duplicate_rows_detected(sample_df, cfg):
    dup = duplication_summary(sample_df, id_cols=["participant_id"])
    assert dup["exact_duplicate_rows"] >= 2


def test_high_missingness_detected(sample_df, cfg):
    miss = missingness_summary(sample_df, cfg["thresholds"])
    assert "bmi" in miss["very_high_missing"] or "bmi" in miss["high_missing"]


def test_type_inference_id_column(sample_df):
    types = infer_types(sample_df, id_cols=["participant_id"])
    assert types["participant_id"] == "id"


def test_type_inference_continuous(sample_df):
    types = infer_types(sample_df)
    assert types["age"] == "continuous"


def test_type_inference_binary(sample_df):
    types = infer_types(sample_df)
    assert types["sex"] == "binary"


def test_type_inference_date(sample_df):
    types = infer_types(sample_df, date_columns=["assessment_date"])
    assert types["assessment_date"] == "date"


def test_report_contains_decision_prompts_section(sample_df, cfg):
    assert "cleaning decision prompts" in run_pipeline(sample_df, cfg).lower()


def test_decision_prompts_generated_for_messy_data(sample_df, cfg):
    types      = infer_types(sample_df, id_cols=["participant_id"], date_columns=["assessment_date"])
    thresholds = cfg["thresholds"]
    privacy    = cfg["privacy"]

    miss = missingness_summary(sample_df, thresholds)
    dups = duplication_summary(sample_df, id_cols=["participant_id"])
    cont = continuous_summary(sample_df, types, thresholds)
    binr = binary_summary(sample_df, types, thresholds)
    cat  = categorical_summary(sample_df, types, thresholds, privacy)
    date = date_summary(sample_df, types, ["assessment_date"])

    prompts = collect_all_prompts(
        miss_summary=miss, dup_summary=dups, cont_df=cont,
        bin_df=binr, cat_df=cat, date_df=date,
        schema_issues=None, thresholds=thresholds,
    )
    assert len(prompts) > 0, "Expected at least one decision prompt for the messy sample dataset"


def test_decision_prompt_structure(sample_df, cfg):
    types      = infer_types(sample_df, id_cols=["participant_id"])
    thresholds = cfg["thresholds"]
    privacy    = cfg["privacy"]

    prompts = collect_all_prompts(
        miss_summary=missingness_summary(sample_df, thresholds),
        dup_summary=duplication_summary(sample_df, id_cols=["participant_id"]),
        cont_df=continuous_summary(sample_df, types, thresholds),
        bin_df=binary_summary(sample_df, types, thresholds),
        cat_df=categorical_summary(sample_df, types, thresholds, privacy),
        date_df=date_summary(sample_df, types, []),
        schema_issues=None, thresholds=thresholds,
    )
    for p in prompts:
        assert p.dimension,                                     "dimension must be non-empty"
        assert p.issue,                                         "issue must be non-empty"
        assert p.question,                                      "question must be non-empty"
        assert isinstance(p.options, list) and len(p.options) > 0, "options must be non-empty list"
        assert p.document,                                      "document must be non-empty"
