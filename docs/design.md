# Design Notes

## Python and R: runnable reporters

The Python and R reporters are **programs**: you run them against a file, they
produce a structured markdown (and optionally HTML) report.  They are designed
to be orchestration layers, not replacements for mature profiling packages.

### What they do

- Load data from a file or a built-in example dataset.
- Infer variable types (continuous, binary, categorical, date, id, empty, constant).
- Compute standard descriptive statistics using **pandas / numpy** (Python) or
  **skimr** (R).
- Apply a small set of custom checks (high missingness, imbalance, high cardinality,
  future dates, duplicates, whitespace/case inconsistencies).
- Optionally call **ydata-profiling** (Python) or **DataExplorer** (R) for a
  richer full HTML report.
- Optionally validate against a user-supplied schema file.

### What they do NOT do

- Reinvent descriptive statistics.  pandas `.describe()`, `skimr::skim()`, and
  ydata-profiling already do this well.
- Replace data validation frameworks like Pandera, Great Expectations, or dbt tests.
- Generate synthetic test data (that is optional and lives in `local/`).

---

## SQL: separate inspection cookbook

SQL is intentionally **not** implemented as a runnable reporter.  Instead it is
a cookbook of query templates.

**Why separate?**

1. SQL inspection is a different workflow — you run queries interactively against
   a live database, not against a file extract.
2. Different teams use different engines (DuckDB, PostgreSQL, BigQuery, SQLite),
   and a single abstraction layer would hide important dialect differences.
3. Production database validation belongs in dbt tests or Soda checks, not
   an ad-hoc Python SQL wrapper.
4. Query templates are self-documenting and easy to adapt without understanding
   a Python/R codebase.

---

## Profiling vs validation

| Goal | Tool |
|------|------|
| Understand data distributions interactively | Python/R reporter (quick mode) |
| Share a detailed data quality report | Python/R reporter (full mode via ydata-profiling / DataExplorer) |
| Validate schema constraints in a file | schema.yaml + `--schema` flag |
| Validate data in a SQL database (ad hoc) | SQL inspection cookbook |
| Validate data in a production pipeline | dbt tests or Soda Core |

---

## Why not make optional packages mandatory?

The reporter must work on a freshly cloned repo with only:
```
pip install pandas numpy pyyaml
```

Optional packages (seaborn, skimpy, ydata-profiling, scikit-learn) enhance the
output but are not required.  This keeps CI lightweight and avoids forcing heavy
installs on users who only need a basic summary.
