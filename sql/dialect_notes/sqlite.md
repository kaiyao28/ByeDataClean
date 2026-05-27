# SQLite — Dialect Notes

SQLite has no built-in `STDDEV`, `PERCENTILE_CONT`, or `information_schema`.
Workarounds are listed below.

## Standard deviation (no built-in)

Compute manually with:

```sql
SELECT
    SQRT(
        AVG(col * col) - AVG(col) * AVG(col)
    ) AS sd_population
FROM my_table
WHERE col IS NOT NULL;
```

Or load the [SQLite statistics extension](https://www.sqlite.org/contrib/) if available.

## Approximate median (no built-in PERCENTILE)

```sql
SELECT col AS approx_median
FROM my_table
WHERE col IS NOT NULL
ORDER BY col
LIMIT 1 OFFSET (
    SELECT COUNT(*) / 2
    FROM my_table
    WHERE col IS NOT NULL
);
```

This returns the lower-median for even-N datasets.

## Table column info (no information_schema)

```sql
PRAGMA table_info(my_table);
```

## Current date

```sql
DATE('now')          -- YYYY-MM-DD
DATETIME('now')      -- YYYY-MM-DD HH:MM:SS
```

## Date comparison

Dates are stored as TEXT in ISO format. Use string comparison:

```sql
WHERE date_col > DATE('now')   -- future dates
WHERE date_col IS NULL         -- missing
```

## Window functions

Supported since SQLite 3.25 (2018). If using an older version, the OVER ()
clauses in the cookbook templates will fail — upgrade SQLite or rewrite with
subqueries.
