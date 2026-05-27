# SQL Inspection Workflow

When inspecting data that lives in a database, work through the cookbook
files in this order.  Each step builds on the previous one.

---

## Suggested order

### 1. Row and column counts (`01_row_and_column_counts.sql`)

Start here.  Know how many rows and columns you have before anything else.

**Decision**: Is the row count what you expected?  Are any columns missing?

---

### 2. Missingness checks (`02_missingness_checks.sql`)

Find NULL patterns for each column you care about.

**Decision**: Which columns have > 20% missing?  Are any columns entirely NULL?
Can you safely ignore sparse columns, or do they need imputation?

---

### 3. Duplicate ID checks (`03_duplicate_checks.sql` + `08_id_integrity_checks.sql`)

Check for NULL IDs and duplicate IDs before joining to other tables.

**Decision**: Are there any rows that share the same ID?  Is this expected
(longitudinal study with multiple visits) or an error?

---

### 4. Continuous summaries (`04_continuous_summary.sql`)

Get mean, SD, min, max, and percentiles for numeric columns.

**Decision**: Are there implausible values (negative age, BMI > 100)?  Are the
distributions skewed?  Are there obvious outliers?

---

### 5. Categorical summaries (`05_categorical_summary.sql`)

Get value counts and identify rare categories.

**Decision**: Are there unexpected category labels (case variants, typos,
whitespace)?  Are rare categories real or data errors?

---

### 6. Date checks (`07_date_checks.sql`)

Check min/max dates, missing dates, and future dates.

**Decision**: Do dates fall within the expected study window?  Are there future
dates that suggest data entry errors?

---

### 7. Range and allowed-value checks (`09_range_and_allowed_value_checks.sql`)

Verify values fall within expected ranges and allowed lists.

**Decision**: How many rows violate business rules?  Should they be excluded,
corrected, or flagged for review?

---

## After SQL inspection

Once you have a clean picture:

- Extract the data to a file and run the Python reporter for a structured
  markdown summary.
- If the table is in a production pipeline, implement dbt tests or Soda checks
  (see `sql/dbt_and_soda_notes.md`).
