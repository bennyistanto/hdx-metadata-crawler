# HDX → RDLS (v0.3) Metadata Pipeline (Notebook-first)

This repository provides a **notebook-first** workflow to crawl **Humanitarian Data Exchange (HDX)** metadata at scale and translate eligible HDX datasets into **Risk Data Library Schema (RDLS) v0.3** JSON.

**Current scope:** the pipeline focuses on producing **RDLS General Metadata** (dataset-level + resources) and **basic risk classification signals**. It does **not yet** populate the detailed **HEVL components** (Hazard / Exposure / Vulnerability / Loss specific metadata blocks) beyond what can be inferred for naming and gating.

---

## Requirements

- **Python**: 3.10+ (3.11 works well)
- **Jupyter**: JupyterLab or classic notebook

### Core packages

- `pandas`
- `requests`
- `pyyaml`
- `jsonschema` *(recommended for RDLS schema validation in later steps)*

Install (pip):

```bash
pip install pandas requests pyyaml jsonschema
````

Install (conda/mamba):

```bash
conda install -c conda-forge pandas requests pyyaml jsonschema
```

### Optional

* `tqdm` (progress bars)

```bash
pip install tqdm
```

**Notes**

- Network access is required for HDX crawling steps.
- Without `jsonschema`, schema validation will be skipped.
  
---

## What this repo does

1. **Crawl HDX catalogue (CKAN)** and download:
   - dataset-level metadata JSON (`download_metadata?format=json`)
   - (optional) resource-level metadata JSON

2. Apply **policy exclusion (OSM)** to avoid mass replication of OSM-derived metadata outputs.

3. Define **mapping rules** from HDX tags/keywords/org hints to internal RDLS component signals:
   - hazard
   - exposure
   - vulnerability_proxy
   - loss_impact

4. **Classify** datasets into RDLS candidates + confidence.

5. Apply **manual overrides** (optional) and finalize the inclusion list.

6. **Translate** included HDX datasets to **RDLS v0.3 JSON** using the official schema + template.
   - Outputs pass JSON schema checks where possible.
   - Generates QA tables and blocked/validation reports.

7. **Validate + package** outputs into a `dist/` bundle (and optional zip) for sharing.

---

## Known limitations (important)

### 1. General metadata only (for now)

The translator currently fills RDLS **general metadata** (identity, description, publisher/org, spatial/time coverage where available, and resources). It does **not yet** populate the detailed RDLS **HEVL blocks** (Hazard/Exposure/Vulnerability/Loss specialized metadata) beyond what’s needed to:

- select the correct RDLS file prefix (hzd/exp/vln/lss)
- enforce component gating rules (e.g., vulnerability requires hazard/exposure)

### 2. Component gating edge cases

You may see blocked records such as:

- `vulnerability_without_hazard_or_exposure`

This is expected under the current policy: vulnerability/loss should be supported by hazard and/or exposure. We are iterating on whether to:

- block such datasets strictly, or
- normalize inclusively (e.g., auto-add exposure) with an audit trail.

### 3. Schema validation failures

If you see failures like:

- `risk_data_type: [] should be non-empty`

it means the translator is producing an empty list where RDLS requires ≥1 enum value. Fix is typically:

- improve `risk_data_type` derivation from classification signals, or
- block the record with a clear reason (preferred) instead of writing invalid JSON.

### 4. OSM policy (team decision)

OSM-derived datasets are currently excluded by policy to avoid generating thousands of nearly identical metadata records. A controlled OSM pilot path exists, but is not part of the main output pipeline.

---

## Repository structure

You will mainly work with notebooks:

```text
notebooks/
  01_rdls_hdx_metadata_crawler.ipynb
  02_rdls_policy_osm_exclusion.ipynb
  03_rdls_define_mapping.ipynb
  04_rdls_classify_hdx_candidates.ipynb
  05_rdls_review_overrides.ipynb
  06_rdls_translate_hdx_to_rdlschema.ipynb
  07_rdls_validate_and_package.ipynb
  (optional) 08_osm_pilot_design.ipynb
````

All generated artifacts are written under:

