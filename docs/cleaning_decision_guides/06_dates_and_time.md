# 06 — Dates and Time

Date columns are deceptively tricky. They can store values as strings in many formats, generate impossible values, and create silent errors when used to derive ages or follow-up durations.

---

## What the QC report tells you

The reporter flags:
- min and max date per date column
- missing dates
- future dates (dates after today)

---

## Step 1: Parse dates correctly

Dates stored as strings are easy to misparse.

```python
# Explicit format is safer than letting pandas guess
df['assessment_date'] = pd.to_datetime(df['assessment_date'], format='%Y-%m-%d', errors='coerce')

# errors='coerce' sets unparseable values to NaT (not a time) instead of raising
```

After parsing, check how many values became NaT:

```python
n_failed = df['assessment_date'].isna().sum() - original_missing_count
print(f"Unparseable dates set to missing: {n_failed}")
```

**Common format codes:**
- `%Y-%m-%d` → 2024-03-15
- `%d/%m/%Y` → 15/03/2024
- `%m/%d/%Y` → 03/15/2024 (US format — easy to confuse with above)
- `%d-%b-%Y` → 15-Mar-2024

> ⚠️ Day/month confusion (03/04 = 3 April or 4 March?) is a common silent error in international datasets. Always check the source documentation for the expected format.

---

## Step 2: Check the date range

```python
print(df['assessment_date'].min())
print(df['assessment_date'].max())
```

**Questions to ask:**
- Does the min date match when data collection started?
- Does the max date match when data collection ended?
- Are there dates before the study began or after it ended?

---

## Step 3: Handle future dates

The reporter flags dates after today's date. Whether this is an error depends on what the column represents.

| Column | Future date | Likely meaning |
|---|---|---|
| Date of birth | Any date after today | Impossible error |
| Assessment date | Future date | Scheduled appointment or data-entry error |
| Follow-up date | Near future | May be valid; depends on study design |
| Discharge date | Far future | Likely error |

**Inspect flagged rows before deciding:**

```python
today = pd.Timestamp.today().normalize()
future = df[df['assessment_date'] > today]
print(future[['participant_id', 'assessment_date']].head(20))
```

---

## Step 4: Check logical consistency between related dates

If you have multiple date columns, check that they are in the expected order.

```python
# Assessment date should not precede date of birth
invalid = df[df['assessment_date'] < df['date_of_birth']]
print(f"Assessment date before birth date: {len(invalid)}")

# End date should not precede start date
invalid = df[df['end_date'] < df['start_date']]
print(f"End date before start date: {len(invalid)}")
```

---

## Step 5: Derive age and follow-up time correctly

Derived variables should only be computed after dates are cleaned and validated.

```python
# Age in years (approximate)
df['age_at_assessment'] = (
    (df['assessment_date'] - df['date_of_birth']).dt.days / 365.25
).round(1)

# Follow-up duration in days
df['followup_days'] = (df['end_date'] - df['start_date']).dt.days
```

Check derived variables immediately:

```python
print(df['age_at_assessment'].describe())
# Any negatives? Any impossibly large values?
```

---

## Step 6: Handle timezone issues (if applicable)

If data were collected across timezones and timestamps are important (not just dates), make sure all timestamps are converted to a consistent timezone before comparison.

```python
# Convert to UTC
df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
```

This matters for event timestamps but is usually not relevant for study dates.

---

## What to document

- Date format(s) found in raw data
- Number of dates that failed to parse (set to missing)
- Whether future dates were expected, set to missing, or reviewed
- Cross-column date logic checks performed
- Any derived date variables created and the formula used
