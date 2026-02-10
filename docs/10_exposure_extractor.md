# 10 - Exposure Block Extractor

**Notebook:** `notebook/10_rdls_exposure_block_extractor.ipynb`

---

## Summary

Extracts detailed exposure information from HDX datasets using a **3-tier extraction cascade** and produces schema-compliant RDLS v0.3 exposure blocks with validated `(category, dimension, quantity_kind)` triplets.

**For Decision Makers:**
> This notebook identifies what assets and populations are documented in each dataset — people, buildings, infrastructure, crops, etc. — and extracts metrics, taxonomy references, and currency information. A tiered approach prioritises title and tags over resource descriptions and notes to avoid misclassification.

---

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| Dataset JSONs | `dataset_metadata/*.json` | Raw HDX metadata (26,246 files) |
| Signal dictionary | `config/signal_dictionary.yaml` | All 7 exposure category patterns from Step 08 |
| Classification | `derived/classification_final.csv` | From Step 05 |
| RDLS Schema | `rdls/schema/rdls_schema_v0.3.json` | Codelist enums for validation |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Extraction CSV | `rdls/extracted/exposure_extraction_results.csv` | All 26,246 records with exposure flags |
| High-confidence CSV | `rdls/extracted/exposure_extraction_high_confidence.csv` | Records with confidence ≥ 0.8 |
| Exposure JSON blocks | `rdls/extracted/rdls_exp-hdx_*.json` | ~20,500 individual RDLS records with exposure blocks |

---

## RDLS Exposure Categories

The RDLS v0.3 schema defines **7 closed codelist values** for `exposure_category`:

| Category | Description | Example Patterns |
|----------|-------------|-----------------|
| **agriculture** | Farming, crops, livestock | `\b(crop\|livestock\|farmland)\b` |
| **buildings** | Structures and facilities | `\b(building\|dwelling\|footprint)\b` |
| **infrastructure** | Networks and utilities | `\b(road\|bridge\|energy\|power.?station)\b` |
| **population** | Human population data | `\b(population.?count\|head.?count\|census.?data)\b` |
| **natural_environment** | Natural assets | `\b(forest\|wetland\|ecosystem)\b` |
| **economic_indicator** | Financial metrics | `\b(GDP\|economic.?indicator)\b` |
| **development_index** | Development indices | `\b(HDI\|human.?development)\b` |

---

## 3-Tier Extraction Cascade

The extractor uses a tiered approach that prioritises authoritative text fields over noisy ones:

### Tier 1 — Title, Name, Tags (confidence weight: 1.0)
- Most authoritative signals
- Matches here are always included
- Example: title "Uganda Energy/Gas Facilities" → `infrastructure`

### Tier 2 — Individual Resources (confidence weight: 0.85)
- Each resource is scanned separately (name + description)
- Can introduce new categories not found in Tier 1
- Source field tracks which resource matched (e.g., `resource[2]`)

### Tier 3 — Notes, Methodology (confidence weight: 0.6)
- **Corroboration only** — cannot introduce new categories
- If a category already appears in Tier 1 or 2, Tier 3 boosts its confidence by +0.05
- If a category appears only in Tier 3, it is **discarded**
- **Exception**: If Tiers 1 and 2 find nothing, Tier 3 is allowed as a fallback

### Why This Matters

Without tiering, a dataset titled "Uganda Energy/Gas Facilities" could be misclassified as `population` because the notes mention "Census Mapping Programme". The cascade ensures the title signal (`infrastructure`) takes precedence.

---

## VALID_TRIPLETS Constraint

Every exposure block must have internally consistent `(category, dimension, quantity_kind)` combinations. The `VALID_TRIPLETS` table enforces this:

| Category | Allowed (dimension, quantity_kind) Pairs |
|----------|------------------------------------------|
| **agriculture** | (structure, area), (product, monetary), (product, count) |
| **buildings** | (structure, count), (structure, monetary), (content, monetary), (content, count) |
| **infrastructure** | (structure, length), (structure, monetary), (structure, count), (disruption, time) |
| **population** | (population, count) |
| **natural_environment** | (structure, area) |
| **economic_indicator** | (product, monetary), (index, count) |
| **development_index** | (index, count) |

If the inferred dimension or quantity_kind is not in the allowed set, the extractor falls back to the first valid triplet for that category.

---

## Key Data Structures

| Structure | Purpose |
|-----------|---------|
| `TieredFields` | Dataclass preserving text field hierarchy (title, name, tags, resources[], notes, methodology) |
| `VALID_TRIPLETS` | Category → allowed (dimension, quantity_kind) pairs |
| `METRIC_DIMENSION_PATTERNS` | 6 dimensions: structure, content, product, disruption, population, index |
| `QUANTITY_KIND_PATTERNS` | 5 kinds: count, area, length, monetary, time |
| `TAXONOMY_PATTERNS` | All 12 RDLS taxonomy schemes (GED4ALL, MOVER, GLIDE, EMDAT, etc.) |
| `CURRENCY_PATTERNS` | 10 ISO 4217 currency codes |

