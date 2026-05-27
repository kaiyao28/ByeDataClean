# Cleaning Rules Reference

Complete reference for every supported action in the YAML rules file.

---

## Rules file structure

```yaml
version: 1                       # required; must be 1
name: "my_cleaning_rules"        # human-readable label for the log

rules:
  - step: 1                      # unique integer; determines execution order
    name: "descriptive_name"     # appears in the cleaning log
    action: "action_name"        # must be one of the supported actions below
    # ... action-specific keys

validation:                      # optional; checks run after all steps
  required_columns: [...]
  unique_keys: [...]
  accepted_values: {...}
  ranges: {...}
```

**Execution order:** steps run in ascending `step` number order, not file order.  
**Dry run:** all actions respect `dry_run=True` — they compute change counts but
return the DataFrame unmodified.

---

## Supported actions

### 1 · `standardise_column_names`

Convert all column names to `snake_case`.

**Risk level:** Low — purely cosmetic rename; no data lost.

```yaml
- step: 1
  name: "standardise_column_names"
  action: "standardise_column_names"
```

No additional keys required. `CamelCase`, spaces, hyphens, slashes → underscore.

---

### 2 · `rename_columns`

Rename specific columns using an explicit mapping.

**Risk level:** Low — no data lost.

```yaml
- step: 2
  name: "rename_participant_id"
  action: "rename_columns"
  mapping:
    OldName: new_name
    "Column With Spaces": cleaner_name
```

| Key | Required | Description |
|---|---|---|
| `mapping` | Yes | Dict of `old_name: new_name` pairs |

Columns in `mapping` that don't exist in the DataFrame are warned and skipped.

---

### 3 · `keep_columns`

Keep only the listed columns; drop everything else.

**Risk level:** Medium — columns are dropped. Requires guard.

```yaml
- step: 3
  name: "keep_analysis_columns"
  action: "keep_columns"
  allow_drop: true              # required guard
  columns:
    - participant_id
    - age
    - diagnosis
```

| Key | Required | Description |
|---|---|---|
| `columns` | Yes | List of column names to keep |
| `allow_drop: true` | Yes | Safety guard — must be explicit |

---

### 4 · `drop_columns`

Drop the listed columns.

**Risk level:** Medium — columns are dropped. Requires guard.

```yaml
- step: 4
  name: "drop_internal_columns"
  action: "drop_columns"
  allow_drop: true              # required guard
  columns:
    - _internal_flag
    - temp_col
```

| Key | Required | Description |
|---|---|---|
| `columns` | Yes | List of column names to drop |
| `allow_drop: true` | Yes | Safety guard — must be explicit |

---

### 5 · `replace_missing_codes`

Replace sentinel values (e.g. `"NA"`, `-9`, `999`) with `NaN`.

**Risk level:** Low-medium — increases missingness but recovers true missingness.

```yaml
- step: 5
  name: "replace_missing_codes"
  action: "replace_missing_codes"
  columns: all                  # or "string", or a list of column names
  missing_codes:
    - "NA"
    - "Unknown"
    - "N/A"
    - -9
    - -99
    - 999
```

| Key | Required | Default | Description |
|---|---|---|---|
| `missing_codes` | Yes | — | List of values to replace with `NaN` |
| `columns` | No | `"all"` | `"all"`, `"string"`, or a list of column names |

**String codes** are applied only to object (string) columns.  
**Numeric codes** are applied only to numeric columns.  
Both types can be mixed in the same `missing_codes` list.

---

### 6 · `trim_whitespace`

Strip leading/trailing whitespace from string columns.

**Risk level:** Very low — whitespace is almost always unintended.

```yaml
- step: 6
  name: "trim_whitespace"
  action: "trim_whitespace"
  columns: string               # or a list of specific columns
```

| Key | Required | Default | Description |
|---|---|---|---|
| `columns` | No | `"string"` | `"all"`, `"string"`, or a list |

Non-string columns are silently skipped even if listed explicitly.

---

### 7 · `standardise_case`

Apply a consistent case transformation to string columns.

