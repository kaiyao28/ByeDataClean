-- ============================================================
-- 05_categorical_summary.sql
-- Purpose : Value counts, percentages, top and rare categories.
-- Usage   : Replace {{ table_name }}, {{ categorical_column }}.
-- ============================================================

-- ── Value counts ──────────────────────────────────────────────────────────────
SELECT
    {{ categorical_column }}   AS category,
    COUNT(*)                   AS n,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM {{ table_name }}
WHERE {{ categorical_column }} IS NOT NULL
GROUP BY {{ categorical_column }}
ORDER BY n DESC;


-- ── Top N categories (e.g. top 10) ───────────────────────────────────────────
SELECT
    {{ categorical_column }} AS category,
    COUNT(*)                 AS n
FROM {{ table_name }}
WHERE {{ categorical_column }} IS NOT NULL
GROUP BY {{ categorical_column }}
ORDER BY n DESC
LIMIT 10;


-- ── Rare categories (< 1% of non-null rows) ──────────────────────────────────
-- Adjust 0.01 to match your rare-category cutoff.
WITH total AS (
    SELECT COUNT(*) AS n_total
    FROM {{ table_name }}
    WHERE {{ categorical_column }} IS NOT NULL
),
counts AS (
    SELECT {{ categorical_column }} AS category, COUNT(*) AS n
    FROM {{ table_name }}
    WHERE {{ categorical_column }} IS NOT NULL
    GROUP BY {{ categorical_column }}
)
SELECT c.category, c.n,
       ROUND(100.0 * c.n / t.n_total, 4) AS pct
FROM counts c
CROSS JOIN total t
WHERE c.n * 1.0 / t.n_total < 0.01
ORDER BY c.n;


-- ── Number of distinct categories ────────────────────────────────────────────
SELECT COUNT(DISTINCT {{ categorical_column }}) AS n_distinct_categories
FROM {{ table_name }};


-- ── Missing (NULL) count ──────────────────────────────────────────────────────
SELECT
    SUM(CASE WHEN {{ categorical_column }} IS NULL THEN 1 ELSE 0 END) AS n_missing
FROM {{ table_name }};
