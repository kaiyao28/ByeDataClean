# Usage Guide

Extended examples and edge cases. For quick start, see the main [README](../README.md).

---

## Python reporter — extended examples

### Run with all columns, ID check, and schema validation

```bash
python python/run_reporter.py \
  --input data/raw/my_data.csv \
  --columns age sex bmi diagnosis assessment_date \
  --id-cols participant_id \
  --schema config/schema.example.yaml \
  --mode quick
```

### Run with a config file that sets everything

```bash
python python/run_reporter.py --config config/reporter_config.yaml
```

This is the preferred approach for reproducible runs. The config file captures every setting in one place. See [`config/reporter_config.example.yaml`](../config/reporter_config.example.yaml) for all fields.

### Override a config file with a CLI flag

CLI flags always take priority over the config file:

```bash
# Use config for everything, but override the mode
python python/run_reporter.py \
  --config config/reporter_config.yaml \
  --mode both
```

### Write the report to a custom directory

```bash
python python/run_reporter.py \
  --input data/raw/my_data.csv \
  --output-dir reports/project_x_qc
```

### Use a type override for a misdetected column

If a column like `visit_number` (values: 1, 2, 3, 4, 5) is being treated as
continuous when you want it treated as categorical, add this to your config:

```yaml
type_overrides:
  visit_number: categorical
```

Or pass the config file. There is no CLI flag for individual type overrides —
the config file is the right place for them.

### Force a column to be treated as a date

If a date column is stored as a string and not auto-detected:

```yaml
date_columns:
  - assessment_date
  - discharge_date
```

### Run on a TSV or Excel file

```bash
python python/run_reporter.py --input data/raw/my_data.tsv
python python/run_reporter.py --input data/raw/my_data.xlsx
python python/run_reporter.py --input data/raw/my_data.parquet
```

File format is detected from the extension automatically.

---

## Python reporter — what the quick report contains

The markdown report covers these sections in order:

1. **Report metadata** — timestamp, input source, selected columns, ID columns, mode, optional package availability
2. **Dataset overview** — row count, column count, memory usage, inferred type distribution
3. **Column inventory** — per-column table of inferred type, missing count, missing %, unique count
4. **Missingness summary** — top missing columns, fully missing, high-missingness flags
5. **Duplication summary** — exact duplicate rows, duplicate ID combinations
6. **Continuous variable summary** — n, missing, mean, SD, median, IQR, min, max, IQR-outlier count
7. **Binary variable summary** — value counts, percentages, imbalance flag
8. **Categorical variable summary** — n categories, high-cardinality flag, rare category count, whitespace/case warnings
9. **Date variable summary** — min date, max date, missing count, future-date count
10. **Schema checks** — (if schema provided) required-column violations, allowed-value violations, range violations, uniqueness violations
11. **Suggested cleaning actions** — bulleted list of warnings generated from all of the above

---

## Python reporter — type inference logic

The reporter infers one of these types per column:

| Inferred type | Rule |
|---|---|
| `empty` | All values are missing |
| `constant` | One unique non-missing value |
| `id` | Listed in `--id-cols` |
| `date` | Datetime dtype, or listed in `date_columns` config |
| `binary` | Exactly 2 unique non-missing values (numeric or string) |
| `continuous` | Numeric with > 10 unique non-missing values |
| `categorical_or_ordinal` | Numeric with 3–10 unique non-missing values |
| `categorical` | String with ≤ `high_cardinality_cutoff` unique values (default: 50) |
| `text_high_cardinality` | String with > `high_cardinality_cutoff` unique values |

Override any column with `type_overrides` in the config.

---

## R reporter — extended examples

### With columns and ID columns

```bash
Rscript r/run_reporter.R \
  --input data/raw/my_data.csv \
  --columns age,sex,bmi,diagnosis \
  --id-cols participant_id
```

Note: for R, multiple column values are passed as a comma-separated string
(not space-separated as in Python), e.g. `--columns age,sex,bmi`.

### Full HTML report

```bash
Rscript r/run_reporter.R \
  --input data/raw/my_data.csv \
  --mode both
```

Requires `DataExplorer`: `install.packages("DataExplorer")`.

### With a config file

```bash
Rscript r/run_reporter.R --config config/reporter_config.example.yaml
```

---

## SQL cookbook — extended examples

### Checking missingness across many columns

Open `02_missingness_checks.sql` and extend the UNION ALL block:

```sql
SELECT 'age' AS col, COUNT(*), SUM(CASE WHEN age IS NULL THEN 1 ELSE 0 END),
       ROUND(100.0 * SUM(CASE WHEN age IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2)
FROM my_table
UNION ALL
SELECT 'bmi', COUNT(*), SUM(CASE WHEN bmi IS NULL THEN 1 ELSE 0 END),
       ROUND(100.0 * SUM(CASE WHEN bmi IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2)
FROM my_table;
```

### DuckDB: inspect a CSV without loading it

```bash
duckdb -c "SUMMARIZE SELECT * FROM 'data/raw/my_data.csv';"
```

This gives you min, max, mean, nulls, and unique counts for every column in one command — useful as a first look before running the Python reporter.

### Finding duplicate participant + visit combinations

```sql
-- From 08_id_integrity_checks.sql
SELECT participant_id, visit_number, COUNT(*) AS n_rows
FROM my_table
GROUP BY participant_id, visit_number
HAVING COUNT(*) > 1
ORDER BY n_rows DESC;
```

---

## Running the edge-case test data generator

For development and testing, `local/create_edge_case_test_data.py` generates a
synthetic CSV with intentional problems (duplicates, outliers, all-missing columns,
inconsistent labels, severe imbalance, future dates).

```bash
python local/create_edge_case_test_data.py
# Output: data/raw/edge_cases.csv

python python/run_reporter.py \
  --input data/raw/edge_cases.csv \
  --id-cols participant_id
```

This file is in `local/` which is git-ignored — it will not be committed.

---

## Testing

```bash
# Run all tests
python -m pytest

# Verbose output
python -m pytest tests/ -v

# Run one test file
python -m pytest tests/test_reporter_smoke.py -v
```

The tests do not read from disk, do not write reports, and do not require any optional packages. They build an in-memory DataFrame and check the full pipeline end-to-end.
