# 04 - Classify RDLS Candidates

**Notebook:** `notebook/04_rdls_classify_hdx_candidates.ipynb`

---

## Summary

Applies the mapping rules from Step 03 to classify all HDX datasets into RDLS risk components with confidence scores.

**For Decision Makers:**
> This notebook is the "sorting hat" - it analyzes every HDX dataset and decides which RDLS category (or categories) it belongs to. The output is a classification table that drives all downstream processing.

---

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| Dataset JSONs | `dataset_metadata/*.json` | Raw HDX metadata |
| Tag mapping | `config/tag_to_rdls_component.yaml` | From Step 03 |
| Keyword mapping | `config/keyword_to_rdls_component.yaml` | From Step 03 |
| Org hints | `config/org_hints.yaml` | From Step 03 |
| OSM exclusions | `policy/osm_excluded_dataset_ids.txt` | From Step 02 |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Classification | `derived/classification_raw.csv` | All datasets with scores |
| Summary | `derived/classification_summary.json` | Aggregate statistics |
| Included IDs | `derived/rdls_included_dataset_ids.txt` | Datasets passing threshold |

---

## Key Configuration

```python
@dataclass
class ClassificationConfig:
    min_confidence: float = 0.3        # Minimum score to include
    multi_component: bool = True       # Allow multiple components per dataset
    apply_osm_exclusion: bool = True   # Use OSM exclusion list
    normalize_scores: bool = True      # Normalize to 0-1 range
```

---

## Classification Output Schema

| Column | Type | Description |
|--------|------|-------------|
| `dataset_id` | str | HDX dataset UUID |
| `title` | str | Dataset title |
| `organization` | str | Publisher organization |
| `hazard_score` | float | Hazard component score |
| `exposure_score` | float | Exposure component score |
| `vulnerability_score` | float | Vulnerability score |
| `loss_score` | float | Loss component score |
| `rdls_components` | str | Assigned components (semicolon-separated) |
| `confidence` | float | Overall confidence (0-1) |
| `included` | bool | Passes threshold for RDLS |

---

## Key Functions

### `RDLSClassifier`
Main classification engine.

```python
classifier = RDLSClassifier(tag_config, keyword_config, org_hints)
result = classifier.classify(dataset_json)
# result.scores: Dict[str, float]
# result.components: List[str]
# result.confidence: float
```

### `score_dataset()`
Computes component scores for a single dataset.

```python
scores = score_dataset(
    tags=["flood", "population"],
    title="Kenya Flood Exposure",
    notes="Population at risk from flooding",
    organization="OCHA"
)
# Returns: {"hazard": 0.85, "exposure": 0.92, ...}
```

---

## How Classification Works

```
For each dataset:
1. Extract tags, title, description, organization
2. Apply tag mapping → component scores
3. Apply keyword matching → add to scores
4. Apply org hints → adjust scores
5. Normalize scores to 0-1 range
6. Assign components where score > threshold
7. Compute overall confidence
8. Mark as included/excluded
```

---

## Component Assignment Rules

| Scenario | Assignment |
|----------|------------|
| Single high score | Assign that component |
| Multiple high scores | Assign all (multi-component) |
| All scores below threshold | Mark as excluded |
| OSM-excluded dataset | Mark as excluded |

**Example:**
```
hazard_score: 0.85
exposure_score: 0.72
vulnerability_score: 0.15
loss_score: 0.08

→ rdls_components: "hazard;exposure"
→ confidence: 0.78
→ included: True
```

---

## Statistics (Typical Run)

| Metric | Value |
|--------|-------|
| Total datasets | 26,246 |
| After OSM exclusion | ~11,000 |
| Classified as RDLS | ~10,759 |
| Hazard signals | ~13.8% |
| Exposure signals | ~75.2% |

---

## Quality Assurance

### Review top classifications
```python
# High-confidence hazard datasets
df[df['hazard_score'] > 0.8].head(20)

# Multi-component datasets
df[df['rdls_components'].str.contains(';')].sample(10)
```

### Check for misclassification
```python
# Low confidence inclusions (may need review)
df[(df['included']) & (df['confidence'] < 0.4)]

# High confidence exclusions (may be missing good data)
df[(~df['included']) & (df['confidence'] > 0.6)]
```

---

## Troubleshooting

### Too many inclusions
- Increase `min_confidence` threshold
- Review and tighten mapping weights

### Too few inclusions
- Decrease `min_confidence` threshold
- Add more tag/keyword mappings
- Review OSM exclusion for false positives

### Wrong component assignments
- Review specific datasets in the classification CSV
- Adjust tag weights in Step 03
- Add keyword patterns for edge cases

---

## Example Output

```csv
dataset_id,title,organization,hazard_score,exposure_score,...,rdls_components,confidence,included
abc123,Kenya Flood Map,OCHA,0.92,0.15,...,hazard,0.88,True
def456,Population Census,WorldPop,0.05,0.95,...,exposure,0.91,True
ghi789,Poverty Index,WFP,0.10,0.45,...,exposure;vulnerability,0.62,True
```

---

[← Previous: Define Mapping](03_define_mapping.md) | [Back to README](../README.md) | [Next: Review & Overrides →](05_review_overrides.md)