```text
hdx_dataset_metadata_dump/
  dataset_metadata/                  # one JSON per HDX dataset (dataset-level export)
  resources/                         # (optional) one JSON per HDX resource
  manifest_*.jsonl                   # crawl manifest(s)
  errors_*.jsonl                     # crawl errors log(s)

  policy/
    osm_excluded_dataset_ids.txt     # dataset_ids excluded by OSM policy

  config/
    tag_to_rdls_component.yaml
    keyword_to_rdls_component.yaml
    org_hints.yaml
    overrides.yaml

  docs/
    mapping_rules.md
    samples_for_mapping.csv          # optional calibration samples

  derived/
    classification_raw.csv
    classification_final.csv
    classification_final_summary.json
    rdls_included_dataset_ids_final.txt

  rdls/
    schema/rdls_schema_v0.3.json
    template/rdls_template_v03.json

    records/                         # RDLS JSON records (Step 06 output)
    index/rdls_index.jsonl
    reports/
      translation_qa.csv
      translation_blocked.csv
      schema_validation.csv
      rdls_validation_summary.md

    dist/                            # distribution bundle (Step 07, in_place mode)
      ...
```

---

## Pipeline steps (end-to-end)

### Step 01 — Crawl HDX metadata

**Notebook:** `01_rdls_hdx_metadata_crawler.ipynb`

**Goal**

- Enumerate HDX datasets via CKAN Action API (`package_search`)
- Download dataset-level metadata JSON (`download_metadata?format=json`)
- (Optional) download resource-level metadata JSON per resource
- Write manifests and error logs for audit and reproducibility

**Inputs**

- Public HDX endpoints (CKAN API + HDX metadata export)

**Outputs**

- `hdx_dataset_metadata_dump/dataset_metadata/*.json`
- (optional) `hdx_dataset_metadata_dump/resources/*.json`
- `hdx_dataset_metadata_dump/manifest_*.jsonl`
- `hdx_dataset_metadata_dump/errors_*.jsonl`

**Method criteria**

- resume-safe (skip existing)
- rate-limited / retry with backoff
- deterministic file naming (`{dataset_uuid}__{slug}.json`)

---

### Step 02 — Apply OSM exclusion policy

**Notebook:** `02_rdls_policy_osm_exclusion.ipynb`

**Goal**

- Detect OSM-derived datasets (OpenStreetMap contributors / HOTOSM exports / ODbL + OSM markers)
- Produce a dataset_id exclusion list

**Inputs**

- `dataset_metadata/*.json`

**Outputs**

- `policy/osm_excluded_dataset_ids.txt`
- Optional reporting tables (if enabled): `osm_exclusion_report.csv`, etc.

**Method criteria**

- conservative detection: prefer strong provenance signals (`dataset_source`, license, resource URLs)
- avoid false positives where non-OSM datasets happen to mention OSM

---

### Step 03 — Define RDLS mapping rules (tags/keywords/org hints)

**Notebook:** `03_rdls_define_mapping.ipynb`

**Goal**

- Define how HDX metadata signals map to internal RDLS component scores:

  - tag weights
  - keyword regex
  - organization hints (“nudges” for frequent publishers)

**Inputs**

- a corpus sample from `dataset_metadata/` (optional for review)
- initial mapping heuristics

**Outputs**

- `config/tag_to_rdls_component.yaml`
- `config/keyword_to_rdls_component.yaml`
- `config/org_hints.yaml`
- `docs/mapping_rules.md`
- optional: `docs/samples_for_mapping.csv`

**Method criteria**

- org hints are intentionally **minimal and conservative** (not an exhaustive list of “good orgs”)
- expand org hints when you see recurring patterns (e.g., WFP) and validate impact via Step 04 outputs

---

### Step 04 — Classify RDLS candidates

**Notebook:** `04_rdls_classify_hdx_candidates.ipynb`

**Goal**

- Score each HDX dataset into RDLS components + confidence
- Apply Step 02 policy exclusion
- Create a classification table for QA and downstream translation

**Inputs**

- `dataset_metadata/*.json`
- mapping configs from `config/*.yaml`
- `policy/osm_excluded_dataset_ids.txt`

**Outputs**

- `derived/classification.csv` (or `classification_raw.csv`)
- `derived/classification_summary.json`
- `derived/rdls_included_dataset_ids.txt`

