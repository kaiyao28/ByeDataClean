"""
io.py
-----
Read and write tabular data.

Supported formats:
  .csv, .tsv, .txt  →  pandas.read_csv
  .xls, .xlsx       →  pandas.read_excel
  .parquet          →  pandas.read_parquet
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


# ── Read ──────────────────────────────────────────────────────────────────────

def read_file(path: str | Path, **kwargs) -> pd.DataFrame:
    """Load a tabular file into a DataFrame.

    Parameters
    ----------
    path:
        File path.  Extension determines the reader.
    **kwargs:
        Passed through to the underlying pandas reader.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    suffix = path.suffix.lower()
    if suffix in (".csv", ".txt"):
        return pd.read_csv(path, **kwargs)
    if suffix == ".tsv":
        return pd.read_csv(path, sep="\t", **kwargs)
    if suffix in (".xls", ".xlsx"):
        return pd.read_excel(path, **kwargs)
    if suffix == ".parquet":
        return pd.read_parquet(path, **kwargs)

    print(f"[io] Unrecognised extension '{suffix}'; attempting CSV read.")
    return pd.read_csv(path, **kwargs)


def select_columns(df: pd.DataFrame, columns: list[str] | None) -> pd.DataFrame:
    """Return *df* restricted to *columns* (or the full frame if None)."""
    if columns is None:
        return df
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(
            f"Requested columns not found in the dataset: {missing}\n"
            f"Available columns: {list(df.columns)}"
        )
    return df[columns]


# ── Write ─────────────────────────────────────────────────────────────────────

def write_file(df: pd.DataFrame, path: str | Path) -> None:
    """Write *df* to CSV or Parquet depending on the file extension."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".parquet":
        df.to_parquet(path, index=False)
    else:
        df.to_csv(path, index=False)


def default_output_path(input_path: str | Path) -> Path:
    """Generate a default output path in data/processed/ from an input path."""
    stem = Path(input_path).stem
    return Path("data/processed") / f"{stem}_cleaned.csv"
