# HDX → RDLS Metadata Pipeline

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![RDLS v0.3](https://img.shields.io/badge/RDLS-v0.3-orange.svg)](https://docs.riskdatalibrary.org/)

A notebook-based pipeline to crawl **Humanitarian Data Exchange (HDX)** metadata and transform it into **Risk Data Library Schema (RDLS) v0.3** JSON records.

---

## Quick Start

```bash
# Clone repository
git clone https://github.com/your-org/hdx-metadata-crawler.git
cd hdx-metadata-crawler

# Install dependencies
pip install pandas requests pyyaml jsonschema tqdm pycountry

# Run notebooks in order (01 → 13)
jupyter lab notebook/
```

📖 **[Full Getting Started Guide →](docs/QUICKSTART.md)**

---

## Requirements

| Package | Required | Purpose |
|---------|----------|---------|
| Python | 3.10+ | Runtime |
| pandas | ✅ | Data processing |
| requests | ✅ | HDX API calls |
| pyyaml | ✅ | Config files |
| jsonschema | ✅ | RDLS validation |
| tqdm | Optional | Progress bars |
| pycountry | Optional | ISO3 country codes |

---

## Pipeline Overview

```
HDX Catalogue → Crawl → Filter → Classify → Translate → Validate → RDLS Bundle
     01          02       03-05      06         07          08-13
```

| Phase | Notebooks | Purpose |
|-------|-----------|---------|
| **Crawl** | 01-02 | Fetch HDX metadata, apply OSM policy |
| **Classify** | 03-05 | Map to RDLS components, review & override |
| **Translate** | 06-07 | Generate RDLS JSON, validate & package |
| **HEVL Extract** | 08-13 | Extract Hazard/Exposure/Vulnerability/Loss signals |

📖 **[Architecture Details →](docs/ARCHITECTURE.md)**

---

## Documentation

### Guides
- [Quick Start](docs/QUICKSTART.md) — Get running in 5 minutes
- [Architecture](docs/ARCHITECTURE.md) — Pipeline design & data flow

### Notebook Reference
| # | Notebook | Documentation |
|---|----------|---------------|
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
| 11 | Vulnerability/Loss Extractor | [docs/11_vulnerability_loss_extractor.md](docs/11_vulnerability_loss_extractor.md) |
| 12 | HEVL Integration | [docs/12_hevl_integration.md](docs/12_hevl_integration.md) |
| 13 | Validation & QA | [docs/13_validation_qa.md](docs/13_validation_qa.md) |

---

## Output Structure

```
hdx_dataset_metadata_dump/
├── dataset_metadata/     # Raw HDX JSON exports
├── derived/              # Classification results
├── config/               # Mapping rules (YAML)
├── policy/               # Exclusion lists
└── rdls/
    ├── records/          # RDLS JSON records
    ├── index/            # Record index
    ├── reports/          # QA reports
    └── dist/             # Deliverable bundle
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
