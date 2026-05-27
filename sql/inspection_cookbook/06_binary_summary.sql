-- ============================================================
-- 06_binary_summary.sql
-- Purpose : Counts, percentages, and imbalance check for binary variables.
-- Usage   : Replace {{ table_name }}, {{ binary_column }}.
-- ============================================================

-- ── Value counts and percentages ─────────────────────────────────────────────
SELECT
    {{ binary_column }}   AS value,
    COUNT(*)              AS n,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2
    )                     AS pct
FROM {{ table_name }}
WHERE {{ binary_column }} IS NOT NULL
GROUP BY {{ binary_column }}
ORDER BY n DESC;


-- ── Missing count ─────────────────────────────────────────────────────────────
SELECT
    SUM(CASE WHEN {{ binary_column }} IS NULL THEN 1 ELSE 0 END) AS n_missing
FROM {{ table_name }};


-- ── Imbalance check ───────────────────────────────────────────────────────────
-- Flags if the dominant class exceeds 95% of non-null rows.
-- Adjust 0.95 to your threshold.
WITH counts AS (
    SELECT {{ binary_column }} AS value, COUNT(*) AS n
    FROM {{ table_name }}
    WHERE {{ binary_column }} IS NOT NULL
    GROUP BY {{ binary_column }}
),
total AS (SELECT SUM(n) AS n_total FROM counts)
SELECT
    c.value,
    c.n,
    ROUND(100.0 * c.n / t.n_total, 2)  AS pct,
    CASE
        WHEN MAX(c.n) OVER () * 1.0 / t.n_total >= 0.95
        THEN 'IMBALANCED (dominant class >= 95%)'
        ELSE 'OK'
    END AS imbalance_flag
FROM counts c
CROSS JOIN total t
ORDER BY c.n DESC;
