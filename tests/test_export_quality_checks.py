"""
test_export_quality_checks.py
-----------------------------
Tests for the dbt, Pandera, and Soda Core exporters.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# The exporter functions live in python/export_quality_checks.py, which is
# not inside the toolkit package. Import it by adding python/ to sys.path.
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from export_quality_checks import export_dbt, export_pandera, export_soda


# ── Shared fixture ────────────────────────────────────────────────────────────

VALIDATION = {
    "required_columns": ["order_id", "order_date"],
    "unique_keys": [["order_id"], ["order_id", "customer_id"]],
    "accepted_values": {
        "region": ["North America", "Europe", "APAC"],
        "refunded": ["yes", "no"],
    },
    "ranges": {
        "order_value": {"min": 0.01, "max": 10000.0},
    },
}

SCHEMA_CFG = {
    "columns": {
        "order_id": {"role": "id"},
        "order_value": {"type": "continuous"},
        "region": {"type": "categorical"},
        "order_date": {"type": "date"},
    }
}


# ── dbt exporter ──────────────────────────────────────────────────────────────

class TestExportDbt:
    def test_creates_file(self, tmp_path):
        out = export_dbt(VALIDATION, tmp_path / "dbt", model_name="orders")
        assert out.exists()
        assert out.name == "schema.yml"

    def test_contains_model_name(self, tmp_path):
        out = export_dbt(VALIDATION, tmp_path, model_name="orders_model")
        content = out.read_text()
        assert "orders_model" in content

    def test_required_column_gets_not_null(self, tmp_path):
        out = export_dbt(VALIDATION, tmp_path)
        content = out.read_text()
        assert "not_null" in content

    def test_unique_key_gets_unique_test(self, tmp_path):
        out = export_dbt(VALIDATION, tmp_path)
        content = out.read_text()
        assert "unique" in content

    def test_accepted_values_exported(self, tmp_path):
        out = export_dbt(VALIDATION, tmp_path)
        content = out.read_text()
        assert "accepted_values" in content
        assert "North America" in content

    def test_range_exported(self, tmp_path):
        out = export_dbt(VALIDATION, tmp_path)
        content = out.read_text()
        assert "0.01" in content

    def test_empty_validation_does_not_crash(self, tmp_path):
        out = export_dbt({}, tmp_path)
        assert out.exists()

    def test_starter_template_warning_present(self, tmp_path):
        out = export_dbt(VALIDATION, tmp_path)
        content = out.read_text()
        assert "STARTER TEMPLATE" in content


# ── Pandera exporter ──────────────────────────────────────────────────────────

class TestExportPandera:
    def test_creates_file(self, tmp_path):
        out = export_pandera(VALIDATION, None, tmp_path / "pandera")
        assert out.exists()
        assert out.name == "schema.py"

    def test_contains_dataframeschema(self, tmp_path):
        out = export_pandera(VALIDATION, None, tmp_path)
        assert "DataFrameSchema" in out.read_text()

    def test_required_column_is_not_nullable(self, tmp_path):
        out = export_pandera(VALIDATION, None, tmp_path)
        content = out.read_text()
        assert "nullable=False" in content

    def test_accepted_values_use_isin(self, tmp_path):
        out = export_pandera(VALIDATION, None, tmp_path)
        content = out.read_text()
        assert "Check.isin" in content

    def test_range_uses_between(self, tmp_path):
        out = export_pandera(VALIDATION, None, tmp_path)
        content = out.read_text()
        assert "Check.between" in content

    def test_schema_cfg_adds_types(self, tmp_path):
        out = export_pandera(VALIDATION, SCHEMA_CFG, tmp_path)
        content = out.read_text()
        assert "'float'" in content or "'datetime'" in content

    def test_without_schema_cfg_uses_object(self, tmp_path):
        out = export_pandera(VALIDATION, None, tmp_path)
        content = out.read_text()
        assert "'object'" in content

    def test_empty_validation_does_not_crash(self, tmp_path):
        out = export_pandera({}, None, tmp_path)
        assert out.exists()


# ── Soda exporter ─────────────────────────────────────────────────────────────

class TestExportSoda:
    def test_creates_file(self, tmp_path):
        out = export_soda(VALIDATION, tmp_path / "soda", dataset_name="orders")
        assert out.exists()
        assert out.name == "checks.yml"

    def test_contains_dataset_name(self, tmp_path):
        out = export_soda(VALIDATION, tmp_path, dataset_name="orders_table")
        assert "orders_table" in out.read_text()

    def test_required_column_gets_missing_count(self, tmp_path):
        out = export_soda(VALIDATION, tmp_path)
        content = out.read_text()
        assert "missing_count" in content

    def test_unique_key_gets_duplicate_count(self, tmp_path):
        out = export_soda(VALIDATION, tmp_path)
        content = out.read_text()
        assert "duplicate_count" in content

    def test_accepted_values_exported(self, tmp_path):
        out = export_soda(VALIDATION, tmp_path)
        content = out.read_text()
        assert "valid values" in content
        assert "North America" in content

    def test_range_min_exported(self, tmp_path):
        out = export_soda(VALIDATION, tmp_path)
        content = out.read_text()
        assert "min(order_value)" in content

    def test_range_max_exported(self, tmp_path):
        out = export_soda(VALIDATION, tmp_path)
        content = out.read_text()
        assert "max(order_value)" in content

    def test_composite_key_is_commented(self, tmp_path):
        out = export_soda(VALIDATION, tmp_path)
        content = out.read_text()
        # composite key [order_id, customer_id] should be commented, not a check
        assert "customer_id" in content
        lines_with_customer = [l for l in content.splitlines() if "customer_id" in l]
        assert all(l.strip().startswith("#") for l in lines_with_customer)

    def test_empty_validation_does_not_crash(self, tmp_path):
        out = export_soda({}, tmp_path)
        assert out.exists()

    def test_starter_template_warning_present(self, tmp_path):
        out = export_soda(VALIDATION, tmp_path)
        assert "STARTER TEMPLATE" in out.read_text()
