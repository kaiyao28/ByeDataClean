"""
profiling.py
------------
Descriptive statistics, custom warnings, and decision prompts.

Merged from three former sub-modules:
  profile.py          — per-column and dataset-level statistics
  custom_checks.py    — warning generators on top of profiling output
  decision_prompts.py — structured analyst decision prompts

No rendering happens here — that is report_writer.py's job.
"""

from __future__ import annotations

import datetime
from collections import Counter
from dataclasses import dataclass
from typing import Any

import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# Dataset statistics (formerly profile.py)
# ─────────────────────────────────────────────────────────────────────────────

def dataset_overview(df: pd.DataFrame, types: dict[str, str]) -> dict[str, Any]:
    """High-level dataset facts."""
    type_counts = Counter(types.values())
    return {
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 ** 2, 3),
        "columns": list(df.columns),
        "type_counts": dict(type_counts),
    }


def column_inventory(df: pd.DataFrame, types: dict[str, str]) -> pd.DataFrame:
    """Return a per-column summary DataFrame."""
    rows = []
    for col in df.columns:
        n_missing  = int(df[col].isna().sum())
        pct_missing = n_missing / len(df) if len(df) > 0 else 0.0
        n_unique   = int(df[col].nunique(dropna=True))
        rows.append({
            "column": col,
            "inferred_type": types.get(col, "unknown"),
            "missing_n": n_missing,
            "missing_pct": round(pct_missing * 100, 1),
            "unique_n": n_unique,
        })
    return pd.DataFrame(rows)


def missingness_summary(
    df: pd.DataFrame,
    thresholds: dict[str, float],
) -> dict[str, Any]:
    miss  = df.isna().sum()
    pct   = miss / len(df) if len(df) > 0 else miss * 0
    high      = thresholds.get("high_missingness", 0.20)
    very_high = thresholds.get("very_high_missingness", 0.50)

    fully_missing    = list(miss[miss == len(df)].index)
    high_missing     = list(pct[(pct > high) & (pct <= very_high)].index)
    very_high_missing = list(pct[pct > very_high].index)

    top = pct.sort_values(ascending=False).head(10)
    return {
        "fully_missing": fully_missing,
        "high_missing": high_missing,
        "very_high_missing": very_high_missing,
        "top_missing": {col: round(v * 100, 1) for col, v in top.items() if v > 0},
    }


def duplication_summary(
    df: pd.DataFrame,
    id_cols: list[str] | None,
) -> dict[str, Any]:
    n_exact_dups = int(df.duplicated().sum())
    result: dict[str, Any] = {"exact_duplicate_rows": n_exact_dups}
    if id_cols:
        valid_id_cols = [c for c in id_cols if c in df.columns]
        if valid_id_cols:
            n_dup_ids = int(df.duplicated(subset=valid_id_cols, keep=False).sum())
            result["duplicate_id_rows"]  = n_dup_ids
            result["id_cols_checked"]    = valid_id_cols
        else:
            result["id_cols_not_found"]  = id_cols
    return result


def continuous_summary(
    df: pd.DataFrame,
    types: dict[str, str],
    thresholds: dict[str, Any],
) -> pd.DataFrame:
    target_types = {"continuous", "categorical_or_ordinal"}
    cols = [c for c, t in types.items() if t in target_types and c in df.columns]
    rows = []
    for col in cols:
        s = df[col].dropna()
        n = len(s)
        n_missing = int(df[col].isna().sum())
        if n == 0:
            continue
        q1, q3 = float(s.quantile(0.25)), float(s.quantile(0.75))
        iqr  = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        n_outliers = int(((s < lower) | (s > upper)).sum())
        rows.append({
            "column": col,
            "type": types[col],
            "n": n,
            "missing": n_missing,
            "mean": round(float(s.mean()), 4),
            "sd": round(float(s.std()), 4),
            "median": round(float(s.median()), 4),
            "iqr": round(iqr, 4),
            "min": round(float(s.min()), 4),
            "max": round(float(s.max()), 4),
            "n_outliers_iqr": n_outliers,
        })
    return pd.DataFrame(rows)


