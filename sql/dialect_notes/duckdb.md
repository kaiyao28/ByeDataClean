# DuckDB — Dialect Notes

DuckDB is an excellent choice for local data inspection: it can query CSV,
Parquet, and JSON files directly without loading them into a table first.

## Useful DuckDB-specific commands

```sql
-- Describe a table or file
DESCRIBE my_table;
DESCRIBE SELECT * FROM 'data/raw/my_data.csv';

-- Summarise all columns at once (similar to pandas.describe())
SUMMARIZE my_table;
SUMMARIZE SELECT * FROM 'data/raw/my_data.csv';

-- Read a CSV directly (no import step)
SELECT * FROM 'data/raw/my_data.csv' LIMIT 5;

-- Percentile / quantile
SELECT QUANTILE_CONT(age, 0.5) AS median_age FROM my_table;

-- Try-cast (returns NULL on failure instead of error)
SELECT TRY_CAST(date_str AS DATE) FROM my_table;

-- GROUP BY ALL (avoid listing every column)
SELECT *, COUNT(*) AS n FROM my_table GROUP BY ALL HAVING n > 1;
```

## Percentile syntax

```sql
QUANTILE_CONT(col, 0.25)   -- 25th percentile
QUANTILE_CONT(col, 0.50)   -- median
QUANTILE_CONT(col, 0.75)   -- 75th percentile
```

## Standard deviation

```sql
STDDEV_SAMP(col)   -- sample standard deviation
STDDEV_POP(col)    -- population standard deviation
```

## Running DuckDB against a CSV from the CLI

```bash
duckdb -c "SUMMARIZE SELECT * FROM 'data/raw/my_data.csv';"
```