**Risk level:** Low — original values can be recovered from the log.

```yaml
- step: 7
  name: "standardise_case"
  action: "standardise_case"
  case: "lower"                 # lower | upper | title
  columns:
    - sex
    - diagnosis
```

| Key | Required | Default | Description |
|---|---|---|---|
| `case` | Yes | — | `"lower"`, `"upper"`, or `"title"` |
| `columns` | No | `"string"` | Columns to apply to |

Apply before `map_categories` so the mapping keys match consistently.

---

### 8 · `map_categories`

Remap categorical values to a standard set.

**Risk level:** Low-medium — unmatched values may be set to missing.

```yaml
- step: 8
  name: "harmonise_sex"
  action: "map_categories"
  column: sex
  mapping:
    M: Male
    male: Male
    F: Female
    female: Female
    "0": Male
    "1": Female
  unmatched_action: warn        # warn | set_missing | keep
```

| Key | Required | Default | Description |
|---|---|---|---|
| `column` | Yes | — | The single column to remap |
| `mapping` | Yes | `{}` | Dict of `from_value: to_value` |
| `unmatched_action` | No | `"warn"` | What to do with values not in mapping |

`unmatched_action` options:
- `warn` — log a warning, leave unmatched values as-is
- `set_missing` — replace unmatched values with `NaN`
- `keep` — silently leave unmatched values unchanged

If the column doesn't exist, a warning is added and the action is skipped.

Use `config/category_mapping.example.yaml` as a reference for common mappings.

---

### 9 · `set_invalid_to_missing`

Set numeric values outside a valid range to `NaN`.

**Risk level:** Medium — increases missingness. Document the valid range
in your decision log.

```yaml
- step: 9
  name: "clip_age_range"
  action: "set_invalid_to_missing"
  column: age
  min: 18
  max: 100
```

| Key | Required | Description |
|---|---|---|
| `column` | Yes | Numeric column to check |
| `min` | No | Values strictly below this → `NaN` |
| `max` | No | Values strictly above this → `NaN` |

Either `min` or `max` may be omitted (one-sided bounds). Both omitted → no-op.

---

### 10 · `flag_outliers_iqr`

Flag outliers using the IQR method (1.5 × IQR fence). Adds a binary flag column.

**Risk level (flagging):** Very low — adds a column, removes nothing.  
**Risk level (removal):** High — requires explicit guards.

```yaml
# Flag only (recommended default)
- step: 10
  name: "flag_bmi_outliers"
  action: "flag_outliers_iqr"
  column: bmi
  output_column: bmi_outlier_flag   # defaults to "{column}_outlier_flag"
  remove: false

# Flag and remove (requires guards)
- step: 10
  name: "remove_bmi_outliers"
  action: "flag_outliers_iqr"
  column: bmi
  output_column: bmi_outlier_flag
  remove: true
  allow_row_drop: true              # required guard when remove: true
```

| Key | Required | Default | Description |
|---|---|---|---|
| `column` | Yes | — | Numeric column to check |
| `output_column` | No | `"{column}_outlier_flag"` | Name of the new flag column |
| `remove` | No | `false` | If `true`, remove outlier rows |
| `allow_row_drop` | Only if `remove: true` | — | Safety guard |

The IQR fence is: `Q1 − 1.5 × IQR` to `Q3 + 1.5 × IQR`.  
The flag column uses dtype `Int8` (nullable integer): `1` = outlier, `0` = not.

**Default is `remove: false`.** Outliers should almost never be removed
automatically — flag them, then decide after reviewing.

---

### 11 · `parse_dates`

Parse string columns to `datetime64`. Unparseable values become `NaT`.

**Risk level:** Low — changes dtype; original strings logged in warnings.

```yaml
- step: 11
  name: "parse_date_columns"
  action: "parse_dates"
  columns:
    - date_of_birth
    - assessment_date
  format: "%Y-%m-%d"            # optional; null = auto-detect
```

