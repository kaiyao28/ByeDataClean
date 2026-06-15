# Exporting Quality Checks

ByeDataClean can convert the validation rules from a cleaning rules YAML file into starter templates for three data-quality frameworks: dbt, Pandera, and Soda Core.

Generated files are **starter templates** — they require review and adaptation before use in a production pipeline. They cover the validation logic that can be inferred automatically; business logic and more complex tests must be added by hand.

---

## When to use this

After completing the profile → decide → clean cycle, you may want to operationalise the quality checks in a production pipeline. For example:

- Your data team uses **dbt** to transform data — export as dbt tests in `schema.yml`.
- Your Python pipeline uses **Pandera** for schema validation — export a `DataFrameSchema` skeleton.
- Your team monitors data freshness and quality with **Soda Core** — export a `checks.yml`.

These exports are one-directional: they represent the validation checks in the cleaning rules YAML, translated into framework-native syntax. They do not import back into ByeDataClean.

---

## Usage

```bash
# Export to dbt
python python/export_quality_checks.py \
  --rules config/example_business_cleaning_rules.yaml \
  --target dbt \
  --output exports/

# Export to Pandera (with optional type hints from schema)
python python/export_quality_checks.py \
  --schema config/schema.example.yaml \
  --rules  config/example_business_cleaning_rules.yaml \
  --target pandera \
  --output exports/

# Export to Soda Core
python python/export_quality_checks.py \
  --rules config/example_business_cleaning_rules.yaml \
  --target soda \
  --output exports/
```

---

## What is exported

The exporter reads the `validation:` section of the cleaning rules YAML:

```yaml
validation:
  required_columns:
    - order_id
    - order_date
  unique_keys:
    - [order_id]
  accepted_values:
    region: ["North America", "Europe", "APAC"]
  ranges:
    order_value:
      min: 0.01
      max: 10000.00
```

| Validation check | dbt | Pandera | Soda |
|---|---|---|---|
| `required_columns` | `not_null` test | `nullable=False` | `missing_count = 0` |
| `unique_keys` (single column) | `unique` test | `unique=True` | `duplicate_count = 0` |
| `unique_keys` (composite) | comment only | not exported | comment only |
| `accepted_values` | `accepted_values` test | `Check.isin(...)` | `invalid_count = 0` with `valid values:` |
| `ranges` | `dbt_utils.expression_is_true` | `Check.between(...)` | `min(col) >=` / `max(col) <=` |

---

## Output examples

### dbt (`exports/dbt/schema.yml`)

```yaml
version: 2

models:
  - name: my_model
    columns:
      - name: order_id
        tests:
          - not_null
          - unique
      - name: order_value
        tests:
          - dbt_utils.expression_is_true:
              expression: "order_value >= 0.01"
```

### Pandera (`exports/pandera/schema.py`)

```python
import pandera as pa
from pandera import Column, DataFrameSchema, Check

schema = DataFrameSchema({
    "order_id":    Column('object', None, nullable=False, unique=True),
    "order_value": Column('object', [Check.between(0.01, 10000.0)], nullable=True),
    "region":      Column('object', [Check.isin(["North America", "Europe", "APAC"])], nullable=True),
})
```

### Soda Core (`exports/soda/checks.yml`)

```yaml
checks for my_model:
  - missing_count(order_id) = 0:
      name: "order_id must not be null"
  - duplicate_count(order_id) = 0:
      name: "order_id must be unique"
  - invalid_count(region) = 0:
      valid values:
        - 'North America'
        - 'Europe'
        - 'APAC'
  - min(order_value) >= 0.01:
      name: "order_value must be >= 0.01"
```

---

## Limitations

- **Composite unique keys** are not natively supported in dbt or Soda. They are exported as a comment; implement as a custom test.
- **Column types** in the Pandera export are inferred from the optional `--schema` file. Without it, all columns default to `object`.
- **Business metadata** (`severity`, `owner`, etc.) is not exported — these are ByeDataClean-specific fields.
- Generated files have **no imports installed** — you still need to `pip install dbt-core`, `pip install pandera`, or `pip install soda-core` in your pipeline environment.

---

## Roadmap

Full integration (round-trip sync, CI-ready test generation) is planned for Stage 4. See [docs/roadmap.md](roadmap.md).

← [README](../README.md) · [Cleaning rules reference](cleaning_rules_reference.md) · [Roadmap](roadmap.md)
