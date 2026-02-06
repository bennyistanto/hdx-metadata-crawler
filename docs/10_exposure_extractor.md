# 10 - Exposure Block Extractor

**Notebook:** `notebook/10_rdls_exposure_block_extractor.ipynb`

---

## Summary

Extracts detailed exposure information from HDX datasets to populate RDLS exposure metadata blocks.

**For Decision Makers:**
> This notebook identifies what assets and populations are documented in each dataset - people, buildings, infrastructure, crops, etc. - and extracts relevant attributes like categories, metrics, and valuations.

---

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| Dataset JSONs | `dataset_metadata/*.json` | Raw HDX metadata |
| Signal dictionary | `config/signal_dictionary.yaml` | From Step 08 |
| Classification | `derived/classification_final.csv` | From Step 05 |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Exposure extracts | `analysis/exposure_extracts.csv` | Per-dataset exposure info |
| Exposure summary | `analysis/exposure_summary.json` | Aggregate statistics |

---

## RDLS Exposure Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **population** | Human population data | Census, demographics, density |
| **buildings** | Structures and facilities | Residential, commercial, industrial |
| **infrastructure** | Networks and utilities | Roads, bridges, power lines |
| **agriculture** | Farming and livestock | Crops, farmland, cattle |
| **environment** | Natural assets | Forests, wetlands, ecosystems |
| **economic** | Financial assets | GDP, property values, assets |

---

## Exposure Attributes Extracted

| Attribute | Description | Example |
|-----------|-------------|---------|
| `exposure_category` | RDLS exposure type | "population" |
| `subcategory` | Detailed classification | "residential_buildings" |
| `metric` | Measurement type | "count", "area_sqkm", "value_usd" |
| `taxonomy` | Classification system | "GED4ALL", "OSM" |
| `temporal_reference` | Data date | "2020" |

---

## Key Functions

### `ExposureExtractor`
Main extraction class.

```python
extractor = ExposureExtractor(signal_dictionary)
exposure_info = extractor.extract(dataset_json)
# exposure_info.category: str
# exposure_info.subcategory: Optional[str]
# exposure_info.metric: Optional[str]
# exposure_info.confidence: float
```

### `infer_exposure_category()`
Maps signals to RDLS exposure categories.

```python
category = infer_exposure_category(
    tags=["population", "census"],
    title="Kenya Population Census 2019"
)
# Returns: "population"
```

### `extract_metrics()`
Identifies measurement types from metadata.

```python
metrics = extract_metrics("Building footprints with area in square meters")
# Returns: ["area_sqm", "count"]
```

---

## Category Inference Rules

| Signal Pattern | Inferred Category |
|----------------|-------------------|
| population, census, demographic, inhabitants | population |
| building, structure, house, facility | buildings |
| road, bridge, highway, infrastructure | infrastructure |
| crop, agriculture, farm, livestock | agriculture |
| forest, wetland, ecosystem | environment |
| GDP, asset, value, economic | economic |

---

## Subcategory Detection

### Buildings
| Subcategory | Signals |
|-------------|---------|
| residential | house, dwelling, residential |
| commercial | shop, office, commercial |
| industrial | factory, warehouse, industrial |
| public | school, hospital, government |
| mixed | building, structure (generic) |

### Infrastructure
| Subcategory | Signals |
|-------------|---------|
| transport | road, bridge, railway, airport |
| utilities | power, water, telecommunications |
| health | hospital, clinic, health facility |
| education | school, university |

---

## Statistics (Typical Run)

```
=== EXPOSURE EXTRACTION SUMMARY ===

Datasets with exposure signals: 19,742

Exposure category distribution:
  - population: 10,267 (52.0%)
  - buildings: 4,542 (23.0%)
  - infrastructure: 2,961 (15.0%)
  - agriculture: 1,185 (6.0%)
  - economic: 592 (3.0%)
  - environment: 195 (1.0%)

Attributes extracted:
  - With subcategory: 8,412 (42.6%)
  - With metric: 6,543 (33.1%)
  - With taxonomy: 2,156 (10.9%)
```

---

## Metric Detection Patterns

```python
metric_patterns = {
    "count": [r"count", r"number of", r"total"],
    "area_sqkm": [r"area", r"sq\s*km", r"square kilometer"],
    "area_sqm": [r"sq\s*m", r"square meter", r"m2"],
    "value_usd": [r"value", r"USD", r"\$", r"dollar"],
    "density": [r"density", r"per\s*km", r"per\s*hectare"],
    "percentage": [r"percent", r"%", r"ratio"],
}
```

---

## Taxonomy Recognition

The extractor identifies standard classification systems:

| Taxonomy | Description | Detection |
|----------|-------------|-----------|
| GED4ALL | Global Exposure Database | "GED4ALL", "global exposure" |
| GHSL | Global Human Settlement | "GHSL", "JRC" |
| WorldPop | Population estimates | "WorldPop" |
| OSM | OpenStreetMap buildings | "OSM", "OpenStreetMap" |
| Custom | Dataset-specific | Default if none detected |

---

## How It Works

```
1. Load datasets classified as exposure
2. For each dataset:
   a. Scan for exposure category signals
   b. Detect subcategories from detailed terms
   c. Extract metrics and measurement types
   d. Identify taxonomy/classification system
   e. Parse temporal reference
3. Aggregate by category and subcategory
4. Export extracts and summary
```

---

## Multi-Category Datasets

Many exposure datasets contain multiple categories:

```json
{
  "title": "Kenya Infrastructure and Population",
  "exposure_categories": ["population", "infrastructure"],
  "subcategories": ["residential", "roads", "health_facilities"]
}
```

The extractor captures all relevant categories.

---

## Troubleshooting

### Missing exposure category
- Review signal dictionary terms
- Check if dataset is primarily non-exposure
- Consider manual assignment via overrides

### Incorrect category
- Review inference rules
- Look for dominant vs. secondary signals
- Multi-category assignment may be needed

### Low subcategory extraction
- Subcategories require more specific terms
- 40-50% extraction rate is typical
- Generic "buildings" or "population" datasets won't have subcategories

---

[← Previous: Hazard Extractor](09_hazard_extractor.md) | [Back to README](../README.md) | [Next: Vulnerability/Loss Extractor →](11_vulnerability_loss_extractor.md)
