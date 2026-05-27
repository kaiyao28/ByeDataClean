"""
test_config_validation.py
--------------------------
Tests for config loading and defaults.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from toolkit.config import DEFAULTS, load_config, validate_config


REPO_ROOT = Path(__file__).parent.parent
EXAMPLE_CONFIG = REPO_ROOT / "config" / "reporter_config.example.yaml"


def test_example_config_loads():
    """The committed example config file must be parseable."""
    cfg = load_config(EXAMPLE_CONFIG)
    assert isinstance(cfg, dict)


def test_example_config_has_thresholds():
    cfg = load_config(EXAMPLE_CONFIG)
    assert "thresholds" in cfg
    assert "high_missingness" in cfg["thresholds"]


def test_defaults_filled_when_fields_absent(tmp_path):
    """A minimal YAML (only example_dataset) should get all defaults."""
    minimal = tmp_path / "minimal.yaml"
    minimal.write_text("example_dataset: penguins\n")
    cfg = load_config(minimal)
    assert cfg["mode"] == DEFAULTS["mode"]
    assert cfg["thresholds"]["high_missingness"] == DEFAULTS["thresholds"]["high_missingness"]
    assert cfg["privacy"]["suppress_id_values"] == DEFAULTS["privacy"]["suppress_id_values"]


def test_defaults_returned_without_config():
    cfg = load_config(None)
    assert cfg["mode"] == "quick"
    assert cfg["output_dir"] == "reports/descriptive_summary"


def test_validate_config_raises_without_input():
    cfg = load_config(None)
    cfg["input_path"] = None
    cfg["example_dataset"] = None
    with pytest.raises(ValueError, match="Provide either"):
        validate_config(cfg)


def test_validate_config_passes_with_example_dataset():
    cfg = load_config(None)
    cfg["example_dataset"] = "penguins"
    validate_config(cfg)  # should not raise


def test_validate_config_raises_on_bad_mode():
    cfg = load_config(None)
    cfg["example_dataset"] = "penguins"
    cfg["mode"] = "invalid_mode"
    with pytest.raises(ValueError, match="mode must be one of"):
        validate_config(cfg)


def test_missing_config_file_raises():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/config.yaml")
