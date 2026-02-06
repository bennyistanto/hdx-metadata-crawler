# 09 - Hazard Block Extractor

**Notebook:** `notebook/09_rdls_hazard_block_extractor.ipynb`

---

## Summary

Extracts detailed hazard information from HDX datasets to populate RDLS hazard metadata blocks.

**For Decision Makers:**
> This notebook identifies specific hazard types (flood, earthquake, cyclone, etc.) and extracts detailed attributes like intensity measures, return periods, and geographic scope.

---

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| Dataset JSONs | `dataset_metadata/*.json` | Raw HDX metadata |
| Signal dictionary | `config/signal_dictionary.yaml` | From Step 08 |
| Classification | `derived/classification_final.csv` | From Step 05 |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Hazard extracts | `analysis/hazard_extracts.csv` | Per-dataset hazard info |
| Hazard summary | `analysis/hazard_summary.json` | Aggregate statistics |

---

## RDLS Hazard Types

The extractor identifies these RDLS-defined hazard types:

| Category | Hazard Types |
|----------|--------------|
| **Hydrological** | flood, coastal_flood, flash_flood |
| **Meteorological** | cyclone, storm, extreme_temperature |
| **Climatological** | drought, wildfire, extreme_precipitation |
| **Geophysical** | earthquake, tsunami, volcanic, landslide |
| **Biological** | epidemic, infestation |
| **Technological** | industrial, transport, infrastructure |

---

## Hazard Attributes Extracted

| Attribute | Description | Example |
|-----------|-------------|---------|
| `hazard_type` | RDLS hazard enum | "flood" |
| `intensity_measure` | How hazard is measured | "depth_m", "magnitude" |
| `return_period` | Frequency estimate | "100-year" |
| `scenario` | Modeling scenario | "historical", "RCP8.5" |
| `temporal_coverage` | Time range | "1990-2020" |

---

## Key Functions

### `HazardExtractor`
Main extraction class.

```python
extractor = HazardExtractor(signal_dictionary)
hazard_info = extractor.extract(dataset_json)
# hazard_info.hazard_type: str
# hazard_info.intensity_measure: Optional[str]
# hazard_info.return_period: Optional[str]
# hazard_info.confidence: float
```

### `infer_hazard_type()`
Maps text signals to RDLS hazard enum.

```python
hazard_type = infer_hazard_type(
    tags=["flood", "risk"],
    title="Kenya Flood Hazard Map",
    description="100-year return period flood depths"
)
# Returns: "flood"
```

### `extract_intensity_measure()`
Identifies measurement units from text.

```python
measure = extract_intensity_measure("Flood depth in meters")
# Returns: "depth_m"
```

---

## Hazard Type Inference Rules

| Signal Pattern | Inferred Type |
|----------------|---------------|
| flood, inundation, river overflow | flood |
| coastal flood, storm surge, sea level | coastal_flood |
| earthquake, seismic, tremor, magnitude | earthquake |
| cyclone, hurricane, typhoon, tropical storm | cyclone |
| drought, dry spell, water scarcity | drought |
| wildfire, bushfire, forest fire | wildfire |
| landslide, mudslide, debris flow | landslide |
| tsunami, tidal wave | tsunami |

---

## Intensity Measures

| Hazard Type | Common Measures |
|-------------|-----------------|
| flood | depth_m, velocity_m_s, duration_hr |
| earthquake | magnitude, pga_g, intensity_mmi |
| cyclone | wind_speed_kmh, pressure_hpa |
| drought | spi, pdsi, rainfall_deficit_mm |
| wildfire | intensity_kw_m, spread_rate |

---

## Statistics (Typical Run)

```
=== HAZARD EXTRACTION SUMMARY ===

Datasets with hazard signals: 3,624

Hazard type distribution:
  - flood: 1,631 (45.0%)
  - earthquake: 653 (18.0%)
  - cyclone: 435 (12.0%)
  - drought: 362 (10.0%)
  - landslide: 217 (6.0%)
  - wildfire: 145 (4.0%)
  - other: 181 (5.0%)

Attributes extracted:
  - With intensity measure: 892 (24.6%)
  - With return period: 543 (15.0%)
  - With scenario: 328 (9.0%)
```

---

## How It Works

```
1. Load datasets classified as hazard
2. For each dataset:
   a. Scan for hazard type signals
   b. Extract intensity measure if mentioned
   c. Look for return period patterns
   d. Identify scenario/modeling info
   e. Compute extraction confidence
3. Aggregate by hazard type
4. Export extracts and summary
```

---

## Pattern Examples

### Return Period Detection
```python
patterns = [
    r"(\d+)[-\s]?year",           # "100-year flood"
    r"(\d+)[-\s]?yr",             # "100yr return"
    r"return period[:\s]+(\d+)",  # "return period: 100"
    r"T(\d+)",                    # "T100 flood"
]
```

### Intensity Detection
```python
patterns = [
    r"depth[:\s]+(\d+\.?\d*)\s*m",     # "depth: 2.5 m"
    r"magnitude[:\s]+(\d+\.?\d*)",      # "magnitude: 6.5"
    r"wind[:\s]+(\d+)\s*km",            # "wind: 150 km/h"
]
```

---

## Troubleshooting

### Missing hazard type
- Check signal dictionary for term coverage
- Review dataset tags and description
- Consider manual classification via overrides

### Wrong hazard type
- Review inference rules
- Check for conflicting signals
- Multi-hazard datasets may need disambiguation

### Low extraction rate
- Many HDX datasets lack detailed hazard attributes
- Focus on well-structured datasets (e.g., from UNDRR, WFP)
- Extraction rate of 20-30% for detailed attributes is normal

---

[← Previous: Signal Analysis](08_signal_analysis.md) | [Back to README](../README.md) | [Next: Exposure Extractor →](10_exposure_extractor.md)
