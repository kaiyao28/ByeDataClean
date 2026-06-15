---
name: Cleaning rule / action request
about: Request a new cleaning action or validation check
title: "[RULE] "
labels: cleaning-action
assignees: ''
---

## What cleaning problem does this address?

<!-- Describe the data quality issue this rule would fix. Example: "Detect and flag rows where a date column contains a timestamp that predates the company's founding." -->

## Proposed action name and syntax

<!-- How would this look in a YAML rules file? -->

```yaml
- step: N
  name: "your_proposed_action"
  action: "your_proposed_action"
  # ... parameters
  decision_status: "approved"
  rationale: >
    Why this action is needed.
```

## Example: before and after

**Before:**

| column | value |
|---|---|
| ... | ... |

**After:**

| column | value |
|---|---|
| ... | ... |

## How common is this problem?

<!-- Is this something you encounter frequently, or a one-off edge case? What types of datasets or industries does this apply to? -->

## Is this covered by an existing action?

<!-- Have you checked the 14 existing actions in `docs/cleaning_rules_reference.md`? Which ones are closest? What's missing? -->

## Would you like to contribute this?

- [ ] Yes, I can submit a pull request
- [ ] I can help with testing
- [ ] No, just suggesting
