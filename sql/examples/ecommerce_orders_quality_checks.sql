-- ============================================================
-- ecommerce_orders_quality_checks.sql
--
-- Purpose : End-to-end data-quality checks for an orders table,
--           mirroring the Python/R ByeDataClean workflow.
--
-- Table   : orders
-- Columns : order_id, customer_id, order_date, order_value,
--           currency, region, acquisition_channel,
--           product_category, refunded, signup_date
--
-- Dialect : ANSI SQL with notes for BigQuery, Snowflake,
--           Postgres, and DuckDB where syntax differs.
--
-- Usage   : Replace `orders` with your actual table/schema name.
--           Run each block independently in your SQL client.
-- ============================================================


-- ── 1. Row count and date range ───────────────────────────────────────────────
-- Python equivalent: QC reporter row-count + missingness summary

SELECT
    COUNT(*)                    AS row_count,
    MIN(order_date)             AS min_order_date,
    MAX(order_date)             AS max_order_date,
    COUNT(DISTINCT order_id)    AS unique_order_ids,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM orders;


-- ── 2. Missingness checks ─────────────────────────────────────────────────────
-- Python equivalent: missingness summary + create_missingness_flags

SELECT
    COUNT(*)                                                        AS total_rows,

    SUM(CASE WHEN order_id           IS NULL THEN 1 ELSE 0 END)    AS missing_order_id,
    SUM(CASE WHEN customer_id        IS NULL THEN 1 ELSE 0 END)    AS missing_customer_id,
    SUM(CASE WHEN order_date         IS NULL THEN 1 ELSE 0 END)    AS missing_order_date,
    SUM(CASE WHEN order_value        IS NULL THEN 1 ELSE 0 END)    AS missing_order_value,
    SUM(CASE WHEN acquisition_channel IS NULL THEN 1 ELSE 0 END)   AS missing_channel,

    ROUND(100.0 * SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                            AS missing_customer_id_pct,
    ROUND(100.0 * SUM(CASE WHEN acquisition_channel IS NULL THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                            AS missing_channel_pct
FROM orders;

-- Business impact: missing customer_id rows are excluded from retention cohort models.
-- Missing acquisition_channel rows bias channel attribution reporting.


-- ── 3. Duplicate order IDs ────────────────────────────────────────────────────
-- Python equivalent: remove_exact_duplicates / duplicate detector

SELECT
    order_id,
    COUNT(*)           AS n_rows,
    SUM(order_value)   AS total_recorded_value,
    MAX(order_value)   AS assumed_true_value,
    SUM(order_value) - MAX(order_value) AS duplicate_overstatement
FROM orders
GROUP BY order_id
HAVING COUNT(*) > 1
ORDER BY n_rows DESC;

-- Business impact: duplicated order IDs inflate GMV and order counts.
-- The `duplicate_overstatement` column shows the exact revenue overcounting.


-- ── 4. Revenue impact of duplicate orders ─────────────────────────────────────

WITH duplicate_orders AS (
    SELECT
        order_id,
        SUM(order_value)   AS total_recorded_value,
        MAX(order_value)   AS assumed_true_value
    FROM orders
    GROUP BY order_id
    HAVING COUNT(*) > 1
)
SELECT
    COUNT(*)                                           AS duplicate_order_ids,
    SUM(total_recorded_value - assumed_true_value)     AS estimated_revenue_overstatement
FROM duplicate_orders;


-- ── 5. Invalid or out-of-range order values ───────────────────────────────────
-- Python equivalent: flag_values_outside_range

SELECT
    order_id,
    order_value,
    CASE
        WHEN order_value < 0        THEN 'negative'
        WHEN order_value = 0        THEN 'zero'
        WHEN order_value > 10000    THEN 'above_ceiling'
        ELSE 'ok'
    END AS value_flag
FROM orders
WHERE order_value < 0.01
   OR order_value > 10000
   OR order_value IS NULL
ORDER BY order_value;


-- ── 6. Date validity checks ───────────────────────────────────────────────────
-- Python equivalent: parse_dates action

-- Future-dated orders (appear in current-period revenue incorrectly)
SELECT
    order_id,
    order_date,
    'future_date' AS flag
FROM orders
WHERE order_date > CURRENT_DATE
-- BigQuery:  WHERE order_date > CURRENT_DATE()
-- DuckDB:    WHERE order_date > CURRENT_DATE
-- Snowflake: WHERE order_date > CURRENT_DATE()

UNION ALL

-- Orders where signup is after order (referential integrity check)
SELECT
    order_id,
    order_date,
    'order_before_signup' AS flag
FROM orders
WHERE signup_date IS NOT NULL
  AND order_date < signup_date;


-- ── 7. Category consistency — region labels ───────────────────────────────────
-- Python equivalent: standardise_categories

SELECT
    region,
    COUNT(*) AS n_rows
FROM orders
GROUP BY region
ORDER BY n_rows DESC;

-- Look for variants like: 'us', 'USA', 'United States', 'North America'
-- These should map to a single canonical label.


-- ── 8. Category consistency — product categories ──────────────────────────────

SELECT
    product_category,
    COUNT(*) AS n_rows
FROM orders
GROUP BY product_category
ORDER BY n_rows DESC;

-- Look for: case variants (APPAREL vs Apparel), typos (Electroncis vs Electronics),
-- spacing differences (home & garden vs Home & Garden).


-- ── 9. Currency code consistency ─────────────────────────────────────────────
-- Python equivalent: standardise_case

SELECT
    currency,
    COUNT(*) AS n_rows
FROM orders
GROUP BY currency
ORDER BY n_rows DESC;

-- Expected: ISO 4217 codes (USD, GBP, EUR) in consistent case.
-- Flag: usd, gbp, Eur, GBP mixed with GBP, etc.


-- ── 10. Missing acquisition channel by region ─────────────────────────────────
-- Python equivalent: flag_missing_channel + cross-tab

SELECT
    region,
    COUNT(*)                                                                 AS total_orders,
    SUM(CASE WHEN acquisition_channel IS NULL THEN 1 ELSE 0 END)            AS missing_channel,
    ROUND(100.0 * SUM(CASE WHEN acquisition_channel IS NULL THEN 1 ELSE 0 END)
          / COUNT(*), 1)                                                     AS missing_channel_pct
FROM orders
GROUP BY region
ORDER BY missing_channel_pct DESC;


-- ── 11. Before / after revenue reconciliation ─────────────────────────────────
-- Python equivalent: validation report + business impact calculator

WITH
raw_gmv AS (
    SELECT SUM(order_value) AS gmv_before_dedup FROM orders
),
deduped_gmv AS (
    SELECT SUM(order_value) AS gmv_after_dedup
    FROM (
        SELECT DISTINCT ON (order_id) order_value
        FROM orders
        ORDER BY order_id, order_value DESC
        -- Postgres / DuckDB syntax. BigQuery: use ROW_NUMBER() instead.
        -- Snowflake: use QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_value DESC) = 1
    ) deduped
),
valid_gmv AS (
    SELECT SUM(order_value) AS gmv_after_filters
    FROM orders
    WHERE order_value > 0
      AND order_date <= CURRENT_DATE
      AND order_id IN (
          SELECT order_id FROM orders GROUP BY order_id HAVING COUNT(*) = 1
      )
)
SELECT
    r.gmv_before_dedup,
    d.gmv_after_dedup,
    v.gmv_after_filters,
    r.gmv_before_dedup - d.gmv_after_dedup  AS dedup_adjustment,
    r.gmv_before_dedup - v.gmv_after_filters AS total_adjustment
FROM raw_gmv r, deduped_gmv d, valid_gmv v;


-- ── 12. Quality scorecard summary ─────────────────────────────────────────────
-- Python equivalent: scorecard output (PASS / WARNING / BLOCKER)
--
-- Run this after all checks above. Replace the subquery results
-- with actual counts from your earlier queries.

SELECT
    'order_id_uniqueness'          AS check_name,
    (SELECT COUNT(*) FROM orders GROUP BY order_id HAVING COUNT(*) > 1)
                                   AS issues_found,
    CASE WHEN (SELECT COUNT(*) FROM orders GROUP BY order_id HAVING COUNT(*) > 1) > 0
         THEN 'BLOCKER' ELSE 'PASS' END AS status

UNION ALL

SELECT
    'order_date_validity',
    (SELECT COUNT(*) FROM orders WHERE order_date > CURRENT_DATE OR order_date IS NULL),
    CASE WHEN (SELECT COUNT(*) FROM orders WHERE order_date > CURRENT_DATE OR order_date IS NULL) > 0
         THEN 'BLOCKER' ELSE 'PASS' END

UNION ALL

SELECT
    'customer_id_completeness',
    (SELECT SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) FROM orders),
    CASE WHEN (SELECT SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) FROM orders) > 0
         THEN 'WARNING' ELSE 'PASS' END

UNION ALL

SELECT
    'acquisition_channel_completeness',
    (SELECT SUM(CASE WHEN acquisition_channel IS NULL THEN 1 ELSE 0 END) FROM orders),
    CASE WHEN (SELECT SUM(CASE WHEN acquisition_channel IS NULL THEN 1 ELSE 0 END) FROM orders) > 0
         THEN 'WARNING' ELSE 'PASS' END

UNION ALL

SELECT
    'order_value_range',
    (SELECT COUNT(*) FROM orders WHERE order_value < 0.01 OR order_value > 10000),
    CASE WHEN (SELECT COUNT(*) FROM orders WHERE order_value < 0.01 OR order_value > 10000) > 0
         THEN 'WARNING' ELSE 'PASS' END

ORDER BY
    CASE status WHEN 'BLOCKER' THEN 1 WHEN 'WARNING' THEN 2 ELSE 3 END;
