# Reporter Reference

Full reference for `python/run_reporter.py` and the reporter config file.

For a quick-start, see the [README](../README.md).

---

## CLI arguments

```bash
python python/run_reporter.py [options]
```

| Argument | Default | What it does |
|---|---|---|
| `--input PATH` | — | Path to your CSV, TSV, Excel, or Parquet file |
| `--example-dataset NAME` | — | Load a built-in dataset (`penguins`, `tips`, `iris`) |
| `--columns COL ...` | all | Analyse only these columns |
| `--id-cols COL ...` | none | Mark columns as IDs — enables duplicate ID checks |
| `--mode quick\|full\|both` | `quick` | Report mode (see below) |
| `--config PATH` | none | Path to a YAML config file |
| `--schema PATH` | none | Path to a schema YAML for validation checks |
| `--output-dir DIR` | `reports/descriptive_summary` | Where to save the markdown report |
| `--date-columns COL ...` | none | Explicitly mark columns as dates |

`--input` and `--example-dataset` are mutually exclusive.

---

## Report modes

All three modes are implemented. `full` and `both` require ydata-profiling.

| Mode | Output | Extra requirement |
|---|---|---|
| `quick` | Markdown summary in `reports/descriptive_summary/` | None |
| `full` | HTML profile in `reports/full_profiles/` | `pip install ydata-profiling` |
| `both` | Both outputs | `pip install ydata-profiling` |

---

## Config file

Copy the example and edit:

```bash
cp config/reporter_config.example.yaml config/reporter_config.yaml
python python/run_reporter.py --config config/reporter_config.yaml
```

### All config keys

```yaml
# ── Input ──────────────────────────────────────────────────────────────────────
input_path: null                  # path to your data file
example_dataset: null             # or: "penguins" | "tips" | "iris"

columns: null                     # null = all columns; or list column names
id_cols: null                     # list column names to treat as IDs
date_columns: []                  # columns to explicitly parse as dates

type_overrides:                   # override auto-detected types
  visit_number: categorical       # treat as categorical even if numeric
  site_id: id

# ── Output ─────────────────────────────────────────────────────────────────────
mode: "quick"                     # quick | full | both
output_dir: "reports/descriptive_summary"
report_basename: null             # auto-generated from input filename if null

# ── Thresholds ─────────────────────────────────────────────────────────────────
thresholds:
  high_missingness: 0.20          # warn if > 20% missing
  very_high_missingness: 0.50     # flag as severe if > 50% missing
  imbalance_cutoff: 0.95          # binary: warn if dominant class > 95%
  high_cardinality_cutoff: 50     # categorical: flag if > 50 unique values
  rare_category_cutoff: 0.01      # flag categories in < 1% of rows
  outlier_iqr_multiplier: 1.5     # IQR multiplier for outlier detection

# ── Privacy ────────────────────────────────────────────────────────────────────
privacy:
  suppress_id_values: true        # do not show ID column values in reports
  suppress_free_text: true        # do not show free-text examples
```

Full example with comments: [`config/reporter_config.example.yaml`](../config/reporter_config.example.yaml)

---

## Schema validation

Pass a schema file to run validation checks in addition to the descriptive summary:

```bash
python python/run_reporter.py \
  --input data/raw/my_data.csv \
  --schema config/schema.example.yaml
```

### Schema file format

```yaml
# config/schema.example.yaml
columns:
  participant_id:
    role: id
    required: true
    unique: true

  age:
    type: continuous
    min: 18
    max: 100

  sex:
    type: categorical
    allowed_values: ["Male", "Female"]

  diagnosis:
    type: categorical
    allowed_values: ["Control", "SCZ", "BD", "MDD"]
```

### Checks performed

| Check | What it detects |
|---|---|
| `required: true` | Column is absent from the file |
| `unique: true` | Column has non-unique values (for ID columns) |
| `min` / `max` | Values outside the numeric range |
| `allowed_values` | Values not in the allowed list (with examples) |

Full reference: [`config/schema.example.yaml`](../config/schema.example.yaml)

---

## Type inference

The reporter automatically infers a type for each column:

| Inferred type | Criteria |
|---|---|
| `id` | Listed in `id_cols`; or high cardinality + all unique |
| `date` | Listed in `date_columns`; or pandas datetime dtype |
| `empty` | All values are null |
| `constant` | One unique non-null value |
| `binary` | Exactly 2 unique non-null values |
| `continuous` | Numeric, more than 2 unique values |
| `categorical` | Object/string, up to `high_cardinality_cutoff` unique values |
| `text_high_cardinality` | Object/string, above `high_cardinality_cutoff` |

Override with `type_overrides` in the config file.

---

## Output files

| File | Location | Contents |
|---|---|---|
| Quick report | `reports/descriptive_summary/<basename>_YYYYMMDD_HHMMSS.md` | Markdown QC summary |
| Full profile | `reports/full_profiles/<basename>_YYYYMMDD_HHMMSS.html` | Interactive HTML |

---

## Back to main docs

← [README](../README.md) · [Usage guide](usage.md) · [Cleaning execution](cleaning_execution.md)
