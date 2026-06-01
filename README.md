# ByeDataClean

[![Tests](https://github.com/kaiyao28/ByeDataClean/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/kaiyao28/ByeDataClean/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

A lightweight toolkit for profiling, deciding, and cleaning tabular data — with reproducible YAML rules, before/after logs, and visual audit flowcharts.

> **Privacy reminder:** Do not commit raw data or share reports without reviewing them first. Reports may contain column names, category labels, and summary statistics from your dataset. See [Safety defaults](#safety-defaults) and [docs/i_have_a_csv_what_do_i_do.md](docs/i_have_a_csv_what_do_i_do.md#what-is-safe-to-share).

---

## Why use this?

- Profile CSV, TSV, Excel, or Parquet files in under 5 minutes — no Python coding required, only CLI commands.
- Identify missingness, duplicates, outliers, invalid ranges, and category inconsistencies.
- Use structured decision guides to choose how to act on each finding.
- Apply explicit YAML cleaning rules that describe every step and your rationale.
- Generate timestamped logs, validation reports, run manifests, and a visual cleaning flowchart.
- Raw data is never overwritten. Every run is auditable.

---

## Workflow

```
Profile → Decide → Clean → Validate → Re-profile
```

| Step | What happens |
|---|---|
| **Profile** | Run the QC reporter on raw data — see warnings, outliers, missingness |
| **Decide** | Review findings; choose cleaning actions using the decision guides |
| **Clean** | Apply explicit YAML rules step-by-step with dry-run preview |
| **Validate** | Check required columns, ranges, accepted values, and unique keys |
| **Re-profile** | Run the QC reporter again — confirm the issues resolved |

---

## Example cleaning flow

The cleaner generates a visual flowchart from the audit log after every run:

```bash
python python/run_cleaner.py \
  --input  data/raw/my_data.csv \
  --rules  config/cleaning_rules.example.yaml \
  --output data/processed/my_data_cleaned.csv \
  --after-report \
  --flowchart
```

```mermaid
flowchart LR
  N0["Raw data<br/>Rows: 100<br/>Columns: 8<br/>Missing cells: 36<br/>Duplicate rows: 4"]
  N1["Step 1: standardise_column_names<br/>Columns renamed: 5"]
  N2["Step 2: replace_missing_codes<br/>Cells changed: 12"]
  N3["Step 3: trim_whitespace<br/>Cells changed: 18"]
  N4["Step 4: map_categories<br/>Cells changed: 9<br/>Warnings: 1"]
  N5["Step 5: flag_bmi_outliers<br/>Outliers flagged: 3<br/>Columns added: 1"]
  N6["Step 6: remove_exact_duplicates<br/>Rows removed: 4<br/>⚠ DESTRUCTIVE"]
  N7["Validation<br/>Passed: 6<br/>All 6 checks passed"]
  N8["Cleaned data<br/>Rows: 96<br/>Columns: 9<br/>Missing cells: 28<br/>Duplicate rows: 0"]

  N0 --> N1 --> N2 --> N3 --> N4 --> N5 --> N6 --> N7 --> N8

  classDef input_node       fill:#e8f1ff,stroke:#2b6cb0,stroke-width:2px;
  classDef clean_step       fill:#f7fafc,stroke:#4a5568,stroke-width:1px;
  classDef destructive_step fill:#ffe8e8,stroke:#c53030,stroke-width:2px;
  classDef warning_step     fill:#fff8db,stroke:#d69e2e,stroke-width:2px;
  classDef validation_node  fill:#e6fffa,stroke:#319795,stroke-width:2px;
  classDef output_node      fill:#e9ffe8,stroke:#2f855a,stroke-width:2px;

  class N0 input_node;
  class N1 clean_step;
  class N2 clean_step;
  class N3 clean_step;
  class N4 warning_step;
  class N5 clean_step;
  class N6 destructive_step;
  class N7 validation_node;
  class N8 output_node;
```

Blue = raw data · Grey = standard step · Yellow = warning · Red = destructive · Teal = validation · Green = cleaned output.

> The diagram is a quick visual summary. The full cleaning log contains detailed rationale, decision status, and per-step before/after counts.

---

## Quick start

### 0. One-command demo (no data needed)

```bash
python python/run_demo.py
```

Runs the full Profile → Dry-run → Clean → Flowchart loop on the bundled example dataset. No internet required. Prints all output paths when done.

### 1. Install

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

See [docs/installation.md](docs/installation.md) for optional packages and R setup.

### 2. Profile the example dataset

A small dirty dataset is included — 50 rows with realistic issues:

```bash
python python/run_reporter.py --input data/examples/example_dirty_data.csv
```

The report will flag: 22% missing BMI, duplicate IDs, an age outlier (999), inconsistent sex labels, and a future assessment date.

### 3. Preview cleaning (dry run)

A matching rules file is included — no editing needed to run the demo:

```bash
python python/run_cleaner.py \
  --input data/examples/example_dirty_data.csv \
  --rules config/example_cleaning_rules.yaml \
  --dry-run
```

Simulates every step and writes a log without touching the data. Review the log, adjust rules, repeat.

### 4. Apply cleaning

```bash
python python/run_cleaner.py \
  --input  data/examples/example_dirty_data.csv \
  --rules  config/example_cleaning_rules.yaml \
  --output data/processed/example_cleaned.csv \
  --confirm-destructive \
  --after-report \
  --flowchart
```

`--confirm-destructive` is required because the rules include `remove_exact_duplicates`.

> **Using your own data?** Replace `example_dirty_data.csv` and `example_cleaning_rules.yaml` with your own paths. Copy `config/cleaning_rules.example.yaml` as a starting template.

---

## Outputs

| Output | Location |
|---|---|
| QC report | `reports/descriptive_summary/` |
| Cleaned data | `data/processed/` |
| Cleaning log | `reports/cleaning_logs/` |
| Run manifest (YAML) | `reports/cleaning_logs/` |
| Validation report | `reports/validation_reports/` |
| Flowchart (`.md` + `.mmd`) | `reports/cleaning_logs/` |

Data and reports are never committed — `data/` and `reports/` are git-ignored.

---

## Safety defaults

- Raw data are **never overwritten** — the cleaner aborts if input and output resolve to the same path.
- **Dry-run** simulates every step and writes a log without touching the data file.
- Row or column drops require `allow_row_drop: true` in the rule **and** `--confirm-destructive` on the CLI.
- Outliers are **flagged by default**, not removed.
- Each rule can carry `decision_status` and `rationale` — both are recorded verbatim in the cleaning log.

---

## Python, R, and SQL

**Python** is the primary workflow. All features described here are implemented in Python.

**R** provides a parallel reporter (`r/run_reporter.R`) using skimr and janitor. A full R cleaning executor is planned for Stage 4.

**SQL** provides a copy-edit-run inspection cookbook (`sql/inspection_cookbook/`) — 9 numbered query templates you run in your own SQL client. No automatic report generation; SQL dialects differ too much for a reliable wrapper.

---

## Config files at a glance

| File | Used by | Controls | Do beginners need to edit it? |
|---|---|---|---|
| `config/reporter_config.example.yaml` | `run_reporter.py` | Columns, thresholds, privacy, output dir | Optional — CLI flags cover most needs |
| `config/schema.example.yaml` | `run_reporter.py --schema` | Expected column types, ranges, allowed values | Optional — for stricter input checks |
| `config/cleaning_rules.example.yaml` | `run_cleaner.py` | Every cleaning step, rationale, validation | **Yes** — copy and edit for each project |
| `config/example_cleaning_rules.yaml` | `run_cleaner.py` / `run_demo.py` | Demo rules for the bundled example dataset | No — demo only |
| `config/cleaning_profiles/*.yaml` | `run_cleaner.py` | Pre-built rule sets for common analysis types | Optional — good starting point |
| `config/category_mapping.example.yaml` | Referenced by `map_categories` rules | Reusable label mappings (sex, diagnosis, etc.) | Optional — useful for shared codelists |

---

## Documentation

**New to this tool?** Start here:
- [docs/i_have_a_csv_what_do_i_do.md](docs/i_have_a_csv_what_do_i_do.md) — step-by-step from raw file to cleaned output
- [docs/yaml_for_beginners.md](docs/yaml_for_beginners.md) — editing YAML rules safely
- [docs/glossary.md](docs/glossary.md) — plain-language definitions

| Need | Read |
|---|---|
| Detailed usage examples | [docs/usage.md](docs/usage.md) |
| Installation options | [docs/installation.md](docs/installation.md) |
| Reporter CLI and config | [docs/reporter_reference.md](docs/reporter_reference.md) |
| Cleaning executor CLI | [docs/cleaning_execution.md](docs/cleaning_execution.md) |
| All 14 cleaning actions | [docs/cleaning_rules_reference.md](docs/cleaning_rules_reference.md) |
| Snapshots and validation | [docs/before_after_validation.md](docs/before_after_validation.md) |
| Cleaning decision guides | [docs/cleaning_decision_guides/README.md](docs/cleaning_decision_guides/README.md) |
| SQL cookbook | [docs/sql_workflow.md](docs/sql_workflow.md) |
| Troubleshooting | [docs/troubleshooting.md](docs/troubleshooting.md) |
| Tests and contributing | [docs/development.md](docs/development.md) |
| Repository structure | [docs/architecture.md](docs/architecture.md) |
| Roadmap | [docs/roadmap.md](docs/roadmap.md) |

---

## Run tests

```bash
python -m pytest
```

130 tests. See [docs/development.md](docs/development.md) for the full breakdown.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
