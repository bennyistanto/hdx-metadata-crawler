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
pip install pandas requests pyyaml jsonschema tqdm pycountry
```

---

## Step 2: Verify Installation

```bash
python -c "import pandas, requests, yaml, jsonschema; print('All dependencies OK')"
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
| 1 | `01_rdls_hdx_metadata_crawler.ipynb` | 30-60 min (network) |
| 2 | `02_rdls_policy_osm_exclusion.ipynb` | 2-5 min |
| 3 | `03_rdls_define_mapping.ipynb` | 1 min |
| 4 | `04_rdls_classify_hdx_candidates.ipynb` | 5-10 min |
| 5 | `05_rdls_review_overrides.ipynb` | 1-2 min |
| 6 | `06_rdls_translate_hdx_to_rdlschema.ipynb` | 5-15 min |
| 7 | `07_rdls_validate_and_package.ipynb` | 2-5 min |
| 8-13 | HEVL extraction notebooks | 10-20 min |

### Option B: Test Run (Quick Validation)

Edit `notebook/06_rdls_translate_hdx_to_rdlschema.ipynb`:

```python
# In cell 1, change:
max_datasets: Optional[int] = 50  # Process only 50 datasets for testing
```

This processes 50 datasets instead of 10,000+ for quick validation.

---

## Step 4: Check Outputs

After running the pipeline, check these locations:

```
hdx_dataset_metadata_dump/
├── dataset_metadata/          # ~26,000 HDX JSON files
├── derived/
│   ├── classification_final.csv
│   └── rdls_included_dataset_ids_final.txt
└── rdls/
    ├── records/               # RDLS JSON outputs
    ├── reports/
    │   ├── schema_validation.csv
    │   └── rdls_validation_summary.md
    └── dist/
        └── rdls_metadata_bundle.zip
```

---

## Step 5: Validate Results

Open the validation summary:

```bash
cat hdx_dataset_metadata_dump/rdls/reports/rdls_validation_summary.md
```

Expected output:
```
# RDLS Validation Summary
- Total JSON files: **50**
- Schema valid: **50**
- Schema invalid: **0**
```

---

## Common Issues

### "Module not found" errors

```bash
pip install <missing-module>
```

### Network timeout during crawl

The crawler is resume-safe. Just re-run notebook 01 - it will skip already downloaded files.

### Schema validation failures

Check `rdls/reports/schema_validation.csv` for details. Common causes:
- Empty `risk_data_type` array
- Missing required fields

---

## Next Steps

1. **Review classification**: Check `derived/classification_final.csv`
2. **Add overrides**: Edit `config/overrides.yaml` to include/exclude specific datasets
3. **Run production**: Set `max_datasets = None` in notebook 06
4. **Explore HEVL**: Run notebooks 08-13 for detailed component extraction

---

## Getting Help

- [Architecture Guide](ARCHITECTURE.md) — Understand the pipeline design
- [Notebook Reference](../README.md#notebook-reference) — Detailed docs per notebook
- [Troubleshooting](#common-issues) — Common issues and fixes

---

[← Back to README](../README.md)
