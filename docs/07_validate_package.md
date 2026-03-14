# 07 - Validate & Package

**Notebook:** `notebook/07_rdls_validate_and_package.ipynb`

---

## Summary

Validates all RDLS JSON records against the schema using JSON Schema Draft 2020-12, performs nested field validation for attributions and resources, detects duplicates, generates QA reports, and packages everything into a distributable ZIP bundle.

**For Decision Makers:**
> This is the final quality gate. It verifies all outputs are schema-compliant, checks that every record has the required attribution roles and resource sub-fields, and creates the deliverable ZIP file that can be shared or uploaded to the Risk Data Library.

---

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| RDLS records | `rdls/records/*.json` | From Step 06 |
| Index | `rdls/index/rdls_index.jsonl` | From Step 06 |
| RDLS Schema | `rdls/schema/rdls_schema_v0.3.json` | Validation schema |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Validation report | `rdls/reports/schema_validation_full.csv` | Per-record schema validation results |
| Missing fields | `rdls/reports/rdls_missing_fields.csv` | Records with missing required fields |
| Duplicates | `rdls/reports/rdls_duplicates.csv` | ID and content duplicate detection |
| Nested field warnings | `rdls/reports/rdls_nested_field_warnings.csv` | Attribution role and resource sub-field gaps |
| Summary | `rdls/reports/rdls_validation_summary.md` | Human-readable validation report |
| Bundle | `rdls/dist/rdls_metadata_bundle.zip` | Deliverable package |

---

## Key Configuration

```python
@dataclass
class ValidationConfig:
    dump_dir: Path = field(default_factory=lambda: (Path("..") / "hdx_dataset_metadata_dump").resolve())
    output_mode: str = "in_place"      # "in_place" or "run_folder" (must match Step 06)
    run_id: Optional[str] = None       # For run_folder mode (None for auto-detect)
```

### Output Mode

The `output_mode` must match Step 06. When set to `"run_folder"`, the notebook resolves the correct run directory using this priority:

1. **Explicit `run_id`:** If provided, uses `rdls/runs/{run_id}/`
2. **`_latest.txt` pointer:** Reads the run ID from `rdls/runs/_latest.txt`
3. **Newest folder fallback:** Picks the most recently modified folder under `rdls/runs/`

In `"in_place"` mode (default), records are read directly from `rdls/records/`.

---

## Schema Validation

The notebook uses `jsonschema.Draft202012Validator` (JSON Schema Draft 2020-12) to validate each record against `rdls_schema_v0.3.json`.

```python
import jsonschema
validator = jsonschema.Draft202012Validator(rdls_schema)
```

### `validate_dataset_obj()`

Validates a single dataset object (extracted from the `datasets` wrapper array):

```python
def validate_dataset_obj(dataset_obj: Dict[str, Any]) -> Tuple[bool, str]:
    errors = sorted(validator.iter_errors(dataset_obj), key=lambda e: e.path)
    if not errors:
        return True, ""
    msgs = [f"{'.'.join(str(p) for p in e.path)}: {e.message}" for e in errors[:10]]
    return False, " | ".join(msgs)
```

Up to 10 errors are captured per record. Error paths use dot notation (e.g., `referenced_by.0.author_names`).

---

## Validation Checks

### 1. JSON Schema Validation

Every record is validated against the RDLS v0.3 schema:
- Required fields present
- Field types correct
- Enum values valid
- Array constraints met (e.g., `minItems`)

### 2. Required Field Check

The schema's top-level required fields are checked programmatically:
- `id`
- `title`
- `risk_data_type`
- `attributions` (non-empty array)
- `spatial`
- `license`
- `resources` (non-empty array)

Empty strings, empty arrays, empty objects, and `None` values are all flagged as missing.

### 3. Duplicate Detection

- **ID duplicates:** Same RDLS ID appearing in multiple files
- **Content duplicates:** Identical file content detected via SHA-256 hash comparison

### 4. Nested Field Validation (M8)

A second pass checks structural completeness beyond what the schema enforces:

**Attribution roles:** Every record must have all 3 required roles:
- `publisher`
- `creator`
- `contact_point`

```python
REQUIRED_ATTRIBUTION_ROLES = {"publisher", "creator", "contact_point"}
attr_roles = {a.get("role") for a in attributions if isinstance(a, dict)}
missing_roles = REQUIRED_ATTRIBUTION_ROLES - attr_roles
```

**Resource sub-fields:** Every resource object must have these 4 fields:
- `id`
- `title`
- `data_format`
- `access_modality`

```python
REQUIRED_RESOURCE_FIELDS = {"id", "title", "data_format", "access_modality"}
missing_res = {k for k in REQUIRED_RESOURCE_FIELDS if not r.get(k)}
```

All gaps are written to `rdls_nested_field_warnings.csv` with columns: `filename`, `rdls_id`, `check`, `detail`, `severity`.

