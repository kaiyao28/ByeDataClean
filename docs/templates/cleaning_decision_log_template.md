# Cleaning Decision Log

**Dataset:** _name or description of the dataset_
**Dataset version / file:** _path or hash/date of the raw file_
**Analyst:** _your name_
**Date started:** _YYYY-MM-DD_
**Analysis purpose:** _one sentence describing what this dataset will be used for_
**Unit of observation:** _e.g. one row per participant / one row per visit / one row per transaction_
**Raw data location:** `data/raw/`
**Cleaned data location:** `data/processed/`
**QC report (before cleaning):** `reports/descriptive_summary/`
**QC report (after cleaning):** `reports/descriptive_summary/`
**Cleaning script:** _path to your cleaning script_

---

## Decision table

> Add one row per cleaning decision. Be specific about what the QC report showed and what you decided.

| Date | Variable(s) | Issue detected | Evidence from QC report | Decision | Rationale | Code / script (line) | Rows / values affected | Reviewer / status |
|---|---|---|---|---|---|---|---|---|
| YYYY-MM-DD | column_name | Brief description of the issue | e.g. "missing_pct = 24.3%" | What you did | Why this was the right choice | cleaning_script.py:42 | e.g. "47 values remapped" | Pending / Approved |
| | | | | | | | | |
| | | | | | | | | |

---

## Example entries (delete these before use)

| Date | Variable(s) | Issue detected | Evidence from QC report | Decision | Rationale | Code / script (line) | Rows / values affected | Reviewer / status |
|---|---|---|---|---|---|---|---|---|
| 2024-11-01 | ethnicity | Labels differ by case and whitespace | possible_case_inconsistency = True; 8 unique values, expected 3 | Strip whitespace; apply mapping in category_mapping.yaml | Labels refer to the same category; inconsistency is data-entry artifact | 02_clean.py:34–41 | 47 values remapped | Approved by PI 2024-11-03 |
| 2024-11-02 | bmi | IQR outlier (BMI = 88) | n_outliers_iqr = 1; value = 88 | Keep; flag for sensitivity analysis | Within physiological range; source record confirmed | 02_clean.py:58–61 | 0 rows removed; flag added to 1 row | Pending |
| 2024-11-02 | participant_id | Duplicate IDs (42 participants appear > once) | duplicate_id_rows = 84 | Keep all rows; unit is participant-visit | Study allows 3 visits/participant; composite key is unique | No rows removed | 0 rows removed | Confirmed by data manager 2024-11-04 |

---

## Exclusion summary

> Record every dataset-level exclusion separately from variable-level cleaning.

| Exclusion criterion | N excluded | N remaining | Rationale |
|---|---|---|---|
| _e.g. Age < 18_ | | | |
| _e.g. Missing primary outcome_ | | | |
| _e.g. Exact duplicate row_ | | | |

**Total rows in raw data:** ___
**Total rows in cleaned data:** ___

---

## Before/after comparison

> Paste key statistics from the QC reports here for a quick sanity check.

| Metric | Before cleaning | After cleaning |
|---|---|---|
| Total rows | | |
| Exact duplicate rows | | |
| % missing in [key variable] | | |
| % missing in [key variable] | | |
| Schema validation passes | — | Yes / No |

---

## Sign-off checklist

```
[ ] Raw data preserved and not modified
[ ] Cleaning script runs from scratch without manual steps
[ ] QC report generated on raw data (before cleaning)
[ ] QC report generated on cleaned data (after cleaning)
[ ] Row counts before and after recorded above
[ ] All duplicate handling documented
[ ] All category mappings documented and applied from config file
[ ] All outlier decisions documented
[ ] Schema validation passed on cleaned data (or exceptions documented)
[ ] Derived variables documented with formula
[ ] This log reviewed by a second analyst
[ ] Analysis script imports data/processed/, not data/raw/
```

**Analyst sign-off:** ___________________________  Date: ___________
**Reviewer sign-off:** ___________________________  Date: ___________
