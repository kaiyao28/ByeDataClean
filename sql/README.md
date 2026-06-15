# SQL quality-check cookbook

This folder contains SQL templates for running the same data-quality checks as the ByeDataClean Python/R workflow — but inside a warehouse or database, without extracting data into pandas.

---

## When to use SQL instead of Python/R

Use the Python/R extract workflow when:
- The dataset arrives as a CSV, Excel, TSV, or Parquet file.
- You need to produce a cleaned file, audit log, scorecard, or stakeholder summary.
- The dataset is small-to-medium and fits comfortably in memory.

Use the SQL workflow when:
- The data lives in a warehouse (Postgres, BigQuery, Snowflake, DuckDB, Redshift).
- Exporting the full table is impractical or slow.
- Checks need to run close to production data, not in a local Python session.
- You want to validate data before building a dbt model or refreshing a dashboard.

The same business questions apply in both cases:
> "Are there duplicate orders? Are revenue figures trustworthy? Which records are missing a customer ID?"

---

## How SQL checks map to ByeDataClean concepts

| ByeDataClean concept | Python/R | SQL equivalent |
|---|---|---|
| Profile: row counts | QC reporter | `COUNT(*)` + `COUNT(DISTINCT id)` |
| Profile: missingness | missingness summary | `SUM(CASE WHEN col IS NULL THEN 1 ELSE 0 END)` |
| Duplicate detection | duplicate detector | `GROUP BY id HAVING COUNT(*) > 1` |
| Range validation | `flag_values_outside_range` | `WHERE value < min OR value > max` |
| Date validity | `parse_dates` | `WHERE date_col > CURRENT_DATE OR date_col IS NULL` |
| Category consistency | `standardise_categories` | `GROUP BY category ORDER BY COUNT(*) DESC` |
| Accepted values | YAML `accepted_values` | `WHERE col NOT IN ('val1', 'val2', ...)` |
| Before/after reconciliation | validation report | Row-count + metric comparison CTEs |
| Business impact | scorecard + impact report | Duplicate revenue overstatement, missing-rate % |
| Quality scorecard | `--scorecard` flag | Aggregated PASS / WARNING / BLOCKER UNION query |

---

## Inspection cookbook

Work through these files in order for a complete quality check. Replace `{{ table_name }}` with your actual table name.

| File | What it checks | Business question protected |
|---|---|---|
| `01_row_and_column_counts.sql` | Table dimensions, date range | Is this the full extract? |
| `02_missingness_checks.sql` | NULL counts and rates per column | Which columns have gaps? |
| `03_duplicate_checks.sql` | Exact duplicate rows, duplicate IDs | Are order/customer IDs unique? |
| `04_continuous_summary.sql` | Mean, SD, min, max, percentiles | Are numeric values in a plausible range? |
| `05_categorical_summary.sql` | Value counts, rare categories | Are category labels consistent? |
| `06_binary_summary.sql` | Binary value counts, imbalance flag | Are flag/status columns clean? |
| `07_date_checks.sql` | Date range, future dates, NULLs | Do dates fall in the expected period? |
| `08_id_integrity_checks.sql` | NULL IDs, duplicate IDs, composite keys | Can rows be joined to other tables? |
| `09_range_and_allowed_value_checks.sql` | Out-of-range values, disallowed categories | Do values meet business rules? |

---

## Worked example: e-commerce orders

`examples/ecommerce_orders_quality_checks.sql` runs end-to-end quality checks on an orders table with the same issues as the bundled Python case study:

- duplicate order IDs and GMV overstatement
- future-dated and unparseable order dates
- missing customer IDs and acquisition channels
- negative and zero order values
- inconsistent region, currency, and category labels
- before/after revenue reconciliation
- final PASS / WARNING / BLOCKER scorecard query

See [docs/case_studies/ecommerce_revenue_quality.md](../docs/case_studies/ecommerce_revenue_quality.md) for the full business context and Python equivalent.

---

## Dialect notes

See `dialect_notes/` for engine-specific syntax differences:

| Engine | Notes file | Key differences |
|---|---|---|
| DuckDB | [dialect_notes/duckdb.md](dialect_notes/duckdb.md) | `DESCRIBE`, `CURRENT_DATE`, `DISTINCT ON` |
| PostgreSQL | [dialect_notes/postgres.md](dialect_notes/postgres.md) | `DISTINCT ON`, `ILIKE`, window functions |
| BigQuery | [dialect_notes/bigquery.md](dialect_notes/bigquery.md) | `CURRENT_DATE()`, `QUALIFY`, backtick names |
| SQLite | [dialect_notes/sqlite.md](dialect_notes/sqlite.md) | No `information_schema`, limited date functions |

---

## Production pipeline validation

Ad-hoc SQL inspection is for analyst review, not automated pipeline monitoring. For continuous validation in production pipelines, see:

- [`dbt_and_soda_notes.md`](dbt_and_soda_notes.md) — dbt generic tests and Soda Core
- [`docs/exporting_quality_checks.md`](../docs/exporting_quality_checks.md) — export ByeDataClean YAML rules to dbt, Pandera, or Soda starter templates
- [`docs/package_comparison.md`](../docs/package_comparison.md) — when to use which tool

---

← [README](../README.md) · [Case study](../docs/case_studies/ecommerce_revenue_quality.md)
