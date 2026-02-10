# 09 - Hazard Block Extractor

**Notebook:** `notebook/09_rdls_hazard_block_extractor.ipynb`

---

## Summary

Extracts detailed hazard information from HDX datasets and produces schema-compliant RDLS v0.3 hazard blocks with properly nested `event_sets`, validated hazard→process type mappings, and inferred intensity measures.

**For Decision Makers:**
> This notebook identifies specific hazard types (flood, earthquake, cyclone, etc.) in each HDX dataset and constructs RDLS-compliant hazard metadata blocks. Each hazard type gets its own event set with validated process types, intensity measures, and return periods.

---

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| Dataset JSONs | `dataset_metadata/*.json` | Raw HDX metadata (26,246 files) |
| Signal dictionary | `config/signal_dictionary.yaml` | Hazard/process type patterns from Step 08 |
| Classification | `derived/classification_final.csv` | From Step 05 |
| RDLS Schema | `rdls/schema/rdls_schema_v0.3.json` | Codelist enums for validation |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Extraction CSV | `rdls/extracted/hazard_extraction_results.csv` | All 26,246 records with hazard flags |
| High-confidence CSV | `rdls/extracted/hazard_extraction_high_confidence.csv` | Records with confidence ≥ 0.8 |
| Hazard JSON blocks | `rdls/extracted/rdls_hzd-hdx_*.json` | ~3,200 individual RDLS records with hazard blocks |

---

## RDLS Hazard Schema

The RDLS v0.3 hazard block uses a nested structure:

```
hazard
└── event_sets[]                    (one per hazard type)
    ├── id, analysis_type
    ├── hazards[]                   (hazard + process type + intensity)
    │   ├── type                    (11 closed codelist values)
    │   ├── hazard_process          (30 closed codelist values)
    │   └── intensity_measure
    └── events[]                    (one per return period, or single fallback)
        ├── calculation_method
        ├── return_period (optional)
        └── occurrence
            └── empirical{} | probabilistic{} | deterministic{}
```

### One Event Set Per Hazard Type

Multi-hazard datasets (e.g., "flood + earthquake") produce **separate event sets** — one per hazard type. This ensures each event set has internally consistent hazard/process/intensity values.

---

## Hazard → Process Type Constraint

The extractor enforces the RDLS schema constraint that each hazard type only allows specific process types. This mapping is loaded directly from the schema:

| Hazard Type | Allowed Process Types |
|-------------|----------------------|
| **coastal_flood** | coastal_flood, storm_surge |
| **convective_storm** | tornado, hail, lightning, rain, snow |
| **drought** | agricultural_drought, hydrological_drought, meteorological_drought, socioeconomic_drought |
| **earthquake** | ground_motion, liquefaction, surface_rupture |
| **extreme_temperature** | extreme_cold, extreme_heat, heat_wave, cold_wave |
| **flood** | fluvial_flood, pluvial_flood, groundwater_flood, flash_flood |
| **landslide** | landslide, mudflow, rockfall, snow_avalanche |
| **strong_wind** | extratropical_cyclone, tropical_cyclone, wind |
| **tsunami** | local_tsunami, distant_tsunami |
| **volcanic** | ashfall, lahar, lava_flow, pyroclastic_flow |
| **wildfire** | wildfire, brush_fire, forest_fire |

If a detected process type is invalid for its hazard type, the extractor falls back to a safe default (typically the first allowed process type).

---

## Key Data Structures

| Structure | Purpose |
|-----------|---------|
| `HAZARD_PROCESS_MAPPINGS` | Schema-derived hazard → valid process types (11 × 30) |
| `HAZARD_PROCESS_DEFAULT` | Fallback process type per hazard (11 entries) |
| `INTENSITY_MEASURE_MAPPINGS` | Default intensity measure per hazard/process type |
| `COMPOUND_HDX_TAGS` | Multi-term HDX tags requiring corroboration (e.g., `earthquake-tsunami`) |
| `RP_PATTERNS` | 6 regex patterns for return period extraction |
| `IM_TEXT_PATTERNS` | 10 regex patterns for intensity measure detection |

