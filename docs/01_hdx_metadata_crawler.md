# 01 - HDX Metadata Crawler

**Notebook:** `notebook/01_rdls_hdx_metadata_crawler.ipynb`

---

## Summary

Crawls the entire HDX (Humanitarian Data Exchange) catalogue via CKAN API and downloads dataset-level metadata JSON for each dataset.

**For Decision Makers:**
> This notebook fetches the raw data from HDX that feeds the entire pipeline. It's a one-time bulk download that takes 4-6 hours for the full catalogue (~26,000 datasets).

---

## Inputs

| Input | Source | Description |
|-------|--------|-------------|
| HDX CKAN API | `https://data.humdata.org/api/3/action/package_search` | Dataset listing |
| HDX Metadata API | `https://data.humdata.org/dataset/{id}/download_metadata` | Per-dataset JSON |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Dataset JSON | `dataset_metadata/{uuid}__{slug}.json` | One file per HDX dataset |
| Manifest | `manifest_{timestamp}.jsonl` | Record of all downloads |
| Error Log | `errors_{timestamp}.jsonl` | Failed downloads for retry |

---

## Key Configuration

```python
@dataclass
class CrawlerConfig:
    max_datasets: Optional[int] = None  # None = all, 100 = test run
    skip_existing: bool = True          # Resume-safe
    rate_limit_delay: float = 0.5       # Seconds between requests
    max_retries: int = 3                # Retry failed requests
    download_resources: bool = False    # Also fetch resource-level metadata
```

---

## Key Functions

### `HDXClient`
Handles all HDX API interactions with rate limiting and retry logic.

```python
client = HDXClient(config)
datasets = client.search_datasets(rows=1000, start=0)
metadata = client.download_dataset_metadata(dataset_id)
```

### `crawl_all_datasets()`
Main orchestration function that:
1. Enumerates all datasets via paginated search
2. Downloads metadata for each dataset
3. Writes manifest and error logs
4. Supports resume from interruption

---

## How It Works

```
1. Query HDX API for dataset list (paginated, 1000 per page)
2. For each dataset:
   a. Check if already downloaded (skip if exists)
   b. Fetch metadata JSON
   c. Save to dataset_metadata/{uuid}__{slug}.json
   d. Log to manifest
3. Write error log for any failures
```

---

## Runtime Estimates

| Scope | Datasets | Time | Disk Space |
|-------|----------|------|------------|
| Test | 100 | 2 min | 20 MB |
| Medium | 1,000 | 15 min | 200 MB |
| Full | 26,246 | 4-6 hours | 5 GB |

---

## Troubleshooting

### Network timeout
The crawler is resume-safe. Simply re-run the notebook - it will skip already downloaded files.

### Rate limiting (429 errors)
Increase `rate_limit_delay` in config:
```python
config = CrawlerConfig(rate_limit_delay=1.0)  # 1 second between requests
```

### Partial downloads
Check `errors_*.jsonl` for failed dataset IDs. Re-run the crawler to retry.

---

## Example Output

```
dataset_metadata/
├── 00a1b2c3-d4e5-f6g7-h8i9-j0k1l2m3n4o5__ethiopia-flood-data.json
├── 00b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6__kenya-population-2020.json
└── ... (26,244 more files)

manifest_20250115_143022.jsonl
errors_20250115_143022.jsonl
```

---

[← Back to README](../README.md) | [Next: OSM Exclusion →](02_policy_osm_exclusion.md)