| Key | Required | Default | Description |
|---|---|---|---|
| `columns` | Yes | — | List of columns to parse |
| `format` | No | `null` | `strftime` format string; null = infer |

Parse failures are warned and set to `NaT`. The warning count appears in the
cleaning log.

---

### 12 · `remove_exact_duplicates`

Drop exact duplicate rows, keeping the first occurrence.

**Risk level:** Medium-high — rows are removed. Requires guard.

```yaml
- step: 12
  name: "remove_exact_duplicate_rows"
  action: "remove_exact_duplicates"
  allow_row_drop: true          # required guard
```

| Key | Required | Description |
|---|---|---|
| `allow_row_drop: true` | Yes | Safety guard — must be explicit |

"Exact" means all column values (including NaN) match. If you only want to
deduplicate on a subset of columns, use `filter_rows_explicit` instead.

---

### 13 · `filter_rows_explicit`

Drop rows matching a pandas query expression, with a documented reason.

**Risk level:** High — rows are removed. Requires guard + reason. Use only
when you have a clear analytical justification.

```yaml
- step: 13
  name: "exclude_under_18"
  action: "filter_rows_explicit"
  allow_row_drop: true          # required guard
  reason: "Protocol excludes participants under 18; confirmed with PI."
  condition: "age >= 18"        # pandas eval expression (KEEP rows where true)
```

| Key | Required | Description |
|---|---|---|
| `condition` | Yes | `df.eval()` expression — rows where True are **kept** |
| `reason` | Yes | Plain-English justification (appears in log) |
| `allow_row_drop: true` | Yes | Safety guard — must be explicit |

The `reason` string is written verbatim into the cleaning log and is part of
your audit trail. Write it as if explaining the decision to a reviewer.

The `condition` is evaluated with `pd.DataFrame.eval()`. Column names with
spaces must be quoted: `condition: "`column name` > 0"`.

---

## Validation block

The optional `validation:` section runs after all cleaning steps and produces
a standalone validation report.

```yaml
validation:
  required_columns:
    - participant_id
    - age
    - diagnosis

  unique_keys:
    - [participant_id]               # single-column key
    - [site, participant_id]         # composite key

  accepted_values:
    sex: [Male, Female]
    diagnosis: [Control, SCZ, BD]

  ranges:
    age:
      min: 18
      max: 100
    bmi:
      min: 10
      max: 80
```

| Check | What it verifies |
|---|---|
| `required_columns` | Each listed column exists in the cleaned data |
| `unique_keys` | Each key (or key combination) has no duplicates |
| `accepted_values` | Non-null values in each column are in the allowed set |
| `ranges` | Non-null numeric values are within `[min, max]` |

Validation failures **do not stop the pipeline or modify data**. They are
observations flagged for review.

---

## Risk levels summary

| Action | Risk | Row drop? | Column drop? | Guard required |
|---|---|---|---|---|
| `standardise_column_names` | Very low | No | No | No |
| `rename_columns` | Low | No | No | No |
| `replace_missing_codes` | Low | No | No | No |
| `trim_whitespace` | Very low | No | No | No |
| `standardise_case` | Low | No | No | No |
| `map_categories` | Low–Med | No | No | No |
| `set_invalid_to_missing` | Medium | No | No | No |
| `flag_outliers_iqr` (flag only) | Very low | No | No | No |
| `parse_dates` | Low | No | No | No |
| `keep_columns` | Medium | No | Yes | `allow_drop: true` |
| `drop_columns` | Medium | No | Yes | `allow_drop: true` |
| `remove_exact_duplicates` | Med–High | Yes | No | `allow_row_drop: true` |
| `flag_outliers_iqr` (remove) | High | Yes | No | `allow_row_drop: true` |
| `filter_rows_explicit` | High | Yes | No | `allow_row_drop: true` + `reason` |

---

## Related docs

- [Cleaning Execution Guide](cleaning_execution.md) — how to run the executor
- [Before/After Validation](before_after_validation.md) — understanding the audit trail
- [Cleaning Decision Guides](cleaning_decision_guides/README.md) — the 10-step workflow
