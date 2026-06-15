"""
test_scorecard.py
-----------------
Tests for toolkit/scorecard.py: build_scorecard() and write_scorecard().
"""

from __future__ import annotations

from pathlib import Path

import pytest

from toolkit.scorecard import _overall_status, _severity_counts, build_scorecard, write_scorecard
from toolkit.validation import ValidationResult


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _val(passed: bool, check: str = "range", col: str = "col", msg: str = "ok") -> ValidationResult:
    return ValidationResult(check=check, column=col, passed=passed, message=msg)


BEFORE = {"n_rows": 100, "n_cols": 5, "n_missing_cells": 20}
AFTER  = {"n_rows":  98, "n_cols": 6, "n_missing_cells": 12}


def _step(severity: str = "", action_required: str = "", destructive: bool = False) -> dict:
    return {
        "step": 1, "name": "test_step", "action": "trim_whitespace",
        "severity": severity, "action_required": action_required,
        "destructive": destructive, "rows_removed": 2 if destructive else 0,
        "columns_removed": [], "stakeholder_note": "", "rationale": "",
    }


# ── _overall_status ────────────────────────────────────────────────────────────

def test_status_pass_no_issues():
    assert _overall_status([], [_val(True)]) == "PASS"


def test_status_blocker_on_val_failure():
    assert _overall_status([], [_val(False)]) == "BLOCKER"


def test_status_blocker_critical_investigate():
    steps = [_step("critical", "investigate")]
    assert _overall_status(steps, []) == "BLOCKER"


def test_status_blocker_high_block_report():
    steps = [_step("high", "block_report")]
    assert _overall_status(steps, []) == "BLOCKER"


def test_status_warning_high_investigate():
    steps = [_step("high", "investigate")]
    assert _overall_status(steps, []) == "WARNING"


def test_status_warning_medium_investigate():
    steps = [_step("medium", "investigate")]
    assert _overall_status(steps, []) == "WARNING"


def test_status_pass_with_low_investigate():
    # low severity + investigate → PASS (only high/medium escalate to WARNING)
    steps = [_step("low", "investigate")]
    assert _overall_status(steps, []) == "PASS"


# ── _severity_counts ──────────────────────────────────────────────────────────

def test_severity_counts_empty():
    counts = _severity_counts([])
    assert counts == {"critical": 0, "high": 0, "medium": 0, "low": 0}


def test_severity_counts_mixed():
    steps = [
        _step("critical"), _step("high"), _step("high"), _step("low"),
    ]
    counts = _severity_counts(steps)
    assert counts["critical"] == 1
    assert counts["high"] == 2
    assert counts["medium"] == 0
    assert counts["low"] == 1


def test_severity_counts_unset_not_counted():
    steps = [_step(""), _step("unknown")]
    counts = _severity_counts(steps)
    assert sum(counts.values()) == 0


# ── build_scorecard ───────────────────────────────────────────────────────────

def test_build_scorecard_returns_string():
    result = build_scorecard("test.csv", BEFORE, AFTER, [], [], "test_rules")
    assert isinstance(result, str)


def test_build_scorecard_contains_dataset_name():
    result = build_scorecard("orders.csv", BEFORE, AFTER, [], [], "biz_rules")
    assert "orders.csv" in result


def test_build_scorecard_status_pass():
    result = build_scorecard("d.csv", BEFORE, AFTER, [], [_val(True)], "r")
    assert "PASS" in result


def test_build_scorecard_status_blocker_on_val_failure():
    result = build_scorecard("d.csv", BEFORE, AFTER, [], [_val(False)], "r")
    assert "BLOCKER" in result


def test_build_scorecard_counts_table():
    result = build_scorecard("d.csv", BEFORE, AFTER, [], [], "r")
    assert "98" in result      # rows after
    assert "100" in result     # rows before


def test_build_scorecard_recommended_use_section():
    result = build_scorecard("d.csv", BEFORE, AFTER, [], [_val(True)], "r")
    assert "Recommended use" in result


def test_build_scorecard_with_business_metadata():
    steps = [
        {
            "step": 1, "name": "dedup", "action": "remove_exact_duplicates",
            "severity": "critical", "action_required": "investigate",
            "destructive": True, "rows_removed": 2, "columns_removed": [],
            "stakeholder_note": "Duplicate orders found.", "rationale": "",
        }
    ]
    result = build_scorecard("d.csv", BEFORE, AFTER, steps, [], "r")
    assert "critical" in result.lower() or "Critical" in result
    assert "dedup" in result


def test_build_scorecard_missing_columns_optional():
    """build_scorecard must not crash when validation_results is empty."""
    result = build_scorecard("d.csv", BEFORE, AFTER, [], [], "")
    assert "Scorecard" in result


# ── write_scorecard ───────────────────────────────────────────────────────────

def test_write_scorecard_creates_file(tmp_path):
    content = "# Test Scorecard\n"
    out = write_scorecard(content, tmp_path, "test")
    assert out.exists()
    assert out.read_text() == content


def test_write_scorecard_filename_contains_scorecard(tmp_path):
    out = write_scorecard("x", tmp_path, "my_rules")
    assert "scorecard" in out.name
    assert out.name.startswith("my_rules_")


def test_write_scorecard_creates_directory(tmp_path):
    nested = tmp_path / "a" / "b"
    out = write_scorecard("x", nested, "test")
    assert out.exists()
