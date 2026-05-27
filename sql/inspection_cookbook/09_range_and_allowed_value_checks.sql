-- ============================================================
-- 09_range_and_allowed_value_checks.sql
-- Purpose : Detect out-of-range numerics and disallowed category values.
-- Usage   : Replace {{ table_name }}, {{ column_name }}, {{ min }}, {{ max }}.
-- ============================================================

-- ── Numeric: out-of-range rows ────────────────────────────────────────────────
-- Adjust min/max to your expected valid range.
SELECT COUNT(*) AS n_out_of_range
FROM {{ table_name }}
WHERE {{ continuous_column }} < {{ min }}
   OR {{ continuous_column }} > {{ max }};

-- Inspect the offending rows:
SELECT *
FROM {{ table_name }}
WHERE {{ continuous_column }} < {{ min }}
   OR {{ continuous_column }} > {{ max }}
LIMIT 20;


-- ── Numeric: values below minimum ────────────────────────────────────────────
SELECT COUNT(*) AS n_below_min
FROM {{ table_name }}
WHERE {{ continuous_column }} < {{ min }};


-- ── Numeric: values above maximum ────────────────────────────────────────────
SELECT COUNT(*) AS n_above_max
FROM {{ table_name }}
WHERE {{ continuous_column }} > {{ max }};


-- ── Categorical: disallowed values ───────────────────────────────────────────
-- List the allowed values in the IN (...) clause.
SELECT
    {{ categorical_column }} AS value,
    COUNT(*)                 AS n
FROM {{ table_name }}
WHERE {{ categorical_column }} IS NOT NULL
  AND {{ categorical_column }} NOT IN ('Control', 'SCZ', 'BD', 'MDD')
GROUP BY {{ categorical_column }}
ORDER BY n DESC;


-- ── Whitespace / case inconsistency ──────────────────────────────────────────
-- Check for leading/trailing spaces:
SELECT COUNT(*) AS n_whitespace_issues
FROM {{ table_name }}
WHERE {{ categorical_column }} <> TRIM({{ categorical_column }});

-- Check for mixed-case duplicates (PostgreSQL / DuckDB / BigQuery):
SELECT
    LOWER({{ categorical_column }}) AS lower_value,
    COUNT(DISTINCT {{ categorical_column }}) AS n_case_variants
FROM {{ table_name }}
WHERE {{ categorical_column }} IS NOT NULL
GROUP BY LOWER({{ categorical_column }})
HAVING COUNT(DISTINCT {{ categorical_column }}) > 1;