**Method criteria**

- “inclusive” classification (multi-component allowed)
- confidence is a QA signal, not a hard gate (unless you decide so)

---

### Step 05 — Review + overrides (optional) → finalize inclusion list

**Notebook:** `05_rdls_review_overrides.ipynb`

**Goal**

- Apply manual review decisions:

  - exclude noisy datasets
  - keep good datasets that were under-scored
  - optionally override components
- Produce final inclusion list for translation

**Inputs**

- `derived/classification.csv`
- `config/overrides.yaml` (defaults to empty)
- `policy/osm_excluded_dataset_ids.txt`

**Outputs**

- `derived/classification_final.csv`
- `derived/classification_final_summary.json`
- `derived/rdls_included_dataset_ids_final.txt`

**Override format**

```yaml
overrides: {}
# Example:
# overrides:
#   <dataset_uuid>:
#     decision: keep   # keep | exclude
#     components: [exposure, vulnerability_proxy]
#     note: "Reason for override"
```

---

### Step 06 — Translate HDX metadata → RDLS v0.3 JSON (General Metadata)

**Notebook:** `06_rdls_translate_hdx_to_rdlschema.ipynb`

**Goal**

- Convert included HDX datasets into RDLS v0.3 JSON using:
  - `rdls_schema_v0.3.json`
  - `rdls_template_v03.json`
- Populate RDLS **general metadata** + resources
- Enforce gating rules (vulnerability/loss require hazard or exposure)
- Validate against JSON schema when available

**Inputs**

- `dataset_metadata/*.json`
- `derived/classification_final.csv`
- `derived/rdls_included_dataset_ids_final.txt`
- `rdls/schema/rdls_schema_v0.3.json`
- `rdls/template/rdls_template_v03.json`

**Outputs**

- `rdls/records/*.json`
- `rdls/index/rdls_index.jsonl`
- `rdls/reports/translation_qa.csv`
- `rdls/reports/translation_blocked.csv`
- `rdls/reports/schema_validation.csv`

**Method criteria**

- never add fields not in RDLS schema; leave blank if no mapping exists
- OpenCodeList fields may accept new values if HDX values do not match enumerations
- file naming convention uses:

  - prefix: `rdls_hzd|rdls_exp|rdls_vln|rdls_lss`
  - provenance token: `hdx_`
  - organization token / ISO3 / hazard suffix where available

---

### Step 07 — Validate + package distribution bundle

**Notebook:** `07_rdls_validate_and_package.ipynb`

**Goal**

- Produce a shareable deliverable in `dist/`
- Optionally generate a zip for transfer

**Inputs**

- `rdls/records/*.json`
- `rdls/index/rdls_index.jsonl`
- `rdls/reports/*`
- RDLS schema for validation checks

**Outputs**

- `rdls/reports/rdls_validation_summary.md`
- `rdls/dist/` (in_place mode)
- optional: compiled zip for easy sharing

**Method criteria**

- `dist/` mirrors the key folder structure (records/index/reports)
- zip is purely a convenience artifact; it contains the dist contents

---

## Why org_hints is short (and how to expand it)

`config/org_hints.yaml` is a **biasing layer**, not a whitelist. It starts with a few high-volume, consistent publishers and can be expanded safely.

Recommended expansion workflow:

1. Use `derived/classification_final.csv` to find top publishers by count.
2. Inspect misclassified items (false positives/negatives).
3. Add small hints (low weights) and re-run Step 04–05.
4. Only keep hints that consistently improve classification.

Example org to add (conservatively): **World Food Programme (WFP)**.

---

## Notes on final mode (in-place) vs run-folder mode

The notebooks support:

- **in_place** mode (recommended for final production): write to `rdls/records`, `rdls/index`, `rdls/reports`, `rdls/dist`
- **run_folder** mode (recommended for experiments): write to `rdls/runs/<RUN_ID>/...`

If using in_place final runs:

- you may want to **clean `rdls/records/`** before Step 06 to avoid mixing old and new outputs.

---

## License and attribution

HDX metadata and derived RDLS metadata remain subject to the original dataset licenses and attribution requirements. Always consult HDX dataset licensing fields and cite upstream sources appropriately in downstream products.
