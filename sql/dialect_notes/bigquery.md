# BigQuery — Dialect Notes

## Approximate percentile (fast, scales to large tables)

```sql
APPROX_QUANTILES(col, 4)[OFFSET(1)] AS p25
APPROX_QUANTILES(col, 4)[OFFSET(2)] AS median
APPROX_QUANTILES(col, 4)[OFFSET(3)] AS p75
```

## Exact percentile (slower, exact)

```sql
PERCENTILE_CONT(col, 0.5) OVER () AS median
```

## Standard deviation

```sql
STDDEV(col)       -- sample standard deviation
STDDEV_POP(col)   -- population standard deviation
```

## Current date

```sql
CURRENT_DATE()    -- parentheses required in BigQuery
```

## Date casting / parsing

```sql
PARSE_DATE('%Y-%m-%d', date_str)   -- string → DATE
CAST(date_str AS DATE)             -- for ISO-format strings
```

## NULL-safe equality

```sql
col IS NULL
col IS NOT NULL
-- BigQuery does not have IS DISTINCT FROM in all versions; use COALESCE tricks
```

## Information schema (project-scoped)

```sql
SELECT column_name, data_type
FROM `my_project.my_dataset.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'my_table';
```
