# 06 - Translate to RDLS

**Notebook:** `notebook/06_rdls_translate_hdx_to_rdlschema.ipynb`

---

## Summary

Transforms classified HDX datasets into RDLS v0.3 JSON records, applying schema validation and component gating rules.

**For Decision Makers:**
> This is the core transformation step that produces the actual RDLS metadata files. Each HDX dataset becomes a schema-compliant JSON record ready for the Risk Data Library.

---

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| Classification | `derived/classification_final.csv` | From Step 05 |
| Included IDs | `derived/rdls_included_dataset_ids_final.txt` | From Step 05 |
| Dataset JSONs | `dataset_metadata/*.json` | Raw HDX metadata |
| RDLS Schema | `rdls/schema/rdls_schema_v0.3.json` | Validation schema |
| RDLS Template | `rdls/template/rdls_template_v03.json` | Record template |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| RDLS records | `rdls/records/*.json` | One file per dataset |
| Index | `rdls/index/rdls_index.jsonl` | Record metadata index |
| Blocked report | `rdls/reports/translation_blocked.csv` | Failed translations |
| Validation report | `rdls/reports/schema_validation.csv` | Schema check results |
| QA report | `rdls/reports/translation_qa.csv` | Quality metrics |

---

## Key Configuration

```python
@dataclass
class TranslationConfig:
    max_datasets: Optional[int] = 50   # None for all, 50 for testing
    output_mode: str = "in_place"      # "in_place" or "run_folder"
    clean_before_run: bool = True      # Clean existing outputs
    skip_existing: bool = False        # Skip already translated
    write_pretty_json: bool = True     # Formatted JSON output
    auto_repair_components: bool = True # Auto-add exposure for V/L
```

---

## RDLS Record Structure

Each output JSON follows the RDLS v0.3 schema:

```json
{
  "datasets": [{
    "id": "rdls_hzd-hdx_ocha_ken_flood_risk_flood",
    "title": "Kenya Flood Risk Map",
    "description": "...",
    "risk_data_type": ["hazard"],
    "spatial": {
      "scale": "national",
      "countries": ["KEN"]
    },
    "license": "CC-BY-4.0",
    "attributions": [
      {"id": "attribution_publisher", "role": "publisher", ...},
      {"id": "attribution_creator", "role": "creator", ...},
      {"id": "attribution_contact", "role": "contact_point", ...}
    ],
    "resources": [
      {"id": "hdx_dataset_metadata_json", ...},
      {"id": "hdx_res_abc123", "data_format": "GeoJSON (geojson)", ...}
    ],
    "links": [{"href": "...", "rel": "describedby"}]
  }]
}
```

---

## Component Gating Rules

The translator enforces RDLS business rules:

| Scenario | Allowed | Action |
|----------|---------|--------|
| Hazard only | ✅ Yes | Proceed |
| Exposure only | ✅ Yes | Proceed |
| Vulnerability only | ❌ No | Auto-add exposure (or block) |
| Loss only | ❌ No | Auto-add exposure (or block) |
| Hazard + Vulnerability | ✅ Yes | Proceed |
| Exposure + Loss | ✅ Yes | Proceed |

With `auto_repair_components=True`, standalone V or L gets exposure added automatically.

---

## File Naming Convention

```
rdls_{prefix}-hdx_{org}_{iso3}_{slug}_{hazard}.json

Components:
- prefix: hzd / exp / vln / lss (based on priority)
- org: organization token (e.g., "ocha", "wfp")
- iso3: country code if single country (e.g., "ken")
- slug: dataset name slug
- hazard: hazard type suffix if applicable (e.g., "flood")
```

**Priority order:** loss > vulnerability > exposure > hazard

**Examples:**
```
rdls_hzd-hdx_ocha_ken_flood_risk_flood.json
rdls_exp-hdx_worldpop_global_population.json
rdls_vln-hdx_wfp_mmr_poverty_index.json
rdls_lss-hdx_undrr_phl_typhoon_damage_windstorm.json
```

---

## Key Functions

### `build_rdls_record()`
Main transformation function.

```python
rdls_record, info = build_rdls_record(hdx_json, classification_row)
# rdls_record: RDLS-compliant dict (or None if blocked)
# info: metadata about the translation
```

### `apply_component_gate()`
Validates and repairs component combinations.

```python
result = apply_component_gate(["vulnerability"])
# result.ok: False (or True if auto-repaired)
# result.risk_data_type: ["exposure", "vulnerability"]
# result.reasons: ["auto_added_exposure_for_vulnerability"]
```

### `build_attributions()`
Creates required attribution objects.

```python
attributions = build_attributions(hdx_json, dataset_id, page_url)
# Returns list of 3 attribution objects (publisher, creator, contact)
```

---

## Mapping Tables

### License Mapping
| HDX License | RDLS License |
|-------------|--------------|
| cc-by-4.0 | CC-BY-4.0 |
| cc0 | CC0-1.0 |
| ODbL | ODbL-1.0 |
| Public Domain | PDDL-1.0 |

### Format Mapping
| HDX Format | RDLS Format |
|------------|-------------|
| CSV | CSV (csv) |
| GEOJSON | GeoJSON (geojson) |
| SHP | Shapefile (shp) |
| XLSX | Excel (xlsx) |
| GPKG | GeoPackage (gpkg) |

---

## Statistics (Typical Run)

| Metric | Value |
|--------|-------|
| Input datasets | 10,759 |
| Successfully translated | 10,500 |
| Blocked (gating rules) | 150 |
| Blocked (missing data) | 109 |
| Schema valid | 10,500 |

---

## Troubleshooting

### Empty risk_data_type
**Cause:** Classification didn't assign components properly.
**Fix:** Review classification in Step 04-05, add overrides if needed.

### Blocked by component gating
**Cause:** Vulnerability or loss without hazard/exposure.
**Fix:** Either:
1. Enable `auto_repair_components=True`
2. Add hazard/exposure to classification via overrides

### Missing required fields
**Cause:** HDX metadata incomplete.
**Fix:** These datasets are blocked automatically. Check `translation_blocked.csv`.

### Schema validation failures
**Cause:** Generated record doesn't match RDLS schema.
**Fix:** Check `schema_validation.csv` for specific errors. Usually indicates a mapping issue.

---

## Test vs Production Mode

### Test Mode (default)
```python
max_datasets = 50  # Process only 50 datasets
```
Use for development and validation.

### Production Mode
```python
max_datasets = None  # Process all datasets
```
Use for final output generation.

---

[← Previous: Review & Overrides](05_review_overrides.md) | [Back to README](../README.md) | [Next: Validate & Package →](07_validate_package.md)
