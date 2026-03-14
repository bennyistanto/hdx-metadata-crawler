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
| HDX CKAN API | `https://data.humdata.org/api/3/action/package_search` | Dataset listing (paginated) |
| HDX Metadata Export | `https://data.humdata.org/dataset/{id}/download_metadata` | Per-dataset JSON |
| CKAN Fallback | `https://data.humdata.org/api/3/action/package_show` | Fallback if export fails |

---

## Outputs

| Output | Path | Description |
|--------|------|-------------|
| Dataset JSON | `dataset_metadata/{uuid}__{slug}.json` | One file per HDX dataset |
| Manifest | `manifest_datasets.jsonl` | Record of all successful downloads |
| Error Log | `errors_datasets.jsonl` | Failed downloads for retry |

---

## Key Configuration

```python
@dataclass
class CrawlerConfig:
    base_url: str = "https://data.humdata.org"
    rows_per_page: int = 500            # Datasets per API page
    requests_per_second: float = 2.0    # Rate limiting
    max_retries: int = 6                # Retry failed requests
    timeout: int = 60                   # HTTP timeout in seconds
    max_datasets: Optional[int] = None  # None = all, e.g. 100 for testing
    add_slug_to_filename: bool = True   # Human-readable filenames
    slug_max_length: int = 80           # Truncate long slugs
```

---

## Key Functions

### `HDXClient`
HTTP client for HDX API with built-in rate limiting, exponential backoff retries, and bot-check detection.

```python
client = HDXClient(config)

# Low-level GET with retries and rate limiting
data = client.get_json(url, params={...})

# CKAN Action API wrapper (validates success field)
result = client.ckan_action("package_search", q="*:*", rows=500, start=0)
```

### `download_dataset_metadata()`
Downloads metadata for a single dataset. Tries the HDX export endpoint first, then falls back to CKAN `package_show` if the export fails.

```python
meta, source = download_dataset_metadata(dataset_id)
# source is "download_metadata" or "ckan_package_show_fallback"
```

### `run_dataset_crawl()`
Main orchestration function that:
1. Enumerates all datasets via paginated `package_search`
2. Downloads metadata for each dataset (with fallback)
3. Writes manifest and error logs
4. Supports resume from interruption (skips existing files)

---

## How It Works

```
1. Query CKAN API for dataset list (paginated, 500 per page, sorted by id)
2. For each dataset:
   a. Check if file already exists on disk (skip if so)
   b. Try HDX download_metadata endpoint
   c. If that fails, fall back to CKAN package_show
   d. Save to dataset_metadata/{uuid}__{slug}.json (atomic write via temp file)
   e. Append success record to manifest_datasets.jsonl
3. On failure: append error record to errors_datasets.jsonl
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
The client uses exponential backoff and respects `Retry-After` headers. To lower request rate, reduce `requests_per_second` in config:
```python
config = CrawlerConfig(requests_per_second=1.0)  # 1 request per second
```

### Bot-check pages
The client detects bot-check/captcha pages and raises an error. If this happens frequently, reduce the request rate.

### Partial downloads
Check `errors_datasets.jsonl` for failed dataset IDs. Re-run the crawler to retry (existing files are skipped automatically).

---

## Example Output

```
hdx_dataset_metadata_dump/
├── dataset_metadata/
│   ├── 00a1b2c3-d4e5-f6g7-h8i9-j0k1l2m3n4o5__ethiopia-flood-data.json
│   ├── 00b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6__kenya-population-2020.json
│   └── ... (26,244 more files)
├── manifest_datasets.jsonl
└── errors_datasets.jsonl
```

---

[← Back to README](../README.md) | [Next: OSM Exclusion →](02_policy_osm_exclusion.md)
