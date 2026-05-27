# 08 — Analysis-Specific Cleaning

The same dataset may need different cleaning depending on what you are doing with it. This guide covers the most common scenarios.

---

## Descriptive / summary analysis

**Goal:** describe the observed data honestly.

**Priorities:**
- Standardise missing codes so missingness is counted correctly
- Standardise category labels for clean tables
- Keep original distributions — avoid unnecessary imputation
- Show missingness explicitly, not hidden by exclusions

**Avoid:**
- Removing outliers unless they are confirmed errors
- Imputing outcome or exposure variables
- Collapsing categories that hide meaningful differences

**Typical flow:**
1. Standardise missing codes
2. Standardise category labels (trim/case/mapping)
3. Run QC report on cleaned data
4. Show missingness table alongside descriptive table

---

## Regression / statistical modelling

**Goal:** valid, unbiased inference.

**Priorities:**
- Define the complete-case vs imputation strategy *before* looking at results
- Check whether missingness is related to outcome (differential missingness)
- Check influential points and leverage
- Pre-define exclusion criteria where possible (e.g. in a statistical analysis plan)

**Avoid:**
- Outcome-informed cleaning (e.g. "we removed outliers and then the p-value became significant")
- Imputing outcomes
- Removing outliers unless confirmed errors

**Typical flow:**
1. Standardise missing codes
2. Apply pre-specified exclusion criteria
3. Check missingness by outcome and exposure
4. Choose imputation strategy (complete-case / multiple imputation)
5. Run QC report on analytic dataset
6. Apply schema validation before modelling
7. Plan sensitivity analyses for key decisions (outliers, imputation)

---

## Machine learning / prediction

**Goal:** robust, generalisable predictions.

**Priorities:**
- Split train/test *before* any imputation or encoding is fitted
- Fit imputation parameters on training data only, apply to test data
- Avoid leakage from outcome or future variables
- Handle unseen categories at inference time (e.g. a category present in test data but not train data)

**Avoid:**
- Fitting scalers or encoders on the full dataset before splitting
- Using post-hoc information to clean (e.g. removing rows based on model residuals)

**Typical flow:**
1. Define train/test split
2. Apply cleaning rules derived only from training data
3. Fit imputer/scaler/encoder on training data
4. Transform test data using fitted objects
5. Validate that test data contains no information leaked from target

```python
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

# All transformers fit on X_train only
pipe = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler()),
])
X_train_clean = pipe.fit_transform(X_train)
X_test_clean  = pipe.transform(X_test)   # ← no refit on test data
```

---

## Longitudinal / repeated-measures data

**Goal:** preserve time structure.

**Priorities:**
- Do not remove duplicate IDs — multiple rows per participant are expected
- Define the composite key (participant_id + visit_number or date)
- Check date order between visits
- Distinguish baseline from follow-up before modelling
- Decide wide vs long format based on analysis requirements

**Avoid:**
- Naively dropping duplicate IDs
- Aggregating to one row per person before understanding the time structure

**Typical flow:**
1. Check composite key (participant_id + visit)
2. Check date order is consistent
3. Derive follow-up duration after date validation
4. Decide wide vs long format for analysis
5. Apply visit-specific and person-level QC separately

---

## Administrative / EHR / registry data

**Goal:** handle messy, real-world records reliably.

**Priorities:**
- Expect coding changes over time (ICD version changes, drug code updates)
- Check for impossible dates (birth after death, event before birth)
- Define phenotype logic explicitly (what counts as a case?)
- Preserve provenance fields (source system, record date, version)

**Avoid:**
- Assuming all records are correct
- Ignoring multiple conflicting records for the same patient

**Typical flow:**
1. Standardise missing codes and date formats
2. Apply date sanity checks
3. Deduplicate using defined priority rules (e.g. most recent non-null value)
4. Apply phenotype definitions with documented thresholds
5. Create a derivation log showing how each derived variable was constructed

---

## Data sharing / public release

**Goal:** safe, interpretable, reproducible data.

**Priorities:**
- De-identify: remove direct identifiers (names, NHS numbers, postcodes, exact dates of birth)
- Suppress indirect identifiers: rare demographic combinations
- Free-text fields: exclude or replace with structured summaries
- Create a codebook documenting every variable
- Prepare a data dictionary for external users

**Avoid:**
- Sharing data with suppressed but reconstructable identifiers
- Sharing raw free-text fields
- Publishing cleaning code that reveals original values

**Typical flow:**
1. Identify all direct and indirect identifiers
2. Remove or pseudonymise identifiers
3. Check residual disclosure risk (small cell suppression)
4. Run QC on the public release version
5. Produce codebook
6. Prepare cleaning and derivation log for transparency

---

## Summary by analysis type

| Analysis type | Most important cleaning step | Key risk to avoid |
|---|---|---|
| Descriptive | Standardise labels; show missingness | Hiding missing data |
| Regression | Check differential missingness | Outcome-informed cleaning |
| Machine learning | Train/test split before fitting | Leakage |
| Longitudinal | Define composite key; check date order | Removing valid repeated rows |
| EHR/administrative | Define phenotype logic; handle coding changes | Assuming all records are correct |
| Data sharing | De-identify; check residual disclosure | Indirect identifier release |
