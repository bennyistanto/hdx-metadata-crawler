# 06 - Translate to RDLS

**Notebook:** `notebook/06_rdls_translate_hdx_to_rdlschema.ipynb`

---

## Summary

Transforms classified HDX datasets into RDLS v0.3 JSON records, applying schema validation, component gating rules, and auto-repair logic. Each included dataset becomes a self-contained JSON file conforming to the RDLS schema, with attributions, resources, spatial metadata, and hazard details derived from the HDX source metadata.

**For Decision Makers:**
> This is the core transformation step that produces the actual RDLS metadata files. Each HDX dataset becomes a schema-compliant JSON record ready for the Risk Data Library. The notebook handles edge cases automatically, including repairing standalone vulnerability or loss datasets by adding an exposure component.

---

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| Classification | `derived/classification_final.csv` | From Step 05 |
| Included IDs | `derived/rdls_included_dataset_ids_final.txt` | From Step 05 |
| Dataset JSONs | `dataset_metadata/*.json` | Raw HDX metadata |
| RDLS Schema | `rdls/schema/rdls_schema_v0.3.json` | Validation schema (Draft 2020-12) |
| RDLS Template | `rdls/template/rdls_template_v03.json` | Record template |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| RDLS records | `rdls/records/*.json` | One file per dataset |
| Index | `rdls/index/rdls_index.jsonl` | Record metadata index |
| Blocked report | `rdls/reports/translation_blocked.csv` | Datasets blocked by policy or missing data |
| Validation report | `rdls/reports/schema_validation.csv` | JSON Schema validation results |
| QA report | `rdls/reports/translation_qa.csv` | Quality metrics per record |

---

## Key Configuration

```python
@dataclass
class TranslationConfig:
    dump_dir: Path = field(default_factory=lambda: (Path("..") / "hdx_dataset_metadata_dump").resolve())
    max_datasets: Optional[int] = None   # None for production, integer for testing
    output_mode: str = "in_place"        # "in_place" or "run_folder"
    clean_before_run: bool = True        # Clean existing outputs (in_place only)
    skip_existing: bool = False          # Skip already translated records
    write_pretty_json: bool = True       # Formatted JSON output
    auto_repair_components: bool = True  # Auto-add exposure for standalone V/L

    def __post_init__(self):
        if self.output_mode == "run_folder" and self.clean_before_run:
            raise ValueError("clean_before_run cannot be True when output_mode='run_folder'")
```

### Output Modes

- **`in_place`** (default): Writes records directly to `rdls/records/`. Old outputs are cleaned before each run when `clean_before_run=True`.
- **`run_folder`**: Creates a timestamped subfolder under `rdls/runs/` (e.g., `rdls/runs/20260214_140000/`). A `_latest.txt` pointer tracks the most recent run. Useful for comparing runs or preserving history.

### Test vs Production

- **Test:** Set `max_datasets = 50` to process a small subset for development and validation.
- **Production:** Set `max_datasets = None` to process all included datasets.

---

## RDLS Record Structure

Each output JSON follows the RDLS v0.3 schema with a `datasets` wrapper array:

```json
{
  "datasets": [{
    "id": "rdls_hzd-ken_ocha_floodriskmap",
    "title": "Kenya Flood Risk Map",
    "description": "...",
    "risk_data_type": ["hazard"],
    "details": "Caveats: ... Methodology: ...",
    "referenced_by": [{"id": "ref_0", "author_names": [...], "url": "..."}],
    "spatial": {
      "scale": "national",
      "countries": ["KEN"]
    },
    "license": "CC-BY-4.0",
    "attributions": [
      {"id": "attribution_publisher", "role": "publisher", "entity": {"name": "...", "url": "..."}},
      {"id": "attribution_creator", "role": "creator", "entity": {"name": "...", "url": "..."}},
      {"id": "attribution_contact", "role": "contact_point", "entity": {"name": "...", "url": "..."}}
    ],
    "resources": [
      {"id": "hdx_res_abc123", "title": "...", "description": "...",
       "data_format": "GeoJSON (geojson)", "access_modality": "file_download", "url": "..."}
    ],
    "links": [
      {"href": "https://docs.riskdatalibrary.org/en/0__3__0/rdls_schema.json", "rel": "describedby"},
      {"href": "https://data.humdata.org/dataset/...", "rel": "source"}
    ]
  }]
}
```

---

## Component Gating Rules

