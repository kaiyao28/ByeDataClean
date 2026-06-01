"""
utils.py
--------
Shared helpers used across the toolkit.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


# ── Optional-package detection ────────────────────────────────────────────────

def check_optional_packages(*names: str) -> dict[str, bool]:
    """Return {package_name: is_available} for each name."""
    return {name: importlib.util.find_spec(name) is not None for name in names}


# ── Logging helpers ───────────────────────────────────────────────────────────

def warn(msg: str) -> None:
    print(f"[WARNING] {msg}", file=sys.stderr)


def info(msg: str) -> None:
    print(f"[INFO] {msg}")


# ── CLI helpers ───────────────────────────────────────────────────────────────

def abort(msg: str, code: int = 1) -> None:
    """Print an error message to stderr and exit."""
    print(f"\n[toolkit] ✗ {msg}", file=sys.stderr)
    sys.exit(code)


def print_banner(dry_run: bool) -> None:
    mode = "DRY RUN — no output will be written" if dry_run else "CLEAN RUN"
    width = 60
    print("─" * width)
    print(f"  ByeDataClean  │  {mode}")
    print("─" * width)


# ── Safety guards ─────────────────────────────────────────────────────────────

def safety_check_output(input_path: str | Path, output_path: str | Path) -> None:
    """Abort if output path resolves to the same file as input.

    Follows symlinks on both sides so a symlink pointing at the input file
    is also caught.
    """
    try:
        in_resolved  = Path(input_path).resolve()
        out_resolved = Path(output_path).resolve()
        if in_resolved == out_resolved:
            abort(
                f"Output path resolves to the same file as input: {in_resolved}\n"
                "  Raw data must never be overwritten. Choose a different output path."
            )
    except SystemExit:
        raise
    except Exception:
        pass  # If resolution fails, let the write step error naturally
