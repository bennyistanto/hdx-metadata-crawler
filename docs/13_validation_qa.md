# 13 - Validation & QA

**Notebook:** `notebook/13_rdls_validation_qa.ipynb`

---

## Summary

Validates all integrated RDLS records against the RDLS v0.3 JSON Schema, scores each record on a composite confidence metric, routes records into quality tiers, and packages the final deliverable bundle.

**For Decision Makers:**
> This is the final quality checkpoint. Every record is validated against the official schema, scored for confidence, and sorted into quality tiers. The output is a production-ready archive with valid records, detailed reports, and a comprehensive manifest.

---

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| Integrated records | `rdls/integrated/*.json` | ~12,500 records from Step 12 |
| RDLS Schema | `rdls/schema/rdls_schema_v0.3.json` | JSON Schema for validation |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Valid records | `rdls/dist/high/*.json` | Production-ready records (valid + high confidence) |
| Invalid records | `rdls/dist/invalid/high/*.json` | Invalid but high-confidence records for review |
| Validation report | `rdls/reports/schema_validation.csv` | Per-record validation results |
| HEVL coverage | `rdls/reports/hevl_coverage_report.csv` | Block completeness data |
| Confidence scores | `rdls/reports/confidence_scores.csv` | Per-record composite scores |
| Master manifest | `rdls/reports/master_manifest.csv` | Full record inventory |
| Final archive | `rdls/dist/rdls_hdx_package_*.zip` | Complete deliverable |

---

## Validation Approach

### JSON Schema Validator

The notebook uses `Draft202012Validator` (with `Draft7Validator` fallback) from the `jsonschema` library:

```python
from jsonschema import Draft202012Validator, Draft7Validator

try:
    validator = Draft202012Validator(schema)
except:
    validator = Draft7Validator(schema)
```

Each record is validated as a complete RDLS document (`{"datasets": [record]}`).

### Error Categorisation

Validation errors are categorised by pattern matching on error messages:

| Category | Pattern | Example |
|----------|---------|---------|
| **anyOf** | `anyOf` constraint failures | `occurrence/empirical: {} should be non-empty` |
| **enum** | Invalid enum value | `'XKX' is not one of [valid ISO3 codes]` |
| **type** | Wrong field type | `expected string, got integer` |
| **missing** | Required field absent | `'title' is a required property` |
| **format** | Invalid format | `not a valid URI` |
| **other** | Uncategorised | Various structural issues |

### Error Summary Column

Each record's validation result includes a `validation_error_summary` column — a semicolon-separated list of error paths and messages for quick diagnosis without re-running validation.

---

## Composite Confidence Scoring

Each record receives a composite quality score (0.0–1.0) based on four weighted dimensions:

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| **HEVL coverage** | 40% | Fraction of declared components that have actual blocks |
| **Block richness** | 25% | Depth and detail of HEVL content (fields populated) |
| **Schema validity** | 20% | Binary: passes schema validation or not |
| **Metadata completeness** | 15% | Description, spatial, attributions, resources present |

### Quality Tiers

Records are routed into a 2D grid: **valid/invalid** × **high/medium/low** confidence:

| Tier | Score Range | Destination |
|------|-------------|-------------|
| High | ≥ 0.8 | `dist/high/` (valid) or `dist/invalid/high/` (invalid) |
| Medium | 0.5–0.8 | `dist/medium/` or `dist/invalid/medium/` |
| Low | < 0.5 | `dist/low/` or `dist/invalid/low/` |

---

## Quality Gates

Three gates determine overall pipeline pass/fail:

### Gate 1: Schema Compliance
```
✅ PASS: Schema valid rate ≥ 99.5%
⚠️ WARN: Schema valid rate 95–99.5%
❌ FAIL: Schema valid rate < 95%
```

### Gate 2: HEVL Coverage
```
✅ PASS: HEVL coverage ≥ 90% where applicable
⚠️ WARN: HEVL coverage 80–90%
❌ FAIL: HEVL coverage < 80%
```

### Gate 3: Data Quality
```
✅ PASS: No critical issues
⚠️ WARN: <10 critical issues
❌ FAIL: ≥10 critical issues
```

---

## How It Works

```
1. Load all integrated RDLS records from rdls/integrated/
2. Load RDLS v0.3 JSON Schema
3. For each record:
   a. Validate against schema using Draft202012Validator
   b. Categorise any validation errors
   c. Check HEVL block completeness
   d. Compute composite confidence score
4. Route records into quality tier directories
5. Generate reports:
   - Schema validation results (per-record)
   - HEVL coverage report
   - Confidence score distribution
   - Master manifest
6. Apply quality gates
7. Package final archive (ZIP)
```

---

## Report Structure

### schema_validation.csv

| Column | Description |
|--------|-------------|
| `id` | RDLS record ID |
| `filename` | Source JSON filename |
| `valid` | Boolean: passes schema validation |
| `error_count` | Number of validation errors |
| `validation_error_summary` | Semicolon-separated error descriptions |

### hevl_coverage_report.csv

| Column | Description |
|--------|-------------|
| `id` | RDLS record ID |
| `risk_data_type` | Declared components |
| `has_hazard_block` | Boolean |
| `has_exposure_block` | Boolean |
| `has_vulnerability_block` | Boolean |
| `has_loss_block` | Boolean |
| `coverage_ratio` | Fraction of declared types with blocks |

### confidence_scores.csv

| Column | Description |
|--------|-------------|
| `id` | RDLS record ID |
| `hevl_score` | HEVL coverage dimension (0–1) |
| `richness_score` | Block richness dimension (0–1) |
| `validity_score` | Schema validity dimension (0 or 1) |
| `metadata_score` | Metadata completeness dimension (0–1) |
| `composite_score` | Weighted total (0–1) |
| `tier` | Quality tier (high/medium/low) |

---

## Final Archive Contents

```
rdls_hdx_package_YYYYMMDD.zip
├── high/                    # Valid, high-confidence records
│   └── *.json
├── invalid/
│   └── high/               # Invalid but high-confidence (for review)
│       └── *.json
├── reports/
│   ├── schema_validation.csv
│   ├── hevl_coverage_report.csv
│   ├── confidence_scores.csv
│   └── master_manifest.csv
└── README.txt
```

---

## Troubleshooting

### High schema failure rate
- Check `schema_validation.csv` for the most common error categories
- `anyOf` errors on `occurrence/empirical: {}` indicate empty occurrence blocks
- `enum` errors on ISO3 codes indicate unrecognised country codes (e.g., `XKX`)
- Fix in source notebooks (09–11) and re-run the pipeline

### Low composite scores
- Check which dimension is dragging the score down
- Low HEVL coverage → review extraction results (NB 09–11)
- Low richness → HEVL blocks may lack detail
- Low validity → fix schema errors first

### Quality gate failures
- Review the specific gate that failed
- Schema compliance is the most common concern
- Some errors (e.g., `XKX` for Kosovo) may be acceptable known limitations

---

[← Previous: HEVL Integration](12_hevl_integration.md) | [Back to README](../README.md)
