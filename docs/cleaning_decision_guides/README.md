# From QC Report to Cleaning Decisions

> **The reporter tells you what may be wrong. It does not automatically decide what to change.**

A QC report is a map of the terrain. You still have to decide which path to take. The right cleaning decisions depend on your analysis purpose, your data source, and what the missingness or outliers actually mean in context.

This guide helps you move from "the report flagged this" to "here is what I decided and why".

---

## The 10-step decision workflow

```
Step 1  │ Define your analysis purpose.
        │   What question are you answering? Descriptive? Regression? Prediction?
        │
Step 2  │ Define the unit of observation.
        │   One row per person? Per visit? Per transaction?
        │
Step 3  │ Identify critical variables.
        │   Which columns are outcome, exposure, or essential covariates?
        │
Step 4  │ Profile the data.
        │   Run the QC reporter. Read the warnings.
        │
Step 5  │ Classify issues by data-quality dimension.
        │   Completeness / Uniqueness / Validity / Consistency / Accuracy / Timeliness
        │
Step 6  │ Choose a cleaning action for each issue.
        │   Use the decision guides below.
        │
Step 7  │ Document your rationale.
        │   Use the cleaning decision log template.
        │
Step 8  │ Apply cleaning in a reproducible script.
        │   Never edit the raw file manually.
        │
Step 9  │ Re-run the QC reporter on the cleaned data.
        │
Step 10 │ Compare before vs after.
        │   Did the issue resolve? Did anything new appear?
```

---

## Data-quality dimensions

Every issue detected by the reporter falls into one of these categories.

| Dimension | What it means | Example issues |
|---|---|---|
| **Completeness** | Required values are present | High missingness, fully empty column |
| **Uniqueness** | Records are not unintentionally duplicated | Duplicate rows, duplicate IDs |
| **Validity** | Values conform to expected type, range, and format | Negative age, BMI of 300, disallowed category |
| **Consistency** | Related fields agree with each other | End date before start date, impossible age given birth year |
| **Accuracy** | Values reflect what was intended to be measured | Outlier from data-entry error vs genuine extreme |
| **Timeliness** | Dates are appropriate and current | Future assessment dates, data from wrong period |

---

## Decision matrix

| Issue | Ask first | Usually safe action | Risky action | Document |
|---|---|---|---|---|
| High missingness | Why is it missing? Is it MCAR, MAR, or MNAR? | Standardise missing codes; flag; note | Blind mean/mode imputation | Missing mechanism assumption |
| Exact duplicate rows | Are these accidental, or repeated measures? | Remove after confirming accident | Removing valid repeated visits | Rows removed and reason |
| Duplicate IDs | Is one row per ID expected? | Check composite key (ID + visit) | Keeping without explanation | Unit of observation decision |
| Outlier flagged | Data-entry error, measurement error, or real extreme? | Flag; review against source | Automatic deletion | Whether kept, capped, removed |
| Invalid range | Is the value logically impossible? | Set missing or correct from source | Keeping impossible values | Threshold used, rows affected |
| Category inconsistency | Same category written differently? | Trim whitespace; standardise case; apply mapping | Ad hoc manual recoding | Mapping dictionary used |
| Rare category | Too sparse for modelling, or meaningful minority? | Combine only with explicit rationale | Hiding a meaningful subgroup | Combination rule and n affected |
| Future date | Is a future date possible for this field? | Check context; correct or set missing | Silently coercing | Field type and action |
| Free text / high cardinality | Is this field needed? Sensitive? | Suppress examples; handle separately | Printing raw values in reports | What was excluded and why |

---

## Detailed guides

Work through these in order when you encounter each type of issue.

| Guide | Topic |
|---|---|
| [01 — Cleaning principles](01_cleaning_principles.md) | Core rules before you start |
| [02 — Missing values](02_missing_values.md) | Missingness, imputation, complete-case |
| [03 — Duplicates and units](03_duplicates_and_units.md) | Rows, IDs, repeated measures |
| [04 — Outliers](04_outliers.md) | Error vs real extreme, flagging, action options |
| [05 — Categorical variables](05_categorical_variables.md) | Labels, mapping, rare categories |
| [06 — Dates and time](06_dates_and_time.md) | Parsing, ranges, derived variables |
| [07 — Schema and validation](07_schema_and_validation.md) | Expected structure, validation checks |
| [08 — Analysis-specific cleaning](08_analysis_specific_cleaning.md) | Decisions that depend on analysis purpose |
| [09 — Cleaning decision log](09_cleaning_decision_log.md) | How to record every decision |

---

## Quick example

**QC report warns:**
> `bmi` has 24% missing values and 3 IQR outliers.

**Analyst asks:**
1. Is BMI critical for my analysis, or is it an optional covariate?
2. Is missingness likely random, or do sicker participants have missing BMI?
3. Are the outliers plausible extreme values (BMI 45) or data-entry errors (BMI 450)?

**Analyst decides:**
- Missingness: check by outcome group; if not differential, use complete-case for main analysis with sensitivity using imputation.
- Outlier at BMI = 88: review source data; plausibly valid; keep but flag in sensitivity analysis.

**Cleaning log entry:**

| Variable | Issue | Decision | Rationale |
|---|---|---|---|
| bmi | 24% missing | Complete-case; sensitivity with mice | Missingness does not differ by outcome group |
| bmi | Outlier (n=1, value=88) | Keep; flag for sensitivity | Within physiological range; no source error found |

---

## Related config templates

- [`config/cleaning_rules.example.yaml`](../../config/cleaning_rules.example.yaml) — per-variable cleaning rules
- [`config/category_mapping.example.yaml`](../../config/category_mapping.example.yaml) — category label standardisation
- [`config/missing_codes.example.yaml`](../../config/missing_codes.example.yaml) — what counts as missing in your dataset

## Decision log template

- [`docs/templates/cleaning_decision_log_template.md`](../templates/cleaning_decision_log_template.md)