---

## Key Classes and Functions

### `HazardExtractor`

Main extraction class with pattern matching against the signal dictionary.

```python
extractor = HazardExtractor(signal_dict, schema_enums)
result = extractor.extract(hdx_record)
# result.hazard_types: List[str]
# result.process_types: Dict[str, str]
# result.return_periods: List[str]
# result.intensity_measures: Dict[str, str]
# result.overall_confidence: float
```

Key methods:
- `_extract_text_fields()` — Parse HDX metadata with compound tag handling
- `_match_patterns()` — Match against signal dictionary patterns
- `_extract_return_periods()` — RP extraction with year-filtering (excludes 2000–2099)
- `_extract_intensity_measures()` — Text-based IM detection with per-hazard defaults
- `_infer_calculation_method()` — Classify as `simulated`, `observed`, or `inferred`

### `build_hazard_block()`

Converts extraction results into RDLS v0.3 JSON structure:
- Creates one `event_set` per hazard type
- Validates every hazard→process pair against `HAZARD_PROCESS_MAPPINGS`
- Builds `events[]` from return periods or creates a single fallback event
- Populates `occurrence` wrapper (`empirical{}`, `probabilistic{}`, or `deterministic{}`)

---

## Compound Tag Handling

HDX uses compound tags like `earthquake-tsunami` and `cyclones-hurricanes-typhoons`. The extractor:

1. Splits compound tags into individual hazard signals
2. Requires **corroboration** from other text fields (title, notes) before accepting the split
3. Without corroboration, only the primary hazard is used

Example: `earthquake-tsunami` tag → checks if "tsunami" appears elsewhere → if yes, emits both `earthquake` and `tsunami` event sets.

---

## Return Period Extraction

Six regex patterns detect return periods:

```
"100-year flood"       → RP = 100
"100yr return"         → RP = 100
"return period: 100"   → RP = 100
"T100 flood"           → RP = 100
"1-in-100 year"        → RP = 100
"AEP 0.01"             → RP = 100
```

Year values (2000–2099) are filtered out to avoid false positives from date strings.

---

## Extraction CSV Columns

| Column | Description |
|--------|-------------|
| `id` | HDX dataset UUID |
| `title` | Dataset title |
| `has_hazard` | Boolean: hazard signals detected |
| `hazard_types` | Comma-separated hazard types |
| `process_types` | Comma-separated process types |
| `analysis_type` | empirical / probabilistic / deterministic |
| `return_periods` | Comma-separated RP values |
| `intensity_measures` | Comma-separated IM values |
| `calculation_method` | observed / simulated / inferred |
| `overall_confidence` | Float 0.0–1.0 |

---

## How It Works

```
1. Load all 26,246 dataset metadata files
2. For each dataset:
   a. Extract text fields (title, tags, notes, resources)
   b. Handle compound HDX tags with corroboration check
   c. Match hazard type patterns from signal dictionary
   d. For each detected hazard type:
      - Validate process type against schema mappings
      - Extract or assign default intensity measure
      - Extract return periods if present
      - Infer calculation method (observed/simulated/inferred)
   e. Compute overall extraction confidence
3. Build RDLS hazard blocks (one event_set per hazard type)
4. Export extraction CSVs and individual JSON files
```

---

## Troubleshooting

### Missing hazard type
- Check signal dictionary for term coverage
- Review dataset tags and description
- Some HDX tags use compound forms that need corroboration

### Wrong process type
- Process types are constrained by hazard type
- Check `HAZARD_PROCESS_MAPPINGS` for allowed combinations
- Invalid process types fall back to the default for that hazard

### No return periods detected
- Most HDX datasets lack explicit RP information
- Detection rate of ~1% is normal for RP extraction
- Datasets without RP get a single fallback event

---

[← Previous: Signal Analysis](08_signal_analysis.md) | [Back to README](../README.md) | [Next: Exposure Extractor →](10_exposure_extractor.md)
