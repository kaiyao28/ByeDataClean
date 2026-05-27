# Troubleshooting

---

## Python — module not found

**`ModuleNotFoundError: No module named 'seaborn'`**

Install it: `pip install seaborn`.
Or use `--input` with a local file instead of `--example-dataset`.

**`ModuleNotFoundError: No module named 'ydata_profiling'`**

Install it: `pip install ydata-profiling`.
Or use `--mode quick` to skip the HTML report.

**`ModuleNotFoundError: No module named 'toolkit'`**

Run the scripts from the repository root:

```bash
# From the repo root:
python python/run_reporter.py --input data/raw/my_data.csv
```

Do not `cd` into `python/` first. The `conftest.py` at the root adds `python/` to `sys.path` for test runs.

---

## Python — file and path errors

**`FileNotFoundError: Input file not found`**

Check the path. Run from the repo root. Use relative paths from the root:

```bash
python python/run_reporter.py --input data/raw/my_data.csv
# NOT: python python/run_reporter.py --input my_data.csv
```

**`ValueError: Requested columns not found`**

Column names in `--columns` are case-sensitive and must match the file exactly. Run without `--columns` first to see all column names in the report.

**`SystemExit: Output path resolves to the same file as input`**

The cleaner will not write cleaned output to the same file as the raw input. Choose a different output path:

```bash
python python/run_cleaner.py \
  --input  data/raw/my_data.csv \
  --output data/processed/my_data_cleaned.csv   # different directory
```

---

## Python — example datasets

**Example dataset fails with a network error**

seaborn downloads datasets on first use and caches them in `~/seaborn-data/`. If you have no internet access and no cache, use `--input` with a local file instead.

**`ModuleNotFoundError: No module named 'sklearn'`** (for iris dataset)

Install `scikit-learn`: `pip install scikit-learn`. Or use `seaborn` for iris: `pip install seaborn`.

---

## Python — cleaning executor

**`This rules file contains row or column drops` error**

The cleaner detected a destructive rule and requires explicit confirmation:

```bash
python python/run_cleaner.py \
  --input  data/raw/my_data.csv \
  --rules  config/my_rules.yaml \
  --dry-run                   # preview first
# then:
python python/run_cleaner.py \
  --input  data/raw/my_data.csv \
  --rules  config/my_rules.yaml \
  --output data/processed/cleaned.csv \
  --confirm-destructive       # explicit confirmation
```

**Rules file validation errors**

Check your YAML syntax. Common issues:
- Missing `version: 1` at the top
- Each rule missing `step` or `action`
- `allow_row_drop: true` not set when using `remove_exact_duplicates`

---

## Type detection

**Date column not detected as a date**

Add the column name to `date_columns` in your config:

```yaml
date_columns:
  - assessment_date
  - baseline_date
```

Or pass a type override:

```yaml
type_overrides:
  assessment_date: date
```

**Numeric ID column detected as continuous**

Add it to `id_cols`:

```yaml
id_cols:
  - participant_id
  - site_id
```

**Low-cardinality numeric column detected as continuous**

Override the type:

```yaml
type_overrides:
  visit_number: categorical
  wave: categorical
```

---

## R

**`Error in library(skimr)`: package not found**

Install from CRAN: `install.packages("skimr")`

**`Error: 'palmerpenguins' is not available`**

Install it: `install.packages("palmerpenguins")`

---

## VS Code

**Script not found or Python not resolving**

Make sure your VS Code Python interpreter is set to the `.venv` interpreter:

1. Open the Command Palette (`Cmd/Ctrl + Shift + P`)
2. Select **Python: Select Interpreter**
3. Choose `.venv/bin/python`

---

## Back to main docs

← [README](../README.md) · [Installation](installation.md) · [Usage guide](usage.md)