---

## Key Classes and Functions

### `ExposureExtractor`

Main extraction class with 3-tier cascade.

```python
extractor = ExposureExtractor(signal_dict, schema_enums)
result = extractor.extract(hdx_record)
# result.categories: List[ExtractionMatch]
# result.metrics: Dict[str, MetricExtraction]
# result.taxonomy_hint: Optional[str]
```

Key methods:
- `_extract_tiered_fields()` — Parse HDX metadata into `TieredFields` (resources as list, not concatenated)
- `_scan_tier1()` / `_scan_tier2()` / `_scan_tier3()` — Tier-specific pattern scanning
- `_merge_tiers()` — Combine tiers with corroboration rules
- `_infer_metrics()` — Detect dimension and quantity_kind per category, scoped to source field
- `extract()` — Main entry point

### `build_exposure_block()`

Converts extraction results into RDLS v0.3 JSON:
- Validates each `(category, dimension, quantity_kind)` against `VALID_TRIPLETS`
- Adds `currency` field when `quantity_kind = monetary`
- Detects taxonomy from all 12 RDLS-defined schemes

---

## Taxonomy Detection

The extractor recognises all 12 RDLS-defined taxonomy schemes:

| Taxonomy | Detection Pattern |
|----------|------------------|
| GED4ALL | `GED4ALL`, `global exposure` |
| MOVER | `MOVER` |
| GLIDE | `GLIDE` |
| EMDAT | `EM-DAT`, `EMDAT` |
| GHSL | `GHSL`, `JRC` |
| WorldPop | `WorldPop` |
| OSM | `OpenStreetMap`, `OSM` |
| GADM | `GADM` |
| GAR | `GAR`, `global assessment` |
| UNDRR | `UNDRR` |
| WHO | `WHO` |
| WFP | `WFP`, `World Food Programme` |

---

## Extraction CSV Columns

| Column | Description |
|--------|-------------|
| `id` | HDX dataset UUID |
| `title` | Dataset title |
| `has_exposure` | Boolean: exposure signals detected |
| `categories` | Comma-separated exposure categories |
| `dimensions` | Comma-separated metric dimensions |
| `quantity_kinds` | Comma-separated quantity kinds |
| `taxonomy` | Detected taxonomy scheme |
| `currency` | ISO 4217 currency code (if monetary) |
| `tier_source` | Which tier produced each category (1/2/3) |
| `overall_confidence` | Float 0.0–1.0 |

---

## How It Works

```
1. Load all 26,246 dataset metadata files
2. For each dataset:
   a. Parse metadata into TieredFields (preserving resource list)
   b. Tier 1: Scan title, name, tags for exposure categories
   c. Tier 2: Scan each resource individually for categories
   d. Tier 3: Scan notes, methodology (corroboration only)
   e. Merge tiers: Tier 1 always included, Tier 2 can add new,
      Tier 3 can only boost existing (unless T1+T2 empty)
   f. For each category:
      - Infer dimension and quantity_kind from scoped text
      - Validate against VALID_TRIPLETS
      - Detect taxonomy scheme
      - Detect currency if monetary
3. Build RDLS exposure blocks with validated triplets
4. Export extraction CSVs and individual JSON files
```

---

## Multi-Category Datasets

Many HDX datasets contain multiple exposure categories. The extractor captures all:

```json
{
  "exposure": [
    {
      "id": "exposure_abc123_1",
      "category": "infrastructure",
      "metrics": [{"dimension": "structure", "quantity_kind": "count"}]
    },
    {
      "id": "exposure_abc123_2",
      "category": "population",
      "metrics": [{"dimension": "population", "quantity_kind": "count"}]
    }
  ]
}
```

---

## Troubleshooting

### Wrong category detected
- Check which tier the category came from (`tier_source` column)
- If from Tier 3 (notes), verify the cascade logic — notes should only corroborate
- Expand signal dictionary patterns if title terms are missing

### Missing category
- Review signal dictionary for term coverage
- Check if the dataset title uses uncommon terminology
- Infrastructure patterns include energy/utility terms (energy, power station, substation, etc.)

### Invalid metric triplet
- The extractor validates against `VALID_TRIPLETS` and falls back to defaults
- Check `VALID_TRIPLETS` table for allowed combinations per category

---

[← Previous: Hazard Extractor](09_hazard_extractor.md) | [Back to README](../README.md) | [Next: Vulnerability/Loss Extractor →](11_vulnerability_loss_extractor.md)
