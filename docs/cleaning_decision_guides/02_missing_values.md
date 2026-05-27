# 02 — Missing Values

Missing data is almost universal. The question is not whether to handle it, but how — and that depends on why it is missing.

---

## What the QC report tells you

The reporter flags:
- missing count and percentage per column
- columns with > 20% missing (high missingness)
- columns with > 50% missing (very high)
- fully missing columns

That is the what. The guide below helps you decide the how.

---

## Step 1: Standardise missing value codes

Before counting NULLs, make sure your missing codes are consistent.

Common non-NULL missing representations:

```
""          (empty string)
"NA"        (string, not R's NA)
"N/A"
"Unknown"
"Prefer not to say"
-9
-99
999
```

If these are in your data, convert them to NULL/NaN before profiling.

See [`config/missing_codes.example.yaml`](../../config/missing_codes.example.yaml) for a template.

---

## Step 2: Ask why the data is missing

This is the most important question. Missingness is usually classified as:

| Mechanism | What it means | Consequence |
|---|---|---|
| **MCAR** — Missing Completely at Random | Probability of missingness is unrelated to any variable, observed or unobserved | Complete-case analysis is unbiased |
| **MAR** — Missing at Random | Probability of missingness depends on observed variables, but not on the missing value itself | Imputation using observed predictors can work |
| **MNAR** — Missing Not at Random | Probability of missingness depends on the unobserved value itself | Most dangerous; imputation will be biased unless you model the mechanism |

You cannot prove MCAR or MAR from data alone. But you can check:
- Does missingness differ between groups defined by observed variables?
- Does missingness differ by outcome?

**If missingness is higher in sicker/poorer/older participants**, it is unlikely to be MCAR.

---

## Step 3: Check missingness by subgroup

```python
# Missingness rate by outcome group
df.groupby('outcome')['bmi'].apply(lambda x: x.isna().mean())
```

```r
library(dplyr)
df %>% group_by(outcome) %>% summarise(pct_missing = mean(is.na(bmi)))
```

If missingness differs by outcome or exposure, complete-case analysis will give biased estimates in most models.

---

## Step 4: Choose a handling strategy

### Option A: Complete-case analysis

Keep only rows where all required variables are present.

**When acceptable:**
- Missingness is small (< 5%) and plausibly MCAR.
- The variable is not critical to the analysis.

**Risks:**
- Reduces sample size.
- Introduces bias if missingness is related to outcome.

---

### Option B: Missingness indicator

Add a binary flag column: `bmi_missing = 1 if bmi is null`.

**When useful:**
- When missingness itself may be informative (e.g. missing BMI may indicate the patient was too ill to weigh).
- As a sensitivity check.

```python
df['bmi_missing'] = df['bmi'].isna().astype(int)
```

---

### Option C: Simple imputation

Replace missing values with the mean, median, or mode.

**When it might be acceptable:**
- Missingness is small.
- Variable is not the primary exposure or outcome.
- Missingness is plausibly MCAR.

**Risks:**
- Underestimates variance.
- Destroys relationships between variables.
- Biased if missingness is related to outcome.

> ⚠️ Never impute and then claim the imputed values are real. Document what was imputed.

---

### Option D: Multiple imputation

Generate several complete datasets, analyse each, and pool results (Rubin's rules).

**When appropriate:**
- Moderate missingness in covariates.
- You have good predictors of the missing values.
- Missingness is plausibly MAR.

**Not for:**
- MNAR missingness (imputation will be biased).
- Outcomes (imputing outcomes changes the analysis question).

Tools: `mice` (R), `sklearn.impute.IterativeImputer` (Python).

---

### Option E: Exclude the variable

If a variable is > 50% missing and not critical to the analysis, consider not including it.

Document: "Variable X was excluded due to >50% missingness. Sensitivity analysis including X is available on request."

---

## Quick reference

| Situation | Suggested first step |
|---|---|
| < 5% missing in a covariate | Complete-case, document |
| 5–20% missing, plausibly MCAR | Complete-case with sensitivity check |
| > 20% missing in a covariate | Check missingness by outcome; consider imputation or exclusion |
| Missingness related to outcome | Do not use complete-case as primary; discuss with statistician |
| Outcome variable missing | Do not impute; define exclusion criteria explicitly |
| Fully missing column | Exclude; check whether data should have been collected |

---

## What to document

- % missing per variable before and after cleaning
- Missingness mechanism assumption (MCAR/MAR/MNAR) and evidence
- Strategy chosen per variable (complete-case / indicator / imputation / exclusion)
- Imputation method and predictors used if applicable
- Row count before and after any exclusions
