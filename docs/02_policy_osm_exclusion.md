# 02 - OSM Policy Exclusion

**Notebook:** `notebook/02_rdls_policy_osm_exclusion.ipynb`

---

## Summary

Detects and excludes OpenStreetMap (OSM) derived datasets from the RDLS pipeline to prevent catalog flooding with thousands of similar building/road extracts.

**For Decision Makers:**
> OSM exports (HOTOSM, OpenStreetMap contributors) create thousands of nearly identical metadata records per country. This notebook identifies and excludes them, keeping the RDLS catalog focused on unique risk datasets. A pilot shortlist is also produced for selective future inclusion.

---

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| Dataset JSONs | `dataset_metadata/*.json` | Raw HDX metadata from Step 01 |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Exclusion List | `policy/osm_excluded_dataset_ids.txt` | Dataset IDs to exclude (one per line) |
| Detection Report | `policy/osm_exclusion_report.csv` | Detailed detection results with reasons |
| Pilot Candidates | `policy/osm_candidates_for_pilot.csv` | Small shortlist for future OSM pilot experiments |

---

## Key Configuration

```python
# Fast prefilter: text scan before JSON parse
USE_FAST_PREFILTER = True

# Pilot shortlist limit per org/theme bucket
PILOT_MAX_PER_BUCKET = 10
```

---

## Detection Rules

The detector uses weighted evidence rules organized into strong and supporting signals. A dataset is flagged as OSM if any strong rule fires, or if two or more supporting signals are present.

### Strong Evidence (any one triggers exclusion)

| Rule | Signal | What it checks |
|------|--------|----------------|
| `dataset_source_mentions_openstreetmap` | dataset_source | "openstreetmap" in dataset_source field |
| `odbl_license_plus_osm_cue` | License + OSM cue | ODbL license AND "openstreetmap" appears in title, notes, or dataset_source |
| `resource_url_osm_domain` | Resource URLs | Download URLs containing openstreetmap.org, hotosm.org, export.hotosm.org, etc. |
| `tag_openstreetmap_present` | Tags | "openstreetmap" tag present |

### Supporting Evidence (2+ triggers exclusion)

| Rule | Signal | What it checks |
|------|--------|----------------|
| `organization_mentions_osm_or_hot` | Organization | Org name contains "hotosm", "openstreetmap", or "humanitarian openstreetmap" |
| `title_mentions_osm_export` | Title | Title contains "openstreetmap export" or similar |
| `notes_mentions_openstreetmap` | Notes/Description | Notes field references OpenStreetMap |

---

## Key Functions

### `prefilter_maybe_osm()`
Fast text scan that checks raw JSON text for OSM markers before parsing. Skips datasets with no OSM indicators, reducing processing time.

```python
if USE_FAST_PREFILTER and not prefilter_maybe_osm(raw_text):
    continue  # Skip JSON parsing entirely
```

### `detect_osm()`
Analyzes a parsed dataset dict for OSM indicators. Returns an `OSMDetectionResult` dataclass with detection outcome and traceable reasons.

```python
result = detect_osm(dataset_dict)
# result.is_osm: bool
# result.reasons: Tuple[str, ...] - rule IDs that fired
# result.signals: Dict[str, Any] - evidence fields for auditing
```

### `OSMDetectionResult`
Frozen dataclass holding detection results:
```python
@dataclass(frozen=True)
class OSMDetectionResult:
    is_osm: bool
    reasons: Tuple[str, ...]
    signals: Dict[str, Any]
```

---

## How It Works

```
1. Load all dataset JSON files from dataset_metadata/
2. For each file:
   a. (Optional) Fast prefilter: scan raw text for OSM markers, skip if none found
   b. Parse JSON and normalize record shape
   c. Run detect_osm() to check all evidence rules
   d. If flagged: add dataset ID to exclusion list, add row to report
3. Deduplicate and sort exclusion IDs
4. Write exclusion list, report CSV, and pilot shortlist
```

---

## Example Detection

**Input dataset:**
```json
{
  "organization": {"title": "HOTOSM"},
  "license_title": "Open Database License (ODbL)",
  "dataset_source": "OpenStreetMap contributors",
  "tags": [{"name": "buildings"}, {"name": "openstreetmap"}]
}
```

**Detection result:**
```
is_osm: True
reasons: ("dataset_source_mentions_openstreetmap", "odbl_license_plus_osm_cue",
          "organization_mentions_osm_or_hot", "tag_openstreetmap_present")
```

---

## Statistics (Actual Run)

| Metric | Value |
|--------|-------|
| Total datasets scanned | 26,246 |
| OSM-derived excluded | 3,649 |
| Retained (non-OSM) | 22,597 |
| Pilot candidates | 138 |
| Detection rate | ~14% |

---

## Troubleshooting

### False positives
If legitimate datasets are being excluded:
1. Check `osm_exclusion_report.csv` for the specific dataset and its `reasons` column
2. Review the detection rules in the notebook -- strong evidence rules trigger independently
3. Consider adjusting the `SUPPORTING_EVIDENCE_THRESHOLD` (default: 2)

### False negatives
If OSM datasets slip through:
1. Review detection patterns and URL markers in the notebook
2. Add new organization or source patterns to the marker lists
3. Check if the dataset uses unusual metadata fields

---

## Why Exclude OSM?

1. **Volume:** ~3,649 OSM exports would dilute the catalog
2. **Redundancy:** Same building/road data repeated per country
3. **Focus:** RDLS targets unique risk assessment data
4. **Quality:** OSM metadata lacks risk-specific attributes

A controlled OSM pilot path exists (via `osm_candidates_for_pilot.csv`) for selective inclusion when needed.

---

[← Previous: HDX Crawler](01_hdx_metadata_crawler.md) | [Back to README](../README.md) | [Next: Define Mapping →](03_define_mapping.md)
