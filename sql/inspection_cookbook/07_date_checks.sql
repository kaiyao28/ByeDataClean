-- ============================================================
-- 07_date_checks.sql
-- Purpose : Min/max date, missing dates, and future-date detection.
-- Usage   : Replace {{ table_name }}, {{ date_column }}.
-- Notes   : Date casting varies by dialect — see notes below.
-- ============================================================

-- ── Basic range and missingness ───────────────────────────────────────────────
SELECT
    MIN({{ date_column }})                                            AS min_date,
    MAX({{ date_column }})                                            AS max_date,
    SUM(CASE WHEN {{ date_column }} IS NULL THEN 1 ELSE 0 END)        AS n_missing,
    COUNT(*)                                                          AS n_total
FROM {{ table_name }};


-- ── Future-date check ────────────────────────────────────────────────────────
-- Replace CURRENT_DATE with the appropriate function for your dialect.
-- PostgreSQL / DuckDB : CURRENT_DATE
-- BigQuery            : CURRENT_DATE()
-- SQLite              : DATE('now')

SELECT COUNT(*) AS n_future_dates
FROM {{ table_name }}
WHERE {{ date_column }} > CURRENT_DATE;


-- ── Rows with future dates (inspect them) ─────────────────────────────────────
SELECT *
FROM {{ table_name }}
WHERE {{ date_column }} > CURRENT_DATE
LIMIT 20;


-- ── Casting strings to dates — dialect notes ──────────────────────────────────
-- If {{ date_column }} is stored as a VARCHAR:

-- PostgreSQL:
--   CAST({{ date_column }} AS DATE)
--   or {{ date_column }}::DATE

-- DuckDB:
--   TRY_CAST({{ date_column }} AS DATE)   -- returns NULL on parse failure

-- BigQuery:
--   PARSE_DATE('%Y-%m-%d', {{ date_column }})

-- SQLite:
--   date({{ date_column }})               -- expects ISO format YYYY-MM-DD


-- ── Count unparseable date strings (DuckDB) ───────────────────────────────────
-- SELECT COUNT(*) AS n_bad_dates
-- FROM {{ table_name }}
-- WHERE TRY_CAST({{ date_column }} AS DATE) IS NULL
--   AND {{ date_column }} IS NOT NULL;
