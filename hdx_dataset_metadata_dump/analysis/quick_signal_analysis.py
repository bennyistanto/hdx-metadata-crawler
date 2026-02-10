#!/usr/bin/env python3
"""
HDX HEVL Signal Extraction Script
Extracts Hazard, Exposure, Vulnerability, and Loss (HEVL) signals from HDX metadata.
"""

import json
import os
import re
from collections import defaultdict
from pathlib import Path
import time

# Configuration
METADATA_DIR = Path(r"C:/Users/benny/OneDrive/Documents/Github/hdx-metadata-crawler/hdx_dataset_metadata_dump/dataset_metadata")
OUTPUT_FILE = Path(r"C:/Users/benny/OneDrive/Documents/Github/hdx-metadata-crawler/hdx_dataset_metadata_dump/analysis/signal_analysis_results.json")

# Regex patterns for signal extraction
PATTERNS = {
    "hazards": {
        "flood": re.compile(r'\bflood(?:ing|s|ed)?\b', re.IGNORECASE),
        "earthquake": re.compile(r'\bearthquake(?:s)?\b', re.IGNORECASE),
        "tsunami": re.compile(r'\btsunami(?:s)?\b', re.IGNORECASE),
        "cyclone": re.compile(r'\bcyclone(?:s)?|hurricane(?:s)?|typhoon(?:s)?\b', re.IGNORECASE),
        "drought": re.compile(r'\bdrought(?:s)?\b', re.IGNORECASE),
        "wildfire": re.compile(r'\bwildfire(?:s)?|forest\s*fire(?:s)?|bushfire(?:s)?\b', re.IGNORECASE),
        "landslide": re.compile(r'\blandslide(?:s)?|mudslide(?:s)?|mudflow(?:s)?\b', re.IGNORECASE),
        "volcanic": re.compile(r'\bvolcan(?:o|ic|oes)|eruption(?:s)?\b', re.IGNORECASE),
    },
    "exposure": {
        "building": re.compile(r'\bbuilding(?:s)?|structure(?:s)?|housing|house(?:s)?\b', re.IGNORECASE),
        "infrastructure": re.compile(r'\binfrastructure|road(?:s)?|bridge(?:s)?|hospital(?:s)?|school(?:s)?|facility|facilities\b', re.IGNORECASE),
        "population": re.compile(r'\bpopulation|people|inhabitants|residents|affected\s*(?:population|people)\b', re.IGNORECASE),
        "agriculture": re.compile(r'\bagriculture|agricultural|crop(?:s)?|farmland|livestock|cattle\b', re.IGNORECASE),
    },
    "analysis_type": {
        "probabilistic": re.compile(r'\bprobabilistic|return\s*period|RP\s*\d+|annual\s*exceedance|AEP|AAL|average\s*annual\s*loss\b', re.IGNORECASE),
        "deterministic": re.compile(r'\bdeterministic|scenario\s*based|single\s*event|historical\s*event\b', re.IGNORECASE),
        "empirical": re.compile(r'\bempirical|observed|historical\s*data|recorded|actual\b', re.IGNORECASE),
    }
}

# Pattern for extracting return period values
RETURN_PERIOD_PATTERN = re.compile(r'(?:return\s*period|RP)\s*[:\s]*(\d+)(?:\s*[-]?\s*year)?|(\d+)\s*[-]?\s*year\s*return\s*period', re.IGNORECASE)


def extract_text_from_metadata(metadata):
    """Extract all searchable text from metadata."""
    text_parts = []

    # Main text fields
    text_fields = ['title', 'name', 'notes', 'dataset_source', 'organization',
                   'methodology_other', 'caveats']
    for field in text_fields:
        if field in metadata and metadata[field]:
            text_parts.append(str(metadata[field]))

    # Tags
    if 'tags' in metadata and metadata['tags']:
        text_parts.extend(metadata['tags'])

    # Resources descriptions and names
    if 'resources' in metadata:
        for resource in metadata['resources']:
            if 'description' in resource and resource['description']:
                text_parts.append(resource['description'])
            if 'name' in resource and resource['name']:
                text_parts.append(resource['name'])

    return ' '.join(text_parts)


def extract_return_periods(text):
    """Extract numeric return period values from text."""
    return_periods = set()
    matches = RETURN_PERIOD_PATTERN.findall(text)
    for match in matches:
        # Each match is a tuple from the two groups
        for value in match:
            if value:
                try:
                    rp = int(value)
                    if 1 <= rp <= 10000:  # Reasonable return period range
                        return_periods.add(rp)
                except ValueError:
                    pass
    return list(return_periods)


