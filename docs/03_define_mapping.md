# 03 - Define RDLS Mapping

**Notebook:** `notebook/03_rdls_define_mapping.ipynb`

---

## Summary

Defines the rules that map HDX metadata signals (tags, keywords, organizations) to RDLS risk components (Hazard, Exposure, Vulnerability, Loss).

**For Decision Makers:**
> This notebook creates the "translation dictionary" that determines how HDX datasets are classified into RDLS categories. It's the core business logic that decides what counts as hazard data vs. exposure data.

---

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| Sample datasets | `dataset_metadata/*.json` | Optional corpus for calibration |
| Existing configs | `config/*.yaml` | Previous mapping rules (if any) |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Tag mapping | `config/tag_to_rdls_component.yaml` | Tag → component weights |
| Keyword mapping | `config/keyword_to_rdls_component.yaml` | Regex patterns |
| Org hints | `config/org_hints.yaml` | Organization biases |
| Reference | `reference/mapping_rules.md` | Human-readable rules |

---

## Mapping Types

### 1. Tag Mapping
Direct mapping from HDX tags to RDLS components with weights.

```yaml
# config/tag_to_rdls_component.yaml
flood:
  hazard: 0.9
  exposure: 0.1
population:
  exposure: 0.95
earthquake:
  hazard: 0.95
```

### 2. Keyword Mapping
Regex patterns applied to title and description.

```yaml
# config/keyword_to_rdls_component.yaml
patterns:
  - regex: "flood|inundation|river overflow"
    component: hazard
    weight: 0.8
  - regex: "population|census|demographic"
    component: exposure
    weight: 0.85
```

### 3. Organization Hints
Biases for known risk data publishers.

```yaml
# config/org_hints.yaml
organizations:
  "World Food Programme":
    exposure: 0.1
    vulnerability: 0.1
  "UNDRR":
    hazard: 0.15
    loss: 0.1
```

---

## RDLS Components Explained

| Component | What it represents | Example datasets |
|-----------|-------------------|------------------|
| **Hazard** | Natural/man-made threats | Flood maps, earthquake zones |
| **Exposure** | Assets at risk | Population, buildings, infrastructure |
| **Vulnerability** | Susceptibility factors | Poverty indices, building quality |
| **Loss** | Historical impacts | Damage reports, casualty data |

---

## Key Functions

### `TagMappingConfig`
Dataclass holding tag-to-component mappings.

```python
@dataclass
class TagMappingConfig:
    mappings: Dict[str, Dict[str, float]]

config.get_weights("flood")
# Returns: {"hazard": 0.9, "exposure": 0.1}
```

### `KeywordMatcher`
Applies regex patterns to text content.

```python
matcher = KeywordMatcher(patterns)
matches = matcher.match("Flood risk assessment for Kenya")
# Returns: [("hazard", 0.8, "flood")]
```

---

## How Scoring Works

```
Final Score = Tag Score + Keyword Score + Org Hint

Where:
- Tag Score = sum of weights for matching tags
- Keyword Score = sum of weights for matching patterns
- Org Hint = bias for known organizations (small, 0.1-0.2)
```

**Example:**
```
Dataset: "Kenya Flood Risk Map" by UNDRR
Tags: ["flood", "risk", "kenya"]

Tag Score:     flood → hazard: 0.9
Keyword Score: "flood" → hazard: 0.8
Org Hint:      UNDRR → hazard: 0.15

Final:         hazard: 1.85 (normalized to confidence)
```

---

## Configuration Best Practices

### Tag Weights
- **0.9-1.0:** Strong signal (flood, earthquake, population)
- **0.5-0.8:** Moderate signal (risk, assessment)
- **0.1-0.4:** Weak signal (data, map)

### Org Hints
- Keep weights **low** (0.1-0.2) to avoid over-biasing
- Only add orgs with consistent, high-quality data
- Review classification results before adding new orgs

### Keyword Patterns
- Use word boundaries: `\bflood\b` not `flood`
- Combine related terms: `flood|inundation|overflow`
- Test patterns against sample datasets

---

## Updating Mappings

1. Run notebook 04 to see classification results
2. Review misclassified datasets
3. Add/adjust mappings in this notebook
4. Re-run notebooks 04-05 to verify improvement

---

## Example Configuration

```yaml
# Tag mapping excerpt
flood:
  hazard: 0.9
  exposure: 0.1
population:
  exposure: 0.95
buildings:
  exposure: 0.9
poverty:
  vulnerability: 0.85
damage:
  loss: 0.9

# Keyword patterns excerpt
patterns:
  - regex: "earthquake|seismic|tremor"
    component: hazard
    weight: 0.85
  - regex: "casualties|fatalities|deaths"
    component: loss
    weight: 0.9
```

---

[← Previous: OSM Exclusion](02_policy_osm_exclusion.md) | [Back to README](../README.md) | [Next: Classify Candidates →](04_classify_candidates.md)
