# Before/After Snapshots and Validation

The cleaning executor automatically captures a statistical snapshot of your
dataset before and after all cleaning steps run. A separate validation check
then tests whether the cleaned data meets your declared expectations.

---

## Dataset snapshots

Every pipeline run captures two snapshots — `before cleaning` and
`after cleaning` — using the same metrics:

| Metric | Description |
|---|---|
| `n_rows` | Total row count |
| `n_cols` | Total column count |
| `n_exact_duplicates` | Rows that are exact copies of another row |
| `n_missing_cells` | Total `NaN` / `NaT` cells across all columns |
| `missingness_pct` | Per-column missingness (only for columns with >0% missing) |
| `columns` | Full list of column names |

These are computed on the DataFrame as-is at the start and end of the pipeline.
No sampling, no approximation.

### Before/after summary table

The cleaning log includes a markdown comparison table like this:

```
| Metric              | Before | After | Change |
|---|---|---|---|
| Rows                | 5,000  | 4,973 | -27    |
| Columns             | 18     | 16    | -2     |
| Exact duplicate rows| 12     | 0     | -12    |
| Total missing cells | 340    | 298   | -42    |
```

Plus, if columns were added or removed:

```
**Columns added:** `['bmi_outlier_flag']`
**Columns removed:** `['_internal_id', 'temp_col']`
```

And per-column missingness changes:

```
**Missingness changes:**
- `age`: 0.0% → 0.5%
- `score`: 12.0% → 9.3%
```

### Reading the snapshot

**Rows going down** is expected when duplicate removal or row filtering steps
are present. Confirm the delta matches your rules.

**Missing cells going up** is expected when `replace_missing_codes` or
`set_invalid_to_missing` convert sentinel values to `NaN`. This is correct —
you are surfacing true missingness rather than hiding it behind codes.

**Missing cells going down** is unusual in this toolkit (no imputation in v1).
If you see this, check whether a step is unintentionally filling nulls.

**Columns going up** is expected if `flag_outliers_iqr` is used (flag columns
are added).

**Columns going down** should be expected only when `keep_columns` or
`drop_columns` steps are present.

---

## Dry-run snapshots

In dry-run mode, the before snapshot is the input DataFrame. The after
snapshot is also the input DataFrame (nothing was modified). So the
before/after table will show no changes — this is correct.

The step log still shows `cells_changed` counts for what *would* have changed.

---

## Validation checks

The `validation:` block in your rules file declares what the cleaned dataset
*should* look like. Checks run after all cleaning steps, on the final DataFrame.

### `required_columns`

```yaml
validation:
  required_columns:
    - participant_id
    - age
    - diagnosis
```

Verifies that each listed column exists in the cleaned dataset. This catches
cases where a `drop_columns` or `keep_columns` step removed a column you
still need downstream.

**Passes:** column is present in the final DataFrame.  
**Fails:** column is missing (was dropped or never existed).

---

### `unique_keys`

```yaml
validation:
  unique_keys:
    - [participant_id]              # single-column key
    - [site_id, participant_id]     # composite key
```

Verifies that the specified column(s) have no duplicate combinations.

**Passes:** no two rows share the same key value(s).  
**Fails:** at least one key value (or combination) appears in more than one row.

For longitudinal data where the same participant appears across time points, use
a composite key:

```yaml
unique_keys:
  - [participant_id, visit_number]
```

---

### `accepted_values`

```yaml
validation:
  accepted_values:
    sex: [Male, Female]
    diagnosis: [Control, SCZ, BD, MDD]
```

Verifies that non-null values in each column are in the allowed list. Null
values (`NaN`) are ignored — this check is about the values that are present.

**Passes:** all non-null values are in the declared list.  
**Fails:** at least one non-null value is not in the list (examples shown).

This check is useful to confirm that `map_categories` worked as expected.

---

### `ranges`

```yaml
validation:
  ranges:
    age:
      min: 18
      max: 100
    bmi:
      min: 10
      max: 80
```

Verifies that non-null numeric values fall within `[min, max]`. Null values are
ignored. Either `min` or `max` can be omitted for one-sided bounds.

**Passes:** all non-null values are within bounds.  
**Fails:** at least one value is below `min` or above `max`.

Note: if you ran `set_invalid_to_missing` with the same bounds, this check
should always pass (the out-of-range values were already set to `NaN`).
Include both for defence-in-depth — in case the order changes.

---

## Validation behaviour

- Validation runs **after** all cleaning steps, on the final cleaned DataFrame.
- Validation **does not modify data**. It only observes and reports.
- Validation failures **do not stop the pipeline**. The cleaned file is still
  written, and the log records the failures for review.
- In dry-run mode, validation runs against the unmodified input DataFrame.

---

## Reading the validation report

The standalone validation report (`reports/validation_reports/`) contains:

```
# Validation Report

- **Timestamp:** 2024-06-15 14:32:01
- **Dataset:** `data/processed/my_data_cleaned.csv`

**Result:** ✗ 1 check(s) failed.
**Checks passed:** 5  |  **Failed:** 1

## Failed Checks

- **[accepted_values]** `sex`: 3 value(s) not in allowed list ['Male', 'Female'].
  Examples: ['male', 'M']

## Passed Checks

- **[required_column]** `participant_id`: 'participant_id' is present.
- **[unique_key]** `participant_id`: Key (participant_id) is unique.
- **[range]** `age`: all values within [18, 100].
- **[range]** `bmi`: all values within [10, 80].
- **[accepted_values]** `diagnosis`: all non-null values are in ['Control', 'SCZ', 'BD'].
```

When a check fails, review the cleaning step responsible for that column and
check whether an earlier step (e.g. `standardise_case` or `map_categories`)
needs to be added or adjusted.

---

## Commit your cleaned data for reproducibility

The cleaning log captures the git commit hash at the time of the run. If you
commit:
1. Your raw data (or document its provenance)
2. Your rules YAML
3. Your cleaned data

…then anyone with the same rules YAML and raw data can reproduce the exact same
cleaned output by running:

```bash
python python/run_cleaner.py \
  --input  data/raw/my_data.csv \
  --rules  config/my_cleaning_rules.yaml \
  --output data/processed/my_data_cleaned.csv
```

---

## Related docs

- [Cleaning Rules Reference](cleaning_rules_reference.md) — every action explained
- [Cleaning Execution Guide](cleaning_execution.md) — how to run the executor
- [Cleaning Decision Guides](cleaning_decision_guides/README.md) — the workflow before writing rules
