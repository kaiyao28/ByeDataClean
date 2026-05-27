# 05 — Categorical Variables

Categorical variables look clean when a list of unique values is short. They can still hide problems: inconsistent labels, rare categories that affect model stability, or high cardinality that needs encoding decisions.

---

## What the QC report tells you

The reporter flags:
- possible leading/trailing whitespace in values
- possible mixed-case values (e.g. "Male" and "male" in the same column)
- high-cardinality columns (> 50 unique values by default)
- rare categories (< 1% of non-null rows by default)
- number of distinct categories

---

## Issue 1: Whitespace and case inconsistency

**Problem:** "Control" and " Control" and "control" are counted as three different categories, but they may mean the same thing.

**Check:**

```python
df['diagnosis'].value_counts(dropna=False)
# Look for near-duplicates that differ only by case/whitespace
```

**Fix — trim and standardise:**

```python
df['diagnosis'] = df['diagnosis'].str.strip().str.title()
```

Or apply a specific mapping to avoid unexpected transformations:

```python
label_map = {
    'control': 'Control',
    ' Control': 'Control',
    'CONTROL': 'Control',
    'scz': 'SCZ',
}
df['diagnosis'] = df['diagnosis'].str.strip().map(label_map).fillna(df['diagnosis'])
```

**Document:** what mapping was applied, how many values were changed.

---

## Issue 2: Disallowed values

The schema file lets you define allowed values per column:

```yaml
diagnosis:
  allowed_values: ["Control", "SCZ", "BD", "MDD"]
```

When the reporter finds values outside this list, you need to decide:

| Situation | Action |
|---|---|
| Typo or encoding error (e.g. "Contrl") | Map to correct value or set missing |
| Legitimate synonym (e.g. "Bipolar" for "BD") | Map using category_mapping config |
| Genuine unknown category | Map to "Unknown" or set missing |
| Category added after schema was defined | Update schema and map |

See [`config/category_mapping.example.yaml`](../../config/category_mapping.example.yaml).

---

## Issue 3: Rare categories

A rare category is one that appears in very few rows (< 1% by default).

**Questions to ask:**
- Is this a real, meaningful subgroup, or a data-entry error?
- Does the analysis depend on distinguishing this category?
- Will models fail or produce unstable estimates with this few observations?

**Options:**

### Keep the rare category

If the category represents a meaningful group (even if small), keep it. Removing it hides real variation. For descriptive analysis, always keep.

### Combine into "Other"

Only if:
- the category is analytically uninformative
- you have a statistical reason (e.g. model convergence)
- you document it explicitly

```python
threshold = 0.01
counts = df['ethnicity'].value_counts(normalize=True)
rare = counts[counts < threshold].index
df['ethnicity_grouped'] = df['ethnicity'].where(~df['ethnicity'].isin(rare), other='Other')
```

> ⚠️ Combining minority groups into "Other" hides health disparities and demographic differences. Do not do this without strong justification.

---

## Issue 4: High cardinality

High-cardinality columns (e.g. free-text job title, hospital name) often need a different strategy than standard categorical encoding.

**Questions to ask:**
- Is this column needed for the analysis?
- Can it be grouped into meaningful higher-level categories?
- Is it a text field that needs a separate NLP workflow?

**Options:**
- Group into a smaller set of categories using a mapping dictionary
- Exclude from the analysis dataset if not needed
- Flag as `text_high_cardinality` in the type override config and handle separately

---

## Issue 5: Unknown / missing categories

Watch for "Unknown", "Not stated", "Prefer not to say" — these may be stored as strings rather than NULL.

Add them to your missing codes config:

```yaml
# config/missing_codes.example.yaml
missing_string_codes:
  - "Unknown"
  - "Not stated"
  - "Prefer not to say"
  - "N/A"
```

Decide whether to convert them to NULL, keep them as an explicit category, or handle them separately.

---

## What to document

- Mapping rules applied (whitespace, case, synonyms)
- Whether any categories were combined and the threshold/rationale used
- Category counts before and after standardisation
- Rare categories kept or combined and why
- Any high-cardinality columns excluded or grouped
