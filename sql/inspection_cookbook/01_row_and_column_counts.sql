-- ============================================================
-- 01_row_and_column_counts.sql
-- Purpose : First sanity check — how big is the table?
-- Usage   : Replace {{ table_name }} and {{ schema_name }}.
-- ============================================================

-- ── Total row count ───────────────────────────────────────────────────────────
SELECT COUNT(*) AS n_rows
FROM {{ table_name }};


-- ── Column count via information_schema ───────────────────────────────────────
-- Supported in: PostgreSQL, DuckDB, BigQuery, SQLite (limited), most ANSI SQL.
-- Not available in some bare SQLite builds — query PRAGMA table_info() instead.

SELECT COUNT(*) AS n_columns
FROM information_schema.columns
WHERE table_name = '{{ table_name }}'
  -- Uncomment if your DB requires a schema qualifier:
  -- AND table_schema = '{{ schema_name }}'
;


-- ── SQLite alternative (no information_schema) ────────────────────────────────
-- PRAGMA table_info({{ table_name }});


-- ── DuckDB — list columns inline ─────────────────────────────────────────────
-- DESCRIBE {{ table_name }};
-- or
-- SELECT column_name, data_type
-- FROM information_schema.columns
-- WHERE table_name = '{{ table_name }}';