def binary_summary(
    df: pd.DataFrame,
    types: dict[str, str],
    thresholds: dict[str, Any],
) -> pd.DataFrame:
    imbalance_cut = thresholds.get("imbalance_cutoff", 0.95)
    cols = [c for c, t in types.items() if t == "binary" and c in df.columns]
    rows = []
    for col in cols:
        vc    = df[col].value_counts(dropna=True)
        total = vc.sum()
        if total == 0:
            continue
        vals    = list(vc.index)
        counts  = list(vc.values)
        pcts    = [round(c / total * 100, 1) for c in counts]
        dominant_pct = max(pcts) / 100
        rows.append({
            "column": col,
            "values": str(vals),
            "counts": str(counts),
            "pcts": str(pcts),
            "imbalanced": dominant_pct >= imbalance_cut,
            "missing": int(df[col].isna().sum()),
        })
    return pd.DataFrame(rows)


def categorical_summary(
    df: pd.DataFrame,
    types: dict[str, str],
    thresholds: dict[str, Any],
    privacy: dict[str, Any],
) -> pd.DataFrame:
    rare_cut   = thresholds.get("rare_category_cutoff", 0.01)
    hcc        = thresholds.get("high_cardinality_cutoff", 50)
    max_levels = privacy.get("max_category_levels_shown", 20)
    target = {"categorical", "categorical_or_ordinal"}
    cols = [c for c, t in types.items() if t in target and c in df.columns]
    rows = []
    for col in cols:
        vc    = df[col].value_counts(dropna=True)
        total = vc.sum()
        n_cats = len(vc)
        rare  = [str(v) for v, c in vc.items() if c / total < rare_cut]
        top   = [(str(v), int(c)) for v, c in vc.head(max_levels).items()]

        str_vals = df[col].dropna().astype(str)
        stripped = str_vals.str.strip()
        has_whitespace = bool((str_vals != stripped).any())
        lowered = str_vals.str.lower()
        has_case_mix = bool(str_vals.nunique() > lowered.nunique())

        rows.append({
            "column": col,
            "n_categories": n_cats,
            "high_cardinality": n_cats > hcc,
            "n_rare": len(rare),
            "rare_examples": str(rare[:5]),
            "top_categories": str(top),
            "possible_whitespace": has_whitespace,
            "possible_case_inconsistency": has_case_mix,
            "missing": int(df[col].isna().sum()),
        })
    return pd.DataFrame(rows)


