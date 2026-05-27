-- ============================================================
-- 08_id_integrity_checks.sql
-- Purpose : NULL IDs, duplicate IDs, and composite key duplicates.
-- Usage   : Replace {{ table_name }}, {{ id_column }}, {{ visit_column }}.
-- ============================================================

-- ── NULL IDs ──────────────────────────────────────────────────────────────────
SELECT COUNT(*) AS n_null_ids
FROM {{ table_name }}
WHERE {{ id_column }} IS NULL;


-- ── Duplicate single ID ───────────────────────────────────────────────────────
SELECT
    {{ id_column }},
    COUNT(*) AS n_rows
FROM {{ table_name }}
WHERE {{ id_column }} IS NOT NULL
GROUP BY {{ id_column }}
HAVING COUNT(*) > 1
ORDER BY n_rows DESC;


-- ── Summary: how many IDs are duplicated? ────────────────────────────────────
SELECT
    COUNT(*) AS n_duplicated_ids
FROM (
    SELECT {{ id_column }}
    FROM {{ table_name }}
    WHERE {{ id_column }} IS NOT NULL
    GROUP BY {{ id_column }}
    HAVING COUNT(*) > 1
) sub;


-- ── Duplicate composite key (ID + date/visit) ─────────────────────────────────
-- Useful for longitudinal studies where each participant may have multiple visits.
SELECT
    {{ id_column }},
    {{ visit_column }},
    COUNT(*) AS n_rows
FROM {{ table_name }}
WHERE {{ id_column }} IS NOT NULL
GROUP BY {{ id_column }}, {{ visit_column }}
HAVING COUNT(*) > 1
ORDER BY n_rows DESC;


-- ── Check for IDs present in table A but missing from table B ────────────────
-- Useful after a merge / join to verify referential integrity.
-- Replace {{ table_a }}, {{ table_b }}, {{ id_column }} accordingly.

SELECT a.{{ id_column }}
FROM {{ table_a }} a
LEFT JOIN {{ table_b }} b ON a.{{ id_column }} = b.{{ id_column }}
WHERE b.{{ id_column }} IS NULL;
