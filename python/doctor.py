#!/usr/bin/env python3
"""
doctor.py
---------
Environment check for ByeDataClean.

Diagnoses common setup problems before you run the reporter or cleaner.

Usage:
    python python/doctor.py
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

_PASS  = "  ✓"
_WARN  = "  ⚠"
_FAIL  = "  ✗"
_INFO  = "  ·"

_required_packages  = ["pandas", "numpy", "yaml"]
_optional_packages  = ["seaborn", "sklearn", "skimpy", "ydata_profiling"]

_ok = True


def _check(label: str, passed: bool, note: str = "", fix: str = "") -> None:
    global _ok
    if passed:
        print(f"{_PASS}  {label}{': ' + note if note else ''}")
    else:
        _ok = False
        print(f"{_FAIL}  {label}{': ' + note if note else ''}")
        if fix:
            print(f"      Fix: {fix}")


def _warn(label: str, note: str = "", fix: str = "") -> None:
    print(f"{_WARN}  {label}{': ' + note if note else ''}")
    if fix:
        print(f"      Fix: {fix}")


def _info(msg: str) -> None:
    print(f"{_INFO}  {msg}")


def main() -> None:
    sep = "─" * 58
    print(f"\n{sep}")
    print("  ByeDataClean  │  doctor")
    print(f"{sep}\n")

    # ── Python version ─────────────────────────────────────────────────────────
    print("Python")
    major, minor = sys.version_info.major, sys.version_info.minor
    _check(
        f"Python {major}.{minor}",
        major >= 3 and minor >= 9,
        note=sys.version.split()[0],
        fix="Install Python 3.9 or later from https://python.org",
    )

    # ── Working directory ─────────────────────────────────────────────────────
    print("\nWorking directory")
    cwd = Path.cwd()
    readme = cwd / "README.md"
    python_dir = cwd / "python"
    _check(
        "README.md present",
        readme.exists(),
        note=str(cwd),
        fix="Run  cd <repo-root>  and then retry.",
    )
    if cwd.name == "python":
        _warn(
            "You appear to be inside python/",
            note=str(cwd),
            fix="Run  cd ..  to go back to the repo root.",
        )

    # ── Required packages ──────────────────────────────────────────────────────
    print("\nRequired packages")
    for pkg in _required_packages:
        try:
            m = importlib.import_module(pkg)
            ver = getattr(m, "__version__", "?")
            _check(pkg, True, note=ver)
        except ImportError:
            _check(
                pkg, False,
                note="not installed",
                fix=f"pip install {pkg.replace('yaml', 'pyyaml')}",
            )

    # ── Optional packages ──────────────────────────────────────────────────────
    print("\nOptional packages")
    for pkg in _optional_packages:
        try:
            m = importlib.import_module(pkg)
            ver = getattr(m, "__version__", "?")
            _info(f"{pkg} {ver}  (installed)")
        except ImportError:
            _info(f"{pkg}  not installed  — run: pip install {pkg.replace('_', '-')}")

    # ── Toolkit import ─────────────────────────────────────────────────────────
    print("\nToolkit")
    sys.path.insert(0, str(python_dir)) if python_dir.exists() else None
    sys.path.insert(0, str(Path(__file__).parent))

    try:
        import toolkit  # noqa: F401
        _check("toolkit importable", True)
    except ImportError as e:
        _check(
            "toolkit importable", False,
            note=str(e),
            fix="Make sure you are running from the repo root: python python/doctor.py",
        )

    # ── Example data ───────────────────────────────────────────────────────────
    print("\nExample files")
    example_csv   = cwd / "data" / "raw" / "example_dirty_data.csv"
    example_rules = cwd / "config" / "example_cleaning_rules.yaml"
    _check(
        "data/examples/example_dirty_data.csv",
        example_csv.exists(),
        fix="Make sure you cloned the full repository.",
    )
    _check(
        "config/example_cleaning_rules.yaml",
        example_rules.exists(),
        fix="Make sure you cloned the full repository.",
    )

    # ── Reports directory writable ─────────────────────────────────────────────
    print("\nOutput directories")
    for subdir in ["reports/cleaning_logs", "reports/descriptive_summary",
                   "reports/validation_reports", "data/processed"]:
        d = cwd / subdir
        d.mkdir(parents=True, exist_ok=True)
        try:
            test_file = d / ".doctor_write_test"
            test_file.write_text("ok")
            test_file.unlink()
            _check(subdir, True, note="writable")
        except OSError as e:
            _check(subdir, False, note=str(e),
                   fix=f"Check folder permissions on {d}")

    # ── Minimal reporter smoke test ────────────────────────────────────────────
    print("\nSmoke tests")
    try:
        import pandas as pd
        from toolkit.type_detection import infer_types
        from toolkit.profiling import dataset_overview
        df = pd.DataFrame({"id": [1, 2, 3], "val": [10.0, None, 30.0]})
        types = infer_types(df)
        dataset_overview(df, types)
        _check("Reporter smoke test", True)
    except Exception as e:
        _check("Reporter smoke test", False, note=str(e))

    try:
        import contextlib, io, tempfile
        from toolkit.cleaning import run_cleaning_pipeline
        import pandas as pd
        df = pd.DataFrame({"ID": [1, 2, 3]})
        rules = {"version": 1, "name": "doctor_test", "rules": [
            {"step": 1, "action": "standardise_column_names",
             "name": "standardise_column_names"},
        ]}
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stdout(io.StringIO()), \
                 contextlib.redirect_stderr(io.StringIO()):
                run_cleaning_pipeline(df, rules, log_dir=tmp, validation_dir=tmp)
        _check("Cleaner dry-run smoke test", True)
    except Exception as e:
        _check("Cleaner dry-run smoke test", False, note=str(e))

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\n{sep}")
    if _ok:
        print("  All checks passed. ByeDataClean should work correctly.\n")
        print("  Try the one-command demo:")
        print("    python python/run_demo.py\n")
    else:
        print("  Some checks failed. Fix the issues above, then re-run:\n")
        print("    python python/doctor.py\n")
    print(sep)


if __name__ == "__main__":
    main()
