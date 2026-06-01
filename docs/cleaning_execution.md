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
5. Writes a timestamped cleaning log, manager summary, run manifest, and validation report
6. Saves the cleaned data to a new file — **never overwriting the raw input**

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

# 3. Full run with after-report and visual flowchart
python python/run_cleaner.py \
  --input  data/raw/my_data.csv \
  --rules  config/cleaning_rules.example.yaml \
  --output data/processed/my_data_cleaned.csv \
  --after-report \
  --flowchart

# 4. Rules that drop rows also need --confirm-destructive
python python/run_cleaner.py \
  --input  data/raw/my_data.csv \
  --rules  config/cleaning_rules.example.yaml \
  --output data/processed/my_data_cleaned.csv \
  --confirm-destructive
```

---

## Command-line flags

| Flag | Default | Purpose |
|---|---|---|
| `--input` | required | Path to the raw data file |
| `--rules` | required | Path to the YAML rules file |
| `--output` | auto-generated | Where to write the cleaned file |
| `--dry-run` | off | Simulate without writing output |
| `--confirm-destructive` | off | Required when rules drop rows or columns and `--dry-run` is not set |
| `--log-dir` | `reports/cleaning_logs/` | Where to write the cleaning log, summary, and run manifest |
| `--validation-dir` | `reports/validation_reports/` | Where to write the validation report |
| `--after-report` | off | Run the QC reporter on the cleaned file immediately after |
| `--flowchart` | off | Generate a Mermaid flowchart alongside the cleaning log |

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
cleaning log and validation report are still written so you can review them.

**Destructive actions require two explicit opt-ins.** Actions that drop rows or
columns require both `allow_row_drop: true` in the rules file step **and**
`--confirm-destructive` on the CLI. Forgetting either one aborts the run.

---

## The dry-run workflow

Always start with a dry run:

```bash
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
  my_data_cleaned.csv                              ← cleaned dataset

reports/cleaning_logs/
  my_rules_cleaning_log_YYYYMMDD_HHMMSS.md        ← full step-by-step log
  my_rules_summary_YYYYMMDD_HHMMSS.md             ← non-technical summary (rows in/out, checks)
  my_rules_YYYYMMDD_HHMMSS_manifest.yaml          ← machine-readable run record
  my_rules_YYYYMMDD_HHMMSS_flow.md                ← Mermaid flowchart (if --flowchart)
  my_rules_YYYYMMDD_HHMMSS_flow.mmd               ← raw Mermaid diagram text

reports/validation_reports/
  my_rules_validation_YYYYMMDD_HHMMSS.md          ← pass/fail validation report
```

All report directories are git-ignored. Commit your cleaned CSV if you want it
in version control.

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

You can call the pipeline directly from Python:

```python
import sys
sys.path.insert(0, "python")  # from the repo root

import pandas as pd
from toolkit.cleaning import run_cleaning_pipeline
from toolkit.config import load_rules

df = pd.read_csv("data/raw/my_data.csv")
rules = load_rules("config/cleaning_rules.example.yaml")

cleaned_df, cleaning_log, validation_report = run_cleaning_pipeline(
    df,
    rules,
    input_path="data/raw/my_data.csv",
    output_path="data/processed/my_data_cleaned.csv",
    rules_path="config/cleaning_rules.example.yaml",
    dry_run=False,
    flowchart=True,
)
```

The function returns:
- `cleaned_df` — the cleaned DataFrame (the original unchanged if `dry_run=True`)
- `cleaning_log` — the full cleaning log as a markdown string
- `validation_report` — the validation report as a markdown string

---

## Interpreting the cleaning log

The cleaning log has these sections:

### Run Metadata
Timestamp, dry-run flag, input/output/rules paths, git commit, before/after row
and column counts.

### Cleaning Flowchart (if `--flowchart` was used)
Embedded Mermaid diagram rendered by GitHub, GitLab, Quarto, and MkDocs.

### Step Summary
A table with one row per step: name, action, decision status, rows Δ, cells changed, warning count.

### Step Impact Summary
A richer table: rows before/after, rows removed, columns before/after, cells changed, warnings.
Always present, even without `--flowchart`.

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

The validation report summarises the pass/fail checks from the `validation:`
block of your rules file.

A **pass** means the cleaned dataset conforms to your declared expectation.

A **fail** flags a discrepancy for review. By default, validation failures do
**not** stop the pipeline — they are advisory.

### Fail-fast mode

To stop the pipeline and prevent output being written when validation fails, set:

```yaml
validation:
  fail_on_error: true
  required_columns: [participant_id, age]
  unique_keys: [[participant_id]]
```

| Mode | Behaviour |
|---|---|
| `fail_on_error: false` (default) | Validation failures are logged; cleaned file is still written |
| `fail_on_error: true` | Validation failures abort the run; cleaned file is **not** written |

Use `fail_on_error: true` for production pipelines or any run where you need
to guarantee output quality.

---

## Common issues

| Problem | Likely cause | Fix |
|---|---|---|
| `Rules file validation failed: 'version' must be 1` | Missing `version: 1` in YAML | Add it as the first key |
| `requires 'allow_row_drop: true'` | Destructive step without guard | Add `allow_row_drop: true` to that step |
| `contains row or column drops` (CLI error) | Missing `--confirm-destructive` | Add the flag, or use `--dry-run` first |
| `Output path resolves to the same file as input` | Output path same as input | Choose a different output path |
| `Column 'X' not found` | Column renamed in an earlier step | Check step order; use post-rename column names |
| Step silently skips | Action name typo | Check against `SUPPORTED_ACTIONS` in `toolkit/config.py` |

---

## Related docs

- [Cleaning Rules Reference](cleaning_rules_reference.md) — all actions, YAML syntax, risk levels
- [Before/After Validation](before_after_validation.md) — understanding snapshots and validation checks
- [Cleaning Decision Guides](cleaning_decision_guides/README.md) — the workflow before you write any rules
- [YAML for beginners](yaml_for_beginners.md) — how to edit cleaning rules safely
