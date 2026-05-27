# 03 — Duplicates and Units of Observation

Duplicate handling is one of the most misunderstood steps in data cleaning. The right action depends entirely on what each row is supposed to represent.

---

## What the QC report tells you

The reporter flags:
- exact duplicate rows (every column identical)
- duplicate values in ID columns (if `--id-cols` is supplied)

Neither is automatically an error.

---

## Step 1: Define your unit of observation

Before removing any duplicates, answer this question:

> **What does one row in this dataset represent?**

Common units:

| Unit | Expected duplicates |
|---|---|
| One row per person | Each person ID should appear once |
| One row per visit | Same person may appear multiple times (once per visit) |
| One row per prescription | Same person, same drug, different dates |
| One row per transaction | Many rows per customer |
| One row per event | Many rows per individual |

If you do not define the unit first, removing duplicates may delete valid records.

---

## Step 2: Check exact duplicate rows

Exact duplicate rows — where every column is identical — are almost always accidental (double-entry, merge error, export bug).

```python
# Find exact duplicates
print(df[df.duplicated(keep=False)])

# Remove them (keep first occurrence)
df_clean = df.drop_duplicates(keep='first')
print(f"Removed {len(df) - len(df_clean)} exact duplicate rows.")
```

```r
sum(duplicated(df))
df_clean <- df[!duplicated(df), ]
```

**Before removing:** check whether the duplicated rows truly are identical in all columns, including timestamps or version fields that might look identical but differ. If in doubt, sort and inspect.

---

## Step 3: Check duplicate IDs

A duplicate ID means the same identifier appears more than once.

```python
dup_ids = df[df.duplicated(subset=['participant_id'], keep=False)]
print(dup_ids[['participant_id']].value_counts().head(20))
```

**Is this an error or expected?**

| If... | Then... |
|---|---|
| Your dataset should have one row per participant | Duplicate ID is likely an error — investigate source |
| Your dataset has repeated visits | Duplicate ID is expected — check the composite key instead |
| Your dataset has multiple measurements per participant | Define the correct key (e.g. participant_id + visit_number) |

---

## Step 4: Check the composite key

For longitudinal or repeated-measures data, the meaningful uniqueness constraint is usually a combination of columns.

```python
# Check uniqueness of participant + visit combination
key = ['participant_id', 'visit_number']
dup_composite = df[df.duplicated(subset=key, keep=False)]
print(f"Rows with duplicate composite key: {len(dup_composite)}")
```

```sql
-- From 03_duplicate_checks.sql
SELECT participant_id, visit_number, COUNT(*) AS n_rows
FROM my_table
GROUP BY participant_id, visit_number
HAVING COUNT(*) > 1;
```

A duplicate composite key (same person, same visit, different row) is more likely to be an error than a duplicate ID alone.

---

## Step 5: Choose an action

### Remove exact accidental duplicates

```python
df_clean = df.drop_duplicates(keep='first')
```

Only after confirming they are accidental. Document how many rows were removed.

---

### Keep all rows (do not deduplicate)

If each row is a valid event or measurement, keep all rows and make sure your analysis accounts for repeated records (e.g. use a multilevel model, or aggregate before modelling).

---

### Aggregate to one row per subject

If your analysis needs one row per person but the data has multiple rows per person:

```python
# Mean of numeric variables per participant
df_agg = df.groupby('participant_id').agg({
    'age': 'first',         # take first (should be constant)
    'bmi': 'mean',          # average across visits
    'diagnosis': 'first',   # take first
}).reset_index()
```

**Risk:** aggregation destroys information about change over time and visit-level variation.

---

### Flag and review

If you are unsure, flag duplicate records and review a sample before deciding.

```python
df['is_duplicate_id'] = df.duplicated(subset=['participant_id'], keep=False)
```

---

## What to document

- Unit of observation decision
- How many exact duplicate rows were found and removed
- Whether duplicate IDs were expected or unexpected
- Composite key used for uniqueness checks
- Rows removed, and any rows kept despite appearing duplicate
