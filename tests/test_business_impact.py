"""
test_business_impact.py
-----------------------
Tests for toolkit/business_impact.py.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import pandas as pd
import pytest

from toolkit.business_impact import (
    _status,
    build_impact_report,
    compute_impact,
    write_impact_report,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _orders_df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


BEFORE = _orders_df([
    {"order_id": "A", "order_value": 100.0,  "customer_id": "C1", "acquisition_channel": "organic",  "order_date": "2024-01-05"},
    {"order_id": "B", "order_value": 200.0,  "customer_id": None,  "acquisition_channel": "paid",     "order_date": "2024-02-10"},
    {"order_id": "C", "order_value": -50.0,  "customer_id": "C3", "acquisition_channel": None,        "order_date": "2024-03-01"},
    {"order_id": "A", "order_value": 100.0,  "customer_id": "C1", "acquisition_channel": "organic",  "order_date": "2024-01-05"},  # dup
    {"order_id": "E", "order_value": 300.0,  "customer_id": "C5", "acquisition_channel": "social",   "order_date": "2027-12-31"},  # future
])

AFTER = _orders_df([
    {"order_id": "A", "order_value": 100.0,  "customer_id": "C1", "acquisition_channel": "organic",  "order_date": "2024-01-05"},
    {"order_id": "B", "order_value": 200.0,  "customer_id": None,  "acquisition_channel": "paid",     "order_date": "2024-02-10"},
    {"order_id": "C", "order_value": None,   "customer_id": "C3", "acquisition_channel": None,        "order_date": "2024-03-01"},
    {"order_id": "E", "order_value": 300.0,  "customer_id": "C5", "acquisition_channel": "social",   "order_date": "2027-12-31"},
])


# ── compute_impact ────────────────────────────────────────────────────────────

def test_row_counts():
    impact = compute_impact(BEFORE, AFTER)
    assert impact["rows_before"] == 5
    assert impact["rows_after"] == 4
    assert impact["rows_removed"] == 1


def test_value_sum():
    impact = compute_impact(BEFORE, AFTER, value_column="order_value")
    # before: 100 + 200 - 50 + 100 + 300 = 650
    assert impact["value_sum_before"] == pytest.approx(650.0)


def test_negative_value_count():
    impact = compute_impact(BEFORE, AFTER, value_column="order_value")
    assert impact["negative_value_count"] == 1


def test_duplicate_id_count():
    impact = compute_impact(BEFORE, AFTER, id_column="order_id")
    assert impact["duplicate_id_count"] == 1


def test_duplicate_value_overcount():
    impact = compute_impact(BEFORE, AFTER, id_column="order_id", value_column="order_value")
    # The extra duplicate of order A ($100) is the overcount
    assert impact["duplicate_value_overcount"] == pytest.approx(100.0)


def test_missing_customer_count():
    impact = compute_impact(BEFORE, AFTER, customer_column="customer_id")
    assert impact["missing_customer_count"] == 1
    assert impact["missing_customer_rate"] == pytest.approx(1 / 5)


def test_missing_channel_count():
    impact = compute_impact(BEFORE, AFTER, channel_column="acquisition_channel")
    assert impact["missing_channel_count"] == 1


def test_future_date_count():
    impact = compute_impact(BEFORE, AFTER, date_column="order_date")
    assert impact["future_date_count"] == 1


def test_missing_optional_columns_all_none():
    """compute_impact must not crash when no optional columns are given."""
    impact = compute_impact(BEFORE, AFTER)
    assert impact["value_sum_before"] is None
    assert impact["duplicate_id_count"] is None
    assert impact["missing_customer_count"] is None
    assert impact["missing_channel_count"] is None
    assert impact["invalid_date_count"] is None


def test_missing_column_not_in_df():
    """Columns not present in the DataFrame are silently skipped."""
    impact = compute_impact(BEFORE, AFTER, id_column="nonexistent_col")
    assert impact["duplicate_id_count"] is None


def test_all_columns_at_once():
    impact = compute_impact(
        BEFORE, AFTER,
        id_column="order_id",
        value_column="order_value",
        date_column="order_date",
        customer_column="customer_id",
        channel_column="acquisition_channel",
    )
    assert impact["duplicate_id_count"] == 1
    assert impact["negative_value_count"] == 1
    assert impact["future_date_count"] == 1
    assert impact["missing_customer_count"] == 1
    assert impact["missing_channel_count"] == 1


# ── _status ────────────────────────────────────────────────────────────────────

def test_status_blocker_on_duplicate():
    impact = compute_impact(BEFORE, AFTER, id_column="order_id")
    assert _status(impact) == "BLOCKER"


def test_status_warning_on_negative_value():
    small_before = _orders_df([{"order_id": "A", "order_value": -10.0}])
    small_after  = _orders_df([{"order_id": "A", "order_value": -10.0}])
    impact = compute_impact(small_before, small_after, value_column="order_value")
    assert _status(impact) == "WARNING"


def test_status_pass_no_issues():
    clean = _orders_df([
        {"order_id": "A", "order_value": 50.0, "customer_id": "C1", "acquisition_channel": "organic"},
        {"order_id": "B", "order_value": 80.0, "customer_id": "C2", "acquisition_channel": "social"},
    ])
    impact = compute_impact(clean, clean, id_column="order_id", value_column="order_value",
                            customer_column="customer_id", channel_column="acquisition_channel")
    assert _status(impact) == "PASS"


# ── build_impact_report ────────────────────────────────────────────────────────

def test_build_impact_report_returns_string():
    impact = compute_impact(BEFORE, AFTER)
    report = build_impact_report(impact, dataset_name="test.csv")
    assert isinstance(report, str)
    assert "Business Impact Report" in report


def test_build_impact_report_includes_dataset_name():
    impact = compute_impact(BEFORE, AFTER)
    report = build_impact_report(impact, dataset_name="orders.csv")
    assert "orders.csv" in report


def test_build_impact_report_shows_status():
    impact = compute_impact(BEFORE, AFTER, id_column="order_id")
    report = build_impact_report(impact)
    assert "BLOCKER" in report


def test_build_impact_report_includes_caveats():
    impact = compute_impact(BEFORE, AFTER)
    report = build_impact_report(impact, caveats=["My custom caveat."])
    assert "My custom caveat." in report


def test_build_impact_report_handles_no_optional_columns():
    """Report must render correctly when no optional columns are analysed."""
    impact = compute_impact(BEFORE, AFTER)
    report = build_impact_report(impact, dataset_name="minimal.csv")
    assert "Business Impact Report" in report
    assert "Caveats" in report


# ── write_impact_report ────────────────────────────────────────────────────────

def test_write_impact_report_creates_file(tmp_path):
    content = "# Test Report\n"
    out = write_impact_report(content, tmp_path / "report.md")
    assert out.exists()
    assert out.read_text() == content


def test_write_impact_report_creates_parent_dirs(tmp_path):
    nested = tmp_path / "a" / "b" / "report.md"
    write_impact_report("x", nested)
    assert nested.exists()
