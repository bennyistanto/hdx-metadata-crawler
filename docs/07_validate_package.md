# 07 - Validate & Package

**Notebook:** `notebook/07_rdls_validate_and_package.ipynb`

---

## Summary

Validates all RDLS JSON records against the schema, generates QA reports, and packages everything into a distributable bundle.

**For Decision Makers:**
> This is the final quality gate. It verifies all outputs are schema-compliant and creates the deliverable ZIP file that can be shared or uploaded to the Risk Data Library.

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
| Validation report | `rdls/reports/schema_validation_full.csv` | Per-record results |
| Missing fields | `rdls/reports/rdls_missing_fields.csv` | Required field gaps |
| Duplicates | `rdls/reports/rdls_duplicates.csv` | ID and content dupes |
| Summary | `rdls/reports/rdls_validation_summary.md` | Human-readable report |
| Bundle | `rdls/dist/rdls_metadata_bundle.zip` | Deliverable package |

---

## Key Configuration

```python
@dataclass
class ValidationConfig:
    output_mode: str = "in_place"      # Must match Step 06
    run_id: Optional[str] = None       # For run_folder mode
```

---

## Validation Checks

### 1. JSON Schema Validation
Every record is validated against `rdls_schema_v0.3.json`:
- Required fields present
- Field types correct
- Enum values valid
- Array constraints met

### 2. Required Field Check
RDLS requires these fields:
- `id`
- `title`
- `risk_data_type`
- `attributions` (min 3)
- `spatial`
- `license`
- `resources` (min 1)

### 3. Duplicate Detection
- **ID duplicates:** Same RDLS ID in multiple files
- **Content duplicates:** Identical file content (SHA-256 hash)

---

## Key Functions

### `validate_dataset_obj()`
Validates a single dataset against schema.

```python
is_valid, error_message = validate_dataset_obj(dataset_dict)
# is_valid: True/False
# error_message: "" or detailed error string
```

### `sha256_file()`
Computes file hash for duplicate detection.

```python
file_hash = sha256_file(Path("record.json"))
# Returns: "a1b2c3d4e5f6..."
```

### `add_folder_to_zip()`
Adds directory contents to ZIP archive.

```python
count = add_folder_to_zip(zip_file, folder, "records")
# Returns: number of files added
```

---

## Validation Summary Report

Generated Markdown report (`rdls_validation_summary.md`):

```markdown
# RDLS Validation Summary

- **Run timestamp:** 2025-01-15T14:30:22Z
- **Records folder:** rdls/records
- **Total JSON files:** 10,500
- **Schema valid:** 10,500
- **Schema invalid:** 0
- **Records missing required fields:** 0
- **Duplicates detected:** 0
```

---

## Bundle Contents

The ZIP bundle (`rdls_metadata_bundle.zip`) contains:

```
rdls_metadata_bundle.zip
├── records/
│   ├── rdls_hzd-hdx_ocha_ken_flood.json
│   ├── rdls_exp-hdx_worldpop_population.json
│   └── ... (all RDLS records)
├── index/
│   └── rdls_index.jsonl
└── reports/
    ├── schema_validation_full.csv
    ├── rdls_missing_fields.csv
    ├── rdls_duplicates.csv
    └── rdls_validation_summary.md
```

---

## Quality Gate

The notebook outputs a quality gate status:

### ✅ PASSED
```
============================================================
QUALITY GATE: PASSED
All 10,500 records are schema-valid with no missing required fields.
============================================================
```

### ⚠️ REVIEW NEEDED
```
============================================================
QUALITY GATE: REVIEW NEEDED
  - 5 records failed schema validation
  - 2 records have missing required fields
Review the reports above for details.
============================================================
```

---

## Statistics (Typical Run)

| Metric | Value |
|--------|-------|
| Total records | 10,500 |
| Schema valid | 10,500 |
| Schema invalid | 0 |
| Missing fields | 0 |
| Duplicate IDs | 0 |
| Duplicate content | 0 |
| Bundle size | 15.2 MB |

---

## Troubleshooting

### Schema validation failures
1. Check `schema_validation_full.csv` for specific errors
2. Common issues:
   - Empty `risk_data_type` array
   - Missing attribution fields
   - Invalid license format
3. Fix in Step 06 and re-run

### Duplicate IDs
1. Check `rdls_duplicates.csv` for affected files
2. Usually indicates collision in naming
3. Step 06 should handle this automatically with UUID suffix

### Large bundle size
- Normal: 1-2 KB per record
- If >5 KB/record: Check for bloated metadata
- Consider `write_pretty_json=False` in Step 06 for smaller files

### Missing required fields
1. Check `rdls_missing_fields.csv`
2. Usually caused by incomplete HDX metadata
3. Fix source data or add to blocked list

---

## Distribution

### Share the bundle
```bash
# Copy to shared location
cp rdls/dist/rdls_metadata_bundle.zip /shared/rdls/

# Or upload to cloud storage
aws s3 cp rdls/dist/rdls_metadata_bundle.zip s3://bucket/rdls/
```

### Extract and verify
```bash
unzip rdls_metadata_bundle.zip -d rdls_output/
ls rdls_output/records/ | wc -l  # Count records
```

---

## Next Steps

After successful validation:

1. **Review reports:** Check summary for any warnings
2. **Distribute bundle:** Share ZIP with stakeholders
3. **Run HEVL extraction:** Notebooks 08-13 for detailed analysis
4. **Archive run:** Keep manifest and reports for audit trail

---

[← Previous: Translate to RDLS](06_translate_to_rdls.md) | [Back to README](../README.md) | [Next: Signal Analysis →](08_signal_analysis.md)
