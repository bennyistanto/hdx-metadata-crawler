# 04 - Classify RDLS Candidates

**Notebook:** `notebook/04_rdls_classify_hdx_candidates.ipynb`

---

## Summary

Applies the mapping rules from Step 03 to classify all HDX datasets into RDLS risk components using integer-based scoring with confidence tiers. Enriches classification signals with a signal dictionary containing additional hazard and exposure patterns, and applies exclusion patterns to reduce false positives.

**For Decision Makers:**
> This notebook is the "sorting hat" - it analyzes every HDX dataset and decides which RDLS category (or categories) it belongs to. The output is a classification table with categorical confidence levels (high/medium/low) that drives all downstream processing.

---

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| Dataset JSONs | `dataset_metadata/*.json` | Raw HDX metadata |
| Tag mapping | `config/tag_to_rdls_component.yaml` | From Step 03 |
| Keyword mapping | `config/keyword_to_rdls_component.yaml` | From Step 03 |
| Org hints | `config/org_hints.yaml` | From Step 03 |
| Signal dictionary | `config/signal_dictionary.yaml` | 89 additional hazard/exposure patterns |
| OSM exclusions | `policy/osm_excluded_dataset_ids.txt` | From Step 02 |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Classification | `derived/classification.csv` | All datasets with scores and confidence |
| Summary | `derived/classification_summary.json` | Aggregate statistics |
| Included IDs | `derived/rdls_included_dataset_ids.txt` | Datasets passing threshold |

---

## Key Configuration

```python
CANDIDATE_MIN_SCORE = 5       # Minimum total score to qualify as RDLS candidate
CONF_HIGH = 7                 # Score threshold for high confidence
CONF_MED = 4                  # Score threshold for medium confidence
KEYWORD_HIT_WEIGHT = 2        # Points awarded per keyword match
```

---

## Classification Output Schema

| Column | Type | Description |
|--------|------|-------------|
| `dataset_id` | str | HDX dataset UUID |
| `title` | str | Dataset title |
| `organization` | str | Publisher organization |
| `hazard_score` | int | Hazard component score |
| `exposure_score` | int | Exposure component score |
| `vulnerability_score` | int | Vulnerability proxy score |
| `loss_score` | int | Loss/impact component score |
| `rdls_components` | str | Assigned components (semicolon-separated) |
| `confidence` | str | Confidence tier: high, medium, or low |
| `included` | bool | Passes threshold for RDLS |

---

## How Classification Works

```
For each dataset:
1. Extract tags, title, description, organization
2. Apply tag mapping -> component scores (integer points)
3. Load signal dictionary (89 additional hazard/exposure patterns)
4. Apply keyword matching -> add KEYWORD_HIT_WEIGHT per match
5. Apply exclusion patterns -> subtract penalty (e.g., -3 for exclusion matches)
6. Apply org hints -> adjust scores
7. Sum integer scores per component
8. Assign components where score >= CANDIDATE_MIN_SCORE
9. Assign confidence tier:
   - high:   total score >= CONF_HIGH (7)
   - medium: total score >= CONF_MED (4)
   - low:    total score >= CANDIDATE_MIN_SCORE (5) but < CONF_HIGH
10. Mark as included/excluded
```

### Signal Dictionary Enrichment

The signal dictionary (`config/signal_dictionary.yaml`) provides 89 additional hazard and exposure patterns beyond the base keyword mappings. These patterns capture domain-specific terminology that improves recall for risk-related datasets.

### Exclusion Patterns

Exclusion patterns reduce false positives by applying a negative score penalty (e.g., -3 points) when a dataset matches known non-risk patterns. This prevents datasets with incidental risk-related keywords from being classified as RDLS candidates.

---

## Component Assignment Rules

| Scenario | Assignment |
|----------|------------|
| Single component above threshold | Assign that component |
| Multiple components above threshold | Assign all (multi-component) |
| All scores below CANDIDATE_MIN_SCORE | Mark as excluded |
| OSM-excluded dataset | Mark as excluded |

**Example:**
```
hazard_score: 8
exposure_score: 6
vulnerability_score: 2
loss_score: 1

-> rdls_components: "hazard;exposure"
-> confidence: high
-> included: True
```

---

## Statistics (Typical Run)

| Metric | Value |
|--------|-------|
| Total non-OSM datasets | 22,597 |
| RDLS candidates | 13,053 (49.7%) |

### Confidence Distribution

| Confidence | Count |
|------------|-------|
| High | 12,306 |
| Medium | 7,762 |
| Low | 6,178 |

### Component Coverage

| Component | Datasets |
|-----------|----------|
| Hazard | 4,109 |
| Exposure | 19,858 |
| Vulnerability proxy | 12,952 |
| Loss/impact | 2,745 |

---

## Quality Assurance

### Review top classifications
```python
# High-confidence datasets
df[df['confidence'] == 'high'].head(20)

# Multi-component datasets
df[df['rdls_components'].str.contains(';')].sample(10)
```

### Check for misclassification
```python
# Low-confidence inclusions (may need review)
df[(df['included']) & (df['confidence'] == 'low')]

# Borderline exclusions (score just below threshold)
df[(~df['included']) & (df['hazard_score'] + df['exposure_score'] >= 3)]
```

---

## Troubleshooting

### Too many inclusions
- Increase `CANDIDATE_MIN_SCORE` threshold
- Add more exclusion patterns to reduce false positives
- Review and tighten mapping weights

### Too few inclusions
- Decrease `CANDIDATE_MIN_SCORE` threshold
- Add more patterns to signal dictionary
- Add more tag/keyword mappings
- Review OSM exclusion for false positives

### Wrong component assignments
- Review specific datasets in `derived/classification.csv`
- Adjust tag weights in Step 03
- Add keyword patterns or exclusion patterns for edge cases
- Check signal dictionary for missing domain terms

---

## Example Output

```csv
dataset_id,title,organization,hazard_score,exposure_score,vulnerability_score,loss_score,rdls_components,confidence,included
abc123,Kenya Flood Map,OCHA,8,2,0,0,hazard,high,True
def456,Population Census,WorldPop,0,9,3,0,exposure;vulnerability_proxy,high,True
ghi789,Poverty Index,WFP,1,6,5,0,exposure;vulnerability_proxy,medium,True
```

---

[<- Previous: Define Mapping](03_define_mapping.md) | [Back to README](../README.md) | [Next: Review & Overrides ->](05_review_overrides.md)
