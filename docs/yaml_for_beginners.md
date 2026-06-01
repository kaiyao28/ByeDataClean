# YAML for data cleaning beginners

ByeDataClean uses YAML files to describe cleaning rules. This guide explains enough YAML to edit cleaning rules safely, without needing to know YAML in general.

---

## What YAML is used for here

In ByeDataClean, YAML files are used for:

- **Cleaning rules** (`config/cleaning_rules.yaml`) — describe each cleaning step
- **Reporter config** (`config/reporter_config.yaml`) — control what the reporter checks
- **Schema validation** (`config/schema.example.yaml`) — declare expected column types and values

You do not need to learn all of YAML. You only need to know how to edit a list of rules.

---

## The three things you need to know

### 1. Indentation means structure

YAML uses spaces (not tabs) to show what belongs to what. Two spaces = one level of nesting.

```yaml
rules:             # this is a list
  - step: 1        # first item — note the two-space indent and dash
    name: "trim"
    action: "trim_whitespace"
```

**Never use tabs.** If your text editor inserts tabs, turn off tab insertion for YAML files.

### 2. A dash means "list item"

The `rules:` key holds a list of steps. Each step starts with `- `:

```yaml
rules:
  - step: 1          # first step
    action: "trim_whitespace"

  - step: 2          # second step
    action: "replace_missing_codes"
```

All lines belonging to the same step must be at the same indent level.

### 3. Strings can be bare or quoted

Most values do not need quotes:

```yaml
action: standardise_column_names
decision_status: approved
```

Use quotes when your value contains special characters (`:`, `#`, `{`, `}`, `[`, `]`), or when it could be misread as a number or boolean:

```yaml
rationale: "Set invalid values to NaN."       # contains a period — safe without quotes
rationale: "Action: remove duplicates"        # contains a colon — NEEDS quotes
missing_codes:
  - "NA"      # would otherwise be interpreted as a null value
  - "True"    # would otherwise be interpreted as a boolean
  - -9        # bare number is fine
```

---

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Mixing tabs and spaces | Parse error | Use spaces only |
| Wrong indentation | Step is ignored or nested incorrectly | Count your spaces carefully |
| Forgetting the dash `-` | The step is not in the list | Add `  - ` before the first key |
| Writing `True` / `False` without quotes | Treated as boolean, not string | Quote it: `"True"` |
| Writing `NA` without quotes | Treated as null | Quote it: `"NA"` |
| Colon in a string without quotes | Parse error | Quote the value |
| Duplicate step numbers | Undefined behaviour | Renumber steps in order |

---

## Copy-paste snippets

Each snippet is a complete rule you can paste into your `rules:` list. Adjust values for your data.

### Standardise column names (always safe)

```yaml
  - step: 1
    name: "standardise_column_names"
    action: "standardise_column_names"
    decision_status: "approved"
    rationale: "Convert all column names to snake_case for consistency."
```

### Replace missing-data codes

```yaml
  - step: 2
    name: "replace_missing_codes"
    action: "replace_missing_codes"
    columns: "all"
    missing_codes:
      - ""
      - "NA"
      - "N/A"
      - "Unknown"
      - "unknown"
      - -9
      - -99
    decision_status: "approved"
    rationale: "These are sentinel values from the export — not real categories."
```

### Trim whitespace from text columns

```yaml
  - step: 3
    name: "trim_whitespace"
    action: "trim_whitespace"
    columns: "string"
    decision_status: "approved"
    rationale: "Leading/trailing spaces cause silent mismatches in value_counts and merges."
```

### Standardise category labels (e.g. sex)

```yaml
  - step: 4
    name: "harmonise_sex_labels"
    action: "map_categories"
    column: "sex"
    mapping:
      M:      "Male"
      male:   "Male"
      MALE:   "Male"
      F:      "Female"
      female: "Female"
    unmatched_action: "warn"
    decision_status: "approved"
    rationale: "Inconsistent capitalisation and abbreviations confirmed in QC report."
```

### Set impossible numeric values to missing

```yaml
  - step: 5
    name: "set_invalid_age_to_missing"
    action: "set_invalid_to_missing"
    column: "age"
    min: 18
    max: 100
    decision_status: "approved"
    rationale: "Ages outside [18, 100] are impossible for this adult cohort."
```

### Flag outliers (does not remove rows)

```yaml
  - step: 6
    name: "flag_bmi_outliers"
    action: "flag_outliers_iqr"
    column: "bmi"
    output_column: "bmi_outlier_flag"
    remove: false
    decision_status: "approved"
    rationale: "Flag only. Analyst will review before deciding whether to set to missing."
```

### Add missing-value indicator columns

```yaml
  - step: 7
    name: "add_missingness_flags"
    action: "create_missingness_flags"
    columns: "all"
    only_if_any_missing: true
    decision_status: "approved"
    rationale: "Required for missing-not-at-random sensitivity analysis."
```

### Remove exact duplicate rows (destructive)

```yaml
  - step: 8
    name: "remove_exact_duplicates"
    action: "remove_exact_duplicates"
    allow_row_drop: true
    decision_status: "approved"
    rationale: "Confirmed accidental double-export with data manager."
```

> When you use this, you must also set `safety: allow_row_drop: true` at the top of the rules file, and add `--confirm-destructive` to the CLI command.

### Validation block

```yaml
validation:
  required_columns:
    - participant_id
    - age
    - sex
  unique_keys:
    - [participant_id]
  accepted_values:
    sex: ["Male", "Female"]
    diagnosis: ["Control", "SCZ", "BD", "MDD"]
  ranges:
    age:
      min: 18
      max: 100
```

---

## Correct vs. incorrect examples

### Indentation

```yaml
# CORRECT
rules:
  - step: 1
    action: "trim_whitespace"
    columns: "string"

# INCORRECT — 'columns' is not at the same level as 'action'
rules:
  - step: 1
    action: "trim_whitespace"
      columns: "string"   # ← extra indent breaks the structure
```

### List items

```yaml
# CORRECT
missing_codes:
  - "NA"
  - -9
  - ""

# INCORRECT — no dash, so these are not list items
missing_codes:
  "NA"
  -9
  ""
```

### Strings that need quotes

```yaml
# CORRECT
rationale: "Action: remove duplicates"    # colon in string — quoted
missing_codes:
  - "NA"                                  # would be null without quotes
  - "True"                                # would be boolean without quotes

# INCORRECT
rationale: Action: remove duplicates      # YAML parse error — unquoted colon
missing_codes:
  - NA                                    # treated as null, not the string "NA"
```

---

## Checking your YAML is valid

Run the environment check before applying rules:

```bash
python python/doctor.py
```

Or use the dry-run command — it will report any YAML errors before touching your data:

```bash
python python/run_cleaner.py \
  --input data/raw/my_data.csv \
  --rules config/my_cleaning_rules.yaml \
  --dry-run
```

---

← [README](../README.md) · [I have a CSV](i_have_a_csv_what_do_i_do.md) · [Cleaning rules reference](cleaning_rules_reference.md)
