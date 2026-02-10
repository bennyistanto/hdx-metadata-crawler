# 08 - HEVL Signal Analysis

**Notebook:** `notebook/08_rdls_hdx_signal_analysis.ipynb`

---

## Summary

Analyses HDX metadata to identify Hazard, Exposure, Vulnerability, and Loss (HEVL) signals, producing the **signal dictionary** — the central configuration that drives all downstream HEVL extraction (notebooks 09–13).

**For Decision Makers:**
> This notebook builds and validates the signal dictionary — a comprehensive mapping of regex patterns, confidence levels, and codelist values that identify specific risk data types in unstructured HDX metadata. It is the foundation for automated HEVL extraction.

---

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| Dataset JSONs | `dataset_metadata/*.json` | Raw HDX metadata (26,246 files) |
| Classification | `derived/classification_final.csv` | From Step 05 |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Signal dictionary | `config/signal_dictionary.yaml` | HEVL signal patterns and codelist mappings |
| Analysis report | `rdls/extracted/hevl_signal_analysis.csv` | Signal frequency data |
| Coverage stats | `rdls/extracted/hevl_coverage_summary.json` | Statistics |

---

## Signal Dictionary Structure

The signal dictionary (`config/signal_dictionary.yaml`) is the central configuration file for all HEVL extraction. Each section maps to an RDLS codelist with regex patterns and confidence levels.

### Sections

| Section | Entries | RDLS Codelist | Used By |
|---------|---------|---------------|---------|
| `hazard_type` | 11 types | `hazard_type` (closed, 11 values) | NB 09 |
| `process_type` | 30 types | `process_type` (closed, 30 values) | NB 09 |
| `exposure_category` | 7 categories | `exposure_category` (closed, 7 values) | NB 10 |
| `analysis_type` | 3 types | `analysis_type` (closed) | NB 09 |
| `return_period` | RP patterns | — | NB 09 |
| `vulnerability_indicators` | V signal patterns | — | NB 11 |
| `loss_indicators` | L signal patterns | — | NB 11 |
| `exclusion_patterns` | False positive rules | — | NB 09–11 |

### Entry Format

Each entry has a `patterns` list (regex, case-insensitive) and a `confidence` level (`high`, `medium`, `low`):

```yaml
hazard_type:
  flood:
    patterns:
      - '\b(flood|flooding|inundation)\b'
      - '\b(fluvial|pluvial|riverine)\b'
    confidence: high

exposure_category:
  buildings:
    patterns:
      - '\b(building|dwelling)\b'
      - '\b(house|housing|residential)\b'
      - '\b(footprint|building.?stock|floor.?area)\b'
    confidence: high
```

### Codelist Alignment

All pattern keys align 1:1 with RDLS v0.3 closed codelist values:

- **11 hazard types**: coastal_flood, convective_storm, drought, earthquake, extreme_temperature, flood, landslide, strong_wind, tsunami, volcanic, wildfire
- **30 process types**: Each linked to a `parent_hazard` (e.g., `storm_surge` → `coastal_flood`)
- **7 exposure categories**: agriculture, buildings, infrastructure, population, natural_environment, economic_indicator, development_index

---

## HEVL Signal Categories

### Hazard Signals
Natural and technological threats:

| Type | Example Patterns |
|------|-----------------|
| flood | `\b(flood\|flooding\|inundation)\b` |
| earthquake | `\b(earthquake\|seismic\|tremor)\b` |
| drought | `\b(drought\|dry.?spell\|water.?scarcity)\b` |
| wildfire | `\b(wildfire\|bush.?fire\|forest.?fire)\b` |

### Exposure Signals
Assets and populations at risk:

| Category | Example Patterns |
|----------|-----------------|
| population | `\b(population\|census)\b` + compound terms like `\b(population.?count\|head.?count)\b` |
| buildings | `\b(building\|dwelling)\b` |
| infrastructure | `\b(road\|bridge\|highway)\b`, `\b(energy\|power.?station)\b` |
| agriculture | `\b(crop\|livestock\|farmland)\b` |

### Vulnerability Signals
Susceptibility factors:

| Pattern Type | Example Terms |
|--------------|---------------|
| Function curves | fragility, vulnerability curve, damage function |
| Structural | building quality, construction type |
| Socioeconomic | poverty index, coping capacity |

### Loss Signals
Historical and projected impacts:

| Pattern Type | Example Terms |
|--------------|---------------|
| Human loss | casualties, fatalities, mortality |
| Economic loss | damage cost, economic loss, insured loss |
| Displacement | displaced, evacuated, affected population |

---

## How It Works

```
1. Load all dataset metadata (26,246 records)
2. For each dataset:
   a. Extract text fields (title, description, tags, notes)
   b. Scan for HEVL signal terms using regex patterns
   c. Record signal matches with context and confidence
3. Aggregate signal frequency statistics
4. Validate signal dictionary against RDLS codelists
5. Export dictionary and coverage reports
```

---

## Confidence Levels

| Level | Confidence | Description |
|-------|-----------|-------------|
| High | 0.9–1.0 | Unambiguous domain terms ("flood map", "earthquake") |
| Medium | 0.6–0.8 | Context-dependent terms ("risk assessment", "exposure") |
| Low | 0.3–0.5 | Generic terms that may indicate HEVL content |

---

## Troubleshooting

### Low signal coverage
- Review pattern lists for missing term variations
- Add domain-specific terminology to signal dictionary
- Check for non-English datasets (patterns are English-only)

### False positives
- Add entries to `exclusion_patterns` section
- Increase confidence thresholds
- Review context requirements

### Signal overlap
- HEVL categories can overlap (e.g., "flood damage" = hazard + loss)
- This is expected and handled in integration (notebook 12)

---

## Next Steps

After signal analysis:
1. Review signal dictionary for completeness
2. Proceed to component extractors (09–11)
3. Integrate signals in notebook 12

---

[← Previous: Validate & Package](07_validate_package.md) | [Back to README](../README.md) | [Next: Hazard Extractor →](09_hazard_extractor.md)
