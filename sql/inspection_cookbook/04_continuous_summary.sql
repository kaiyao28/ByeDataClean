-- ============================================================
-- 04_continuous_summary.sql
-- Purpose : Descriptive statistics for a continuous column.
-- Usage   : Replace {{ table_name }}, {{ continuous_column }}.
-- ============================================================

-- ── Core summary (standard SQL, works everywhere) ────────────────────────────
SELECT
    '{{ continuous_column }}'                           AS column_name,
    COUNT({{ continuous_column }})                      AS n_non_null,
    COUNT(*) - COUNT({{ continuous_column }})           AS n_missing,
    ROUND(AVG({{ continuous_column }}), 4)              AS mean,
    -- STDDEV / STDEV / STD — dialect-dependent (see notes below)
    ROUND(MIN({{ continuous_column }}), 4)              AS min_val,
    ROUND(MAX({{ continuous_column }}), 4)              AS max_val
FROM {{ table_name }};


-- ── Standard deviation — dialect notes ───────────────────────────────────────
-- PostgreSQL, DuckDB : STDDEV(col) or STDDEV_SAMP(col)
-- SQLite             : No built-in; use extension or calculate manually
-- BigQuery           : STDDEV(col) or STDDEV_SAMP(col)

-- Example (PostgreSQL / DuckDB):
SELECT
    ROUND(STDDEV_SAMP({{ continuous_column }}), 4) AS sd
FROM {{ table_name }};


-- ── Percentiles — dialect notes ───────────────────────────────────────────────
-- PostgreSQL:
--   PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {{ continuous_column }}) AS p25
--   PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY {{ continuous_column }}) AS median
--   PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {{ continuous_column }}) AS p75

-- DuckDB:
--   QUANTILE_CONT({{ continuous_column }}, 0.25) AS p25
--   QUANTILE_CONT({{ continuous_column }}, 0.50) AS median
--   QUANTILE_CONT({{ continuous_column }}, 0.75) AS p75

-- BigQuery:
--   APPROX_QUANTILES({{ continuous_column }}, 4)[OFFSET(1)] AS p25
--   APPROX_QUANTILES({{ continuous_column }}, 4)[OFFSET(2)] AS median
--   APPROX_QUANTILES({{ continuous_column }}, 4)[OFFSET(3)] AS p75

-- SQLite: No native percentile; approximate with ORDER BY + LIMIT:
-- SELECT {{ continuous_column }}
-- FROM {{ table_name }}
-- WHERE {{ continuous_column }} IS NOT NULL
-- ORDER BY {{ continuous_column }}
-- LIMIT 1 OFFSET (SELECT COUNT(*)/2 FROM {{ table_name }} WHERE {{ continuous_column }} IS NOT NULL);


-- ── Full summary (PostgreSQL / DuckDB) ───────────────────────────────────────
SELECT
    COUNT({{ continuous_column }})                                                      AS n,
    COUNT(*) - COUNT({{ continuous_column }})                                           AS n_missing,
    ROUND(AVG({{ continuous_column }}), 4)                                              AS mean,
    ROUND(STDDEV_SAMP({{ continuous_column }}), 4)                                      AS sd,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY {{ continuous_column }}), 4)    AS median,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {{ continuous_column }}), 4)    AS p25,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {{ continuous_column }}), 4)    AS p75,
    ROUND(MIN({{ continuous_column }}), 4)                                              AS min_val,
    ROUND(MAX({{ continuous_column }}), 4)                                              AS max_val
FROM {{ table_name }};
