# 12 - HEVL Integration

**Notebook:** `notebook/12_rdls_hevl_integration.ipynb`

---

## Summary

Integrates extracted HEVL (Hazard, Exposure, Vulnerability, Loss) blocks into unified RDLS records using a **merge-only approach** — NB 06 records serve as the authoritative base, and HEVL JSON blocks from NB 09–11 are inserted without rebuilding any metadata.

**For Decision Makers:**
> This notebook combines the general metadata from notebook 06 with the detailed HEVL component blocks from notebooks 09–11. It reconciles `risk_data_type` to match actual content and produces complete, integrated RDLS records ready for validation.

---

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| NB 06 base records | `rdls/records/*.json` | ~13,000 general metadata records (authoritative) |
| NB 06 index | `rdls/index/rdls_index.jsonl` | JSONL mapping dataset_id → filename |
| Hazard CSV | `rdls/extracted/hazard_extraction_results.csv` | Boolean `has_hazard` flags |
| Exposure CSV | `rdls/extracted/exposure_extraction_results.csv` | Boolean `has_exposure` flags |
| Vulnerability CSV | `rdls/extracted/vulnerability_extraction_results.csv` | Boolean `has_vulnerability` flags |
| Loss CSV | `rdls/extracted/loss_extraction_results.csv` | Boolean `has_loss` flags |
| HEVL JSON blocks | `rdls/extracted/rdls_hzd-hdx_*.json`, `rdls_exp-hdx_*.json`, `rdls_vln-hdx_*.json`, `rdls_lss-hdx_*.json` | Individual HEVL blocks from NB 09–11 |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Integrated records | `rdls/integrated/rdls_*.json` | ~12,500 complete RDLS records |
| Integration index | `rdls/integrated/rdls_index.csv`, `rdls_index.jsonl` | Lookup table |
| Skipped records | `rdls/integrated/integration_skipped.csv` | Records that could not be integrated |

---

## Merge-Only Architecture

NB 12 does **not** rebuild general metadata or HEVL blocks. Instead:

```
NB 06 Base Records ──────────────┐
  (id, title, spatial, license,  │
   attributions, resources)      │
                                 ├──→ Deep-copy base
NB 09-11 HEVL JSON Blocks ──────┤    + Insert HEVL blocks
  (hazard event_sets, exposure   │    + Reconcile risk_data_type
   categories, vulnerability     │    + Derive filename prefix
   functions, loss entries)      │    + Write to integrated/
                                 │
NB 09-11 Extraction CSVs ───────┘
  (has_hazard, has_exposure,
   has_vulnerability, has_loss)
```

### Why Merge-Only?

- **NB 06 records are authoritative** for general metadata (spatial, license, attributions, resources)
- **NB 09–11 blocks are authoritative** for HEVL component details
- Avoiding rebuild prevents drift between notebook outputs
- Reconciliation catches cases where CSV flags and actual blocks disagree

---

## Risk Data Type Reconciliation

The integration applies a **two-stage reconciliation** to ensure `risk_data_type` matches reality:

### Stage 1: CSV Flags → Declared Types

Read boolean flags from the four extraction CSVs and build a canonical ordered list:

```
has_hazard=True, has_exposure=True, has_loss=True
→ risk_data_type: ["hazard", "exposure", "loss"]
```

### Stage 2: Actual Blocks → Reconciled Types

After merging HEVL JSON blocks into the record, scan what is actually present:

```
Declared: ["hazard", "exposure", "loss"]
Actual blocks present: hazard ✓, exposure ✓, loss ✗ (no JSON block)
→ Reconciled: ["hazard", "exposure"]
```

Components flagged in CSV but lacking an actual JSON block are **dropped** from `risk_data_type`. This prevents downstream consumers from expecting data that does not exist.

### Validation Rules

- Vulnerability and loss **cannot stand alone** — they require at least hazard or exposure
- If V/L are the only components and no H/E is present, the record is skipped
- This constraint is configurable via `REQUIRE_HE_FOR_VL`

---

## Filename Prefix Priority

Each integrated record gets a filename prefix based on its primary component, using a priority rule:

```
loss > vulnerability > exposure > hazard
```

| Components Present | Prefix | Rationale |
|--------------------|--------|-----------|
| hazard only | `rdls_hzd-hdx_` | Single component |
| exposure only | `rdls_exp-hdx_` | Single component |
| hazard + exposure | `rdls_exp-hdx_` | Exposure higher priority |
| exposure + loss | `rdls_lss-hdx_` | Loss highest priority |
| hazard + exposure + vulnerability + loss | `rdls_lss-hdx_` | Loss highest priority |

---

## Key Functions

| Function | Purpose |
|----------|---------|
| `load_nb06_index()` | Parse JSONL index to map dataset_id → filename |
| `load_nb06_records()` | Load NB 06 JSON files indexed by full HDX UUID |
| `load_hevl_jsons()` | Load HEVL JSON blocks, resolve UUID8 → full UUID |
| `determine_risk_data_types()` | Convert boolean flags to canonical component list |
| `validate_component_combination()` | Check if V/L standalone is allowed |
| `determine_filename_prefix()` | Apply priority rule for filename |
| `integrate_record()` | Core merge: deep-copy base, insert blocks, reconcile |
| `process_integration()` | Loop over all records, write JSONs, collect stats |
| `generate_rdls_index()` | Scan output JSONs, build CSV + JSONL index |

---

## UUID Resolution

NB 09–11 use 8-character UUID prefixes in filenames (e.g., `rdls_hzd-hdx_001d5cac.json`), while NB 06 uses full UUIDs. The integration:

1. Builds a mapping from UUID8 prefix → full UUID
2. Resolves each HEVL JSON block to its corresponding NB 06 base record
3. Logs unresolved UUIDs in the skipped records file

---

## How It Works

```
1. Load NB 06 base records (~13,000 JSON files) indexed by full UUID
2. Load 4 extraction CSVs and merge boolean flags by dataset_id
3. Load all HEVL JSON blocks from rdls/extracted/ directory
4. For each dataset with any HEVL flag:
   a. Deep-copy the NB 06 base record
   b. Insert hazard/exposure/vulnerability/loss blocks if available
   c. Reconcile risk_data_type: drop components without actual blocks
   d. Derive filename prefix using priority rule
   e. Write integrated record to rdls/integrated/
5. Generate integration index (CSV + JSONL)
6. Log skipped records with reasons
```

---

## Troubleshooting

### Missing HEVL blocks in integrated record
- Verify the HEVL JSON block exists in `rdls/extracted/`
- Check UUID8 → full UUID resolution in the logs
- The block may have been filtered by confidence thresholds in NB 09–11

### risk_data_type mismatch
- Reconciliation drops components without actual JSON blocks
- Check extraction CSVs vs. actual JSON files for the dataset
- This is expected behaviour: CSV flags indicate signal detection, but blocks may not have been produced

### Skipped records
- Check `integration_skipped.csv` for specific reasons
- Common causes: no NB 06 base record, V/L without H/E, UUID resolution failure

---

[← Previous: V/L Extractor](11_vulnerability_loss_extractor.md) | [Back to README](../README.md) | [Next: Validation & QA →](13_validation_qa.md)
