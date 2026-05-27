# Package Comparison

A brief reference for choosing the right tool.

---

## Python packages

### ydata-profiling
- **What**: Generates a comprehensive HTML report from a DataFrame — distributions, correlations, missing values, duplicates.
- **Strength**: Rich interactive output; minimal code.
- **Limitation**: Can be slow on wide or large datasets; heavyweight dependency footprint.
- **Use when**: You want a shareable HTML report without writing any code.

### skimpy
- **What**: Lightweight console summary — similar to R's `skimr`.
- **Strength**: Fast, minimal, prints nicely in a terminal or notebook.
- **Limitation**: No HTML output; no schema validation.
- **Use when**: You want a quick terminal summary alongside your own analysis.

### pandera
- **What**: Schema-based DataFrame validation with type annotations.
- **Strength**: Pythonic schema definitions; integrates with type checkers.
- **Limitation**: Validation only, no profiling; requires schema upfront.
- **Use when**: You have a defined schema and want to enforce it programmatically.

### Great Expectations
- **What**: Full data quality framework with HTML "data docs".
- **Strength**: Very powerful; integrates with pipelines; rich expectation library.
- **Limitation**: Heavy setup; steep learning curve; overkill for one-off checks.
- **Use when**: You need repeatable, documented expectations in a data pipeline.

---

## R packages

### skimr
- **What**: Produces a clean, grouped summary via `skim(df)`.
- **Strength**: Works immediately on any data frame; handles mixed types.
- **Limitation**: Console-only output; no HTML report.
- **Use when**: You want a quick summary at the start of any analysis.

### janitor
- **What**: Data cleaning helpers — `clean_names()`, `tabyl()`, `remove_empty()`.
- **Strength**: Extremely practical; fills gaps that base R and dplyr leave.
- **Limitation**: Not a profiler; no statistical summaries.
- **Use when**: Cleaning messy column names, cross-tabulating, removing empty rows/cols.

### DataExplorer
- **What**: Generates a full HTML report via `create_report(df)`.
- **Strength**: Very fast to use; covers distributions, missingness, PCA.
- **Limitation**: Less customisable than ydata-profiling equivalent.
- **Use when**: You want a one-click HTML report in R.

### pointblank
- **What**: Data validation framework with HTML agent reports.
- **Strength**: Very readable validation DSL; integrates with pipelines.
- **Limitation**: More complex than basic schema checks; requires schema design.
- **Use when**: You want documented, pipeline-ready validation in R.

---

## SQL / pipeline tools

### dbt generic tests
- **What**: `not_null`, `unique`, `accepted_values`, `relationships` built into dbt.
- **Strength**: Version-controlled, runs automatically in dbt pipeline.
- **Use when**: Your data lives in a warehouse and you use dbt.

### Soda Core
- **What**: Standalone data quality checks in YAML.
- **Strength**: Works without dbt; supports many databases.
- **Use when**: You want automated checks without a full dbt setup.
