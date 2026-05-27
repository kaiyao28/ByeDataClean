# 09 — Cleaning Decision Log

A cleaning decision log is a record of every intentional change made to the data. It is not optional — it is the difference between reproducible analysis and analysis nobody can audit or re-run.

---

## Why you need it

- It lets collaborators understand what was done and why.
- It lets you reconstruct your own decisions six months later.
- It is required for publication, audit, and regulatory submission in most research contexts.
- It makes peer review and replication possible.
- It forces you to think before you clean ("if I cannot justify this in one sentence, I should not do it").

---

## What to record per decision

| Field | What to write |
|---|---|
| **Date** | When the decision was made |
| **Analyst** | Who made the decision |
| **Dataset version** | Which file/commit was used |
| **Variable(s) affected** | Column name(s) |
| **Issue detected** | What the QC report or inspection found |
| **Evidence** | Specific numbers from the QC report |
| **Decision** | What you decided to do |
| **Rationale** | Why this was the right choice |
| **Code / script** | Where in the cleaning script this is implemented |
| **Impact** | How many rows/values were affected; before/after comparison |
| **Reviewer / status** | Who reviewed or approved the decision |

---

## The template

The reusable template is at [`docs/templates/cleaning_decision_log_template.md`](../templates/cleaning_decision_log_template.md).

Copy it into your project and fill it in as you work through cleaning decisions.

---

## Three example entries

### Example 1: Category standardisation

| Field | Value |
|---|---|
| Date | 2024-11-01 |
| Analyst | J. Smith |
| Variable(s) | ethnicity |
| Issue | Labels differ by case and whitespace ("White British", " white british", "WHITE BRITISH") |
| Evidence | Categorical summary shows 8 unique values where 3 are expected; possible_case_inconsistency = True |
| Decision | Strip whitespace, title-case, apply mapping dictionary |
| Rationale | Labels refer to the same category; inconsistency is a data-entry artifact |
| Code | `02_clean.py`, lines 34–41; mapping defined in `config/category_mapping.yaml` |
| Impact | 47 rows remapped; 3 → 1 unique values for White British group |
| Reviewer | Approved by PI, 2024-11-03 |

---

### Example 2: Outlier retained

| Field | Value |
|---|---|
| Date | 2024-11-02 |
| Analyst | J. Smith |
| Variable(s) | bmi |
| Issue | 1 value flagged as IQR outlier (BMI = 88) |
| Evidence | Continuous summary shows n_outliers_iqr = 1; value is 88 |
| Decision | Keep the value in main analysis; include in sensitivity analysis as flagged |
| Rationale | BMI 88 is within physiological range (morbid obesity); source record confirmed; removing would introduce selection bias |
| Code | `02_clean.py`, lines 58–61; sensitivity in `04_sensitivity.py` |
| Impact | 0 rows removed; bmi_iqr_flag = 1 added for 1 row |
| Reviewer | Pending |

---

### Example 3: Duplicate ID — kept as valid repeated visits

| Field | Value |
|---|---|
| Date | 2024-11-02 |
| Analyst | J. Smith |
| Variable(s) | participant_id |
| Issue | 42 participants appear more than once; duplicate ID flagged |
| Evidence | Duplication summary: duplicate_id_rows = 84; id_cols_checked = ['participant_id'] |
| Decision | Keep all rows; unit of observation is participant-visit, not participant |
| Rationale | Study design allows up to 3 visits per participant; duplicate composite key (participant_id + visit_number) = 0 |
| Code | No rows removed; composite key check in `01_profile.py`, lines 12–15 |
| Impact | 0 rows removed; dataset remains at N = 412 rows |
| Reviewer | Confirmed by data manager, 2024-11-04 |

---

## Checklist before final analysis

Copy this into your project for sign-off.

```
[ ] Raw data preserved and not modified
[ ] Cleaning script runs from scratch without manual steps
[ ] QC report generated on raw data (before cleaning)
[ ] QC report generated on cleaned data (after cleaning)
[ ] Row counts before and after recorded
[ ] Missingness before and after recorded
[ ] All duplicate handling documented
[ ] All category mappings documented and applied from config file
[ ] All outlier decisions documented
[ ] Schema validation passed on cleaned data (or exceptions documented)
[ ] Derived variables documented with formula
[ ] Cleaning decision log reviewed by a second person
[ ] Analysis script imports cleaned data, not raw data
```
