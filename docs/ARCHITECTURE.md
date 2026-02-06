# Architecture Guide

This document describes the HDX → RDLS pipeline design, data flow, and key decisions.

---

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HDX → RDLS METADATA PIPELINE                        │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │   HDX    │    │  Filter  │    │ Classify │    │Translate │    │ Validate │
  │  Crawl   │───▶│   OSM    │───▶│   RDLS   │───▶│  to JSON │───▶│ Package  │
  │  01-02   │    │    02    │    │  03-05   │    │  06-07   │    │  08-13   │
  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
       │               │               │               │               │
       ▼               ▼               ▼               ▼               ▼
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │ 26,246   │    │  OSM     │    │ class_   │    │  RDLS    │    │  Bundle  │
  │ JSON     │    │ excluded │    │ final    │    │ records/ │    │  .zip    │
  │ files    │    │ _ids.txt │    │ .csv     │    │ *.json   │    │          │
  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

---

## Phase Details

### Phase 1: Crawl (Notebooks 01-02)

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
- Deterministic file naming

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

### Phase 3: Classify (Notebooks 03-05)

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

**RDLS Components:**

| Component | Signal Sources |
|-----------|---------------|
| Hazard | flood, earthquake, cyclone tags |
| Exposure | population, buildings, infrastructure |
| Vulnerability | poverty index, vulnerability indicators |
| Loss | damage, casualties, economic loss |

---

### Phase 4: Translate (Notebooks 06-07)

**Purpose:** Generate RDLS v0.3 JSON records

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
    ├── rdls_hzd-*.json   └─────────────────┘
    ├── rdls_exp-*.json
    ├── rdls_vln-*.json
    └── rdls_lss-*.json
```

**File Naming Convention:**
```
rdls_{prefix}-hdx_{org}_{iso3}_{slug}_{hazard}.json

Examples:
  rdls_hzd-hdx_wfp_mmr_flood_risk_flood.json
  rdls_exp-hdx_worldpop_ken_population.json
```

---

### Phase 5: HEVL Extraction (Notebooks 08-13)

**Purpose:** Extract detailed Hazard/Exposure/Vulnerability/Loss signals

```
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │  Signal  │    │  Hazard  │    │ Exposure │    │  V / L   │
  │ Analysis │───▶│ Extract  │───▶│ Extract  │───▶│ Extract  │
  │    08    │    │    09    │    │    10    │    │    11    │
  └──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                       │
                                                       ▼
                                              ┌──────────────┐
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
│  │   ├── tag_to_rdls.yaml       ◀── Notebook 03                            │
│  │   ├── keyword_to_rdls.yaml                                              │
│  │   ├── org_hints.yaml                                                    │
│  │   └── overrides.yaml         ◀── Notebook 05 (manual)                   │
│  │                                                                          │
│  ├── derived/                                                               │
│  │   ├── classification_final.csv    ◀── Notebook 04-05                    │
│  │   └── rdls_included_ids.txt                                             │
│  │                                                                          │
│  └── rdls/                                                                  │
│      ├── schema/                ◀── RDLS v0.3 schema (provided)            │
│      ├── records/               ◀── Notebook 06 (RDLS JSON)                │
│      ├── index/                 ◀── Notebook 06                            │
│      ├── reports/               ◀── Notebook 06-07, 13                     │
│      └── dist/                  ◀── Notebook 07 (final bundle)             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### 1. Schema-First Approach

- Only populate fields defined in RDLS v0.3 schema
- Leave optional fields absent rather than empty
- Validate every record against JSON Schema

### 2. Component Gating Rules

```
✅ Hazard alone        → allowed
✅ Exposure alone      → allowed
❌ Vulnerability alone → blocked (requires H or E)
❌ Loss alone          → blocked (requires H or E)
✅ H + V               → allowed
✅ E + L               → allowed
```

### 3. OSM Exclusion Policy

- OSM-derived datasets excluded by default
- Prevents catalog flooding with duplicates
- Controlled pilot path for selective inclusion

### 4. Resume-Safe Processing

- All notebooks can be re-run safely
- Crawl skips existing files
- Translation can skip existing records

### 5. Separation of Concerns

- **01-02**: Data acquisition
- **03-05**: Business logic (classification)
- **06-07**: Schema transformation
- **08-13**: Deep analysis (HEVL)

---

## Configuration Reference

| File | Purpose | Edited By |
|------|---------|-----------|
| `config/tag_to_rdls.yaml` | Tag → component weights | Notebook 03 |
| `config/keyword_to_rdls.yaml` | Keyword regex patterns | Notebook 03 |
| `config/org_hints.yaml` | Organization biases | Manual |
| `config/overrides.yaml` | Per-dataset overrides | Manual |
| `config/signal_dictionary.yaml` | HEVL signal patterns | Notebook 08 |

---

## Scaling Considerations

| Dataset Count | Crawl Time | Translate Time | Disk Space |
|---------------|------------|----------------|------------|
| 50 (test) | 2 min | 30 sec | 10 MB |
| 1,000 | 15 min | 5 min | 200 MB |
| 10,000 | 2 hours | 30 min | 2 GB |
| 26,246 (full) | 4-6 hours | 1-2 hours | 5 GB |

---

[← Back to README](../README.md) | [Quick Start →](QUICKSTART.md)
