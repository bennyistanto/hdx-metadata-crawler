# Quick Start Guide

Get the HDX → RDLS pipeline running in 5 minutes.

---

## Prerequisites

- **Python 3.10+** installed
- **Jupyter Lab** or Jupyter Notebook
- Internet connection (for HDX API access)

---

## Step 1: Clone & Install

```bash
# Clone the repository
git clone https://github.com/your-org/hdx-metadata-crawler.git
cd hdx-metadata-crawler

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install pandas requests pyyaml jsonschema tqdm pycountry numpy
```

---

## Step 2: Verify Installation

```bash
python -c "import pandas, requests, yaml, jsonschema, numpy; print('All dependencies OK')"
```

---

## Step 3: Run the Pipeline

### Option A: Full Pipeline (Production)

Run notebooks **01 → 13** in sequence:

```bash
jupyter lab notebook/
```

Open each notebook and run all cells in order:

| Order | Notebook | Time Estimate |
|-------|----------|---------------|
| 1 | `01_rdls_hdx_metadata_crawler.ipynb` | 30–60 min (network) |
| 2 | `02_rdls_policy_osm_exclusion.ipynb` | 2–5 min |
| 3 | `03_rdls_define_mapping.ipynb` | 1 min |
| 4 | `04_rdls_classify_hdx_candidates.ipynb` | 5–10 min |
| 5 | `05_rdls_review_overrides.ipynb` | 1–2 min |
| 6 | `06_rdls_translate_hdx_to_rdlschema.ipynb` | 5–15 min |
| 7 | `07_rdls_validate_and_package.ipynb` | 2–5 min |
| 8 | `08_rdls_hdx_signal_analysis.ipynb` | 5–10 min |
| 9 | `09_rdls_hazard_block_extractor.ipynb` | 5–10 min |
| 10 | `10_rdls_exposure_block_extractor.ipynb` | 5–10 min |
| 11 | `11_rdls_vulnerability_loss_extractor.ipynb` | 5–10 min |
| 12 | `12_rdls_hevl_integration.ipynb` | 5–10 min |
| 13 | `13_rdls_validation_qa.ipynb` | 2–5 min |

### Option B: Test Run (Quick Validation)

Edit `notebook/06_rdls_translate_hdx_to_rdlschema.ipynb`:

```python
# In cell 1, change:
max_datasets: Optional[int] = 50  # Process only 50 datasets for testing
```

This processes 50 datasets instead of 13,000+ for quick validation.

---

## Step 4: Check Outputs

After running the pipeline, check these locations:

```
hdx_dataset_metadata_dump/
├── dataset_metadata/          # ~26,000 HDX JSON files
├── derived/
│   ├── classification_final.csv
│   └── rdls_included_dataset_ids_final.txt
├── config/
│   ├── signal_dictionary.yaml    # Central HEVL configuration
│   ├── tag_to_rdls.yaml
│   ├── keyword_to_rdls.yaml
│   └── overrides.yaml
└── rdls/
    ├── schema/                # RDLS v0.3 JSON Schema
    ├── template/              # RDLS record template
    ├── example/               # Reference examples
    ├── records/               # NB 06 general metadata
    ├── extracted/             # NB 09-11 HEVL CSVs + JSON blocks
    ├── integrated/            # NB 12 merged records
    ├── reports/               # NB 13 validation reports
    └── dist/                  # Final deliverable bundle
```

---

## Step 5: Validate Results

Open the validation report:

```bash
# Check schema validation results
cat hdx_dataset_metadata_dump/rdls/reports/schema_validation.csv | head -5

# Check the final archive
ls -la hdx_dataset_metadata_dump/rdls/dist/
```

---

## Configuration

The pipeline uses YAML configuration files in `hdx_dataset_metadata_dump/config/`:

| File | Purpose |
|------|---------|
| `signal_dictionary.yaml` | Central HEVL signal patterns (hazard types, exposure categories, etc.) |
| `tag_to_rdls.yaml` | HDX tag → RDLS component weight mappings |
| `keyword_to_rdls.yaml` | Regex keyword patterns for classification |
| `org_hints.yaml` | Organisation-level bias scores |
| `overrides.yaml` | Per-dataset manual include/exclude overrides |

See [Configuration Reference](ARCHITECTURE.md#configuration-reference) for full details.

---

## Common Issues

### "Module not found" errors

```bash
pip install <missing-module>
```

Ensure `numpy` is installed (required for statistical computations in NB 08–13).

### Network timeout during crawl

The crawler is resume-safe. Just re-run notebook 01 — it skips already downloaded files.

### Schema validation failures

Check `rdls/reports/schema_validation.csv` for details. Common causes:

- Empty `risk_data_type` array
- Missing required fields
- Invalid country codes (e.g., `XKX` for Kosovo)

### CLEANUP_MODE

All notebooks have a `CLEANUP_MODE` variable in cell 1. Set to `True` to clear previous outputs before re-running:

```python
CLEANUP_MODE = True   # Remove stale outputs before processing
```

---

## Next Steps

1. **Review classification**: Check `derived/classification_final.csv`
2. **Add overrides**: Edit `config/overrides.yaml` to include/exclude specific datasets
3. **Run production**: Set `max_datasets = None` in notebook 06
4. **Tune signal dictionary**: Edit `config/signal_dictionary.yaml` to add patterns
5. **Explore HEVL**: Review extraction CSVs in `rdls/extracted/`

---

## Getting Help

- [Architecture Guide](ARCHITECTURE.md) — Pipeline design and configuration reference
- [Notebook Reference](../README.md#notebook-reference) — Detailed docs per notebook
- [Troubleshooting](#common-issues) — Common issues and fixes

---

[← Back to README](../README.md)
