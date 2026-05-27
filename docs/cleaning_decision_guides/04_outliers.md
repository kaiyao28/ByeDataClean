# 04 — Outliers

> **Outlier ≠ error.**

An outlier is a value that is statistically far from the rest. An error is a value that does not reflect reality. These are not the same thing, and they require different responses.

---

## What the QC report tells you

The reporter flags IQR-based outliers:
- values below Q1 − 1.5 × IQR
- values above Q3 + 1.5 × IQR

This is a statistical flag, not a verdict. The reporter does not know whether the value is an error.

---

## Step 1: Separate statistical outliers from impossible values

Ask: is this value physically, biologically, or logically possible?

| Value | Type | Action |
|---|---|---|
| BMI = 450 | Impossible | Set missing; check source |
| BMI = 72 | Statistically extreme but possible | Do not remove automatically |
| Age = −4 | Impossible | Set missing; check source |
| Age = 98 | Plausible extreme | Keep; flag for sensitivity |
| Systolic BP = 300 | Very unlikely but occasionally possible | Review source |
| Test score = 150 (max = 100) | Impossible | Set missing; check coding |

Define the impossible range explicitly in your schema or cleaning rules:

```yaml
# config/cleaning_rules.example.yaml
rules:
  bmi:
    min: 10
    max: 80
    invalid_action: set_missing_after_review
  age:
    min: 0
    max: 120
    invalid_action: set_missing_after_review
```

---

## Step 2: Ask why the extreme value exists

For values that are statistically extreme but not impossible:

1. **Data-entry error** — e.g. participant typed their weight in pounds instead of kg, or a digit was duplicated (BMI = 2244 instead of 22.4).
2. **Measurement error** — e.g. broken scale, incorrect instrument calibration.
3. **Coding error** — e.g. missing-value code (−9, 999) not converted to NULL.
4. **True extreme** — e.g. a patient with genuine morbid obesity.

Check the source record if possible. If source data are unavailable, make a documented assumption.

---

## Step 3: Choose an action

### Option A: Keep the value

If the value is plausible and you cannot confirm an error, keep it. Note it in the decision log and plan a sensitivity analysis.

**When appropriate:**
- value is extreme but within the physiological/logical range
- no source error found
- removing it would bias the sample toward a narrower distribution

---

### Option B: Set to missing

If the value is impossible, set it to NaN and document the threshold:

```python
df.loc[df['bmi'] > 80, 'bmi'] = float('nan')
n_set_missing = (df['bmi'] > 80).sum()
print(f"Set {n_set_missing} BMI values above 80 to missing.")
```

---

### Option C: Winsorise (cap at a threshold)

Replace extreme values with the threshold value rather than removing them.

```python
lower = df['bmi'].quantile(0.01)
upper = df['bmi'].quantile(0.99)
df['bmi_winsorised'] = df['bmi'].clip(lower, upper)
```

**When appropriate:**
- You need all rows in the model (e.g. small sample).
- You want to reduce influence of extremes without losing observations.

**Risk:** winsorisation changes the variable distribution. Create a new column rather than overwriting.

---

### Option D: Transform the variable

Log or square-root transformation can reduce the influence of extreme values without removing them:

```python
import numpy as np
df['bmi_log'] = np.log(df['bmi'].clip(lower=0.01))
```

**When appropriate:**
- The variable has a right-skewed distribution and the analysis allows transformation.
- Transformation is interpretable in context.

---

### Option E: Run a sensitivity analysis

Keep the outlier in the main analysis, and re-run the analysis excluding it to check whether conclusions change.

```python
# Main analysis on full data
# Sensitivity analysis excluding flagged rows
df_sensitivity = df[df['bmi_outlier_flag'] == 0]
```

This is often the most honest approach when you cannot confirm the value is an error.

---

## Step 4: Flag for downstream use

Whether or not you remove, always create a flag column so downstream analysts know which rows were reviewed:

```python
upper_bound = df['bmi'].quantile(0.75) + 1.5 * (df['bmi'].quantile(0.75) - df['bmi'].quantile(0.25))
df['bmi_iqr_flag'] = (df['bmi'] > upper_bound).astype(int)
```

---

## What to document

- Threshold used to define "extreme" (IQR rule, z-score, domain range)
- Whether flagged values were reviewed against source data
- Action taken: kept / set missing / winsorised / transformed
- Number of rows affected
- Whether a sensitivity analysis was planned or run
