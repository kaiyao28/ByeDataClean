-- ============================================================
-- 02_missingness_checks.sql
-- Purpose : Count and percentage of NULLs per column.
-- Usage   : Replace {{ table_name }}, {{ column_name }}.
-- ============================================================

-- ── Single column ─────────────────────────────────────────────────────────────
SELECT
    '{{ column_name }}'                                       AS column_name,
    COUNT(*)                                                  AS n_rows,
    SUM(CASE WHEN {{ column_name }} IS NULL THEN 1 ELSE 0 END) AS n_missing,
    ROUND(
        100.0 * SUM(CASE WHEN {{ column_name }} IS NULL THEN 1 ELSE 0 END)
        / COUNT(*), 2
    )                                                         AS pct_missing
FROM {{ table_name }};


-- ── Multiple columns — repeat this pattern ────────────────────────────────────
-- Copy-paste and UNION ALL for as many columns as you need.

SELECT 'age'     AS column_name, COUNT(*) AS n_rows,
       SUM(CASE WHEN age     IS NULL THEN 1 ELSE 0 END) AS n_missing,
       ROUND(100.0 * SUM(CASE WHEN age     IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_missing
FROM {{ table_name }}
UNION ALL
SELECT 'sex',   COUNT(*),
       SUM(CASE WHEN sex     IS NULL THEN 1 ELSE 0 END),
       ROUND(100.0 * SUM(CASE WHEN sex     IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2)
FROM {{ table_name }}
UNION ALL
SELECT 'bmi',   COUNT(*),
       SUM(CASE WHEN bmi     IS NULL THEN 1 ELSE 0 END),
       ROUND(100.0 * SUM(CASE WHEN bmi     IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2)
FROM {{ table_name }};


-- ── DuckDB shortcut — SUMMARIZE gives missingness for all columns ─────────────
-- SUMMARIZE {{ table_name }};
