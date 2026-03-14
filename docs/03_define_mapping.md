# 03 - Define RDLS Mapping

**Notebook:** `notebook/03_rdls_define_mapping.ipynb`

---

## Summary

Defines the rules that map HDX metadata signals (tags, keywords, organizations) to RDLS risk components (Hazard, Exposure, Vulnerability Proxy, Loss/Impact). Also scans the non-OSM corpus to collect tag, organization, and format statistics for calibration.

**For Decision Makers:**
> This notebook creates the "translation dictionary" that determines how HDX datasets are classified into RDLS categories. It's the core business logic that decides what counts as hazard data vs. exposure data. It also produces a review sample CSV for human calibration.

---

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| Dataset JSONs | `dataset_metadata/*.json` | HDX metadata from Step 01 |
| OSM Exclusion List | `policy/osm_excluded_dataset_ids.txt` | IDs to exclude (from Step 02) |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Tag mapping | `config/tag_to_rdls_component.yaml` | Tag to component integer scores |
| Keyword mapping | `config/keyword_to_rdls_component.yaml` | Regex patterns per component |
| Org hints | `config/org_hints.yaml` | Organization component biases |
| Mapping rules doc | `reference/mapping_rules.md` | Human-readable rules reference |
| Review sample | `reference/samples_for_mapping.csv` | Random sample for calibration |

---

## Mapping Types

### 1. Tag Mapping
Direct mapping from HDX tags to RDLS components with integer point scores (2-5, where 5 is strongest signal). Tags are grouped by target component.

```yaml
# config/tag_to_rdls_component.yaml
hazard:
  flooding: 5
  drought: 5
  cyclones-hurricanes-typhoons: 5
  earthquake-tsunami: 5
  natural disasters: 3
  forecasting: 2
  topography: 2
exposure:
  facilities-infrastructure: 5
  populated places-settlements: 4
  population: 4
  health facilities: 4
  geodata: 2
vulnerability_proxy:
  demographics: 4
  poverty: 4
  socioeconomics: 4
  food security: 3
  health: 2
loss_impact:
  damage assessment: 5
  casualties: 5
  fatalities: 5
  affected population: 4
```

### 2. Keyword Mapping
Regex patterns applied to title and description, grouped by component.

```yaml
# config/keyword_to_rdls_component.yaml
hazard:
  - \bflood(s|ing)?\b
  - \bdrought\b
  - \bcyclone(s)?\b
  - \bhazard\b
exposure:
  - \broad(s)?\b
  - \bhospital(s)?\b
  - \binfrastructure\b
vulnerability_proxy:
  - \bpoverty\b
  - \bfood security\b
  - \bvulnerability\b
loss_impact:
  - \bdamage\b
  - \bloss(es)?\b
  - \bcasualt(y|ies)\b
```

### 3. Organization Hints
Integer biases for known data publishers, keyed by component.

```yaml
# config/org_hints.yaml
World Bank Group:
  vulnerability_proxy: 2
The DHS Program:
  vulnerability_proxy: 4
Food and Agriculture Organization:
  vulnerability_proxy: 3
UNICEF:
  vulnerability_proxy: 3
```

---

## RDLS Components Explained

| Component | What it represents | Example datasets |
|-----------|-------------------|------------------|
| **Hazard** | Natural/man-made threats | Flood maps, earthquake zones, cyclone tracks |
| **Exposure** | Assets at risk | Population, buildings, infrastructure, health facilities |
| **Vulnerability Proxy** | Susceptibility indicators | Poverty indices, demographics, food security |
| **Loss/Impact** | Historical impacts | Damage reports, casualty data, affected populations |

---

## How Scoring Works

Scores are simple integer sums. Each matching tag contributes its point value (2-5) to the corresponding component. Keyword matches and org hints add additional points.

```
Component Score = sum(matching tag scores) + keyword matches + org hint

Where:
- Tag scores: 2-5 points per matching tag
- Keyword matches: each regex hit contributes to its component
- Org hints: 0-4 points for known organizations
```

**Example:**
```
Dataset: "Kenya Flood Risk Map"
Tags: ["flooding", "hazards and risk"]
Organization: unknown

Tag scores:  flooding → hazard: 5
             hazards and risk → hazard: 3
Keyword:     "flood" → hazard (regex match)

Result:      hazard: 8+ points (strong hazard signal)
```

---

## Corpus Statistics (Actual Run)

| Metric | Value |
|--------|-------|
| Non-OSM datasets | 22,597 |
| Unique tags | 142 |
| Unique organizations | 357 |
| Unique resource formats | 47 |
| Review sample rows | 440 |

---

## Configuration Best Practices

### Tag Scores
- **5:** Strong, unambiguous signal (flooding, earthquake-tsunami, damage assessment)
- **3-4:** Moderate signal (natural disasters, demographics, affected population)
- **2:** Weak/contextual signal (topography, geodata, forecasting)

### Org Hints
- Keep scores **modest** (2-4) to avoid over-biasing classification
- Only add orgs with consistent, well-known data themes
- Review classification results before adding new orgs

### Keyword Patterns
- Use word boundaries: `\bflood\b` not `flood`
- Combine related terms in separate patterns per component
- Test patterns against the review sample CSV

---

## Updating Mappings

1. Run notebook 04 to see classification results
2. Review misclassified datasets
3. Add/adjust mappings in this notebook
4. Re-run notebooks 04-05 to verify improvement

---

## Example Configuration

```yaml
# Tag mapping excerpt (integer scores)
hazard:
  flooding: 5
  drought: 5
  earthquake-tsunami: 5
  climate hazards: 4
  hydrology: 3
exposure:
  facilities-infrastructure: 5
  population: 4
  health facilities: 4
  roads: 4
vulnerability_proxy:
  poverty: 4
  socioeconomics: 4
  food security: 3
loss_impact:
  damage assessment: 5
  casualties: 5
  affected population: 4

# Keyword patterns excerpt (regex, grouped by component)
hazard:
  - \bearthquake(s)?\b
  - \btsunami\b
  - \breturn period\b
loss_impact:
  - \bfatalit(y|ies)\b
  - \bcasualt(y|ies)\b
  - \baffected\b
```

---

[← Previous: OSM Exclusion](02_policy_osm_exclusion.md) | [Back to README](../README.md) | [Next: Classify Candidates →](04_classify_candidates.md)
