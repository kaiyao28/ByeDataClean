-- ============================================================
-- 03_duplicate_checks.sql
-- Purpose : Detect exact duplicate rows and duplicate IDs.
-- Usage   : Replace {{ table_name }}, {{ id_column }}.
-- ============================================================

-- ── Exact duplicate rows ──────────────────────────────────────────────────────
-- This groups by all columns and finds groups with count > 1.
-- Dialect note: SELECT * in a GROUP BY needs all columns listed explicitly
-- in standard SQL; some dialects (DuckDB) allow GROUP BY ALL.

-- DuckDB / PostgreSQL (list your actual columns):
SELECT
    {{ id_column }}, age, sex, bmi, diagnosis,  -- list all relevant columns
    COUNT(*) AS n_duplicates
FROM {{ table_name }}
GROUP BY {{ id_column }}, age, sex, bmi, diagnosis
HAVING COUNT(*) > 1
ORDER BY n_duplicates DESC;


-- ── DuckDB shortcut ───────────────────────────────────────────────────────────
-- SELECT *, COUNT(*) OVER (PARTITION BY * ) AS n  -- not standard; use above


-- ── Duplicate single ID ───────────────────────────────────────────────────────
SELECT
    {{ id_column }},
    COUNT(*) AS n_rows
FROM {{ table_name }}
GROUP BY {{ id_column }}
HAVING COUNT(*) > 1
ORDER BY n_rows DESC;


-- ── Duplicate composite ID (e.g. participant + visit) ─────────────────────────
SELECT
    {{ id_column }},
    {{ visit_column }},   -- replace with your second key
    COUNT(*) AS n_rows
FROM {{ table_name }}
GROUP BY {{ id_column }}, {{ visit_column }}
HAVING COUNT(*) > 1
ORDER BY n_rows DESC;


-- ── Count how many rows are involved ─────────────────────────────────────────
SELECT COUNT(*) AS rows_with_duplicate_id
FROM (
    SELECT {{ id_column }}
    FROM {{ table_name }}
    GROUP BY {{ id_column }}
    HAVING COUNT(*) > 1
) dups
JOIN {{ table_name }} t ON t.{{ id_column }} = dups.{{ id_column }};
