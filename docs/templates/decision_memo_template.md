# Data Quality Decision Memo

**Dataset:** [FILL IN: file name or dataset name]
**Prepared by:** [FILL IN: analyst name]
**Date:** [FILL IN: YYYY-MM-DD]
**Review requested from:** [FILL IN: data owner / product owner / finance / stakeholder]

---

## Question

> Can the dataset `[FILL IN]` be used for `[FILL IN: e.g. the Q1 retention analysis / the March revenue dashboard / the churn prediction model]`?

---

## Recommendation

Choose one:

- [ ] **Use** — this dataset meets quality requirements for the intended purpose.
- [ ] **Use with caveats** — known issues exist but do not block the analysis. See caveats below.
- [ ] **Do not use yet** — blocking data quality issues must be resolved before proceeding.

**Reason (1–2 sentences):**
[FILL IN]

---

## Main data-quality risks

List the most significant issues found during profiling and cleaning. Focus on what could distort the metric or conclusion you care about.

| Issue | Severity | Business metric affected |
|---|---|---|
| [FILL IN: e.g. 3% of order IDs are duplicated] | Critical / High / Medium / Low | [FILL IN: e.g. GMV, revenue] |
| [FILL IN] | | |
| [FILL IN] | | |

---

## Business metrics affected

Which specific numbers, dashboards, or reports could be impacted by these issues?

- [FILL IN: e.g. Monthly GMV figure — may be overcounted by ~2.5% due to duplicate orders]
- [FILL IN: e.g. Retention cohort — 8% of orders cannot be joined to CRM due to missing customer_id]
- [FILL IN: e.g. Channel attribution model — 8% of orders have no acquisition_channel]

---

## Cleaning actions applied

The following automated cleaning steps were applied using ByeDataClean:

| Step | Action | Decision status | Rows affected |
|---|---|---|---|
| [FILL IN: 1] | [FILL IN: e.g. remove_exact_duplicates] | approved | [FILL IN: 1 row removed] |
| [FILL IN: 2] | [FILL IN: e.g. map_categories (region)] | approved | [FILL IN: 5 cells changed] |

Cleaning log: `[FILL IN: path to cleaning log]`

---

## Remaining unresolved issues

Issues that have been detected but require human decision before the data is ready for full use:

| Issue | Action required | Owner |
|---|---|---|
| [FILL IN: e.g. 1 future-dated order (ORD-1050, $425)] | Investigate — confirm if valid pre-order or entry error | [FILL IN: data owner] |
| [FILL IN: e.g. 1 negative-value order (-$150)] | Investigate — determine if refund or data error | [FILL IN: analyst] |

If there are no unresolved issues, write: _No unresolved issues._

---

## What decisions are safe after cleaning

Analysis or reporting that is acceptable to proceed with, given the current data state:

- [FILL IN: e.g. Descriptive analysis of product mix and regional distribution]
- [FILL IN: e.g. Customer-level ranking for orders with a valid customer_id (92% of orders)]
- [FILL IN: e.g. Refund rate calculation — refunded flag now standardised to yes/no]

---

## What decisions are NOT safe without further investigation

Analysis or reporting that should NOT proceed until the unresolved issues above are addressed:

- [FILL IN: e.g. Publishing GMV to the board — two orders with invalid values are unresolved]
- [FILL IN: e.g. Channel attribution modelling — 8% of orders have no acquisition_channel]
- [FILL IN: e.g. Retention analysis using the full dataset — 8% of customer_ids are missing]

---

## Next actions

| Action | Owner | By when |
|---|---|---|
| [FILL IN: e.g. Confirm status of ORD-1050 (future date)] | [FILL IN: data owner] | [FILL IN: YYYY-MM-DD] |
| [FILL IN: e.g. Decide treatment of negative-value order] | [FILL IN: analyst] | [FILL IN: YYYY-MM-DD] |
| [FILL IN: e.g. Investigate missing customer_ids in source system] | [FILL IN: data engineering] | [FILL IN: YYYY-MM-DD] |

---

## Supporting documents

- Cleaning log: `[FILL IN]`
- Validation report: `[FILL IN]`
- Data quality scorecard: `[FILL IN]`
- Business impact report: `[FILL IN]`

---

_This memo was prepared using [ByeDataClean](https://github.com/kaiyao28/ByeDataClean).
Template: `docs/templates/decision_memo_template.md`_
