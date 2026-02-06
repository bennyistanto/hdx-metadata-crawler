# 02 - OSM Policy Exclusion

**Notebook:** `notebook/02_rdls_policy_osm_exclusion.ipynb`

---

## Summary

Detects and excludes OpenStreetMap (OSM) derived datasets from the RDLS pipeline to prevent catalog flooding with thousands of similar building/road extracts.

**For Decision Makers:**
> OSM exports (HOTOSM, OpenStreetMap contributors) create thousands of nearly identical metadata records per country. This notebook identifies and excludes them, keeping the RDLS catalog focused on unique risk datasets.

---

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| Dataset JSONs | `dataset_metadata/*.json` | Raw HDX metadata from Step 01 |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Exclusion List | `policy/osm_excluded_dataset_ids.txt` | Dataset IDs to exclude |
| Detection Report | `policy/osm_detection_report.csv` | Detailed detection results |

---

## Key Configuration

```python
@dataclass
class OSMDetectionConfig:
    check_organization: bool = True    # Check org name for OSM indicators
    check_license: bool = True         # Check for ODbL license
    check_source: bool = True          # Check dataset_source field
    check_tags: bool = True            # Check for OSM-related tags
    confidence_threshold: float = 0.6  # Minimum confidence to exclude
```

---

## Detection Rules

The detector uses multiple signals with weighted scoring:

| Signal | Weight | Examples |
|--------|--------|----------|
| Organization | 0.4 | "HOTOSM", "OpenStreetMap" |
| License | 0.3 | "ODbL", "Open Database License" |
| Source URL | 0.2 | "openstreetmap.org", "hotosm" |
| Tags | 0.1 | "openstreetmap", "osm", "hotosm" |

**Threshold:** Dataset excluded if combined score ≥ 0.6

---

## Key Functions

### `OSMDetector`
Analyzes dataset metadata for OSM indicators.

```python
detector = OSMDetector(config)
result = detector.detect(dataset_json)
# result.is_osm: bool
# result.confidence: float
# result.signals: List[str]
```

### `detect_osm_signals()`
Returns detailed signal breakdown:
```python
{
    "org_match": True,
    "license_match": True,
    "source_match": False,
    "tag_match": True,
    "confidence": 0.8
}
```

---

## How It Works

```
1. Load all dataset JSON files
2. For each dataset:
   a. Check organization name for OSM patterns
   b. Check license for ODbL
   c. Check dataset_source for OSM URLs
   d. Check tags for OSM keywords
   e. Compute weighted confidence score
3. If confidence ≥ threshold: add to exclusion list
4. Write exclusion list and report
```

---

## Example Detection

**Input dataset:**
```json
{
  "organization": "HOTOSM",
  "license_title": "Open Database License (ODbL)",
  "dataset_source": "OpenStreetMap contributors",
  "tags": ["buildings", "openstreetmap", "hotosm"]
}
```

**Detection result:**
```
is_osm: True
confidence: 0.95
signals: ["org:HOTOSM", "license:ODbL", "source:openstreetmap", "tag:openstreetmap"]
```

---

## Statistics (Typical Run)

| Metric | Value |
|--------|-------|
| Total datasets | 26,246 |
| OSM detected | ~15,000 |
| Retained | ~11,000 |
| Detection rate | ~57% |

---

## Troubleshooting

### False positives
If legitimate datasets are being excluded:
1. Check `osm_detection_report.csv` for the specific dataset
2. Adjust confidence threshold or disable specific checks
3. Consider adding to `config/overrides.yaml` to force inclusion

### False negatives
If OSM datasets slip through:
1. Review detection patterns in the notebook
2. Add new organization or source patterns
3. Lower the confidence threshold

---

## Why Exclude OSM?

1. **Volume:** ~15,000 OSM exports would dominate the catalog
2. **Redundancy:** Same building/road data repeated per country
3. **Focus:** RDLS targets unique risk assessment data
4. **Quality:** OSM metadata lacks risk-specific attributes

A controlled OSM pilot path exists for selective inclusion when needed.

---

[← Previous: HDX Crawler](01_hdx_metadata_crawler.md) | [Back to README](../README.md) | [Next: Define Mapping →](03_define_mapping.md)
