# Architecture Guide

This document describes the HDX → RDLS pipeline design, data flow, configuration, and key decisions.

---

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HDX → RDLS METADATA PIPELINE                        │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │   HDX    │    │  Filter  │    │ Classify │    │Translate │    │   HEVL   │
  │  Crawl   │───▶│   OSM    │───▶│   RDLS   │───▶│  to JSON │───▶│ Extract  │
  │  01-02   │    │    02    │    │  03-05   │    │  06-07   │    │  08-13   │
  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
       │               │               │               │               │
       ▼               ▼               ▼               ▼               ▼
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │ 26,246   │    │  OSM     │    │ class_   │    │  RDLS    │    │integrated│
  │ JSON     │    │ excluded │    │ final    │    │ records/ │    │ + dist/  │
  │ files    │    │ _ids.txt │    │ .csv     │    │ *.json   │    │          │
  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

---

## Phase Details

### Phase 1: Crawl (Notebooks 01–02)

**Purpose:** Fetch all HDX dataset metadata via CKAN API

```
HDX CKAN API                      Local Storage
────────────                      ─────────────
package_search ──────────────────▶ dataset_metadata/
  (paginated)                        ├── {uuid}__{slug}.json
                                     ├── {uuid}__{slug}.json
download_metadata ───────────────▶   └── ... (26,246 files)
  ?format=json
                                  manifest_*.jsonl
                                  errors_*.jsonl
```

**Key Features:**

- Resume-safe (skips existing files)
- Rate-limited with exponential backoff
- Deterministic file naming: `{uuid}__{slug}.json`

---

### Phase 2: Filter (Notebook 02)

**Purpose:** Apply policy exclusions (OSM datasets)

```
dataset_metadata/*.json
         │
         ▼
  ┌─────────────────┐
  │  OSM Detection  │
  │  - org name     │
  │  - license      │
  │  - source URL   │
  │  - tags         │
  └─────────────────┘
         │
         ▼
policy/osm_excluded_dataset_ids.txt
```

**Why exclude OSM?**

- Thousands of nearly identical building/road extracts
- Would overwhelm RDLS catalog with duplicates
- Controlled OSM pilot path available separately

---

### Phase 3: Classify (Notebooks 03–05)

**Purpose:** Map HDX metadata to RDLS risk components

```
                    ┌─────────────────┐
                    │  Mapping Rules  │
                    │  config/*.yaml  │
                    └────────┬────────┘
                             │
dataset_metadata/*.json      │      policy/osm_excluded_ids.txt
         │                   │                   │
         └───────────────────┼───────────────────┘
                             ▼
                    ┌─────────────────┐
                    │   Classifier    │
                    │   (Notebook 04) │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Overrides      │
                    │  (Notebook 05)  │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
  classification_     rdls_included_      classification_
  final.csv           dataset_ids.txt    summary.json
```

**RDLS Risk Data Types:**

| Component | Signal Sources |
|-----------|---------------|
| Hazard | flood, earthquake, cyclone, drought, wildfire tags |
| Exposure | population, buildings, infrastructure, agriculture |
| Vulnerability | fragility curves, vulnerability functions, socio-economic indices |
| Loss | damage, casualties, economic loss, displacement |

---

### Phase 4: Translate (Notebooks 06–07)

**Purpose:** Generate RDLS v0.3 JSON records with general metadata

```
classification_final.csv
         │
         ▼
  ┌─────────────────┐     ┌─────────────────┐
  │  Record Builder │────▶│  JSON Schema    │
  │  - attributions │     │  Validation     │
  │  - resources    │     └────────┬────────┘
  │  - spatial      │              │
  │  - license      │              ▼
  └────────┬────────┘     ┌─────────────────┐
           │              │  Reports        │
           ▼              │  - blocked.csv  │
  rdls/records/           │  - validation   │
    └── *.json            └─────────────────┘
```

**File Naming Convention:**
```
rdls_{prefix}-hdx_{org}_{iso3}_{slug}_{hazard}.json

Examples:
  rdls_hzd-hdx_wfp_mmr_flood_risk_flood.json
  rdls_exp-hdx_worldpop_ken_population.json
```

---

### Phase 5: HEVL Extraction (Notebooks 08–13)

**Purpose:** Extract detailed Hazard/Exposure/Vulnerability/Loss component blocks, integrate them into RDLS records, and validate.

