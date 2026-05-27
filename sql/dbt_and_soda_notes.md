# dbt Tests and Soda Core — Notes for Production SQL Validation

The SQL inspection cookbook in this repo is intended for **interactive,
exploratory** data quality checks.  For automated, repeatable validation in a
production data pipeline, consider the tools below.

---

## dbt generic tests

If your team uses [dbt](https://docs.getdbt.com/), the built-in generic tests
cover most of the same checks as the cookbook:

| dbt test | Equivalent cookbook check |
|----------|--------------------------|
| `not_null` | `02_missingness_checks.sql` |
| `unique` | `08_id_integrity_checks.sql` |
| `accepted_values` | `09_range_and_allowed_value_checks.sql` |
| `relationships` | `08_id_integrity_checks.sql` (cross-table) |

Example `schema.yml` snippet:

```yaml
models:
  - name: my_table
    columns:
      - name: participant_id
        tests:
          - not_null
          - unique

      - name: diagnosis
        tests:
          - accepted_values:
              values: ['Control', 'SCZ', 'BD', 'MDD']
```

Run with: `dbt test`

For range checks, the [dbt-utils](https://github.com/dbt-labs/dbt-utils) package
adds `expression_is_true`, which can encode `age BETWEEN 18 AND 100`.

---

## Soda Core

[Soda Core](https://docs.soda.io/soda-core/overview-main.html) is a standalone
open-source data quality tool that works with SQL databases without requiring dbt.

Example `checks.yaml`:

```yaml
checks for my_table:
  - missing_count(participant_id) = 0
  - duplicate_count(participant_id) = 0
  - invalid_count(diagnosis) = 0:
      valid values: [Control, SCZ, BD, MDD]
  - min(age) >= 18
  - max(age) <= 100
```

Run with: `soda scan -d my_datasource checks.yaml`

---

## When to use each tool

| Tool | Best for |
|------|---------|
| This SQL cookbook | Ad-hoc interactive inspection, one-time data reviews |
| dbt generic tests | Ongoing validation baked into a dbt pipeline |
| Soda Core | Standalone data quality checks without a full dbt setup |
| Python reporter | File-based data (CSV, Excel, Parquet) before loading to a DB |
