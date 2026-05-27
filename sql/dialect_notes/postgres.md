# PostgreSQL — Dialect Notes

## Percentile

```sql
PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY col) AS median
PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY col) AS p25
PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY col) AS p75
```

## Standard deviation

```sql
STDDEV(col)        -- alias for STDDEV_SAMP
STDDEV_SAMP(col)   -- sample standard deviation
STDDEV_POP(col)    -- population standard deviation
```

## Date casting

```sql
CAST(date_str AS DATE)
date_str::DATE     -- PostgreSQL shorthand
```

## Current date

```sql
CURRENT_DATE       -- no parentheses needed
NOW()::DATE        -- timestamp truncated to date
```

## List all columns with data types

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name   = 'my_table'
ORDER BY ordinal_position;
```
