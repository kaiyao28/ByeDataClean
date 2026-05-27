"""
example_datasets.py
-------------------
Load built-in public example datasets.

Datasets are never committed to the repo.  Internet / package availability is
handled gracefully: if loading fails, a clear message is printed and None is
returned so the caller can exit cleanly.
"""

from __future__ import annotations

import sys
from typing import Optional

import pandas as pd

AVAILABLE = ["penguins", "tips", "iris"]


def load_example_dataset(name: str) -> Optional[pd.DataFrame]:
    """Return a DataFrame for the named example dataset, or None on failure."""
    name = name.strip().lower()
    if name in ("penguins", "tips"):
        return _load_seaborn_dataset(name)
    if name == "iris":
        return _load_iris()
    print(
        f"[example_datasets] Unknown example dataset: {name!r}.\n"
        f"  Available: {AVAILABLE}\n"
        "  Use --input to load your own file instead.",
        file=sys.stderr,
    )
    return None


def _load_seaborn_dataset(name: str) -> Optional[pd.DataFrame]:
    try:
        import seaborn as sns  # type: ignore
    except ImportError:
        print(
            f"[example_datasets] 'seaborn' is not installed — cannot load '{name}'.\n"
            "  Install it with:  pip install seaborn\n"
            "  Or use --input to load your own file.",
            file=sys.stderr,
        )
        return None
    try:
        df = sns.load_dataset(name)
        print(f"[example_datasets] Loaded '{name}' from seaborn ({df.shape[0]:,} rows × {df.shape[1]} cols).")
        return df
    except Exception as exc:
        print(
            f"[example_datasets] Could not load '{name}' via seaborn: {exc}\n"
            "  This may be a network issue.  Use --input to load your own file instead.",
            file=sys.stderr,
        )
        return None


def _load_iris() -> Optional[pd.DataFrame]:
    try:
        from sklearn.datasets import load_iris  # type: ignore
        raw = load_iris(as_frame=True)
        df = raw.frame
        df["target_name"] = raw.target_names[df["target"]]
        print(f"[example_datasets] Loaded 'iris' from scikit-learn ({df.shape[0]} rows × {df.shape[1]} cols).")
        return df
    except ImportError:
        pass
    try:
        import seaborn as sns  # type: ignore
        df = sns.load_dataset("iris")
        print(f"[example_datasets] Loaded 'iris' from seaborn ({df.shape[0]} rows × {df.shape[1]} cols).")
        return df
    except Exception:
        pass
    print(
        "[example_datasets] Could not load 'iris'.\n"
        "  Install scikit-learn (pip install scikit-learn) or seaborn (pip install seaborn),\n"
        "  or use --input to load your own file.",
        file=sys.stderr,
    )
    return None
