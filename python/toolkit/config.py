"""
config.py
---------
Load and validate configuration for both the reporter and the cleaner.

Reporter config
---------------
  Priority (highest to lowest):
    CLI flags > reporter_config.yaml > built-in DEFAULTS

Cleaner config
--------------
  Cleaning rules are loaded from a YAML file using load_rules().
  Rules are validated using validate_rules() before touching any data.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml


# ─────────────────────────────────────────────────────────────────────────────
# Reporter config
# ─────────────────────────────────────────────────────────────────────────────

DEFAULTS: dict[str, Any] = {
    "input_path": None,
    "example_dataset": None,
    "output_dir": "reports/descriptive_summary",
    "full_profile_dir": "reports/full_profiles",
    "report_basename": "descriptive_qc_report",
    "columns": None,
    "id_cols": None,
    "mode": "quick",
    "type_overrides": {},
    "date_columns": [],
    "schema_path": None,
    "thresholds": {
        "high_missingness": 0.20,
        "very_high_missingness": 0.50,
        "imbalance_cutoff": 0.95,
        "high_cardinality_cutoff": 50,
        "rare_category_cutoff": 0.01,
        "outlier_method": "iqr",
    },
    "privacy": {
        "suppress_id_values": True,
        "suppress_free_text_examples": True,
        "max_category_levels_shown": 20,
        "max_text_length_shown": 40,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge *override* into *base* (base is not mutated)."""
    result = copy.deepcopy(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Return a reporter config dict with defaults filled in.

    Parameters
    ----------
    config_path:
        Path to a YAML config file.  If None, only defaults are returned.
    """
    cfg = copy.deepcopy(DEFAULTS)
    if config_path is not None:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with path.open() as fh:
            user_cfg = yaml.safe_load(fh) or {}
        cfg = _deep_merge(cfg, user_cfg)
    return cfg


def apply_cli_overrides(cfg: dict[str, Any], cli_args: Any) -> dict[str, Any]:
    """Merge argparse namespace *cli_args* into *cfg* (CLI takes priority)."""
    cfg = copy.deepcopy(cfg)
    mapping = {
        "input": "input_path",
        "example_dataset": "example_dataset",
        "columns": "columns",
        "id_cols": "id_cols",
        "mode": "mode",
        "schema": "schema_path",
        "output_dir": "output_dir",
    }
    for cli_attr, cfg_key in mapping.items():
        val = getattr(cli_args, cli_attr, None)
        if val is not None:
            cfg[cfg_key] = val
    return cfg


def validate_config(cfg: dict[str, Any]) -> None:
    """Raise ValueError if the reporter config is clearly invalid."""
    if cfg.get("input_path") is None and cfg.get("example_dataset") is None:
        raise ValueError("Provide either --input <path> or --example-dataset <name>.")
    valid_modes = {"quick", "full", "both"}
    if cfg.get("mode") not in valid_modes:
        raise ValueError(f"mode must be one of {valid_modes!r}; got {cfg['mode']!r}")


# ─────────────────────────────────────────────────────────────────────────────
# Cleaner config
# ─────────────────────────────────────────────────────────────────────────────

SUPPORTED_ACTIONS = {
    "standardise_column_names",
    "rename_columns",
    "keep_columns",
    "drop_columns",
    "replace_missing_codes",
    "trim_whitespace",
    "standardise_case",
    "map_categories",
    "set_invalid_to_missing",
    "flag_outliers_iqr",
    "parse_dates",
    "remove_exact_duplicates",
    "filter_rows_explicit",
    "create_missingness_flags",
}

VALID_SEVERITIES = {"critical", "high", "medium", "low"}
VALID_ACTION_REQUIRED = {"block_report", "investigate", "clean_with_rule", "flag_only"}


def load_rules(rules_path: str | Path) -> dict[str, Any]:
    """Load YAML cleaning rules file and return as dict."""
    path = Path(rules_path)
    if not path.exists():
        raise FileNotFoundError(f"Rules file not found: {path}")
    with path.open() as fh:
        return yaml.safe_load(fh) or {}


def validate_rules(rules: dict[str, Any]) -> list[str]:
    """Return a list of validation error messages (empty list = valid).

    Also checks the global ``safety:`` block if present — global
    ``allow_row_drop: false`` overrides any per-step setting.
    """
    errors: list[str] = []

    if rules.get("version") != 1:
        errors.append("'version' must be 1.")

    steps = rules.get("rules", [])
    if not isinstance(steps, list):
        errors.append("'rules' must be a list of step dicts.")
        return errors

    # Global safety block
    safety = rules.get("safety", {}) or {}
    global_no_row_drop = safety.get("allow_row_drop") is False
    global_no_col_drop = safety.get("allow_column_drop") is False

    seen_steps: set[int] = set()
    for i, step in enumerate(steps):
        loc = f"rules[{i}]"
        if not isinstance(step, dict):
            errors.append(f"{loc}: each rule must be a dict.")
            continue

        step_num = step.get("step")
        if step_num is None:
            errors.append(f"{loc}: missing 'step' number.")
        elif step_num in seen_steps:
            errors.append(f"{loc}: duplicate step number {step_num}.")
        else:
            seen_steps.add(step_num)

        action = step.get("action")
        if not action:
            errors.append(f"{loc}: missing 'action'.")
            continue
        if action not in SUPPORTED_ACTIONS:
            errors.append(
                f"{loc}: unsupported action '{action}'. "
                f"Supported: {sorted(SUPPORTED_ACTIONS)}"
            )
            continue

        # Destructive action guards (per-step)
        if action in ("keep_columns", "drop_columns"):
            if global_no_col_drop:
                errors.append(
                    f"{loc} ({action}): blocked by global 'safety.allow_column_drop: false'."
                )
            elif not step.get("allow_drop"):
                errors.append(
                    f"{loc} ({action}): requires 'allow_drop: true' in this rule "
                    "to confirm the column drop is intentional."
                )

        if action == "remove_exact_duplicates":
            if global_no_row_drop:
                errors.append(
                    f"{loc} (remove_exact_duplicates): blocked by global 'safety.allow_row_drop: false'."
                )
            elif not step.get("allow_row_drop"):
                errors.append(
                    f"{loc} (remove_exact_duplicates): requires 'allow_row_drop: true'."
                )

        if action == "filter_rows_explicit":
            if global_no_row_drop:
                errors.append(
                    f"{loc} (filter_rows_explicit): blocked by global 'safety.allow_row_drop: false'."
                )
            else:
                if not step.get("allow_row_drop"):
                    errors.append(f"{loc} (filter_rows_explicit): requires 'allow_row_drop: true'.")
                if not step.get("reason"):
                    errors.append(
                        f"{loc} (filter_rows_explicit): requires a 'reason' string "
                        "documenting why rows are being dropped."
                    )

        if action == "flag_outliers_iqr" and step.get("remove") is True:
            if global_no_row_drop:
                errors.append(
                    f"{loc} (flag_outliers_iqr with remove: true): blocked by global 'safety.allow_row_drop: false'."
                )
            elif not step.get("allow_row_drop"):
                errors.append(
                    f"{loc} (flag_outliers_iqr with remove: true): requires 'allow_row_drop: true'."
                )

        # Optional business metadata validation
        severity = step.get("severity")
        if severity is not None and severity not in VALID_SEVERITIES:
            errors.append(
                f"{loc}: invalid 'severity' value {severity!r}. "
                f"Must be one of {sorted(VALID_SEVERITIES)}."
            )

        action_req = step.get("action_required")
        if action_req is not None and action_req not in VALID_ACTION_REQUIRED:
            errors.append(
                f"{loc}: invalid 'action_required' value {action_req!r}. "
                f"Must be one of {sorted(VALID_ACTION_REQUIRED)}."
            )

    return errors


def has_destructive_rules(rules: dict[str, Any]) -> bool:
    """Return True if any rule would drop rows or columns."""
    row_drop_actions = {"remove_exact_duplicates", "filter_rows_explicit"}
    col_drop_actions = {"keep_columns", "drop_columns"}
    for step in rules.get("rules", []):
        action = step.get("action", "")
        if action in row_drop_actions:
            return True
        if action in col_drop_actions:
            return True
        if action == "flag_outliers_iqr" and step.get("remove") is True:
            return True
    return False