The translator enforces RDLS business rules on `risk_data_type` combinations. Vulnerability and loss cannot appear as standalone components without hazard or exposure.

| Scenario | Allowed | Action |
|----------|---------|--------|
| Hazard only | Yes | Proceed |
| Exposure only | Yes | Proceed |
| Vulnerability only | No | Auto-add exposure (M5) or block |
| Loss only | No | Auto-add exposure (M5) or block |
| Hazard + Vulnerability | Yes | Proceed |
| Exposure + Loss | Yes | Proceed |
| Empty / unrecognized | No | Block with reason `empty_or_unrecognized_components` |

### Auto-Repair (M5)

When `auto_repair_components=True` (the default), standalone vulnerability or loss datasets are automatically repaired by adding `exposure` to the component set:

```python
def apply_component_gate(components: List[str]) -> ComponentGateResult:
    rset = {c for c in (components or []) if c in allowed}

    if "vulnerability" in rset and not ({"hazard", "exposure"} & rset):
        if config.auto_repair_components:
            rset.add("exposure")
            reasons.append("auto_added_exposure_for_vulnerability")

    if "loss" in rset and not ({"hazard", "exposure"} & rset):
        if config.auto_repair_components:
            rset.add("exposure")
            reasons.append("auto_added_exposure_for_loss")

    return ComponentGateResult(ok=ok, reasons=tuple(reasons), risk_data_type=sorted(rset))
```

The `ComponentGateResult` is a frozen dataclass with fields:
- `ok` (bool): Whether the dataset passes gating
- `reasons` (Tuple[str, ...]): Reason codes (e.g., `auto_added_exposure_for_vulnerability`)
- `risk_data_type` (List[str]): The validated/repaired component list

When `auto_repair_components=False`, standalone V or L datasets are blocked instead.

---

## File Naming Convention

Record IDs and filenames are built by `build_nb06_rdls_id()` using this structure:

```
rdls_{types_seg}-{geo_org}_{title_slug}.json
```

### Segments

| Segment | Source | Example |
|---------|--------|---------|
| `types_seg` | Component encoding | `hzd`, `exp`, `vln`, `lss`, `hv`, `hevl` |
| `geo_org` | `{iso3}_{org_shortname}` or just `{org_shortname}` | `ken_ocha`, `worldpop` |
| `title_slug` | Slugified title (stop words removed) | `floodriskmap` |

### Component Encoding

- **Single component:** 3-letter code (`hzd`, `exp`, `vln`, `lss`)
- **Multiple components:** Single-letter concatenation in HEVL order (`h`, `e`, `v`, `l`)
  - Example: hazard + vulnerability = `hv`
  - Example: all four = `hevl`

### Country Encoding

- Single country: lowercase ISO3 (e.g., `ken`)
- Multiple countries (up to 5): concatenated lowercase ISO3 codes (e.g., `kenmwi`)
- More than 5 countries: omitted (global-scope dataset)

### Collision Proofing

If a filename already exists on disk, an 8-character dataset UUID prefix is appended:

```
rdls_hzd-ken_ocha_floodriskmap_a1b2c3d4.json
```

### Examples

```
rdls_hzd-ken_ocha_floodriskmap.json
rdls_exp-worldpop_populationdensity.json
rdls_ev-mmr_wfp_povertyindex.json
rdls_lss-phl_undrr_typhoondamage.json
```

---

## Attribution Building

Every RDLS record requires exactly 3 attribution objects with roles `publisher`, `creator`, and `contact_point`. The `build_attributions()` function derives these from HDX metadata:

```python
def build_attributions(hdx, dataset_id, dataset_page_url):
    org = (hdx.get("organization") or "").strip() or "Not specified"
    src = (hdx.get("dataset_source") or "").strip() or org
    creator_url = src if looks_like_url(src) else dataset_page_url

    return [
        {"id": "attribution_publisher",  "role": "publisher",     "entity": {"name": org, "url": dataset_page_url}},
        {"id": "attribution_creator",    "role": "creator",       "entity": {"name": src, "url": creator_url}},
        {"id": "attribution_contact",    "role": "contact_point", "entity": {"name": org, "url": dataset_page_url}},
    ]
```

| Role | Name source | URL source |
|------|-------------|------------|
| `publisher` | HDX `organization` | Dataset page URL |
| `creator` | HDX `dataset_source` (falls back to `organization`) | Source URL if valid, else dataset page URL |
| `contact_point` | HDX `organization` | Dataset page URL |

