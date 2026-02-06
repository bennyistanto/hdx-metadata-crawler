# 12 - HEVL Integration

**Notebook:** `notebook/12_rdls_hevl_integration.ipynb`

---

## Summary

Integrates the extracted Hazard, Exposure, Vulnerability, and Loss signals into unified RDLS records.

**For Decision Makers:**
> This notebook combines all the detailed HEVL information from notebooks 09-11 into comprehensive RDLS metadata records. It's where the individual component extractions come together.

---

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| Hazard extracts | `analysis/hazard_extracts.csv` | From Step 09 |
| Exposure extracts | `analysis/exposure_extracts.csv` | From Step 10 |
| V/L extracts | `analysis/vulnerability_extracts.csv` | From Step 11 |
| RDLS records | `rdls/records/*.json` | From Step 06-07 |
| Signal dictionary | `config/signal_dictionary.yaml` | From Step 08 |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Integrated records | `rdls/records/*.json` | Enhanced RDLS files |
| Integration report | `analysis/hevl_integration_report.csv` | Per-record status |
| Coverage summary | `analysis/hevl_coverage_final.json` | Final statistics |

---

## Integration Process

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Hazard    │     │  Exposure   │     │    V / L    │
│  Extracts   │     │  Extracts   │     │  Extracts   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   Integration   │
                  │     Engine      │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Enhanced RDLS  │
                  │    Records      │
                  └─────────────────┘
```

---

## Enhanced RDLS Record Structure

Before integration:
```json
{
  "datasets": [{
    "id": "rdls_hzd-hdx_ocha_ken_flood",
    "title": "Kenya Flood Hazard Map",
    "risk_data_type": ["hazard"],
    "spatial": {...},
    "resources": [...]
  }]
}
```

After integration:
```json
{
  "datasets": [{
    "id": "rdls_hzd-hdx_ocha_ken_flood",
    "title": "Kenya Flood Hazard Map",
    "risk_data_type": ["hazard"],
    "hazard": {
      "type": "flood",
      "intensity_measure": "depth_m",
      "return_periods": ["10", "50", "100"]
    },
    "spatial": {...},
    "resources": [...]
  }]
}
```

---

## HEVL Block Schemas

### Hazard Block
```json
{
  "hazard": {
    "type": "flood",
    "process_type": "riverine_flood",
    "intensity_measure": "depth_m",
    "return_periods": ["100"],
    "scenario": "historical"
  }
}
```

### Exposure Block
```json
{
  "exposure": {
    "category": "buildings",
    "subcategory": "residential",
    "taxonomy": "GED4ALL",
    "metric": "count"
  }
}
```

### Vulnerability Block
```json
{
  "vulnerability": {
    "category": "socioeconomic",
    "indicator": "poverty_headcount",
    "unit": "percentage"
  }
}
```

### Loss Block
```json
{
  "loss": {
    "category": "economic",
    "type": "direct_damage",
    "unit": "USD",
    "hazard_link": "flood"
  }
}
```

---

## Key Functions

### `HEVLIntegrator`
Main integration class.

```python
integrator = HEVLIntegrator(
    hazard_extracts,
    exposure_extracts,
    vulnerability_extracts,
    loss_extracts
)
enhanced_record = integrator.integrate(rdls_record, dataset_id)
```

### `merge_hevl_blocks()`
Combines component blocks into record.

```python
merged = merge_hevl_blocks(
    record=base_record,
    hazard=hazard_block,
    exposure=exposure_block,
    vulnerability=vulnerability_block,
    loss=loss_block
)
```

---

## Multi-Component Integration

Datasets with multiple components get all relevant blocks:

```json
{
  "id": "rdls_exp-hdx_wfp_mli_food_security",
  "risk_data_type": ["exposure", "vulnerability"],
  "exposure": {
    "category": "population",
    "subcategory": "food_insecure"
  },
  "vulnerability": {
    "category": "socioeconomic",
    "indicator": "food_security_index"
  }
}
```

---

## Integration Rules

### Merge Conflicts
When extracts disagree:
1. Prefer higher confidence extracts
2. Merge complementary information
3. Log conflicts for review

### Missing Extracts
If component has no extract:
1. Keep existing `risk_data_type`
2. Leave HEVL block empty
3. Record in integration report

### Validation
After integration:
1. Re-validate against RDLS schema
2. Check HEVL blocks are well-formed
3. Ensure consistency with `risk_data_type`

---

## Statistics (Typical Run)

```
=== HEVL INTEGRATION SUMMARY ===

Records processed: 10,500

Hazard blocks added: 3,421 (32.6%)
Exposure blocks added: 7,842 (74.7%)
Vulnerability blocks added: 1,654 (15.8%)
Loss blocks added: 1,234 (11.8%)

Integration status:
  - Fully integrated: 8,456 (80.5%)
  - Partial integration: 1,876 (17.9%)
  - No HEVL data: 168 (1.6%)

Schema validation:
  - Valid after integration: 10,492 (99.9%)
  - Invalid: 8 (0.1%)
```

---

## How It Works

```
1. Load all HEVL extracts (09-11 outputs)
2. Load existing RDLS records (06-07 outputs)
3. For each record:
   a. Match dataset_id to extracts
   b. Build HEVL blocks from extracts
   c. Merge blocks into record
   d. Re-validate against schema
4. Write enhanced records
5. Generate integration report
```

---

## Troubleshooting

### Missing HEVL blocks
- Check if extracts exist (review 09-11 outputs)
- Verify dataset_id matching
- May indicate extraction gaps

### Schema validation failures
- HEVL block may have invalid values
- Check enum values match RDLS schema
- Review specific field constraints

### Duplicate/conflicting blocks
- Multiple extracts for same dataset
- Integration engine should merge
- Check integration report for conflicts

---

[← Previous: V/L Extractor](11_vulnerability_loss_extractor.md) | [Back to README](../README.md) | [Next: Validation & QA →](13_validation_qa.md)
