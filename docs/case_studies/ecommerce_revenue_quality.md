# Case Study: E-Commerce Revenue Quality

**Dataset:** `data/examples/dirty_orders.csv`
**Rules:** `config/example_business_cleaning_rules.yaml`
**Industry:** E-commerce / retail analytics

---

## Business question

> Can we trust the Q1–Q2 2024 order data for the board revenue presentation?

A data analyst is asked to produce a GMV (Gross Merchandise Value) summary by region and acquisition channel for a quarterly business review. Before presenting, they run ByeDataClean on the raw orders export.

---

## The dataset

60 rows representing orders placed between January and May 2024, exported from an order management system. Columns:

| Column | Description |
|---|---|
| `order_id` | Unique order identifier |
| `customer_id` | Customer identifier (links to CRM) |
| `order_date` | Date order was placed |
| `order_value` | Order value in the order currency |
| `currency` | ISO currency code |
| `region` | Sales region |
| `acquisition_channel` | Marketing channel that drove the order |
| `product_category` | Product category |
| `refunded` | Whether the order was refunded |
| `signup_date` | Date the customer signed up |

---

## What ByeDataClean detects

Running the profiler (`python python/run_reporter.py --input data/examples/dirty_orders.csv`) flags:

| Issue | Detail | Business risk |
|---|---|---|
| **Duplicate order ID** | ORD-1005 appears twice, identical on all columns | Inflates GMV by $312.75 |
| **Negative order value** | ORD-1021: order_value = -149.99 | Unclear: refund or entry error? Suppresses GMV |
| **Zero order value** | ORD-1028: order_value = 0.00 | Ambiguous: cancelled or data gap? |
| **Future-dated order** | ORD-1050: order_date = 2027-03-15 | Will appear in "current period" if not filtered |
| **Invalid calendar date** | ORD-1030: order_date = 2023-02-29 (non-leap year) | Crashes date parsing; order excluded from time series |
| **Missing customer_id** | 5 orders (8%) have no customer_id | Excludes those orders from retention/cohort analysis |
| **Missing acquisition_channel** | 5 orders (8%) have no channel | Biases channel attribution; organic underreported |
| **Inconsistent region labels** | "us", "USA", "united states", "Asia Pacific", "EU" | Regional dashboard double-counts North America and Europe |
| **Inconsistent currency casing** | "usd", "gbp", "Eur" | FX conversion lookups fail on non-uppercase codes |
| **Category typo / casing** | "Electroncis", "APPAREL", "home & garden", "Home and Garden" | Electronics revenue appears fragmented across 3 rows |
| **Inconsistent refunded flag** | "Y", "True", "FALSE" mixed with "yes"/"no" | Refund rate calculation is incorrect |

---

## Cleaning rules applied

The 12-step rules in `config/example_business_cleaning_rules.yaml` address each issue:

| Step | Action | What it fixes |
|---|---|---|
| 1 | `standardise_column_names` | Consistent snake_case for SQL and BI tools |
| 2 | `replace_missing_codes` | Empty strings → NaN in customer_id, channel |
| 3 | `trim_whitespace` | Strips export whitespace from all string columns |
| 4 | `map_categories` (currency) | usd/gbp/Eur → USD/GBP/EUR |
| 5 | `map_categories` (region) | 5 variants → 3 canonical regions |
| 6 | `map_categories` (product_category) | Typo + casing → 3 canonical categories |
| 7 | `map_categories` (refunded) | Y/True/FALSE → yes/no |
| 8 | `parse_dates` | Parses order_date and signup_date; invalid dates → NaT |
| 9 | `set_invalid_to_missing` | order_value ≤ 0 → NaN (flagged for review) |
| 10 | `flag_outliers_iqr` | Adds `order_value_outlier_flag` for analyst review |
| 11 | `create_missingness_flags` | Adds flags for missing customer_id and channel |
| 12 | `remove_exact_duplicates` | Removes the ORD-1005 duplicate row |

---

## Before / after metric impact

### GMV

| Scenario | GMV (USD equivalent) | Notes |
|---|---|---|
| As exported (raw) | $12,614 | Includes all issues |
| After removing duplicate | $12,301 | −$313, −2.5% |
| Excluding future-dated order (2027) from Jan–Apr 2024 | $11,876 | −$425 from period analysis |
| After setting invalid order values to NaN | Row excluded from sum | −$150 entry under investigation |

**Headline risk:** The as-reported GMV of $12,614 may overstate the correctable Jan–Apr 2024 figure by $313–$738 (2.5%–5.8%), depending on how the invalid and future-dated orders are resolved.

### Channel attribution

