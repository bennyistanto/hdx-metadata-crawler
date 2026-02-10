# HDX → RDLS Metadata Pipeline

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![RDLS v0.3](https://img.shields.io/badge/RDLS-v0.3-orange.svg)](https://docs.riskdatalibrary.org/)

A notebook-based pipeline to crawl **Humanitarian Data Exchange ([HDX](https://data.humdata.org/))** metadata and transform it into **Risk Data Library Standard ([RDLS](https://riskdatalibrary.org/standard/))** schema v0.3 JSON records.

---

## Quick Start

```bash
# Clone repository
git clone https://github.com/your-org/hdx-metadata-crawler.git
cd hdx-metadata-crawler

# Install dependencies
pip install pandas requests pyyaml jsonschema tqdm pycountry numpy

# Run notebooks in order (01 → 13)
jupyter lab notebook/
```

📖 **[Full Getting Started Guide →](docs/QUICKSTART.md)**

---

## Requirements

| Package | Required | Purpose |
| ------- | -------- | ------- |
| Python | 3.10+ | Runtime |
| pandas | ✅ | Data processing |
| requests | ✅ | HDX API calls |
| pyyaml | ✅ | Configuration files |
| jsonschema | ✅ | RDLS schema validation |
| numpy | ✅ | Statistical computations |
| tqdm | Optional | Progress bars |
| pycountry | Optional | ISO 3166 country codes |

---

## Pipeline Overview

```
HDX Catalogue → Crawl → Filter → Classify → Translate → HEVL Extract → Integrate → Validate
                01-02     03-05     06-07       09-11         12           13
```

The pipeline has three major phases:

| Phase | Notebooks | Purpose |
| ----- | --------- | ------- |
| **Crawl & Classify** | 01–05 | Fetch HDX metadata, apply OSM exclusion, classify into RDLS components |
| **Translate** | 06–07 | Generate RDLS v0.3 JSON with general metadata (spatial, license, attributions, resources) |
| **HEVL Extraction** | 08–13 | Extract Hazard/Exposure/Vulnerability/Loss signals, integrate, and validate |

📖 **[Architecture Details →](docs/ARCHITECTURE.md)**

---

## Configuration

The pipeline uses YAML configuration files to control classification and HEVL extraction. All configuration is in `hdx_dataset_metadata_dump/config/`.

| File | Purpose | Used By |
| ---- | ------- | ------- |
| `tag_to_rdls.yaml` | HDX tag → RDLS component weight mappings | NB 03–04 |
| `keyword_to_rdls.yaml` | Regex keyword patterns for classification | NB 03–04 |
| `org_hints.yaml` | Organization-level bias scores | NB 04 |
| `overrides.yaml` | Per-dataset manual include/exclude overrides | NB 05 |
| **`signal_dictionary.yaml`** | **HEVL signal patterns, exposure categories, hazard/process types** | **NB 08–12** |

### Signal Dictionary

The signal dictionary (`config/signal_dictionary.yaml`) is the central configuration for HEVL extraction. It defines regex patterns that map unstructured HDX text to RDLS codelist values.

**Sections:**

| Section | Content | RDLS Codelist |
| ------- | ------- | ------------- |
| `hazard_type` | 11 hazard types with regex patterns | `hazard_type` (closed, 11 values) |
| `process_type` | 30 hazard process types with `parent_hazard` links | `process_type` (closed, 30 values) |
| `exposure_category` | 7 exposure categories with detection patterns | `exposure_category` (closed, 7 values) |
| `analysis_type` | 3 analysis types (probabilistic, deterministic, empirical) | `analysis_type` (closed) |
| `return_period` | Return period extraction patterns | — |
| `vulnerability_indicators` | Vulnerability signal patterns | — |
| `loss_indicators` | Loss signal patterns | — |
| `exclusion_patterns` | False positive suppression rules | — |

Each entry has a `patterns` list (regex, case-insensitive) and a `confidence` level (`high`, `medium`, `low`):

```yaml
hazard_type:
  flood:
    patterns:
      - '\b(flood|flooding|inundation)\b'
      - '\b(fluvial|pluvial|riverine)\b'
    confidence: high

exposure_category:
  buildings:
    patterns:
      - '\b(building|dwelling)\b'
      - '\b(house|housing|residential)\b'
      - '\b(footprint|building.?stock|floor.?area)\b'
    confidence: high
```

📖 **[Full Configuration Reference →](docs/ARCHITECTURE.md#configuration-reference)**

---

## HEVL Component Extraction

Notebooks 09–11 extract the four RDLS risk components using schema-validated constraint tables that enforce correct field combinations.

### Constraint Tables

Each HEVL component uses constraint tables derived from the RDLS v0.3 schema to ensure internally consistent output:

| Component | Constraint | Purpose |
| --------- | ---------- | ------- |
| **Hazard** (NB 09) | `hazard_process_mappings` | Ensures process type is valid for hazard type (e.g., `coastal_flood` only allows `coastal_flood` or `storm_surge`) |
| **Exposure** (NB 10) | `VALID_TRIPLETS` | Maps each `exposure_category` to allowed `(metric_dimension, quantity_kind)` pairs |
| **Vulnerability** (NB 11) | `FUNCTION_TYPE_CONSTRAINTS` | Maps each function type to allowed `impact_metric` values |
| **Vulnerability** (NB 11) | `VULN_CATEGORY_DEFAULTS` | Maps each `category` to typical function type and metric overrides |
| **Loss** (NB 11) | `VALID_ASSET_TRIPLETS` | Maps `asset_category` to allowed `asset_dimension` values |
| **Loss** (NB 11) | `LOSS_SIGNAL_DEFAULTS` | Unified per-signal defaults for all loss fields |
| **Shared** (NB 11) | `IMPACT_METRIC_CONSTRAINTS` | Maps each of 20 `impact_metric` values to expected `quantity_kind` and valid `impact_type` |

---

## Documentation

### Guides

- [Quick Start](docs/QUICKSTART.md) — Get running in 5 minutes
- [Architecture](docs/ARCHITECTURE.md) — Pipeline design, data flow, and configuration reference

### Notebook Reference

| # | Notebook | Documentation |
| --- | -------- | ------------- |
| 01 | HDX Metadata Crawler | [docs/01_hdx_metadata_crawler.md](docs/01_hdx_metadata_crawler.md) |
| 02 | OSM Policy Exclusion | [docs/02_policy_osm_exclusion.md](docs/02_policy_osm_exclusion.md) |
| 03 | Define RDLS Mapping | [docs/03_define_mapping.md](docs/03_define_mapping.md) |
| 04 | Classify Candidates | [docs/04_classify_candidates.md](docs/04_classify_candidates.md) |
| 05 | Review & Overrides | [docs/05_review_overrides.md](docs/05_review_overrides.md) |
| 06 | Translate to RDLS | [docs/06_translate_to_rdls.md](docs/06_translate_to_rdls.md) |
| 07 | Validate & Package | [docs/07_validate_package.md](docs/07_validate_package.md) |
| 08 | HEVL Signal Analysis | [docs/08_signal_analysis.md](docs/08_signal_analysis.md) |
| 09 | Hazard Extractor | [docs/09_hazard_extractor.md](docs/09_hazard_extractor.md) |
| 10 | Exposure Extractor | [docs/10_exposure_extractor.md](docs/10_exposure_extractor.md) |
| 11 | Vulnerability & Loss Extractor | [docs/11_vulnerability_loss_extractor.md](docs/11_vulnerability_loss_extractor.md) |
| 12 | HEVL Integration | [docs/12_hevl_integration.md](docs/12_hevl_integration.md) |
| 13 | Validation & QA | [docs/13_validation_qa.md](docs/13_validation_qa.md) |

---

## Output Structure

```
hdx_dataset_metadata_dump/
├── dataset_metadata/          # Raw HDX JSON (26,246 files)
├── derived/                   # Classification results
├── config/                    # Mapping rules and signal dictionary (YAML)
├── policy/                    # Exclusion lists
└── rdls/
    ├── schema/                # RDLS v0.3 JSON Schema
    ├── template/              # RDLS record template
    ├── example/               # Reference examples (Chattogram, Freetown, etc.)
    ├── records/               # NB 06 general metadata records
    ├── extracted/             # NB 09-11 HEVL extraction CSVs + JSON blocks
    ├── integrated/            # NB 12 merged records (general + HEVL)
    ├── reports/               # NB 13 validation reports
    └── dist/                  # Final deliverable bundle
```

---

## License

This pipeline is open source. HDX metadata and derived RDLS outputs remain subject to their original dataset licenses. Always check HDX licensing fields and cite sources appropriately.

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run the pipeline end-to-end
4. Submit a pull request

---

<p align="center">
  <b>HDX</b> → <b>RDLS</b> | Risk Data Library Schema v0.3
</p>