---

## Resource Building

The `build_resources()` function converts each HDX resource into an RDLS resource object. Each resource requires `id`, `title`, `data_format`, and `access_modality`.

### Format Resolution Order

1. **Service format check:** If the HDX format is `GEOSERVICE`, `API`, or `WEB APP`, map to the corresponding RDLS format and access modality
2. **Service URL detection:** Refine using URL patterns (ArcGIS REST, WMS, WFS, WCS)
3. **Direct dictionary lookup:** Match against the `HDX_FORMAT_TO_RDLS` mapping table
4. **ZIP/archive inference:** For ZIP, 7Z, TAR, GZ formats, infer the actual data format from the filename or URL
5. **URL extension guessing:** Match file extensions in the download URL
6. **Filename inference:** Last resort pattern matching on resource name and URL
7. **Skip:** If no format can be determined, the resource is omitted and the HDX format is tracked as unmapped

### Access Modality

- Default: `file_download` for standard file resources
- `REST` for ArcGIS REST services and geoservices
- `API` for API-type resources
- `WMS`, `WFS`, `WCS` for OGC service URLs
- `download_page` for web app resources

### Temporal Annotation

Each resource is annotated with temporal coverage parsed from the HDX `dataset_date` field, supporting ISO date ranges (`[start TO end]`), open-ended ranges (`[start TO *]`), and relative expressions. Duration is computed as ISO 8601 (e.g., `P1Y`, `P6M`, `P30D`).

---

## Mapping Tables

### License Mapping

The `map_license()` function uses a two-tier approach: pattern-based regex matching first, then a direct dictionary fallback.

**Pattern matching** (evaluated first):

| Pattern | RDLS License |
|---------|-------------|
| Contains `cc0` or `public domain` + `cc0` | `CC0-1.0` |
| Contains `odbl` or `open database license` | `ODbL-1.0` |
| Contains `pddl` or `public domain dedication` | `PDDL-1.0` |
| CC BY (no SA/ND/NC) with version detection | `CC-BY-4.0` / `CC-BY-3.0` |
| CC BY-SA with version detection | `CC-BY-SA-4.0` / `CC-BY-SA-3.0` |
| CC BY-NC with version detection | `CC-BY-NC-4.0` / `CC-BY-NC-3.0` |

**Direct dictionary fallback** (`HDX_LICENSE_TO_RDLS`):

| HDX Key | RDLS License |
|---------|-------------|
| `public domain` | `PDDL-1.0` |
| `odbl` | `ODbL-1.0` |
| `cc-by-4.0` | `CC-BY-4.0` |
| `cc by 4.0` | `CC-BY-4.0` |
| `cc-by` | `CC-BY-4.0` |
| `cc0` | `CC0-1.0` |
| `cc0-1.0` | `CC0-1.0` |
| `copyright` | `Copyright` |

If no match is found, the raw license string is passed through unchanged.

### Format Mapping (`HDX_FORMAT_TO_RDLS`)

RDLS uses a closed codelist of 21 `data_format` values. The mapping table has 23 entries covering direct and alias matches:

| HDX Format | RDLS Format |
|------------|-------------|
| CSV | CSV (csv) |
| XLS, XLSX, EXCEL | Excel (xlsx) |
| JSON | JSON (json) |
| GEOJSON | GeoJSON (geojson) |
| SHP, SHAPEFILE | Shapefile (shp) |
| GPKG, GEOPACKAGE | GeoPackage (gpkg) |
| KML, KMZ | KML (kml) |
| PDF | PDF (pdf) |
| NC, NETCDF | NetCDF (nc) |
| TIF, TIFF, GEOTIFF | GeoTIFF (tif) |
| COG | Cloud Optimized GeoTIFF (cog) |
| PARQUET, APACHE PARQUET | Parquet (parquet) |
| XML | XML (xml) |
| GEODATABASE, GDB | File Geodatabase (gdb) |
| TOPOJSON | GeoJSON (geojson) |
| MBTILES | GeoPackage (gpkg) |
| TSV, TXT | CSV (csv) |

**Skipped formats** (non-data): HTML, PNG, JPEG, JPG, GIF, EMF, RAR, QGIS, ESRI ARCMAP PROJECT FILE

**Service formats** (special handling):

| HDX Format | RDLS Format | Access Modality |
|------------|-------------|-----------------|
| GEOSERVICE | GeoJSON (geojson) | REST |
| API | JSON (json) | API |
| WEB APP | CSV (csv) | download_page |

