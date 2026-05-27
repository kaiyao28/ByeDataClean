# 01 — Cleaning Principles

Core rules to follow before touching any data.

---

## 1. Cleaning is purpose-dependent

There is no universal cleaning recipe. The right action depends on:

- what question you are answering
- what the data source is and how it was collected
- which variables are outcomes, exposures, or covariates
- what biases your cleaning decisions could introduce

A value that is an "outlier" in a regression model may be a valid extreme in a descriptive analysis. A duplicate row that should be removed in a cross-sectional study may be a valid repeated visit in a longitudinal one.

> **Before cleaning anything: write down what you are trying to analyse.**

---

## 2. Do not clean blindly

Do not:
- remove outliers just because they are flagged
- impute missing values by default
- merge rare categories without checking their meaning
- drop duplicate IDs without understanding whether duplication is expected

Every cleaning decision should be a conscious choice, not an automatic step.

---

## 3. Preserve raw data

**Never edit the raw data file.**

Keep the original file exactly as received. Save all cleaned versions separately.

```
data/raw/my_data.csv          ← original; never touch this
data/processed/my_data_clean.csv   ← output of your cleaning script
```

If you need to fix a value, do it in a script, not in the spreadsheet.

---

## 4. Prefer reproducible scripts over manual edits

Every cleaning step should be in a script that can be re-run from scratch.

If you rename categories, write the mapping in a config file or code. If you drop rows, do it with a documented condition. If you impute, record the method and parameters.

Manual edits in Excel or direct database changes are:
- invisible to other analysts
- irreproducible
- a source of silent errors

---

## 5. Separate profiling, cleaning, validation, and modelling

These are distinct steps. Keep them in separate scripts.

```
01_profile.py       ← run QC reporter; read warnings; do not clean yet
02_clean.py         ← apply documented cleaning decisions
03_validate.py      ← re-run QC after cleaning; check schema
04_analyse.py       ← analysis on clean data only
```

If cleaning and analysis are in the same script, it is easy to over-clean in response to modelling results — which introduces bias.

---

## 6. Record every cleaning decision

Use the [cleaning decision log](09_cleaning_decision_log.md).

For each decision record:
- what the issue was
- what evidence you had (e.g. from the QC report)
- what you decided
- why
- what code implements it
- how many rows/values were affected

If you cannot explain a cleaning decision in a sentence, you probably should not make it.

---

## 7. Re-run QC after cleaning

After applying cleaning, run the reporter again on the cleaned dataset.

Check:
- Did the original issue resolve?
- Did row count change as expected?
- Did missingness change?
- Did any new warnings appear?

Before/after comparison is the simplest form of cleaning validation.

---

## 8. Make exclusions explicit and visible

If you exclude rows, say so clearly:

```python
# Exclude participants under 18
df_clean = df[df['age'] >= 18].copy()
n_excluded = len(df) - len(df_clean)
print(f"Excluded {n_excluded} rows (age < 18).")
```

Every exclusion should appear in your cleaning log and, if the analysis is published, in a CONSORT-style exclusion table or methods section.

---

## 9. Think about bias, not just tidiness

Cleaning decisions can introduce bias.

Examples of biased cleaning:
- removing participants with high missingness when missingness is related to outcome → complete-case bias
- removing outliers selectively → inflated precision, narrowed distributions
- collapsing rare minority groups → erased signal
- imputing using outcome-correlated predictors without appropriate methods → biased coefficients

Tidiness is not the same as correctness. A clean-looking dataset can still produce biased estimates.

---

## 10. The goal is fitness for purpose, not perfection

You are cleaning the data for a specific analysis. The same dataset may need different cleaning for a different analysis. A dataset that is clean for a regression model may not be clean for a machine learning pipeline.

Do not try to produce one "clean" version of the data for all purposes. Instead, document what cleaning was applied and why, and keep the raw data available.