| Channel | Orders (raw) | Orders (after missing flagged) |
|---|---|---|
| organic | 17 | 17 |
| paid_search | 15 | 15 |
| referral | 13 | 13 |
| social | 10 | 10 |
| **missing** | 5 | 5 (flagged, excluded from attribution model) |

8% of orders cannot be attributed to any channel. An attribution model trained on this data would overweight every channel's share by ~8%.

### Customer retention analysis

5 orders (8%) have no `customer_id`. These orders cannot be joined to the CRM or included in cohort-based retention analysis. If ignored silently, retention rates will be calculated on a biased subset.

### Regional breakdown

Before cleaning, "North America" appears as 5 distinct labels. After `map_categories`, all collapse to one. The regional revenue report would have previously shown:

| Raw label | Orders |
|---|---|
| North America | 22 |
| us | 1 |
| USA | 1 |
| united states | 1 |
| (total uncombined) | 25 |

After cleaning: **North America: 25 orders.**

---

## What decisions are safe after cleaning

- **Descriptive analysis of product mix by region** — categories and regions are now consistent.
- **Refund rate calculation** — `refunded` column is now in a consistent yes/no format.
- **Top-10 customer ranking** — customer_id is intact for 92% of orders; the 8% missing are flagged.
- **Currency-split revenue** — currency codes are now ISO-compliant; FX lookups will succeed.

## What decisions are NOT safe without further investigation

- **Publishing GMV to the board** — the future-dated order (ORD-1050, $425) must be confirmed as valid or excluded. The negative-value order (-$150) needs a decision: data error or refund record.
- **Channel attribution modelling** — 8% missing acquisition_channel means any channel model is biased. Investigate the source system for missing values before fitting.
- **Retention cohort analysis** — the 5 orders with no `customer_id` cannot be linked to CRM records. Understand why these are missing before running churn or LTV calculations.
- **Time-series analysis** — ORD-1030 has an invalid date (2023-02-29) and ORD-1050 has a future date (2027-03-15). Both are coerced to NaT or flagged by the pipeline, but the data owner should confirm whether these are real orders or export artefacts.

---

## How to run this example

**Profile the raw data:**

```bash
python python/run_reporter.py --input data/examples/dirty_orders.csv
```

**Preview cleaning steps (dry run):**

```bash
python python/run_cleaner.py \
  --input data/examples/dirty_orders.csv \
  --rules config/example_business_cleaning_rules.yaml \
  --dry-run
```

**Apply cleaning with flowchart:**

```bash
python python/run_cleaner.py \
  --input  data/examples/dirty_orders.csv \
  --rules  config/example_business_cleaning_rules.yaml \
  --output data/processed/orders_cleaned.csv \
  --confirm-destructive \
  --after-report \
  --flowchart
```

**Compare before/after:**

```bash
python python/run_reporter.py --input data/processed/orders_cleaned.csv
```

Outputs are written to `reports/` and ignored by git — safe to delete after reviewing.

---

## Connection to data quality frameworks

The issues in this dataset correspond to standard checks in tools like Great Expectations, Soda Core, and dbt tests:

| Issue type | Great Expectations | Soda | dbt test |
|---|---|---|---|
| Duplicate order_id | `expect_column_values_to_be_unique` | `no_duplicates` | `unique` |
| Missing customer_id | `expect_column_values_to_not_be_null` | `missing_count` | `not_null` |
| Invalid region labels | `expect_column_values_to_be_in_set` | `invalid_count` | `accepted_values` |
| Negative order values | `expect_column_values_to_be_between` | `min` | `not_null` + dbt test |
| Future dates | Custom expectation | `failed_rows` | Custom macro |

ByeDataClean covers the detection and documentation step. For production pipelines, the validation checks in the YAML rules file can be translated to any of the above frameworks. See [docs/roadmap.md](../roadmap.md) for planned export support.

---

## Running the same checks in SQL

When the orders table lives in a warehouse and is too large to export, the same quality-control logic can be applied in SQL directly against the source table. The file `sql/examples/ecommerce_orders_quality_checks.sql` contains SQL equivalents for every check in this case study:

- duplicate order ID detection and revenue overstatement calculation
- missingness rates for customer_id and acquisition_channel
- future-dated and invalid order date detection
- out-of-range order value checks
- category and region consistency inspection
- before/after GMV reconciliation query
- final PASS / WARNING / BLOCKER scorecard query

See [sql/README.md](../../sql/README.md) for how SQL checks map to ByeDataClean Python workflow concepts, and dialect notes for Postgres, BigQuery, Snowflake, and DuckDB.

---

← [Case studies index](.) · [README](../../README.md) · [Cleaning rules reference](../cleaning_rules_reference.md) · [SQL checks](../../sql/examples/ecommerce_orders_quality_checks.sql)
