# I have a CSV file. What do I do?

This guide is for analysts who are new to ByeDataClean. It walks you through the whole process from raw file to cleaned output, step by step.

---

## Before you start

**What is the "project root"?**

The project root is the top-level folder of the repository — the one that contains `README.md`, `python/`, `data/`, `config/`, and `reports/`. All commands in this guide must be run from that folder.

When you open a terminal, check that you are in the right place:

```bash
ls
```

You should see `README.md`, `python/`, `data/`, etc. If you see only Python files, you are probably inside `python/`. Run `cd ..` to go back up.

---

## Step 1 — Put your file in `data/raw/`

Copy or move your CSV file into the `data/raw/` folder:

```
data/
  raw/
    my_study_data.csv     ← put it here
```

Do not rename the original file. Do not open it in Excel and re-save it.

> **Safety note:** `data/raw/` is git-ignored — your file will never be committed to version control by accident. Do not move it into `data/processed/` yet.

---

## Step 2 — Run a QC report

This reads your file and produces a report showing potential data-quality problems.

```bash
python python/run_reporter.py --input data/raw/my_study_data.csv
```

The report is saved to `reports/descriptive_summary/`. Open it in any markdown viewer (GitHub, VS Code preview, Typora, etc.).

---

## Step 3 — Read the report

The report has several sections. Here is what to look for in each:

| Section | What to check |
|---|---|
| **Dataset overview** | Does the row count match what you expect? Are there extra or missing columns? |
| **Missingness** | Which columns have a lot of missing values? Is that expected? |
| **Duplicates** | Are there exact duplicate rows? Duplicate IDs? |
| **Continuous variables** | Are there impossible values (negative age, BMI of 300)? |
| **Categorical variables** | Are there inconsistent labels ("Male" and "male" and "M")? Rare categories? |
| **Cleaning decision prompts** | The report suggests questions to answer before cleaning. Read these carefully. |

> **Important:** The report tells you what might be wrong. It does not clean anything automatically. Every cleaning decision is yours to make.

---

## Step 4 — Copy and edit the cleaning rules file

Create your own cleaning rules file from the template:

```bash
cp config/cleaning_rules.example.yaml config/my_cleaning_rules.yaml
```

Open `config/my_cleaning_rules.yaml` in any text editor.

Each rule looks like this:

```yaml
- step: 1
  name: "standardise_column_names"
  action: "standardise_column_names"
  decision_status: "approved"
  rationale: "Always normalise names for consistency."
```

Edit the rules to match what you decided after reading the report. See [docs/cleaning_rules_reference.md](cleaning_rules_reference.md) for all available actions and [docs/yaml_for_beginners.md](yaml_for_beginners.md) if you are new to YAML.

---

## Step 5 — Dry run (always do this first)

A dry run simulates every cleaning step and tells you exactly what would change — without writing anything to `data/processed/`.

```bash
python python/run_cleaner.py \
  --input data/raw/my_study_data.csv \
  --rules config/my_cleaning_rules.yaml \
  --dry-run
```

Read the log that gets written to `reports/cleaning_logs/`. Check:

- Are the right cells being changed?
- Is the row count changing by the expected amount?
- Are there warnings you did not expect?

Adjust your rules file and repeat until the dry run looks right.

---

## Step 6 — Apply cleaning

When the dry run looks correct, apply cleaning for real:

```bash
python python/run_cleaner.py \
  --input  data/raw/my_study_data.csv \
  --rules  config/my_cleaning_rules.yaml \
  --output data/processed/my_study_data_cleaned.csv \
  --after-report \
  --flowchart
```

If your rules remove rows or columns, you also need to add `--confirm-destructive`.

This writes:

| File | What it is |
|---|---|
| `data/processed/my_study_data_cleaned.csv` | The cleaned dataset |
| `reports/cleaning_logs/…_cleaning_log_….md` | Full step-by-step log |
| `reports/cleaning_logs/…_manifest_….yaml` | Machine-readable run record (git commit, row counts) |
| `reports/validation_reports/…_validation_….md` | Pass/fail checks |
| `reports/cleaning_logs/…_flow.md` | Visual cleaning flowchart |
| `reports/descriptive_summary/…_after_….md` | QC report on cleaned data |

---

## Step 7 — Check the outputs

Open the cleaning log and read through it:

- Did each step do what you intended?
- Did validation pass? If a check failed, is it expected (e.g., an outlier you kept intentionally)?
- Does the before/after summary match your expectations?

Open the QC report for the cleaned data and compare it with the raw-data report:

- Did the duplicate rows go away?
- Did the category inconsistencies get resolved?
- Did the missingness change in the expected direction?

---

## What is safe to share?

| File | Safe to share? | Why |
|---|---|---|
| `config/my_cleaning_rules.yaml` | Yes | Contains only your decisions and rationale — no data |
| `reports/cleaning_logs/…_cleaning_log.md` | **Review first** | Contains row/column counts and category labels from your data |
| `reports/descriptive_summary/…_report.md` | **Review first** | Contains summary statistics, category labels, and sample strings |
| `reports/cleaning_logs/…_flow.md` | **Review first** | Contains counts but no individual-level data |
| `data/raw/…` | **No** | Contains raw participant data |
| `data/processed/…` | **No** | Contains cleaned participant data |

Before sharing a report, check whether it includes category labels or string examples that could identify individuals. Set `privacy.suppress_id_values: true` and `privacy.suppress_free_text: true` in your reporter config to reduce exposure.

---

## Troubleshooting

See [docs/troubleshooting.md](troubleshooting.md) for common errors and how to fix them.

Run the environment check:

```bash
python python/doctor.py
```

---

← [README](../README.md) · [YAML for beginners](yaml_for_beginners.md) · [Cleaning rules reference](cleaning_rules_reference.md)
