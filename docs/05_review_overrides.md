# 05 - Review & Overrides

**Notebook:** `notebook/05_rdls_review_overrides.ipynb`

---

## Summary

Applies manual review decisions and automated component dependency enforcement to the classification results. Generates review packs prioritizing low and medium confidence datasets, enforces co-occurrence rules for components, and applies manual overrides.

**For Decision Makers:**
> This is the "human in the loop" step where domain experts can override automated classifications. It also enforces structural rules (e.g., vulnerability data must co-occur with hazard or exposure). It's optional but recommended for high-quality outputs.

---

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| Classification | `derived/classification.csv` | From Step 04 |
| Overrides config | `config/overrides.yaml` | Manual review decisions |
| OSM exclusions | `policy/osm_excluded_dataset_ids.txt` | From Step 02 |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Final classification | `derived/classification_final.csv` | With overrides and dependency fixes applied |
| Final summary | `derived/classification_final_summary.json` | Updated statistics |
| Included IDs | `derived/rdls_included_dataset_ids_final.txt` | Final inclusion list |

---

## Key Configuration

```python
REVIEW_PACK_SIZE = 1500
PRIORITIZE_CONFIDENCE = ('low', 'medium')
ALLOW_OSM_OVERRIDE = False    # OSM datasets cannot be overridden back in
```

---

## Component Dependency Enforcement

A key automated step in this notebook is component dependency enforcement. The rule:

> **`vulnerability_proxy` and `loss_impact` must co-occur with `hazard` or `exposure`.** If a dataset has vulnerability_proxy or loss_impact but lacks both hazard and exposure, `exposure` is automatically added.

This ensures structural validity of RDLS records, since vulnerability and loss data only make sense in the context of a hazard or exposure.

### Dependency Enforcement Statistics

| Metric | Count |
|--------|-------|
| Total datasets with components added | 2,837 |
| Additions for vulnerability_proxy | 2,481 |
| Additions for loss_impact | 356 |

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
    components: [vulnerability_proxy]
    note: "Correctly classified as vulnerability proxy, not exposure"
```

---

## Override Fields

| Field | Required | Values | Description |
|-------|----------|--------|-------------|
| `decision` | Yes | `keep` / `exclude` | Include or exclude from RDLS |
| `components` | No | List of components | Override component assignment |
| `note` | No | String | Reason for override (documentation) |

**Policy constraint:** `ALLOW_OSM_OVERRIDE = False` means OSM-excluded datasets cannot be overridden back into the classification, regardless of manual review decisions.

---

## How Overrides Work

```
1. Load classification.csv from Step 04
2. Generate review packs (REVIEW_PACK_SIZE = 1,500)
   - Prioritize low and medium confidence datasets
3. Apply component dependency enforcement:
   - If vulnerability_proxy or loss_impact present without hazard or exposure,
     auto-add exposure
4. For each dataset with an override:
   a. Check OSM policy (skip if OSM-excluded and ALLOW_OSM_OVERRIDE = False)
   b. Apply decision (keep/exclude)
   c. Replace components if specified
   d. Mark as manually reviewed
5. Write classification_final.csv
```

---

## Review Workflow

### Step 1: Review packs
The notebook generates review packs of up to 1,500 datasets, prioritizing those with low and medium confidence for expert review.

### Step 2: Identify candidates for review
```python
# Low-confidence inclusions
review_candidates = df[
    (df['included']) &
    (df['confidence'] == 'low')
].sort_values('hazard_score')

# Medium-confidence for spot checks
spot_check = df[
    (df['included']) &
    (df['confidence'] == 'medium')
].sample(50)
```

### Step 3: Review specific datasets
```python
# Get dataset details
dataset_id = "abc123-def456"
details = df[df['dataset_id'] == dataset_id]
print(details[['title', 'organization', 'rdls_components', 'confidence']])
```

### Step 4: Add overrides
Edit `config/overrides.yaml`:
```yaml
overrides:
  "abc123-def456":
    decision: keep
    components: [hazard]
    note: "Reviewed: valid flood hazard map"
```

### Step 5: Re-run notebook
Run this notebook to apply overrides, enforce dependencies, and generate final outputs.

---

## Statistics Comparison

The notebook outputs before/after statistics:

```
=== CLASSIFICATION SUMMARY ===

Before Overrides & Dependency Enforcement:
  Total non-OSM: 22,597
  RDLS candidates: 13,053

After Overrides & Dependency Enforcement:
  Datasets with components auto-added: 2,837
    - vulnerability_proxy dependencies: 2,481
    - loss_impact dependencies: 356
  Manual overrides applied: [per config/overrides.yaml]
```

---

## Best Practices

### When to use overrides

**Good use cases:**
- Dataset with sparse metadata but known value
- Misclassified due to unusual terminology
- Duplicates that should be excluded
- Known high-quality sources

**Avoid:**
- Mass overrides (fix mapping rules instead)
- Overrides without documentation
- Overriding based on organization alone
- Attempting to override OSM-excluded datasets (blocked by policy)

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
3. Check if dataset is OSM-excluded (ALLOW_OSM_OVERRIDE = False blocks these)
4. Re-run the notebook

### Too many overrides needed
If you need >50 overrides, consider:
- Adjusting mapping rules in Step 03
- Adding organization hints
- Adding patterns to signal dictionary
- Reviewing classification thresholds in Step 04

### Dependency enforcement added unexpected components
This is expected behavior. If a dataset has vulnerability_proxy or loss_impact without hazard or exposure, exposure is auto-added. To prevent this:
- Review whether the dataset truly belongs in the vulnerability/loss category
- Use an override to set the correct component list explicitly

---

## Example Override Scenarios

### Scenario 1: Missing tag
Dataset "Somalia Drought Impact" has no "drought" tag but clearly is drought data.
```yaml
"drought-impact-somalia-uuid":
  decision: keep
  components: [hazard, loss_impact]
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
  components: [vulnerability_proxy]
  note: "Poverty index is vulnerability proxy, not exposure"
```

---

[<- Previous: Classify Candidates](04_classify_candidates.md) | [Back to README](../README.md) | [Next: Translate to RDLS ->](06_translate_to_rdls.md)
