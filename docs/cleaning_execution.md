# Cleaning Execution Guide

This guide covers how to run the config-driven cleaning executor after you have
written your cleaning rules YAML.

---

## Overview

The cleaning executor is a Python script that:

1. Reads a raw data file (CSV, TSV, Excel, Parquet)
2. Loads a YAML rules file describing what to clean and in what order
3. Applies each step in sequence, logging every change
4. Validates the cleaned dataset against your declared expectations
5. Writes a timestamped cleaning log and validation report
6. Saves the cleaned data to a new file (never overwriting the raw input)

The executor does **not** make decisions for you. It applies only what you have
explicitly declared in the rules file.

---

## Quick start

```bash
# 1. Dry run — simulate cleaning without writing output
python python/run_cleaner.py \
  --input  data/raw/my_data.csv \
  --rules  config/cleaning_rules.example.yaml \
  --dry-run

# 2. Full clean run
python python/run_cleaner.py \
  --input  data/raw/my_data.csv \
  --rules  config/cleaning_rules.example.yaml \
  --output data/processed/my_data_cleaned.csv

# 3. Clean + auto-run the QC reporter on the cleaned file
python python/run_cleaner.py \
  --input  data/raw/my_data.csv \
  --rules  config/cleaning_rules.example.yaml \
  --output data/processed/my_data_cleaned.csv \
  --after-report
```

---

## Command-line flags

| Flag | Default | Purpose |
|---|---|---|
| `--input` | required | Path to the raw data file |
| `--rules` | required | Path to the YAML rules file |
| `--output` | auto-generated | Where to write the cleaned file |
| `--dry-run` | off | Simulate without writing output |
| `--log-dir` | `reports/cleaning_logs/` | Where to write the cleaning log |
| `--validation-dir` | `reports/validation_reports/` | Where to write the validation report |
| `--after-report` | off | Run the QC reporter on the cleaned file immediately after |

---

## Input formats supported

| Extension | Read method |
|---|---|
| `.csv`, `.txt` | `pd.read_csv` |
| `.tsv` | `pd.read_csv(sep="\t")` |
| `.xlsx`, `.xls` | `pd.read_excel` |
| `.parquet` | `pd.read_parquet` |

Output is written as CSV by default, or Parquet if the output path ends in `.parquet`.

---

## Safety guarantees

**Raw data is never overwritten.** If `--output` resolves to the same path as
`--input` (including via symlinks), the executor aborts before touching any data.

**Dry-run is always safe.** With `--dry-run`, no data file is written. The
cleaning log and validation report are still written (they are always useful for
review even in dry-run mode).

**Destructive actions require explicit opt-in.** Actions that drop rows or
columns will not run unless the corresponding guard key is present in the rules
file. The executor validates this before touching any data.

---

## The dry-run workflow

Always start with a dry run:

```
python python/run_cleaner.py \
  --input data/raw/my_data.csv \
  --rules config/cleaning_rules.example.yaml \
  --dry-run
```

This will:
- Print each step with `(DRY RUN)` marker
- Count how many cells/rows would be changed per step
- Write a cleaning log to `reports/cleaning_logs/` showing what *would* happen
- Run validation on the current (unmodified) data and report any issues

Review the log, adjust your rules, then re-run without `--dry-run`.

---

## Output files

After a full clean run you get:

```
data/processed/
  my_data_cleaned.csv           ← cleaned dataset

reports/cleaning_logs/
  my_rules_cleaning_log_YYYYMMDD_HHMMSS.md   ← full step-by-step log

reports/validation_reports/
  my_rules_validation_YYYYMMDD_HHMMSS.md     ← pass/fail validation report
```

Both report directories are git-ignored (they contain run-specific outputs).
Commit your cleaned CSV if you want it in version control.

---

## Using a cleaning profile

Profiles are pre-built YAML rules for common analysis types:

```bash
python python/run_cleaner.py \
  --input  data/raw/my_data.csv \
  --rules  config/cleaning_profiles/descriptive_analysis.yaml \
  --output data/processed/my_data_descriptive.csv
```

Available profiles:

| Profile | Conservative? | Row drops? | Notes |
|---|---|---|---|
| `descriptive_analysis.yaml` | ✓ Very | No | Flag only, never remove |
| `regression_analysis.yaml` | ✓ | No | No outcome-informed cleaning |
| `machine_learning.yaml` | Moderate | Duplicates only | No imputation, no scaling |
| `longitudinal_analysis.yaml` | Moderate | No | Composite keys, duplicate IDs valid |

---

## Python API

You can also call the pipeline directly from Python:

```python
import pandas as pd
from data_cleaning.cleaner import run_cleaning_pipeline
from data_cleaning.config import load_rules

df = pd.read_csv("data/raw/my_data.csv")
rules = load_rules("config/cleaning_rules.example.yaml")

cleaned_df, cleaning_log, validation_report = run_cleaning_pipeline(
    df,
    rules,
    input_path="data/raw/my_data.csv",
    output_path="data/processed/my_data_cleaned.csv",
    rules_path="config/cleaning_rules.example.yaml",
    dry_run=False,
)
```

The function returns:
- `cleaned_df` — the cleaned DataFrame (or the original if `dry_run=True`)
- `cleaning_log` — the full cleaning log as a markdown string
- `validation_report` — the validation report as a markdown string

---

## Interpreting the cleaning log

The cleaning log has these sections:

### Run Metadata
Timestamp, dry-run flag, input/output/rules paths, git commit, before/after row
and column counts.

### Step Summary
A table with one row per step: name, action, rows Δ, cells changed, warning count.

### Detailed Step Notes
Per-step breakdown with exact details (e.g. which columns renamed, how many
values replaced) and any warnings (e.g. unrecognised category values).

### Validation Summary
Pass/fail for each validation check declared in the `validation:` block.

### Before / After Summary
A markdown table comparing row count, column count, duplicate count, and total
missing cell count before and after cleaning.

---

## Interpreting the validation report

The validation report is a standalone document summarising only the
pass/fail checks from the `validation:` section of your rules file.

A **pass** means the cleaned dataset conforms to your declared expectation.  
A **fail** flags a discrepancy for review — it does not stop the pipeline.

Validation failures do **not** modify data. They are observations, not fixes.

---

## Common issues

| Problem | Likely cause | Fix |
|---|---|---|
| `Rules file validation failed: 'version' must be 1` | Missing `version: 1` in YAML | Add it as the first key |
| `requires 'allow_row_drop: true'` | Destructive step without guard | Add `allow_row_drop: true` to that step |
| `Output path resolves to the same file as input` | Output path same as input | Choose a different output path |
| `Column 'X' not found` | Column renamed in an earlier step | Check step order; use post-rename column names |
| Step silently skips | Action name typo | Check against `SUPPORTED_ACTIONS` in `config.py` |

---

## Related docs

- [Cleaning Rules Reference](cleaning_rules_reference.md) — all actions, YAML syntax, risk levels
- [Before/After Validation](before_after_validation.md) — understanding snapshots and validation checks
- [Cleaning Decision Guides](cleaning_decision_guides/README.md) — the workflow before you write any rules
