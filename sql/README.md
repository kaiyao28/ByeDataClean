# SQL Inspection Cookbook

## Why SQL is separate from the Python / R reporter

The Python and R reporters are **runnable programs** — give them a file, get a
structured report.  SQL is intentionally different: it is a **step-by-step
inspection cookbook** of copy-paste query templates you run interactively
against a database or query engine.

The separation exists because:

- SQL inspection happens *before* data leaves the database (no file extract needed).
- Different teams use different engines (DuckDB, PostgreSQL, BigQuery, SQLite).
- Query templates are more reusable than a Python wrapper that abstracts them away.
- Production database validation belongs in dbt tests or Soda checks, not ad-hoc scripts.

---

## How to use the inspection cookbook

1. Open a SQL file from `inspection_cookbook/`.
2. Replace the `{{ placeholder }}` tokens with your actual table and column names.
3. Run the query in your preferred SQL client (DBeaver, DataGrip, `psql`, DuckDB CLI, etc.).
4. Read the inline comments — they explain dialect differences where they exist.

Work through the files in order for a complete inspection:

| File | What it checks |
|------|---------------|
| `01_row_and_column_counts.sql` | Basic table dimensions |
| `02_missingness_checks.sql` | NULL counts per column |
| `03_duplicate_checks.sql` | Exact duplicate rows, duplicate IDs |
| `04_continuous_summary.sql` | Mean, SD, min, max, percentiles |
| `05_categorical_summary.sql` | Value counts, rare categories |
| `06_binary_summary.sql` | Binary value counts, imbalance flag |
| `07_date_checks.sql` | Date range, missing dates, future dates |
| `08_id_integrity_checks.sql` | NULL IDs, duplicate IDs, composite keys |
| `09_range_and_allowed_value_checks.sql` | Out-of-range values, disallowed categories |

---

## Dialect notes

See `dialect_notes/` for engine-specific tips:

- [DuckDB](dialect_notes/duckdb.md)
- [PostgreSQL](dialect_notes/postgres.md)
- [BigQuery](dialect_notes/bigquery.md)
- [SQLite](dialect_notes/sqlite.md)

---

## Production database validation

If you are validating data in a production database pipeline, ad-hoc SQL
inspection is not enough.  See [`dbt_and_soda_notes.md`](dbt_and_soda_notes.md)
for guidance on dbt generic tests and Soda Core.