---

## Key Functions

### `validate_dataset_obj()`

Validates a single dataset against the RDLS schema.

```python
is_valid, error_message = validate_dataset_obj(dataset_dict)
# is_valid: True/False
# error_message: "" or pipe-separated error strings
```

### `sha256_file()`

Computes file hash for duplicate detection.

```python
file_hash = sha256_file(Path("record.json"))
# Returns: "a1b2c3d4e5f6..."
```

### `iter_record_files()`

Gets a sorted list of all JSON record files in the records directory.

### `add_folder_to_zip()`

Adds directory contents to a ZIP archive, preserving relative paths.

```python
count = add_folder_to_zip(zip_file, folder, "records")
# Returns: number of files added
```

---

## Validation Summary Report

The notebook generates a Markdown summary (`rdls_validation_summary.md`) with all key metrics:

```markdown
# RDLS Validation Summary

- **Run timestamp:** 2026-02-14T14:04:41.943266+00:00
- **Records folder:** `rdls/records`
- **Total JSON files:** **13,152**
- **Schema valid:** **13,143**
- **Schema invalid:** **9**
- **Records missing required fields:** **0**
- **Duplicates detected:** **0**
- **Nested field warnings:** **0**
```

If there are missing fields or duplicates, the summary includes breakdowns by field name and duplicate type.

---

## Bundle Contents

The ZIP bundle (`rdls_metadata_bundle.zip`) contains all records, the index, and all reports:

```
rdls_metadata_bundle.zip
+-- records/
|   +-- rdls_hzd-ken_ocha_floodriskmap.json
|   +-- rdls_exp-worldpop_populationdensity.json
|   +-- ... (all RDLS records)
+-- index/
|   +-- rdls_index.jsonl
+-- reports/
    +-- schema_validation_full.csv
    +-- rdls_missing_fields.csv
    +-- rdls_duplicates.csv
    +-- rdls_nested_field_warnings.csv
    +-- rdls_validation_summary.md
    +-- ... (other reports from Step 06)
```

---

## Quality Gate

The notebook outputs a quality gate status that accounts for schema validation, missing required fields, and nested field warnings.

### PASSED

```
============================================================
QUALITY GATE: PASSED
All 13,143 records are schema-valid with no missing required fields or nested field warnings.
============================================================
```

The gate passes only when all three conditions are met:
- Zero schema-invalid records
- Zero records with missing required fields
- Zero nested field warnings

### REVIEW NEEDED

```
============================================================
QUALITY GATE: REVIEW NEEDED
  - 9 records failed schema validation
  - 3 records have nested field warnings (attribution roles / resource sub-fields)
Review the reports above for details.
============================================================
```

The gate triggers review when any of the three checks produces failures. Each failure category is listed separately.

---

## Statistics (Actual Run)

| Metric | Value |
|--------|-------|
| Total records | 13,152 |
| Schema valid | 13,143 |
| Schema invalid | 9 |
| Missing required fields | 0 |
| Duplicate IDs | 0 |
| Duplicate content | 0 |
| Nested field warnings | 0 |
| Bundle size | 36.18 MB |

---

## Troubleshooting

### Schema validation failures
1. Check `schema_validation_full.csv` for specific error paths and messages
2. Common issues:
   - Empty `author_names` array in `referenced_by` objects
   - Empty `resources` array
   - Invalid `countries` codes (e.g., `XKX` for Kosovo)
   - Invalid license format
3. Fix the translation logic in Step 06 and re-run

### Duplicate IDs
1. Check `rdls_duplicates.csv` for affected files
2. Usually indicates a collision in the naming convention
3. Step 06 handles this automatically by appending a UUID suffix, but edge cases may occur

### Nested field warnings
1. Check `rdls_nested_field_warnings.csv` for specific records
2. Missing attribution roles indicate the `build_attributions()` function in Step 06 did not produce all 3 roles
3. Missing resource sub-fields indicate format mapping gaps in Step 06

### Large bundle size
- Normal: 1-2 KB per record (pretty-printed JSON)
- If significantly larger: Check for bloated metadata or unnecessary fields
- Consider `write_pretty_json=False` in Step 06 for smaller files

### Missing required fields
1. Check `rdls_missing_fields.csv` for the specific fields
2. Usually caused by incomplete HDX metadata
3. Fix source data or add to the blocked list in Step 05

---

## Next Steps

After successful validation:

1. **Review reports:** Check the summary for any warnings or failures
2. **Distribute bundle:** Share the ZIP with stakeholders
3. **Run HEVL extraction:** Notebooks 08-13 for detailed analysis
4. **Archive run:** Keep the manifest and reports for audit trail

---

[< Previous: Translate to RDLS](06_translate_to_rdls.md) | [Back to README](../README.md) | [Next: Signal Analysis >](08_signal_analysis.md)
