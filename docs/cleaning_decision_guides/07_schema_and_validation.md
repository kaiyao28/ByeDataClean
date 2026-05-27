# 07 — Schema and Validation

A schema is a written description of what your data should look like. Validation is the process of checking whether the actual data matches it.

Profiling (what the reporter does) and validation (what the schema check does) are different:

| | Profiling | Validation |
|---|---|---|
| Purpose | Understand what the data looks like | Check whether it meets defined expectations |
| Input | Any data | Data + schema |
| Output | Descriptive statistics | Pass/fail checks |
| When to use | At the start, before cleaning | After cleaning, before analysis |

Both are useful. Use profiling to understand, schema validation to confirm.

---

## What a schema defines

The example schema in [`config/schema.example.yaml`](../../config/schema.example.yaml) covers:

- **Required columns** — must be present in the file
- **Role** — `id` columns expected to be unique
- **Type** — `continuous`, `binary`, `categorical`, `date`
- **Allowed values** — for categorical/binary columns
- **Numeric range** — min and max for continuous columns
- **Uniqueness** — flag non-unique values in ID columns

---

## Step 1: Create a schema for your dataset

Start with the example and adapt it:

```yaml
columns:
  participant_id:
    role: id
    required: true
    unique: true

  age:
    type: continuous
    required: false
    min: 18
    max: 100

  sex:
    type: binary
    allowed_values: ["Female", "Male"]

  diagnosis:
    type: categorical
    allowed_values: ["Control", "SCZ", "BD", "MDD"]

  assessment_date:
    type: date
```

---

## Step 2: Run schema validation

```bash
python python/run_reporter.py \
  --input data/raw/my_data.csv \
  --schema config/schema.yaml
```

The report will include a **Schema Checks** section listing:
- missing required columns
- allowed value violations (with examples of bad values)
- numeric range violations (count above max, below min)
- non-unique ID values

---

## Step 3: Interpret schema violations

**Missing required column**
→ The column may be named differently than expected. Check column names in the inventory section. Update the schema or rename the column in your cleaning script.

**Allowed value violation**
→ Check the example values shown. Are they typos, synonyms, or genuinely unexpected categories? Apply a category mapping (see [guide 05](05_categorical_variables.md)).

**Range violation**
→ Are these impossible values or plausible extremes? If impossible, set to missing. If plausible, review source data. Consider widening the schema range if the range was too strict.

**Non-unique ID**
→ Investigate whether the duplicate is accidental or expected. See [guide 03](03_duplicates_and_units.md).

---

## Step 4: Validate after cleaning

Re-run the reporter with the schema after applying cleaning:

```bash
python python/run_reporter.py \
  --input data/processed/my_data_clean.csv \
  --schema config/schema.yaml
```

All schema checks should pass on the cleaned dataset. If they do not, revise the cleaning script before proceeding to analysis.

---

## When to use production validation tools

The schema check in this toolkit is lightweight and file-based. For more rigorous validation, consider:

- **Pandera** (Python): define schemas as code with type annotations; integrates with type checkers
- **Great Expectations**: comprehensive expectation library; HTML "data docs" output
- **dbt generic tests**: version-controlled, pipeline-integrated (see [`sql/dbt_and_soda_notes.md`](../../sql/dbt_and_soda_notes.md))
- **Soda Core**: standalone YAML-based checks against a live database

See [`docs/package_comparison.md`](../package_comparison.md) for a comparison.

---

## What to document

- Schema file location and version
- Any schema violations found and how they were resolved
- Whether validation was re-run after cleaning and result
- If schema was updated, why and by whom