```
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │  Signal  │    │  Hazard  │    │ Exposure │    │  V + L   │
  │ Analysis │───▶│ Extract  │───▶│ Extract  │───▶│ Extract  │
  │    08    │    │    09    │    │    10    │    │    11    │
  └──────────┘    └──────────┘    └──────────┘    └──────────┘
       │               │               │               │
       ▼               └───────────────┼───────────────┘
  signal_                              │
  dictionary.yaml               ┌──────┴───────┐
                                │ Integration  │
                                │     12       │
                                └──────┬───────┘
                                       │
                                       ▼
                                ┌──────────────┐
                                │ Validation   │
                                │   QA  13     │
                                └──────────────┘
```

**Key design: Schema-validated constraint tables**

Each extractor uses constraint tables derived from the RDLS v0.3 schema. These tables restrict field combinations to only those that are semantically valid, preventing inconsistent output like a `population` category paired with a `length` quantity_kind.

See [Constraint Tables](#constraint-tables) below for details.

---

## Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA ARTIFACTS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  hdx_dataset_metadata_dump/                                                 │
│  │                                                                          │
│  ├── dataset_metadata/          ◀── Notebook 01 (26,246 JSON files)        │
│  │                                                                          │
│  ├── policy/                                                                │
│  │   └── osm_excluded_ids.txt   ◀── Notebook 02                            │
│  │                                                                          │
│  ├── config/                                                                │
│  │   ├── tag_to_rdls.yaml       ◀── Notebook 03 (tag weights)             │
│  │   ├── keyword_to_rdls.yaml   ◀── Notebook 03 (regex patterns)          │
│  │   ├── org_hints.yaml         ◀── Manual (organization biases)           │
│  │   ├── overrides.yaml         ◀── Manual (per-dataset overrides)         │
│  │   └── signal_dictionary.yaml ◀── Notebook 08 (HEVL patterns)           │
│  │                                                                          │
│  ├── derived/                                                               │
│  │   ├── classification_final.csv    ◀── Notebook 04-05                    │
│  │   └── rdls_included_ids.txt                                             │
│  │                                                                          │
│  └── rdls/                                                                  │
│      ├── schema/                ◀── RDLS v0.3 schema (provided)            │
│      ├── template/              ◀── RDLS record template (provided)        │
│      ├── example/               ◀── Reference examples (provided)          │
│      ├── records/               ◀── Notebook 06 (general metadata JSON)    │
│      ├── extracted/             ◀── Notebook 09-11 (CSVs + HEVL JSONs)    │
│      ├── integrated/            ◀── Notebook 12 (merged records)           │
│      ├── reports/               ◀── Notebook 13 (validation reports)       │
│      └── dist/                  ◀── Notebook 13 (final bundle)             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Configuration Reference

### Classification Configuration (Notebooks 03–05)

| File | Purpose | Edited By |
| ---- | ------- | --------- |
| `config/tag_to_rdls.yaml` | Tag → component weights | Notebook 03 (auto-generated) |
| `config/keyword_to_rdls.yaml` | Keyword regex → component scores | Notebook 03 (auto-generated) |
| `config/org_hints.yaml` | Organization → likely component biases | Manual |
| `config/overrides.yaml` | Per-dataset include/exclude/reclassify | Manual |

### Signal Dictionary (Notebooks 08–12)

`config/signal_dictionary.yaml` is the central HEVL extraction configuration. All HEVL extractors load it at startup.

**Hazard Type Section** — 11 entries mapping to RDLS `hazard_type` codelist:

| Codelist Value | Pattern Examples | Confidence |
| -------------- | ---------------- | ---------- |
| `flood` | `flood`, `flooding`, `inundation`, `fluvial`, `pluvial` | high |
| `coastal_flood` | `coastal.?flood`, `storm.?surge`, `sea.?level.?rise` | high |
| `earthquake` | `earthquake`, `seismic`, `quake`, `ground.?motion` | high |
| `tsunami` | `tsunami`, `tidal.?wave` | high |
| `drought` | `drought`, `dry.?spell`, `water.?scarcity` | high |
| `landslide` | `landslide`, `mudslide`, `debris.?flow`, `rockfall` | high |
| `volcanic` | `volcanic`, `eruption`, `lava`, `ashfall`, `lahar` | high |
| `wildfire` | `wildfire`, `bushfire`, `forest.?fire` | high |
| `extreme_temperature` | `heat.?wave`, `cold.?wave`, `extreme.?temperature` | high |
| `strong_wind` | `strong.?wind`, `cyclone`, `hurricane`, `typhoon` | high |
| `convective_storm` | `convective`, `hail`, `thunderstorm`, `tornado` | medium |

**Process Type Section** — 30 entries, each with a `parent_hazard` field linking to its hazard type. The schema's `hazard_process_mappings` enforces that a process can only appear under its parent hazard.

**Exposure Category Section** — 7 entries mapping to RDLS `exposure_category` codelist:

| Codelist Value | Definition | Key Patterns |
| -------------- | ---------- | ------------ |
| `buildings` | Residential, commercial, industrial, public-service buildings | `building`, `dwelling`, `housing`, `footprint` |
| `infrastructure` | Lifelines: transport, communications, energy, water | `road`, `bridge`, `power.?station`, `pipeline`, `hospital` |
| `population` | People | `population`, `demographic`, `census` (compound form only) |
| `agriculture` | Crops, livestock, agribusiness | `agriculture`, `crop`, `livestock`, `farmland` |
| `natural_environment` | Forestry, vegetation, ecosystems | `ecosystem`, `forest`, `wetland`, `land.?cover` |
| `economic_indicator` | Macroeconomic metrics | `gdp`, `economic.?indicator`, `trade` |
| `development_index` | Composite social/economic development stats | `hdi`, `poverty.?index`, `vulnerability.?index` |

**Other Sections:**

| Section | Purpose |
| ------- | ------- |
| `analysis_type` | Probabilistic, deterministic, empirical detection patterns |
| `return_period` | Numeric return period extraction (e.g., "100-year flood") |
| `vulnerability_indicators` | General vulnerability signal detection |
| `loss_indicators` | General loss signal detection |
| `format_hints` | Data format → likely content type mapping |
| `organization_hints` | Known organizations and their typical data types |
| `exclusion_patterns` | False positive suppression (e.g., "flood of data" is not a flood) |

---

## Constraint Tables

Constraint tables are Python dictionaries defined in the extraction notebooks that enforce valid field combinations per the RDLS v0.3 schema. They prevent the extractors from generating semantically invalid output.

### Hazard Constraints (NB 09)

**`hazard_process_mappings`** — loaded from the schema, maps each hazard type to its allowed process types:

| Hazard Type | Allowed Process Types |
| ----------- | -------------------- |
| `flood` | `fluvial_flood`, `pluvial_flood`, `groundwater_flood` |
| `coastal_flood` | `coastal_flood`, `storm_surge` |
| `earthquake` | `primary_rupture`, `secondary_rupture`, `ground_motion`, `liquefaction` |
| `drought` | `agricultural_drought`, `hydrological_drought`, `meteorological_drought`, `socioeconomic_drought` |
| `landslide` | `snow_avalanche`, `landslide_general`, `landslide_rockslide`, `landslide_mudflow`, `landslide_rockfall` |
| `tsunami` | `tsunami` |
| `volcanic` | `ashfall`, `volcano_ballistics`, `lahar`, `lava`, `pyroclastic_flow` |
| `wildfire` | `wildfire` |
| `extreme_temperature` | `extreme_cold`, `extreme_heat` |
| `strong_wind` | `extratropical_cyclone`, `tropical_cyclone`, `tornado` |
| `convective_storm` | `tornado` |

All 11 hazard types and all 30 process types in the schema are covered. The extractor validates every hazard→process pair and falls back to a default process when no specific one is detected.

### Exposure Constraints (NB 10)

**`VALID_TRIPLETS`** — maps each exposure_category to allowed `(metric_dimension, quantity_kind)` pairs. First entry is the default.

| Category | Allowed (dimension, quantity_kind) Pairs |
| -------- | ---------------------------------------- |
| `agriculture` | (structure, area), (product, monetary), (product, count) |
| `buildings` | (structure, count), (structure, monetary), (structure, area), (content, monetary) |
| `infrastructure` | (structure, length), (structure, monetary), (disruption, time), (disruption, monetary) |
| `population` | (population, count) |
| `natural_environment` | (structure, area) |
| `economic_indicator` | (product, monetary), (index, count) |
| `development_index` | (index, count) |

### Vulnerability Constraints (NB 11)

Four constraint tables:

**`FUNCTION_TYPE_CONSTRAINTS`** — maps each vulnerability function type to its default and allowed impact metrics:

| Function Type | Default Metric | Allowed Metrics |
| ------------- | -------------- | --------------- |
| `vulnerability` | `damage_ratio` | damage_ratio, mean_damage_ratio, casualty_ratio_vulnerability, downtime_vulnerability |
| `fragility` | `probability` | probability, damage_index, damage_ratio, mean_damage_ratio |
| `damage_to_loss` | `loss_ratio` | loss_ratio, mean_loss_ratio, economic_loss_value, insured_loss_value, asset_loss, downtime_loss, casualty_count, displaced_count |
| `engineering_demand` | `damage_index` | damage_index, damage_ratio, mean_damage_ratio, probability |

**`VULN_CATEGORY_DEFAULTS`** — maps each exposure category to its typical vulnerability function type and metric:

| Category | Typical Function | Override Metric | Override Qty |
| -------- | ---------------- | --------------- | ------------ |
| `buildings` | fragility | damage_ratio | ratio |
| `infrastructure` | vulnerability | downtime_vulnerability | time |
| `population` | vulnerability | casualty_ratio_vulnerability | ratio |
| `agriculture` | vulnerability | damage_ratio | ratio |
| `economic_indicator` | damage_to_loss | economic_loss_value | monetary |
| `development_index` | vulnerability | damage_index | count |

**`FUNCTION_TYPE_APPROACH_DEFAULTS`** — default approach and relationship per function type:

| Function Type | Typical Approach | Typical Relationship |
| ------------- | ---------------- | -------------------- |
| `vulnerability` | empirical | discrete |
| `fragility` | analytical | math_parametric |
| `damage_to_loss` | empirical | discrete |
| `engineering_demand` | analytical | math_parametric |

### Loss Constraints (NB 11)

**`VALID_ASSET_TRIPLETS`** — maps asset_category to allowed asset_dimension values:

| Asset Category | Allowed Dimensions |
| -------------- | ------------------- |
| `agriculture` | product, structure, content |
| `buildings` | structure, content |
| `infrastructure` | structure, disruption |
| `population` | population |
| `natural_environment` | structure, index |
| `economic_indicator` | product, index |
| `development_index` | index |

**`LOSS_SIGNAL_DEFAULTS`** — unified defaults for each loss signal type:

| Signal Type | Asset Category | Impact Metric | Quantity Kind | Loss Type |
| ----------- | -------------- | ------------- | ------------- | --------- |
| `human_loss` | population | casualty_count | count | count |
| `displacement` | population | displaced_count | count | count |
| `affected_population` | population | exposure_to_hazard | count | count |
| `economic_loss` | buildings | economic_loss_value | monetary | ground_up |
| `structural_damage` | buildings | damage_ratio | ratio | ground_up |
| `agricultural_loss` | agriculture | asset_loss | monetary | ground_up |
| `catastrophe_model` | buildings | loss_annual_average_value | monetary | ground_up |

### Shared Constraint (NB 11)

**`IMPACT_METRIC_CONSTRAINTS`** — maps all 20 `impact_metric` codelist values to their expected `quantity_kind` and applicable `impact_type` values. Used by both vulnerability and loss extractors.

---

## Key Design Decisions

### 1. Schema-First Approach

- Only populate fields defined in RDLS v0.3 schema
- Leave optional fields absent rather than fill with defaults
- Validate every record against JSON Schema
- Constraint tables enforce valid field combinations at extraction time

### 2. Component Gating Rules

```
✅ Hazard alone        → allowed
✅ Exposure alone      → allowed
❌ Vulnerability alone → blocked (requires H or E)
❌ Loss alone          → blocked (requires H or E)
✅ H + V               → allowed
✅ E + L               → allowed
```

### 3. Tiered Extraction Cascade (NB 10)

The exposure extractor uses a 3-tier text scanning approach:

| Tier | Fields | Weight | Purpose |
| ---- | ------ | ------ | ------- |
| Tier 1 | title, name, tags | 1.0 | Highest confidence — explicit metadata |
| Tier 2 | individual resources | 0.85 | Per-resource scanning |
| Tier 3 | notes, methodology | 0.6 | Corroboration only (never adds new categories) |

This prevents incidental keyword matches in long description text from introducing false categories.

### 4. OSM Exclusion Policy

- OSM-derived datasets excluded by default
- Prevents catalog flooding with duplicates
- Controlled pilot path for selective inclusion

### 5. Resume-Safe Processing

- All notebooks can be re-run safely
- Crawl skips existing files
- HEVL extractors overwrite previous outputs cleanly

### 6. Separation of Concerns

- **01–02**: Data acquisition
- **03–05**: Business logic (classification)
- **06–07**: Schema transformation (general metadata)
- **08**: Signal analysis (builds detection patterns)
- **09–11**: Component extraction (populates HEVL blocks)
- **12**: Integration (merges general + HEVL)
- **13**: Validation and packaging

---

## Scaling Considerations

| Dataset Count | Crawl Time | Translate Time | HEVL Extract | Disk Space |
| ------------- | ---------- | -------------- | ------------ | ---------- |
| 50 (test) | 2 min | 30 sec | 1 min | 10 MB |
| 1,000 | 15 min | 5 min | 5 min | 200 MB |
| 10,000 | 2 hours | 30 min | 20 min | 2 GB |
| 26,246 (full) | 4–6 hours | 1–2 hours | 40–60 min | 5 GB |

---

[← Back to README](../README.md) | [Quick Start →](QUICKSTART.md)
