# 05 - Review & Overrides

**Notebook:** `notebook/05_rdls_review_overrides.ipynb`

---

## Summary

Applies manual review decisions to the classification results, allowing you to include, exclude, or re-classify specific datasets.

**For Decision Makers:**
> This is the "human in the loop" step where domain experts can override automated classifications. It's optional but recommended for high-quality outputs.

---

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| Raw classification | `derived/classification_raw.csv` | From Step 04 |
| Overrides config | `config/overrides.yaml` | Manual review decisions |
| OSM exclusions | `policy/osm_excluded_dataset_ids.txt` | From Step 02 |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Final classification | `derived/classification_final.csv` | With overrides applied |
| Final summary | `derived/classification_final_summary.json` | Updated statistics |
| Included IDs | `derived/rdls_included_dataset_ids_final.txt` | Final inclusion list |

---

## Override Format

```yaml
# config/overrides.yaml
overrides:
  # Force include a dataset
  "abc123-def456-ghi789":
    decision: keep
    components: [hazard, exposure]
    note: "Important flood risk dataset, low score due to sparse metadata"

  # Force exclude a dataset
  "xyz789-abc123-def456":
    decision: exclude
    note: "Duplicate of another dataset"

  # Change component assignment
  "mno456-pqr789-stu012":
    decision: keep
    components: [vulnerability]  # Override original classification
    note: "Correctly classified as vulnerability, not exposure"
```

---

## Override Fields

| Field | Required | Values | Description |
|-------|----------|--------|-------------|
| `decision` | Yes | `keep` / `exclude` | Include or exclude from RDLS |
| `components` | No | List of components | Override component assignment |
| `note` | No | String | Reason for override (documentation) |

---

## Key Functions

### `OverrideConfig`
Loads and validates override configuration.

```python
overrides = OverrideConfig.load("config/overrides.yaml")
override = overrides.get("abc123-def456")
# override.decision: "keep"
# override.components: ["hazard", "exposure"]
```

### `apply_overrides()`
Applies overrides to classification DataFrame.

```python
df_final = apply_overrides(df_raw, overrides)
# Returns DataFrame with overrides applied
```

---

## How Overrides Work

```
For each dataset in classification_raw.csv:
1. Check if dataset_id has an override
2. If override exists:
   a. Apply decision (keep/exclude)
   b. Replace components if specified
   c. Mark as manually reviewed
3. If no override: keep original classification
4. Write classification_final.csv
```

---

## Review Workflow

### Step 1: Identify candidates for review
```python
# Low-confidence inclusions
review_candidates = df[
    (df['included']) &
    (df['confidence'] < 0.5)
].sort_values('confidence')

# High-confidence exclusions
missed_candidates = df[
    (~df['included']) &
    (df['confidence'] > 0.4)
]
```

### Step 2: Review specific datasets
```python
# Get dataset details
dataset_id = "abc123-def456"
details = df[df['dataset_id'] == dataset_id]
print(details[['title', 'organization', 'rdls_components', 'confidence']])
```

### Step 3: Add overrides
Edit `config/overrides.yaml`:
```yaml
overrides:
  "abc123-def456":
    decision: keep
    components: [hazard]
    note: "Reviewed: valid flood hazard map"
```

### Step 4: Re-run notebook
Run this notebook to apply overrides and generate final outputs.

---

## Statistics Comparison

The notebook outputs before/after statistics:

```
=== CLASSIFICATION SUMMARY ===

Before Overrides:
  Total: 11,246
  Included: 10,759
  Excluded: 487

After Overrides:
  Total: 11,246
  Included: 10,782 (+23)
  Excluded: 464 (-23)
  Manual keeps: 25
  Manual excludes: 2
```

---

## Best Practices

### When to use overrides

✅ **Good use cases:**
- Dataset with sparse metadata but known value
- Misclassified due to unusual terminology
- Duplicates that should be excluded
- Known high-quality sources

❌ **Avoid:**
- Mass overrides (fix mapping rules instead)
- Overrides without documentation
- Overriding based on organization alone

### Documentation
Always include a `note` explaining the override:
```yaml
"abc123":
  decision: keep
  note: "WFP vulnerability assessment - low score due to missing tags"
```

---

## Troubleshooting

### Override not applied
1. Check dataset_id matches exactly (UUID format)
2. Verify YAML syntax (proper indentation)
3. Re-run the notebook

### Too many overrides needed
If you need >50 overrides, consider:
- Adjusting mapping rules in Step 03
- Adding organization hints
- Reviewing classification threshold

---

## Example Override Scenarios

### Scenario 1: Missing tag
Dataset "Somalia Drought Impact" has no "drought" tag but clearly is drought data.
```yaml
"drought-impact-somalia-uuid":
  decision: keep
  components: [hazard, loss]
  note: "Drought impact assessment - missing drought tag"
```

### Scenario 2: Duplicate dataset
Two datasets contain the same data.
```yaml
"duplicate-dataset-uuid":
  decision: exclude
  note: "Duplicate of dataset xyz - keep original"
```

### Scenario 3: Wrong component
Dataset classified as exposure but is actually vulnerability.
```yaml
"poverty-index-uuid":
  decision: keep
  components: [vulnerability]
  note: "Poverty index is vulnerability proxy, not exposure"
```

---

[← Previous: Classify Candidates](04_classify_candidates.md) | [Back to README](../README.md) | [Next: Translate to RDLS →](06_translate_to_rdls.md)
