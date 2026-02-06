# 13 - Validation & QA

**Notebook:** `notebook/13_rdls_validation_qa.ipynb`

---

## Summary

Final validation and quality assurance of all RDLS records, including HEVL block completeness and schema compliance.

**For Decision Makers:**
> This is the final quality checkpoint. It validates every record, generates comprehensive QA reports, and produces the final deliverable with full HEVL metadata.

---

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| Integrated records | `rdls/records/*.json` | From Step 12 |
| RDLS Schema | `rdls/schema/rdls_schema_v0.3.json` | Validation schema |
| Integration report | `analysis/hevl_integration_report.csv` | From Step 12 |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Final validation | `rdls/reports/final_validation.csv` | Per-record results |
| HEVL coverage | `rdls/reports/hevl_coverage_report.csv` | Block completeness |
| Quality summary | `rdls/reports/qa_summary.md` | Human-readable report |
| Final bundle | `rdls/dist/rdls_metadata_final.zip` | Production deliverable |

---

## QA Checks Performed

### 1. Schema Validation
- All required fields present
- Field types correct
- Enum values valid
- Array constraints met

### 2. HEVL Completeness
- Hazard block matches risk_data_type
- Exposure block populated
- V/L blocks present where classified
- No orphan HEVL blocks

### 3. Data Consistency
- ID uniqueness across records
- No duplicate content (hash check)
- Spatial consistency (valid ISO3 codes)
- License format compliance

### 4. Content Quality
- Title not empty or generic
- Description meaningful (>20 chars)
- Resources have valid URLs
- Attributions complete

---

## Key Functions

### `QAValidator`
Comprehensive validation class.

```python
validator = QAValidator(schema)
results = validator.validate_all(records_dir)
# results.passed: int
# results.failed: int
# results.warnings: int
# results.issues: List[QAIssue]
```

### `check_hevl_completeness()`
Validates HEVL block coverage.

```python
coverage = check_hevl_completeness(record)
# coverage.has_hazard_block: bool
# coverage.has_exposure_block: bool
# coverage.matches_risk_type: bool
```

### `generate_qa_report()`
Creates comprehensive quality report.

```python
report = generate_qa_report(validation_results)
# Returns Markdown-formatted report
```

---

## QA Severity Levels

| Level | Description | Action Required |
|-------|-------------|-----------------|
| **ERROR** | Schema violation | Must fix before delivery |
| **WARNING** | Quality concern | Review and document |
| **INFO** | Minor observation | Optional improvement |

---

## HEVL Coverage Matrix

The notebook generates a coverage matrix:

```
                    Hazard  Exposure  Vulnerability  Loss
risk_data_type       3,421    7,842         1,654   1,234
HEVL block present   3,218    7,456         1,432   1,098
Coverage rate        94.1%    95.1%         86.6%   89.0%
```

---

## Quality Metrics

### Record-Level Metrics
| Metric | Target | Typical |
|--------|--------|---------|
| Schema valid | 100% | 99.9% |
| Title present | 100% | 100% |
| Description >20 chars | >95% | 97% |
| Resources valid | 100% | 99.5% |

### HEVL Metrics
| Metric | Target | Typical |
|--------|--------|---------|
| Hazard block where classified | >90% | 94% |
| Exposure block where classified | >90% | 95% |
| V/L block where classified | >80% | 87% |
| HEVL-risk_type consistency | 100% | 99.8% |

---

## QA Report Structure

Generated `qa_summary.md`:

```markdown
# RDLS Quality Assurance Report

Generated: 2025-01-15T14:30:00Z
Total records: 10,500

## Schema Validation
- Passed: 10,492 (99.9%)
- Failed: 8 (0.1%)

## HEVL Completeness
- Full coverage: 8,234 (78.4%)
- Partial coverage: 2,156 (20.5%)
- No HEVL: 110 (1.0%)

## Issues Summary
### Errors (8)
- Missing required field 'license': 3 records
- Invalid hazard_type enum: 5 records

### Warnings (45)
- Generic title detected: 12 records
- Missing description: 33 records

## Recommendations
1. Review 8 schema errors for manual fix
2. Consider enriching 33 records with descriptions
3. HEVL coverage meets target (>95%)
```

---

## Final Bundle Contents

```
rdls_metadata_final.zip
├── records/
│   └── *.json (10,500 files)
├── index/
│   └── rdls_index.jsonl
├── reports/
│   ├── final_validation.csv
│   ├── hevl_coverage_report.csv
│   ├── qa_summary.md
│   └── schema_validation_full.csv
└── README.txt
```

---

## Quality Gates

### Gate 1: Schema Compliance
```
✅ PASS: Schema valid rate ≥ 99.5%
❌ FAIL: Schema valid rate < 99.5%
```

### Gate 2: HEVL Coverage
```
✅ PASS: HEVL coverage ≥ 90% where applicable
⚠️ WARN: HEVL coverage 80-90%
❌ FAIL: HEVL coverage < 80%
```

### Gate 3: Data Quality
```
✅ PASS: No critical issues
⚠️ WARN: <10 critical issues
❌ FAIL: ≥10 critical issues
```

---

## Statistics (Typical Run)

```
=== FINAL QA SUMMARY ===

Records processed: 10,500

Schema validation:
  - Passed: 10,492 (99.9%)
  - Failed: 8 (0.1%)

HEVL coverage:
  - Hazard: 94.1%
  - Exposure: 95.1%
  - Vulnerability: 86.6%
  - Loss: 89.0%

Quality gates:
  ✅ Schema compliance: PASS (99.9%)
  ✅ HEVL coverage: PASS (91.2% avg)
  ✅ Data quality: PASS (8 issues)

Final bundle: rdls_metadata_final.zip (18.5 MB)
```

---

## How It Works

```
1. Load all integrated RDLS records
2. For each record:
   a. Validate against JSON schema
   b. Check HEVL block completeness
   c. Verify data consistency
   d. Assess content quality
   e. Record issues by severity
3. Aggregate metrics and statistics
4. Generate QA report
5. Apply quality gates
6. Package final deliverable
```

---

## Troubleshooting

### Schema failures
1. Check `final_validation.csv` for specific errors
2. Fix in source records or integration
3. Re-run validation

### Low HEVL coverage
- Review extraction results (09-11)
- Check integration matching (12)
- May indicate extraction pattern gaps

### Quality gate failures
- Review QA report for specific issues
- Prioritize ERROR-level items
- Document known limitations

---

## Post-QA Actions

1. **Fix critical errors:** Address schema violations
2. **Document warnings:** Explain known limitations
3. **Distribute bundle:** Share final ZIP
4. **Archive reports:** Keep QA artifacts for audit

---

[← Previous: HEVL Integration](12_hevl_integration.md) | [Back to README](../README.md)