def analyze_file(file_path):
    """Analyze a single JSON file for HEVL signals."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return None, f"Error reading {file_path}: {e}"

    text = extract_text_from_metadata(metadata)

    signals = {
        "id": metadata.get("id", ""),
        "title": metadata.get("title", ""),
        "hazards": [],
        "exposure": [],
        "analysis_types": [],
        "return_periods": []
    }

    # Check for hazards
    for hazard_type, pattern in PATTERNS["hazards"].items():
        if pattern.search(text):
            signals["hazards"].append(hazard_type)

    # Check for exposure categories
    for exposure_type, pattern in PATTERNS["exposure"].items():
        if pattern.search(text):
            signals["exposure"].append(exposure_type)

    # Check for analysis types
    for analysis_type, pattern in PATTERNS["analysis_type"].items():
        if pattern.search(text):
            signals["analysis_types"].append(analysis_type)

    # Extract return period values
    signals["return_periods"] = extract_return_periods(text)

    return signals, None


def main():
    print("=" * 60)
    print("HDX HEVL Signal Extraction Analysis")
    print("=" * 60)

    start_time = time.time()

    # Get all JSON files
    json_files = list(METADATA_DIR.glob("*.json"))
    total_files = len(json_files)
    print(f"Found {total_files:,} JSON files to analyze")
    print("-" * 60)

    # Results storage
    results = {
        "summary": {
            "total_files": total_files,
            "files_with_hazards": 0,
            "files_with_exposure": 0,
            "files_with_analysis_types": 0,
            "files_with_return_periods": 0,
            "errors": 0,
        },
        "hazard_counts": defaultdict(int),
        "exposure_counts": defaultdict(int),
        "analysis_type_counts": defaultdict(int),
        "return_period_distribution": defaultdict(int),
        "detailed_results": [],
        "errors": []
    }

    # Process files
    for i, file_path in enumerate(json_files):
        # Progress reporting
        if (i + 1) % 5000 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            remaining = (total_files - i - 1) / rate if rate > 0 else 0
            print(f"Progress: {i + 1:,}/{total_files:,} files ({(i+1)/total_files*100:.1f}%) - "
                  f"Elapsed: {elapsed:.1f}s - Est. remaining: {remaining:.1f}s")

        signals, error = analyze_file(file_path)

        if error:
            results["errors"].append(error)
            results["summary"]["errors"] += 1
            continue

        # Update counts
        if signals["hazards"]:
            results["summary"]["files_with_hazards"] += 1
            for h in signals["hazards"]:
                results["hazard_counts"][h] += 1

        if signals["exposure"]:
            results["summary"]["files_with_exposure"] += 1
            for e in signals["exposure"]:
                results["exposure_counts"][e] += 1

        if signals["analysis_types"]:
            results["summary"]["files_with_analysis_types"] += 1
            for a in signals["analysis_types"]:
                results["analysis_type_counts"][a] += 1

        if signals["return_periods"]:
            results["summary"]["files_with_return_periods"] += 1
            for rp in signals["return_periods"]:
                # Group return periods
                if rp <= 10:
                    bucket = "1-10"
                elif rp <= 25:
                    bucket = "11-25"
                elif rp <= 50:
                    bucket = "26-50"
                elif rp <= 100:
                    bucket = "51-100"
                elif rp <= 250:
                    bucket = "101-250"
                elif rp <= 500:
                    bucket = "251-500"
                elif rp <= 1000:
                    bucket = "501-1000"
                else:
                    bucket = "1000+"
                results["return_period_distribution"][bucket] += 1

        # Store detailed results only for files with any signals
        if signals["hazards"] or signals["analysis_types"] or signals["return_periods"]:
            results["detailed_results"].append({
                "id": signals["id"],
                "title": signals["title"],
                "hazards": signals["hazards"],
                "exposure": signals["exposure"],
                "analysis_types": signals["analysis_types"],
                "return_periods": signals["return_periods"]
            })

    # Convert defaultdicts to regular dicts for JSON serialization
    results["hazard_counts"] = dict(results["hazard_counts"])
    results["exposure_counts"] = dict(results["exposure_counts"])
    results["analysis_type_counts"] = dict(results["analysis_type_counts"])
    results["return_period_distribution"] = dict(results["return_period_distribution"])

    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    results["summary"]["processing_time_seconds"] = round(elapsed_time, 2)

    # Print summary
    print("-" * 60)
    print(f"Analysis complete in {elapsed_time:.2f} seconds")
    print("-" * 60)
    print("\nSUMMARY:")
    print(f"  Total files analyzed: {total_files:,}")
    print(f"  Files with hazard signals: {results['summary']['files_with_hazards']:,}")
    print(f"  Files with exposure signals: {results['summary']['files_with_exposure']:,}")
    print(f"  Files with analysis type signals: {results['summary']['files_with_analysis_types']:,}")
    print(f"  Files with return periods: {results['summary']['files_with_return_periods']:,}")
    print(f"  Errors: {results['summary']['errors']:,}")

    print("\nHAZARD COUNTS:")
    for hazard, count in sorted(results["hazard_counts"].items(), key=lambda x: -x[1]):
        print(f"  {hazard}: {count:,}")

    print("\nEXPOSURE COUNTS:")
    for exposure, count in sorted(results["exposure_counts"].items(), key=lambda x: -x[1]):
        print(f"  {exposure}: {count:,}")

    print("\nANALYSIS TYPE COUNTS:")
    for atype, count in sorted(results["analysis_type_counts"].items(), key=lambda x: -x[1]):
        print(f"  {atype}: {count:,}")

    print("\nRETURN PERIOD DISTRIBUTION:")
    period_order = ["1-10", "11-25", "26-50", "51-100", "101-250", "251-500", "501-1000", "1000+"]
    for bucket in period_order:
        if bucket in results["return_period_distribution"]:
            print(f"  {bucket} years: {results['return_period_distribution'][bucket]:,}")

    # Save results
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