def date_summary(
    df: pd.DataFrame,
    types: dict[str, str],
    date_columns: list[str],
) -> pd.DataFrame:
    today = datetime.date.today()
    cols  = [c for c, t in types.items() if t == "date" and c in df.columns]
    for c in (date_columns or []):
        if c in df.columns and c not in cols:
            cols.append(c)
    rows = []
    for col in cols:
        try:
            parsed = pd.to_datetime(df[col], errors="coerce")
        except Exception:
            continue
        n_missing = int(parsed.isna().sum())
        valid = parsed.dropna()
        if len(valid) == 0:
            rows.append({"column": col, "min_date": None, "max_date": None,
                         "missing": n_missing, "future_dates": 0})
            continue
        min_d = valid.min().date()
        max_d = valid.max().date()
        n_future = int((valid.dt.date > today).sum())
        rows.append({
            "column": col,
            "min_date": str(min_d),
            "max_date": str(max_d),
            "missing": n_missing,
            "future_dates": n_future,
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Custom warnings (formerly custom_checks.py)
# ─────────────────────────────────────────────────────────────────────────────

def check_high_missingness(df: pd.DataFrame, thresholds: dict[str, float]) -> list[str]:
    warnings = []
    high      = thresholds.get("high_missingness", 0.20)
    very_high = thresholds.get("very_high_missingness", 0.50)
    pct = df.isna().mean()
    for col, p in pct.items():
        if p >= very_high:
            warnings.append(f"'{col}' is {p*100:.0f}% missing — consider dropping or imputing carefully.")
        elif p >= high:
            warnings.append(f"'{col}' is {p*100:.0f}% missing — review before analysis.")
    return warnings


def check_near_zero_variance(df: pd.DataFrame, types: dict[str, str]) -> list[str]:
    return [f"'{col}' has only one unique value — likely uninformative."
            for col, t in types.items() if t == "constant"]


def check_binary_imbalance(binary_df: pd.DataFrame, thresholds: dict[str, float]) -> list[str]:
    if binary_df.empty:
        return []
    return [f"'{row['column']}' is severely imbalanced — may cause modelling issues."
            for _, row in binary_df.iterrows() if row.get("imbalanced", False)]


def check_high_cardinality(cat_df: pd.DataFrame) -> list[str]:
    if cat_df.empty:
        return []
    return [f"'{row['column']}' has {row['n_categories']} unique values — "
            "may need grouping or encoding decisions."
            for _, row in cat_df.iterrows() if row.get("high_cardinality", False)]


def check_future_dates(date_df: pd.DataFrame) -> list[str]:
    if date_df.empty:
        return []
    return [f"'{row['column']}' has {int(row['future_dates'])} future date(s) — "
            "verify data entry is correct."
            for _, row in date_df.iterrows() if row.get("future_dates", 0) > 0]


def check_duplicate_rows(dup_summary: dict[str, Any]) -> list[str]:
    warnings = []
    n = dup_summary.get("exact_duplicate_rows", 0)
    if n > 0:
        warnings.append(f"{n} exact duplicate row(s) found — deduplicate before analysis.")
    n_id = dup_summary.get("duplicate_id_rows", 0)
    if n_id > 0:
        id_cols = dup_summary.get("id_cols_checked", [])
        warnings.append(f"{n_id} rows share duplicate ID values in {id_cols} — "
                        "review for data integrity issues.")
    return warnings


def check_whitespace_case(cat_df: pd.DataFrame) -> list[str]:
    if cat_df.empty:
        return []
    warnings = []
    for _, row in cat_df.iterrows():
        if row.get("possible_whitespace", False):
            warnings.append(f"'{row['column']}' may have leading/trailing whitespace — consider str.strip().")
        if row.get("possible_case_inconsistency", False):
            warnings.append(f"'{row['column']}' may have mixed-case values — consider str.lower() or str.title().")
    return warnings


def collect_all_warnings(
    df: pd.DataFrame,
    types: dict[str, str],
    thresholds: dict[str, float],
    dup_summary: dict[str, Any],
    binary_df: pd.DataFrame,
    cat_df: pd.DataFrame,
    date_df: pd.DataFrame,
) -> list[str]:
    """Aggregate all custom-check warnings into one list."""
    w: list[str] = []
    w += check_high_missingness(df, thresholds)
    w += check_near_zero_variance(df, types)
    w += check_binary_imbalance(binary_df, thresholds)
    w += check_high_cardinality(cat_df)
    w += check_future_dates(date_df)
    w += check_duplicate_rows(dup_summary)
    w += check_whitespace_case(cat_df)
    return w


# ─────────────────────────────────────────────────────────────────────────────
# Decision prompts (formerly decision_prompts.py)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DecisionPrompt:
    """A single structured cleaning decision prompt."""
    dimension: str       # data-quality dimension (Completeness, Uniqueness, etc.)
    variable: str        # column name(s) or "dataset"
    issue: str           # what was detected
    question: str        # key question to answer before acting
    options: list[str]   # possible actions (not prescriptions)
    document: str        # what to record in the decision log


def _fmt_pct(p: float) -> str:
    return f"{p:.1f}%"


def prompts_from_missingness(
    miss_summary: dict[str, Any],
    thresholds: dict[str, float],
) -> list[DecisionPrompt]:
    prompts: list[DecisionPrompt] = []
    high      = thresholds.get("high_missingness", 0.20)
    very_high = thresholds.get("very_high_missingness", 0.50)

    for col in miss_summary.get("fully_missing", []):
        prompts.append(DecisionPrompt(
            dimension="Completeness", variable=col,
            issue=f"'{col}' is 100% missing — no values were recorded.",
            question="Was this column expected to contain data? Is it a data-collection failure, or was it never applicable?",
            options=[
                "Exclude from analysis (document reason).",
                "Check whether the column name is correct (possible import error).",
                "If data were collected on paper, check whether values need to be entered.",
            ],
            document="Why the column is empty; whether it was excluded and from which analyses.",
        ))

    for col in miss_summary.get("very_high_missing", []):
        pct = miss_summary["top_missing"].get(col, very_high * 100)
        prompts.append(DecisionPrompt(
            dimension="Completeness", variable=col,
            issue=f"'{col}' has {_fmt_pct(pct)} missing values (very high threshold: >{very_high*100:.0f}%).",
            question="Is this variable critical for the analysis? Does missingness differ by outcome or subgroup?",
            options=[
                "Exclude the variable from analysis if not critical.",
                "Check missingness by outcome group before deciding on imputation.",
                "Use multiple imputation if missingness is MAR and variable is important.",
                "Add a missingness indicator flag (binom: 0/1) to capture its potential informative nature.",
            ],
            document="% missing; mechanism assumption (MCAR/MAR/MNAR); strategy chosen; rows/columns excluded.",
        ))

    for col in miss_summary.get("high_missing", []):
        if col in miss_summary.get("very_high_missing", []):
            continue
        pct = miss_summary["top_missing"].get(col, high * 100)
        prompts.append(DecisionPrompt(
            dimension="Completeness", variable=col,
            issue=f"'{col}' has {_fmt_pct(pct)} missing values (above {high*100:.0f}% threshold).",
            question="Why is this variable missing? Is missingness random or related to outcome/exposure?",
            options=[
                "Check missingness by outcome group.",
                "Use complete-case analysis if missingness is small and plausibly MCAR.",
                "Consider imputation if missingness is MAR and variable is a key covariate.",
                "Document assumption about missing mechanism.",
            ],
            document="% missing; mechanism assumption; handling strategy.",
        ))

    return prompts


def prompts_from_duplicates(dup_summary: dict[str, Any]) -> list[DecisionPrompt]:
    prompts: list[DecisionPrompt] = []
    n_exact = dup_summary.get("exact_duplicate_rows", 0)
    if n_exact > 0:
        prompts.append(DecisionPrompt(
            dimension="Uniqueness", variable="dataset",
            issue=f"{n_exact:,} exact duplicate row(s) found (every column is identical).",
            question="Are these accidental duplicates (e.g. from an export or merge error), or valid repeated records?",
            options=[
                "If accidental: remove with drop_duplicates(keep='first') and document.",
                "If valid repeated records: define the correct unit of observation and composite key.",
                "Inspect a sample of duplicate rows before deciding.",
            ],
            document="Number of rows removed; how you confirmed they were accidental; row count before and after.",
        ))
    n_dup_ids = dup_summary.get("duplicate_id_rows", 0)
    if n_dup_ids > 0:
        id_cols = dup_summary.get("id_cols_checked", [])
        prompts.append(DecisionPrompt(
            dimension="Uniqueness", variable=str(id_cols),
            issue=f"{n_dup_ids:,} rows share duplicate values in ID column(s) {id_cols}.",
            question="Is one row per ID expected, or are repeated visits/events valid?",
            options=[
                "If one row per ID is expected: investigate source; remove or merge duplicates with documented logic.",
                "If repeated measures are expected: define composite key (ID + visit/date) and re-check.",
                "If uncertainty: keep all rows and flag duplicates with a binary column.",
            ],
            document="Unit of observation decision; composite key used; rows removed or kept; reason.",
        ))
    return prompts


def prompts_from_outliers(cont_df: pd.DataFrame) -> list[DecisionPrompt]:
    prompts: list[DecisionPrompt] = []
    if cont_df.empty:
        return prompts
    for _, row in cont_df.iterrows():
        n_out = int(row.get("n_outliers_iqr", 0))
        if n_out == 0:
            continue
        col = row["column"]
        prompts.append(DecisionPrompt(
            dimension="Accuracy", variable=col,
            issue=f"'{col}' has {n_out} IQR-flagged outlier(s). Range: [{row['min']} – {row['max']}]; IQR: {row['iqr']}.",
            question="Are these values impossible (data-entry error) or plausible extremes? Can you check the source record?",
            options=[
                "If impossible: set to missing and document the threshold.",
                "If plausible extreme: keep; add an IQR flag column; plan sensitivity analysis.",
                "If uncertain: flag only; review against source data before acting.",
                "If many outliers: consider log transformation rather than removal.",
            ],
            document="Threshold used; n values affected; whether reviewed against source; action taken; sensitivity plan.",
        ))
    return prompts


def prompts_from_binary(bin_df: pd.DataFrame, thresholds: dict[str, float]) -> list[DecisionPrompt]:
    prompts: list[DecisionPrompt] = []
    if bin_df.empty:
        return prompts
    for _, row in bin_df.iterrows():
        if not row.get("imbalanced", False):
            continue
        prompts.append(DecisionPrompt(
            dimension="Accuracy", variable=row["column"],
            issue=f"'{row['column']}' is severely imbalanced (≥{thresholds.get('imbalance_cutoff', 0.95)*100:.0f}%). "
                  f"Values: {row['values']}, counts: {row['counts']}.",
            question="Is this imbalance real (e.g. rare disease in a population sample), or a data-collection issue?",
            options=[
                "If real: keep as-is; note imbalance in results; use appropriate model.",
                "If a data-collection issue: check source; contact data provider.",
                "If used as an outcome in a model: consider class-weighted loss or resampling.",
            ],
            document="Imbalance ratio; whether it reflects true population prevalence or a sampling artifact.",
        ))
    return prompts


def prompts_from_categoricals(cat_df: pd.DataFrame) -> list[DecisionPrompt]:
    prompts: list[DecisionPrompt] = []
    if cat_df.empty:
        return prompts
    for _, row in cat_df.iterrows():
        col = row["column"]
        if row.get("possible_whitespace", False) or row.get("possible_case_inconsistency", False):
            issues = []
            if row.get("possible_whitespace"):
                issues.append("leading/trailing whitespace")
            if row.get("possible_case_inconsistency"):
                issues.append("mixed case (e.g. 'Male' and 'male')")
            prompts.append(DecisionPrompt(
                dimension="Validity", variable=col,
                issue=f"'{col}' may have label inconsistencies: {' and '.join(issues)}.",
                question="Do values that differ only by case or whitespace represent the same category?",
                options=[
                    "Apply str.strip() and a case standard (str.lower(), str.title(), or str.upper()).",
                    "Use a category mapping file (config/category_mapping.yaml) for explicit control.",
                    "Check value_counts() before and after to confirm the result.",
                ],
                document="Mapping applied; values changed; before/after unique value counts.",
            ))
        if row.get("high_cardinality", False):
            prompts.append(DecisionPrompt(
                dimension="Validity", variable=col,
                issue=f"'{col}' has {int(row['n_categories'])} unique values (high cardinality).",
                question="Is this a free-text field, an ID-like column, or a categorical variable that needs grouping?",
                options=[
                    "If free text: exclude from standard analysis; consider NLP workflow separately.",
                    "If groupable: define a mapping to a smaller set of meaningful categories.",
                    "If ID-like: mark as id in type_overrides config.",
                    "If needed as-is: use embedding or hashing for ML; treat as-is for descriptive analysis.",
                ],
                document="Decision on how to handle; any grouping mapping applied.",
            ))
        if int(row.get("n_rare", 0)) > 0:
            prompts.append(DecisionPrompt(
                dimension="Validity", variable=col,
                issue=f"'{col}' has {int(row['n_rare'])} rare category/categories (< 1% of rows).",
                question="Are these rare categories meaningful subgroups, typos, or analytically uninformative?",
                options=[
                    "Keep if meaningful (e.g. a rare diagnosis): note sparsity in results.",
                    "Combine into 'Other' only if analytically justified and not hiding real variation.",
                    "Set to missing if they represent data-entry errors.",
                ],
                document="Which categories were kept, combined, or set missing; rationale; n affected.",
            ))
    return prompts


def prompts_from_dates(date_df: pd.DataFrame) -> list[DecisionPrompt]:
    prompts: list[DecisionPrompt] = []
    if date_df.empty:
        return prompts
    for _, row in date_df.iterrows():
        n_future = int(row.get("future_dates", 0))
        if n_future > 0:
            prompts.append(DecisionPrompt(
                dimension="Timeliness", variable=row["column"],
                issue=f"'{row['column']}' has {n_future} date(s) after today's date.",
                question="Are future dates valid for this field (e.g. scheduled appointments), or data-entry errors?",
                options=[
                    "If impossible (e.g. date of birth): set to missing; check source.",
                    "If possibly valid (e.g. scheduled appointment): keep; note in results.",
                    "Check whether the values use a different date format (DD/MM vs MM/DD confusion).",
                ],
                document="N future dates found; field type; action taken; rows affected.",
            ))
    return prompts


def prompts_from_schema_issues(schema_issues: dict[str, list[str]] | None) -> list[DecisionPrompt]:
    if not schema_issues:
        return []
    prompts: list[DecisionPrompt] = []
    for col_msg in schema_issues.get("allowed_value_violations", []):
        prompts.append(DecisionPrompt(
            dimension="Validity", variable="(see message)", issue=col_msg,
            question="Are these values synonyms (apply mapping), typos (correct), or genuinely unknown (set missing)?",
            options=[
                "Apply category_mapping.yaml to standardise synonyms.",
                "Set confirmed errors to missing and document.",
                "Update allowed_values in schema if the value is legitimately valid.",
            ],
            document="Values found; action per value; mapping file used.",
        ))
    for col_msg in schema_issues.get("range_violations", []):
        prompts.append(DecisionPrompt(
            dimension="Validity", variable="(see message)", issue=col_msg,
            question="Are these values impossible (set missing) or plausible extremes (keep and flag)?",
            options=[
                "If impossible: set to missing; document threshold.",
                "If plausible: keep; widen schema range; add to sensitivity analysis.",
            ],
            document="Threshold used; n values affected; action taken.",
        ))
    for col_msg in schema_issues.get("uniqueness_violations", []):
        prompts.append(DecisionPrompt(
            dimension="Uniqueness", variable="(see message)", issue=col_msg,
            question="Is uniqueness truly expected? Are these accidental duplicates or valid repeated records?",
            options=[
                "If accidental: deduplicate with documented logic.",
                "If valid: update schema (set unique: false); define composite key.",
            ],
            document="Unit of observation decision; rows removed or kept.",
        ))
    return prompts


def collect_all_prompts(
    miss_summary: dict[str, Any],
    dup_summary: dict[str, Any],
    cont_df: pd.DataFrame,
    bin_df: pd.DataFrame,
    cat_df: pd.DataFrame,
    date_df: pd.DataFrame,
    schema_issues: dict[str, list[str]] | None,
    thresholds: dict[str, float],
) -> list[DecisionPrompt]:
    """Return all decision prompts for the current dataset."""
    prompts: list[DecisionPrompt] = []
    prompts += prompts_from_missingness(miss_summary, thresholds)
    prompts += prompts_from_duplicates(dup_summary)
    prompts += prompts_from_outliers(cont_df)
    prompts += prompts_from_binary(bin_df, thresholds)
    prompts += prompts_from_categoricals(cat_df)
    prompts += prompts_from_dates(date_df)
    prompts += prompts_from_schema_issues(schema_issues)
    return prompts