---

## Details and Referenced-By

The `build_details()` function composes the RDLS `details` string from:
- **Caveats:** HDX `caveats` field (data quality / limitations)
- **Methodology:** HDX `methodology_other` field (preferred) or `methodology` field (if not generic)

These are concatenated into a single `details` string. If methodology text contains URLs, they are extracted into `referenced_by` objects with author names derived from the dataset source.

---

## Error Tracking and Blocking

Datasets can be blocked at two points:

1. **Missing HDX JSON:** If the dataset metadata file is not found on disk, the dataset is blocked with reason `missing_hdx_dataset_json`.
2. **Component gating failure:** If `apply_component_gate()` returns `ok=False`, the dataset is blocked with specific reason codes (e.g., `empty_or_unrecognized_components`, `vulnerability_without_hazard_or_exposure`).

All blocked datasets are written to `translation_blocked.csv` with columns: `dataset_id`, `status`, `reason`, `risk_data_type`.

Records that are written but fail schema validation are still saved to disk. Validation failures are tracked in `schema_validation.csv` with the specific error messages (up to 10 errors per record).

---

## Key Functions

### `build_rdls_record()`

Main transformation function that orchestrates all sub-functions.

```python
rdls_record, info = build_rdls_record(hdx_json, classification_row)
# rdls_record: RDLS-compliant dict (or None if blocked)
# info: dict with rdls_id, filename, risk_data_type, spatial_scale, blocked status, etc.
```

### `apply_component_gate()`

Validates and optionally repairs component combinations.

```python
gate = apply_component_gate(["vulnerability"])
# gate.ok: True (auto-repaired) or False (blocked)
# gate.risk_data_type: ["exposure", "vulnerability"]
# gate.reasons: ("auto_added_exposure_for_vulnerability",)
```

### `build_attributions()`

Creates the 3 required attribution objects from HDX metadata.

### `build_resources()`

Converts HDX resources to RDLS resource objects, applying format mapping and temporal annotation.

### `map_license()`

Maps HDX license strings to RDLS license identifiers using pattern matching and dictionary lookup.

### `map_data_format()`

Maps HDX format strings to RDLS `data_format` enum values, with fallback inference from filenames and URLs.

### `build_nb06_rdls_id()`

Constructs the RDLS record ID and filename from components, country codes, organization, and title.

---

## Nested Required Fields Check (M8)

At the end of the notebook, a post-translation audit verifies:
- **Attribution roles:** All 3 required roles (`publisher`, `creator`, `contact_point`) are present in every record
- **Resource sub-fields:** Every resource has `id`, `title`, `data_format`, and `access_modality`

Results are reported in the QA summary output. Any gaps are logged as warnings.

---

## Statistics (Actual Run)

| Metric | Value |
|--------|-------|
| Classification rows | 26,246 |
| RDLS candidates (included IDs) | 13,053 |
| Records written | 13,152 (some datasets produce multiple records) |
| Blocked (gating/missing data) | 9 |
| Schema valid (at translation) | 13,143 |
| Nested field warnings | 0 |
| Unmapped HDX formats | 1 (`zipped jpeg`) |

---

## Troubleshooting

### Empty risk_data_type
**Cause:** Classification didn't assign components properly.
**Fix:** Review classification in Step 04-05, add overrides if needed.

### Blocked by component gating
**Cause:** Vulnerability or loss without hazard/exposure, and auto-repair is disabled.
**Fix:** Either:
1. Enable `auto_repair_components=True` (default)
2. Add hazard/exposure to classification via overrides in Step 05

### Missing required fields
**Cause:** HDX metadata incomplete (e.g., no resources, no organization).
**Fix:** These datasets are blocked automatically. Check `translation_blocked.csv` for specific reasons.

### Schema validation failures
**Cause:** Generated record doesn't match RDLS schema constraints (e.g., empty `author_names` arrays in `referenced_by`, empty `resources` array).
**Fix:** Check `schema_validation.csv` for specific error paths. Common issues include empty `referenced_by` author names and resources arrays. These are addressed in Step 07 validation.

### Filename collisions
**Cause:** Two datasets produce the same ID slug.
**Fix:** Handled automatically by appending an 8-character UUID prefix. Check for `_` + hex suffix in filenames.

---

[< Previous: Review & Overrides](05_review_overrides.md) | [Back to README](../README.md) | [Next: Validate & Package >](07_validate_package.md)
