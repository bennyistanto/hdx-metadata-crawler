# 08 - HEVL Signal Analysis

**Notebook:** `notebook/08_rdls_hdx_signal_analysis.ipynb`

---

## Summary

Analyzes HDX metadata to identify Hazard, Exposure, Vulnerability, and Loss (HEVL) signals for detailed RDLS component extraction.

**For Decision Makers:**
> This notebook builds the "signal dictionary" - a comprehensive mapping of terms, patterns, and indicators that identify specific risk data types. It's the foundation for the detailed HEVL extraction in notebooks 09-13.

---

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| Dataset JSONs | `dataset_metadata/*.json` | Raw HDX metadata |
| Classification | `derived/classification_final.csv` | From Step 05 |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Signal dictionary | `config/signal_dictionary.yaml` | HEVL signal patterns |
| Analysis report | `analysis/hevl_signal_analysis.csv` | Signal frequency data |
| Coverage stats | `analysis/hevl_coverage_summary.json` | Statistics |

---

## HEVL Signal Categories

### Hazard Signals
Natural and man-made threats:

| Category | Example Terms |
|----------|---------------|
| Hydro | flood, inundation, river overflow |
| Seismic | earthquake, tremor, fault line |
| Meteorological | cyclone, hurricane, typhoon, storm |
| Climate | drought, heatwave, wildfire |
| Geophysical | landslide, avalanche, volcanic |

### Exposure Signals
Assets and populations at risk:

| Category | Example Terms |
|----------|---------------|
| Population | census, demographic, inhabitants |
| Infrastructure | buildings, roads, bridges, hospitals |
| Economic | GDP, assets, property values |
| Agricultural | crops, livestock, farmland |

### Vulnerability Signals
Susceptibility factors:

| Category | Example Terms |
|----------|---------------|
| Socioeconomic | poverty, inequality, income |
| Capacity | coping, resilience, preparedness |
| Physical | building quality, age, materials |
| Social | education, health, access |

### Loss Signals
Historical and projected impacts:

| Category | Example Terms |
|----------|---------------|
| Human | casualties, fatalities, injuries |
| Economic | damage, losses, costs |
| Physical | destroyed, damaged, affected |
| Disruption | displacement, evacuation |

---

## Key Functions

### `SignalAnalyzer`
Scans metadata for HEVL signals.

```python
analyzer = SignalAnalyzer()
signals = analyzer.analyze(dataset_json)
# signals.hazard: List[SignalMatch]
# signals.exposure: List[SignalMatch]
# signals.vulnerability: List[SignalMatch]
# signals.loss: List[SignalMatch]
```

### `build_signal_dictionary()`
Generates the comprehensive signal dictionary.

```python
dictionary = build_signal_dictionary(datasets, min_frequency=5)
# Returns structured YAML-compatible dict
```

---

## Signal Dictionary Structure

```yaml
# config/signal_dictionary.yaml
hazard:
  flood:
    terms: ["flood", "flooding", "inundation"]
    patterns: ["flood\\s+risk", "flood\\s+map"]
    weight: 0.9
  earthquake:
    terms: ["earthquake", "seismic", "tremor"]
    patterns: ["magnitude\\s+\\d", "richter"]
    weight: 0.9

exposure:
  population:
    terms: ["population", "census", "inhabitants"]
    patterns: ["pop\\s+density", "demographic"]
    weight: 0.85
  buildings:
    terms: ["buildings", "structures", "houses"]
    patterns: ["building\\s+footprint"]
    weight: 0.8
```

---

## Analysis Metrics

The notebook produces statistics on signal coverage:

```
=== HEVL SIGNAL COVERAGE ===

Total datasets analyzed: 26,246

Hazard signals:
  - Datasets with signals: 3,624 (13.8%)
  - Most common: flood (45%), earthquake (18%), cyclone (12%)

Exposure signals:
  - Datasets with signals: 19,742 (75.2%)
  - Most common: population (52%), buildings (23%), infrastructure (15%)

Vulnerability signals:
  - Datasets with signals: 2,156 (8.2%)
  - Most common: poverty (38%), vulnerability index (25%)

Loss signals:
  - Datasets with signals: 1,843 (7.0%)
  - Most common: damage (42%), casualties (28%), economic loss (18%)
```

---

## How It Works

```
1. Load all dataset metadata
2. For each dataset:
   a. Extract text fields (title, description, tags)
   b. Scan for HEVL signal terms
   c. Apply regex patterns
   d. Record signal matches with context
3. Aggregate signal frequency statistics
4. Build signal dictionary with weights based on frequency
5. Export dictionary and reports
```

---

## Tuning Signal Weights

Signal weights should reflect reliability:

| Confidence | Weight | Example |
|------------|--------|---------|
| High | 0.9-1.0 | "flood map", "earthquake" |
| Medium | 0.6-0.8 | "risk assessment", "exposure" |
| Low | 0.3-0.5 | Generic terms like "data", "map" |

---

## Troubleshooting

### Low signal coverage
- Review term lists for missing variations
- Add domain-specific terminology
- Check for non-English datasets

### False positives
- Add exclusion patterns
- Increase weight threshold
- Review context requirements

### Signal overlap
- HEVL categories can overlap (e.g., "flood damage" = hazard + loss)
- This is expected and handled in integration (notebook 12)

---

## Next Steps

After signal analysis:
1. Review signal dictionary for completeness
2. Proceed to component extractors (09-11)
3. Integrate signals in notebook 12

---

[← Previous: Validate & Package](07_validate_package.md) | [Back to README](../README.md) | [Next: Hazard Extractor →](09_hazard_extractor.md)
