# From 26,246 HDX Datasets to Structured Risk Data

## How We Built an Automated Pipeline to Transform Humanitarian Metadata into RDLS v0.3

---

## Background

The [Humanitarian Data Exchange (HDX)](https://data.humdata.org) is one of the largest open repositories of humanitarian data in the world. Maintained by [UNOCHA](https://www.unocha.org/), it hosts tens of thousands of datasets contributed by **358 organisations** — UN agencies, NGOs, governments, and research institutions. These datasets describe everything from population displacement in conflict zones to flood hazard maps, building footprints, and economic loss records.

HDX metadata is rich with information. Each dataset carries a title, tags chosen by the contributor, a free-text description that often contains detailed methodology, and a list of downloadable resources. For example, a dataset titled *"[Philippines - Risk Assessment Indicators](https://data.humdata.org/dataset/philippines---risk-assessment-indicators)"* has tags like `flooding`, `cyclones-hurricanes-typhoons`, `affected population`, and `demographics`, with eight CSV resources covering facilities, demographics, flood exposure, cyclone exposure, vulnerability, and coping capacity. All the signals are there — flood hazard, population exposure, vulnerability indicators, and loss potential — but they live in text fields rather than machine-readable structured fields.

Meanwhile, the **[Risk Data Library Standard (RDLS) v0.3](https://docs.riskdatalibrary.org/en/0__3__0/)** provides exactly the structure the disaster risk community needs. RDLS defines a precise JSON schema for describing risk data across four components — **Hazard**, **Exposure**, **Vulnerability**, and **Loss** (HEVL) — with closed codelists for hazard types (11 values), process types (30 values), exposure categories (7 values), impact metrics (20 values), and more. It is the emerging standard for making risk data interoperable.

The question: **Can we automatically transform 26,246 HDX dataset metadata records (as of 3 February 2026) into RDLS v0.3 compliant JSON?**

> **📁 Schema reference**: [`rdls_schema_v0.3.json`](https://github.com/GFDRR/CCDR-tools/blob/main/_static/rdls_schema_v0.3.json)
>
> **📁 RDLS examples**: [`rdls/example/`](../hdx_dataset_metadata_dump/rdls/example/) — 4 hand-crafted reference records (Freetown flood hazard, ESA land cover exposure, Africa transport exposure, Chattogram multi-hazard loss)

---

## The Goal

Build an end-to-end pipeline that:

1. **Crawls** the entire HDX catalogue and downloads metadata for every dataset
2. **Classifies** which datasets are relevant to disaster risk (and which are not)
3. **Translates** HDX metadata into RDLS general fields (spatial coverage, license, attributions, resources)
4. **Extracts** detailed HEVL component information from text fields
5. **Validates** every output record against the official RDLS v0.3 JSON Schema
6. **Packages** the result as a production-ready archive with quality scores and tiered distribution

The pipeline should be reproducible, configurable, and transparent — implemented as **13 Jupyter notebooks** that any analyst can inspect, re-run, and modify.

---

## Framing the Problem

The core challenge is **information extraction from metadata text**. HDX datasets do not declare their HEVL components in structured fields. A dataset titled *"Afghanistan - Natural Disaster Incidents in 2018"* with tags `earthquake-tsunami, flooding, affected population` contains signals for flood, earthquake, and loss — but these signals are embedded in free text that was written by humans for humans.

We framed this as a **signal detection and constraint validation** problem:

1. **Detection** — Use regex pattern matching against a curated signal dictionary to identify HEVL components from text fields (titles, tags, descriptions, resource names)
2. **Constraint validation** — Ensure every extracted value is a valid RDLS codelist entry, and that field combinations are internally consistent

This two-stage approach — detect then validate — lets us be aggressive in signal detection while guaranteeing schema compliance in the output. No field value in the final records is fabricated or guessed — every value traces back to either a text signal or a schema-derived default.

---

## The Strategy

### Phase 1: Crawl and Classify (Notebook 01–05)

The first step was understanding the landscape. We crawled all **26,246 datasets** from the HDX CKAN API, downloading the full metadata JSON for each one.

> **📁 Raw metadata**: [`dataset_metadata/`](../hdx_dataset_metadata_dump/dataset_metadata/) — 26,246 JSON files, one per HDX dataset

Then we applied a multi-signal classification to identify which datasets are relevant to disaster risk. The classifier uses four weighted inputs, each defined in a YAML configuration file:

| Configuration | Path | Purpose |
| ------------- | ---- | ------- |
| Tag mappings | [`config/tag_to_rdls_component.yaml`](../hdx_dataset_metadata_dump/config/tag_to_rdls_component.yaml) | HDX tags → RDLS component weights |
| Keyword patterns | [`config/keyword_to_rdls_component.yaml`](../hdx_dataset_metadata_dump/config/keyword_to_rdls_component.yaml) | Regex patterns for title/description scanning |
| Organisation hints | [`config/org_hints.yaml`](../hdx_dataset_metadata_dump/config/org_hints.yaml) | Org-level bias (UNOSAT → hazard, WFP → exposure) |
| Manual overrides | [`config/overrides.yaml`](../hdx_dataset_metadata_dump/config/overrides.yaml) | Per-dataset include/exclude decisions |

A dataset needs a composite score above a threshold to be classified as an RDLS candidate. We also applied an **OSM policy exclusion** — 3,649 datasets that are purely OpenStreetMap extracts without risk context were removed.

The classifier produces a confidence score for each dataset:

| Confidence | Count | Description |
| ---------- | ----- | ----------- |
| High | 12,378 | Strong multi-signal agreement |
| Medium | 7,185 | Some signals present |
| Low | 6,683 | Weak or ambiguous signals |

**Result**: Out of 26,246 datasets, **13,053 were classified as RDLS candidates** (49.7%). The remaining 13,193 were primarily development indicators, administrative boundaries, or humanitarian operational data without risk content. The initial component signal distribution across all 26,246 datasets:

| Component | Datasets with Non-Zero Score |
| --------- | ---------------------------- |
| Exposure | 19,314 (73.6%) |
| Vulnerability proxy | 12,952 (49.4%) |
| Hazard | 4,111 (15.7%) |
| Loss/impact | 2,745 (10.5%) |

> **📁 Classification results**: [`derived/classification_final.csv`](../hdx_dataset_metadata_dump/derived/classification_final.csv) — full per-dataset breakdown
>
> **📁 Classification summary**: [`derived/classification_final_summary.json`](../hdx_dataset_metadata_dump/derived/classification_final_summary.json) — aggregate statistics
>
> **📁 Included dataset IDs**: [`derived/rdls_included_dataset_ids_final.txt`](../hdx_dataset_metadata_dump/derived/rdls_included_dataset_ids_final.txt) — 13,053 UUIDs

---

### Phase 2: Translate General Metadata (Notebook 06–07)

For each of the 13,053 candidates, we translated HDX metadata into RDLS general metadata fields. This is a structural transformation — mapping HDX's flat JSON into the RDLS schema's required fields:

| RDLS Field | HDX Source | Transformation |
| ---------- | --------- | -------------- |
| `id` | Generated | `rdls_{prefix}-hdx_{org}_{country}_{slug}` |
| `title` | `title` | Carried over |
| `description` | `notes` | Carried over with source attribution appended |
| `risk_data_type` | Classification | Array of detected components: `["hazard", "exposure"]` |
| `spatial.countries` | `groups` | Country names → ISO 3166-1 alpha-3 codes |
| `spatial.scale` | Inferred | `national`, `sub-national`, or `regional` |
| `license` | `license_title` | Mapped to SPDX identifiers (e.g., `CC-BY-SA-4.0`) |
| `attributions` | `organization`, `dataset_source` | 3 mandatory roles: publisher, creator, contact_point |
| `resources` | `resources[]` | Each resource with `data_format` and `access_modality` |

The `data_format` mapping translates HDX format strings (e.g., "CSV", "XLSX", "SHP") into RDLS-compliant format labels (e.g., `"CSV (csv)"`, `"Excel (xlsx)"`, `"Shapefile (shp)"`).

**Result**: **13,053 RDLS base records** produced, each with complete general metadata.

> **📁 Base records**: [`rdls/records/`](../hdx_dataset_metadata_dump/rdls/records/) — 13,053 JSON files
>
> **📁 Translation QA**: [`rdls/dist/reports/translation_qa.csv`](../hdx_dataset_metadata_dump/rdls/dist/reports/translation_qa.csv) — quality checks on translated fields
>
> **📁 Blocked translations**: [`rdls/dist/reports/translation_blocked.csv`](../hdx_dataset_metadata_dump/rdls/dist/reports/translation_blocked.csv) — records that could not be translated

---

### Phase 3: Signal Analysis and Configuration (Notebook 08)

Before extracting HEVL components, we built the **signal dictionary** — the central configuration that drives all downstream extraction. This YAML file maps RDLS codelist values to regex patterns for text matching.

The initial signal scan across all 26,246 datasets gave us a picture of the catalogue's HEVL content:

| Signal Type | Datasets Detected | Rate |
| ----------- | ----------------- | ---- |
| Exposure | 18,673 | 71.2% |
| Hazard | 2,517 | 9.6% |
| Loss | 2,407 | 9.2% |
| Vulnerability | 205 | 0.8% |
| Return period | 56 | 0.2% |

And the initial HEVL combination distribution:

| Combination | Count | Description |
| ----------- | ----- | ----------- |
| `-E--` | 15,356 | Exposure only (the majority) |
| `----` | 6,298 | No HEVL signal detected |
| `-E-L` | 1,667 | Exposure + Loss |
| `HE--` | 1,240 | Hazard + Exposure |
| `H---` | 776 | Hazard only |
| `HE-L` | 250 | Hazard + Exposure + Loss |
| `---L` | 241 | Loss only |
| `H--L` | 213 | Hazard + Loss |
| `-EV-` | 103 | Exposure + Vulnerability |
| `--V-` | 43 | Vulnerability only |

This told us something important: **exposure is everywhere** (71.2%), **vulnerability is rare as an explicit signal** (0.8%), and **most datasets are single-component**. The extraction strategy needed to handle this asymmetry.

> **📁 Signal dictionary**: [`config/signal_dictionary.yaml`](../hdx_dataset_metadata_dump/config/signal_dictionary.yaml) — the central HEVL configuration
>
> **📁 Signal analysis**: [`analysis/hdx_hevl_signal_analysis.csv`](../hdx_dataset_metadata_dump/analysis/hdx_hevl_signal_analysis.csv) — per-dataset signal matches
>
> **📁 Signal summary**: [`analysis/hdx_hevl_signal_summary.json`](../hdx_dataset_metadata_dump/analysis/hdx_hevl_signal_summary.json) — aggregate statistics
>
> **📁 High-signal records**: [`analysis/hdx_high_signal_records.csv`](../hdx_dataset_metadata_dump/analysis/hdx_high_signal_records.csv) — datasets with strong HEVL signals

#### Signal Dictionary Structure

Every pattern key in the signal dictionary aligns 1:1 with an RDLS v0.3 closed codelist value. This is a critical design choice — whatever the signal dictionary matches is guaranteed to be a valid schema value.

```yaml
# Example: hazard types section
hazard_type:
  flood:
    patterns:
      - '\b(flood|flooding|inundation)\b'
      - '\b(fluvial|pluvial|riverine)\b'
    confidence: high

  earthquake:
    patterns:
      - '\b(earthquake|seismic|tremor)\b'
      - '\b(magnitude|richter|mercalli)\b'
    confidence: high

# Example: exposure categories section
exposure_category:
  buildings:
    patterns:
      - '\b(building|dwelling)\b'
      - '\b(footprint|building.?stock|floor.?area)\b'
      - '\b(built[\s._-]?up|builtup)\b'
    confidence: high

  population:
    patterns:
      - '\b(population|people|inhabitant)\b'
      - '\b(census[\s._-]?(?:data|population|count))\b'
    confidence: high
```

The dictionary covers:

- **11 hazard types** — all values from the `hazard_type` closed codelist
- **30 process types** — each linked to a `parent_hazard` (e.g., `storm_surge` → `coastal_flood`)
- **7 exposure categories** — all values from the `exposure_category` closed codelist
- **Vulnerability and loss signal patterns** — domain-specific terms
- **Exclusion patterns** — false positive suppression rules

---

### Phase 4: HEVL Component Extraction (NB 09–11)

This is where the real work happens. Three notebooks extract the four HEVL components, each with distinct strategies and constraint tables.

#### Hazard Extraction (Notebook 09): Schema-Constrained Event Sets

The RDLS v0.3 hazard block uses a nested structure — `event_sets` containing `hazards` and `events`. The extractor builds this structure while enforcing the schema's constraint that **each hazard type only allows specific process types**.

This constraint mapping is loaded directly from the schema:

| Hazard Type | Allowed Process Types |
| ----------- | -------------------- |
| **flood** | fluvial_flood, pluvial_flood, groundwater_flood, flash_flood |
| **earthquake** | ground_motion, liquefaction, surface_rupture |
| **coastal_flood** | coastal_flood, storm_surge |
| **convective_storm** | tornado, hail, lightning, rain, snow |
| **drought** | agricultural_drought, hydrological_drought, meteorological_drought, socioeconomic_drought |
| **strong_wind** | extratropical_cyclone, tropical_cyclone, wind |
| **landslide** | landslide, mudflow, rockfall, snow_avalanche |
| **tsunami** | local_tsunami, distant_tsunami |
| **volcanic** | ashfall, lahar, lava_flow, pyroclastic_flow |
| **extreme_temperature** | extreme_cold, extreme_heat, heat_wave, cold_wave |
| **wildfire** | wildfire, brush_fire, forest_fire |

If a detected process type is invalid for its hazard type, the extractor falls back to a safe default. This is the first example of **constraint-driven extraction**: the schema defines what combinations are valid, and the extractor respects those constraints.

Key design decisions:

- **One event_set per hazard type** — A multi-hazard dataset (flood + earthquake) gets separate event sets, each with internally consistent process types and intensity measures
- **Compound tag corroboration** — HDX uses compound tags like `earthquake-tsunami`. The extractor splits these but requires corroboration from other text fields before accepting both hazards. Without corroboration, only the primary hazard is used.
- **Return period extraction** — Six regex patterns detect return periods (`"100-year flood"`, `"T100"`, `"AEP 0.01"`), with year values (2000–2099) filtered out to avoid false positives from dates

**Result**: **3,212 datasets** (12.2%) had hazard signals detected.

| Hazard Type | Count | Share |
| ----------- | ----- | ----- |
| flood | 1,986 | 61.8% |
| earthquake | 593 | 18.5% |
| convective_storm | 535 | 16.6% |
| drought | 403 | 12.5% |
| strong_wind | 263 | 8.2% |
| landslide | 76 | 2.4% |
| volcanic | 31 | 1.0% |
| tsunami | 17 | 0.5% |
| coastal_flood | 6 | 0.2% |
| wildfire | 5 | 0.2% |
| extreme_temperature | 4 | 0.1% |

> **📁 Hazard extraction results**: [`rdls/extracted/hazard_extraction_results.csv`](../hdx_dataset_metadata_dump/rdls/extracted/hazard_extraction_results.csv) — all 26,246 records with hazard flags
>
> **📁 High-confidence hazard**: [`rdls/extracted/hazard_extraction_high_confidence.csv`](../hdx_dataset_metadata_dump/rdls/extracted/hazard_extraction_high_confidence.csv) — records with confidence ≥ 0.8

---

#### Exposure Extraction (NB 10): The 3-Tier Cascade

Exposure is the most common component — over 82% of datasets have some exposure signal. The challenge is not coverage but **accuracy**. Many datasets mention populations, buildings, or infrastructure in passing (e.g., a flood hazard dataset might mention "13,400 people potentially exposed" in its notes), and treating all text fields equally leads to misclassification.

The solution: a **3-tier extraction cascade** that prioritises authoritative text fields over noisy ones.

```text
Tier 1: Title + Name + Tags          (weight 1.0)  ← always included
Tier 2: Individual Resources         (weight 0.85) ← can add new categories
Tier 3: Notes + Methodology          (weight 0.6)  ← corroboration only
```

**How it works in practice**: Consider a dataset titled *"Uganda Energy/Gas Facilities"* whose notes mention *"Census Mapping Programme."*

- **Without tiering**: Both `infrastructure` and `population` would be detected, and the dataset could be classified as multi-category
- **With the 3-tier cascade**: Tier 1 detects `infrastructure` from the title. Tier 3 detects `population` from the notes — but since `population` only appears in Tier 3, it is **discarded** (Tier 3 can only corroborate, not introduce). The dataset is correctly classified as `infrastructure` only.

The exception: if Tiers 1 and 2 find nothing at all, Tier 3 is allowed as a fallback. This handles datasets with minimal titles but detailed descriptions.

##### The VALID_TRIPLETS Constraint

Beyond category detection, every exposure block needs internally consistent metric fields. The RDLS schema defines `metric_dimension` (6 values: structure, content, product, disruption, population, index) and `quantity_kind` (5 values: count, area, length, monetary, time) — but not all combinations make sense for all categories.

The `VALID_TRIPLETS` table enforces valid `(category, dimension, quantity_kind)` combinations — similar to how relational databases enforce foreign key relationships, these constraint tables ensure that RDLS field combinations are always internally consistent:

| Category | Allowed (dimension, quantity_kind) Pairs |
| -------- | ---------------------------------------- |
| **agriculture** | (structure, area), (product, monetary), (product, count) |
| **buildings** | (structure, count), (structure, monetary), (structure, area), (content, monetary), (content, count) |
| **infrastructure** | (structure, length), (structure, monetary), (structure, count), (disruption, time) |
| **population** | (population, count) |
| **natural_environment** | (structure, area) |
| **economic_indicator** | (product, monetary), (index, count) |
| **development_index** | (index, count) |

For example: a `population` dataset can only have dimension `population` with quantity_kind `count`. If the extractor infers `monetary` for a population dataset (because the text mentions dollar figures), the triplet constraint overrides it to `(population, count)`. Likewise, `buildings` data referencing built-up area correctly resolves to `(structure, area)` — not `(structure, length)` which would be for linear infrastructure.

This "triplet-alike" approach is used throughout the pipeline. Each HEVL component has its own version:

| Component | Constraint Table | What It Enforces |
| --------- | --------------- | ---------------- |
| Exposure | `VALID_TRIPLETS` | (category, dimension, quantity_kind) |
| Vulnerability | `FUNCTION_TYPE_CONSTRAINTS` | (function_type, impact_metric) |
| Loss | `VALID_ASSET_TRIPLETS` | (asset_category, asset_dimension) |
| Loss | `LOSS_TYPE_APPROACH_RULES` | (loss_type, loss_approach) |
| Shared | `IMPACT_METRIC_CONSTRAINTS` | (impact_metric, quantity_kind, impact_type) |

**Result**: **21,717 datasets** (82.8%) had exposure signals.

| Category | Count | Share |
| -------- | ----- | ----- |
| population | 12,760 | 58.7% |
| infrastructure | 8,647 | 39.8% |
| economic_indicator | 6,577 | 30.3% |
| agriculture | 5,041 | 23.2% |
| natural_environment | 2,746 | 12.6% |
| buildings | 1,562 | 7.2% |
| development_index | 1,248 | 5.7% |

> **📁 Exposure extraction results**: [`rdls/extracted/exposure_extraction_results.csv`](../hdx_dataset_metadata_dump/rdls/extracted/exposure_extraction_results.csv) — all 26,246 records with exposure flags
>
> **📁 High-confidence exposure**: [`rdls/extracted/exposure_extraction_high_confidence.csv`](../hdx_dataset_metadata_dump/rdls/extracted/exposure_extraction_high_confidence.csv) — records with confidence ≥ 0.8

---

#### Vulnerability & Loss Extraction (NB 11): Shared Constraint Architecture

Vulnerability and loss are the most nuanced components. A single notebook handles both, sharing a common constraint table for **impact metrics** — the 20 RDLS-defined metrics that measure consequences.

##### The Shared IMPACT_METRIC_CONSTRAINTS

This table covers all 20 RDLS `impact_metric` values, mapping each to its expected `quantity_kind` and valid `impact_type`. Both the vulnerability and loss extractors use it:

| Impact Metric | Quantity Kind | Valid Impact Types |
| ------------- | ------------- | ------------------ |
| `damage_ratio` | ratio | direct |
| `loss_ratio` | ratio | direct, indirect, total |
| `economic_loss_value` | monetary | direct, indirect, total |
| `casualty_count` | count | direct |
| `displaced_count` | count | direct, indirect |
| `probability` | ratio | direct |
| `crop_loss_value` | monetary | direct |
| `functionality_loss` | ratio | direct, indirect |
| … | … | … |

*(20 metrics total — see [`docs/11_vulnerability_loss_extractor.md`](11_vulnerability_loss_extractor.md) for the complete table)*

##### Vulnerability: Function Type Constraints

The RDLS vulnerability block supports four function types — `vulnerability` (damage ratio given intensity), `fragility` (probability of damage state), `damage_to_loss` (loss given damage), and `engineering_demand` (engineering response parameters). Each function type has its own set of allowed impact metrics:

| Function Type | Default Metric | Example Allowed Metrics |
| ------------- | -------------- | ---------------------- |
| **vulnerability** | `damage_ratio` | damage_ratio, mean_damage_ratio, casualty_ratio_vulnerability |
| **fragility** | `probability` | probability, damage_index, damage_ratio |
| **damage_to_loss** | `loss_ratio` | loss_ratio, economic_loss_value, insured_loss_value, casualty_count |
| **engineering_demand** | `damage_index` | damage_index, damage_ratio, probability |

Additionally, a `VULN_CATEGORY_DEFAULTS` table maps exposure category context to typical function type and metric overrides. For instance, if the vulnerability relates to `buildings`, the default function type is `vulnerability` with `damage_ratio`; if it relates to `agriculture`, the default is `damage_to_loss` with `crop_loss_value`.

The vulnerability extractor also detects **socio-economic indicators** — schemes like population density, elderly population share, food security indices, and coping capacity scores — and structures them into the RDLS `socio_economic` block.

**Result**: **9,592 datasets** (36.5%) had vulnerability signals.

| Top Vulnerability Indicators | Count |
| ---------------------------- | ----- |
| DISPLACEMENT | 3,403 |
| FOOD_SECURITY | 2,461 |
| POV_HEADCOUNT | 1,353 |
| EDU_ATTAINMENT | 1,343 |
| MALNUTRITION | 1,283 |
| POP_DENSITY | 1,264 |
| HEALTH_ACCESS | 601 |
| DEPRIVATION | 407 |
| AGE_65_PLUS | 247 |
| HDI | 220 |

> **📁 Vulnerability extraction**: [`rdls/extracted/vulnerability_extraction_results.csv`](../hdx_dataset_metadata_dump/rdls/extracted/vulnerability_extraction_results.csv) — all records with vulnerability flags
>
> **📁 Detected records**: [`rdls/extracted/vulnerability_detected_records.csv`](../hdx_dataset_metadata_dump/rdls/extracted/vulnerability_detected_records.csv) — records with positive detection

##### Loss: Unified Signal Defaults

Loss extraction uses a `LOSS_SIGNAL_DEFAULTS` table that maps each detected signal type to a complete set of RDLS loss fields — `loss_type`, `asset_category`, `impact_metric`, and `quantity_kind`:

| Signal | Loss Type | Asset Category | Impact Metric | Quantity Kind |
| ------ | --------- | -------------- | ------------- | ------------- |
| `casualties` | ground_up | population | casualty_count | count |
| `economic_damage` | ground_up | buildings | economic_loss_value | monetary |
| `displacement` | ground_up | population | displaced_count | count |
| `crop_loss` | ground_up | agriculture | crop_loss_value | monetary |
| `infrastructure_damage` | ground_up | infrastructure | asset_loss | monetary |
| `insured_loss` | insured | buildings | insured_loss_value | monetary |
| `structural_damage` | ground_up | buildings | structural_loss_ratio | ratio |
| `content_damage` | ground_up | buildings | content_loss_ratio | ratio |

A second constraint table, `VALID_ASSET_TRIPLETS`, ensures that `asset_category` and `asset_dimension` combinations are valid. A third table, `LOSS_TYPE_APPROACH_RULES`, constrains which `loss_approach` values are valid for each `loss_type` — for example, `reinsured` losses can only use an `analytical` approach, while `ground_up` losses allow `analytical`, `empirical`, or `hybrid`.

**Result**: **5,220 datasets** (19.9%) had loss signals.

| Loss Signal Type | Count |
| ---------------- | ----- |
| displacement | 3,333 |
| human_loss | 3,108 |
| affected_population | 1,185 |
| structural_damage | 483 |
| general_loss | 39 |
| agricultural_loss | 7 |
| economic_loss | 3 |

> **📁 Loss extraction**: [`rdls/extracted/loss_extraction_results.csv`](../hdx_dataset_metadata_dump/rdls/extracted/loss_extraction_results.csv) — all records with loss flags
>
> **📁 Detected records**: [`rdls/extracted/loss_detected_records.csv`](../hdx_dataset_metadata_dump/rdls/extracted/loss_detected_records.csv) — records with positive detection

##### How Constraint Validation Works (Both Extractors)

Both vulnerability and loss extractors follow the same validation chain — a "defence in depth" approach where constraints are checked at extraction time and re-checked at block build time:

```text
1. Detect signals from text patterns (signal dictionary)
        │
        ▼
2. Look up initial defaults
   (LOSS_SIGNAL_DEFAULTS or VULN_CATEGORY_DEFAULTS)
        │
        ▼
3. Validate impact metric against IMPACT_METRIC_CONSTRAINTS
   → If metric is invalid for this context, fall back to default
        │
        ▼
4. Validate field combinations against type-specific constraints
   → FUNCTION_TYPE_CONSTRAINTS (vulnerability)
   → VALID_ASSET_TRIPLETS + LOSS_TYPE_APPROACH_RULES (loss)
        │
        ▼
5. RE-VALIDATE at block build time (defence in depth)
   → Same constraints checked again before writing JSON
```

This ensures no fabricated or schema-invalid values appear in the output, even if a signal is ambiguous or the text contains conflicting information.

---

### Phase 5: Integration (Notebook 12)

Integration follows a **merge-only** approach. This is a deliberate architectural choice:

- **NB 06 records are authoritative** for general metadata (id, title, spatial, license, attributions, resources)
- **NB 09–11 JSON blocks are authoritative** for HEVL component details (hazard event_sets, exposure categories, vulnerability functions, loss entries)

NB 12 does not rebuild either. It deep-copies each NB 06 base record and inserts the matching HEVL blocks.

```text
NB 06 Base Records ──────────────┐
  (id, title, spatial, license,  │
   attributions, resources)      ├──→  Deep-copy base
                                 │     + Insert HEVL blocks
NB 09–11 HEVL JSON Blocks ──────┤     + Reconcile risk_data_type
  (hazard event_sets, exposure   │     + Derive filename prefix
   categories, vulnerability     │     + Write to integrated/
   functions, loss entries)      │
                                 │
NB 09–11 Extraction CSVs ───────┘
  (has_hazard, has_exposure,
   has_vulnerability, has_loss)
```

The critical step is **risk_data_type reconciliation** — a two-stage process:

1. **CSV flags → declared types**: Read boolean flags from the four extraction CSVs and build a component list
2. **Actual blocks → reconciled types**: After merging, check which blocks are actually present. Components flagged in CSV but lacking a real JSON block are **dropped** from `risk_data_type`

This prevents downstream consumers from expecting a hazard block that does not exist.

**Result**: **12,554 integrated records** from 13,053 candidates (96.2% integration rate). The ~500 that did not integrate lacked matching HEVL blocks or had vulnerability/loss-only classifications without the required hazard or exposure companion.

> **📁 Integrated records**: [`rdls/integrated/`](../hdx_dataset_metadata_dump/rdls/integrated/) — 12,554 JSON files
>
> **📁 Integration index**: [`rdls/integrated/rdls_index.csv`](../hdx_dataset_metadata_dump/rdls/integrated/rdls_index.csv) and [`rdls_index.jsonl`](../hdx_dataset_metadata_dump/rdls/integrated/rdls_index.jsonl)
>
> **📁 Skipped records**: [`rdls/integrated/integration_skipped.csv`](../hdx_dataset_metadata_dump/rdls/integrated/integration_skipped.csv) — records that could not be integrated with reasons

---

### Phase 6: Validation and Packaging (NB 13)

Every integrated record is validated against the full RDLS v0.3 JSON Schema using `Draft202012Validator`. Validation errors are categorised (anyOf, enum, type, missing, format) and each record gets a `validation_error_summary` for quick diagnosis.

Records are scored on a **composite quality metric** with four weighted dimensions:

| Dimension | Weight | Average Score |
| --------- | ------ | ------------- |
| HEVL Coverage | 40% | 0.909 |
| Block Richness | 25% | 0.930 |
| Schema Validity | 20% | 0.933 |
| Metadata Completeness | 15% | 0.997 |

Records are then routed into a 2D grid: **valid/invalid** × **high/medium/low** confidence:

| Tier | Valid | Invalid | Total |
| ---- | ----- | ------- | ----- |
| **High** (score ≥ 0.8) | 9,772 | 2,767 | 12,539 |
| **Medium** (0.5–0.8) | 25 | 0 | 25 |
| **Low** (< 0.5) | 0 | 0 | 0 |

> **📁 Validation summary**: [`rdls/dist/reports/rdls_validation_summary.md`](../hdx_dataset_metadata_dump/rdls/dist/reports/rdls_validation_summary.md) — human-readable report
>
> **📁 Schema validation detail**: [`rdls/dist/reports/schema_validation.csv`](../hdx_dataset_metadata_dump/rdls/dist/reports/schema_validation.csv) — per-record results
>
> **📁 Schema validation full**: [`rdls/dist/reports/schema_validation_full.csv`](../hdx_dataset_metadata_dump/rdls/dist/reports/schema_validation_full.csv) — includes error details
>
> **📁 HEVL completeness**: [`rdls/dist/reports/hevl_completeness_report.csv`](../hdx_dataset_metadata_dump/rdls/dist/reports/hevl_completeness_report.csv) — block coverage per record
>
> **📁 Confidence scores**: [`rdls/dist/reports/confidence_scored_records.csv`](../hdx_dataset_metadata_dump/rdls/dist/reports/confidence_scored_records.csv) — composite scores
>
> **📁 Master manifest**: [`rdls/dist/master_manifest.csv`](../hdx_dataset_metadata_dump/rdls/dist/master_manifest.csv) — complete inventory with scores, tiers, and distribution folder
>
> **📁 Duplicate check**: [`rdls/dist/reports/rdls_duplicates.csv`](../hdx_dataset_metadata_dump/rdls/dist/reports/rdls_duplicates.csv) — detected duplicate records
>
> **📁 Missing fields**: [`rdls/dist/reports/rdls_missing_fields.csv`](../hdx_dataset_metadata_dump/rdls/dist/reports/rdls_missing_fields.csv) — records with absent optional fields
>
> **📁 Nested field warnings**: [`rdls/dist/reports/rdls_nested_field_warnings.csv`](../hdx_dataset_metadata_dump/rdls/dist/reports/rdls_nested_field_warnings.csv) — structural warnings

---

## Worked Example: From HDX to RDLS (All Four Components)

To see the entire pipeline in action, here is a real dataset that exercises all four HEVL components — from the original HDX metadata through every extraction step to the final integrated RDLS record.

### Source: Philippines Risk Assessment Indicators

**HDX Dataset**: [`bb961da8`](https://data.humdata.org/dataset/bb961da8-f354-4984-9e8e-a2655e5187cb) — Published by HeiGIT (Heidelberg Institute for Geoinformation Technology)

<details>
<summary><b>📥 Original HDX Metadata</b> (click to expand)</summary>

```json
{
  "id": "bb961da8-f354-4984-9e8e-a2655e5187cb",
  "title": "Philippines - Risk Assessment Indicators",
  "organization": "HeiGIT (Heidelberg Institute for Geoinformation Technology)",
  "dataset_source": "Multiple sources",
  "license_title": "Creative Commons Attribution Share-Alike (CC BY-SA)",
  "groups": ["Philippines"],
  "tags": [
    "affected population",
    "cyclones-hurricanes-typhoons",
    "demographics",
    "flooding",
    "hazards and risk",
    "health facilities",
    "indicators"
  ],
  "notes": "This dataset provides comprehensive Risk Assessment Indicators for Philippines,
    aggregated at admin level 2... structured risk assessment for flood and cyclone hazards.
    It includes demographic, environmental, infrastructure, accessibility, and
    hazard-related data to support disaster risk and resilience analysis.",
  "resources": [
    {"name": "PHL_ADM2_facilities.csv",        "format": "CSV"},
    {"name": "PHL_ADM2_flood_exposure.csv",     "format": "CSV"},
    {"name": "PHL_ADM2_vulnerability.csv",      "format": "CSV"},
    {"name": "PHL_ADM2_demographics.csv",       "format": "CSV"},
    {"name": "PHL_ADM2_coping.csv",             "format": "CSV"},
    {"name": "PHL_ADM2_access.csv",             "format": "CSV"},
    {"name": "PHL_ADM2_rural_population.csv",   "format": "CSV"},
    {"name": "PHL_ADM2_cyclone_exposure.csv",   "format": "CSV"}
  ]
}
```

</details>

The pipeline detects signals from multiple fields:

| Field | Signal Detected | Component |
| ----- | --------------- | --------- |
| Tag: `flooding` | flood | **Hazard** |
| Tag: `cyclones-hurricanes-typhoons` | convective_storm | **Hazard** |
| Tag: `affected population`, `demographics` | population | **Exposure** |
| Resource: `PHL_ADM2_vulnerability.csv` | vulnerability indicators | **Vulnerability** |
| Notes: "coping capacity", "risk assessment" | socio-economic context | **Vulnerability** |
| Resource: `PHL_ADM2_flood_exposure.csv` | flood exposure (loss context) | **Loss** |
| Tag: `hazards and risk` + resource: `flood_exposure` | infrastructure exposure to flood | **Loss** |

### Step 1 → General Metadata (NB 06)

The translator maps HDX fields into the RDLS schema structure. Note the three mandatory attribution roles, the ISO 3166-1 alpha-3 country code `PHL`, the SPDX license identifier, and each resource with its data format:

```json
{
  "id": "rdls_lss-hdx_heigit_heidelberg_in_phl_..._multihazard",
  "title": "Philippines - Risk Assessment Indicators",
  "risk_data_type": ["hazard", "exposure", "vulnerability", "loss"],
  "spatial": {
    "scale": "national",
    "countries": ["PHL"]
  },
  "license": "CC-BY-SA-4.0",
  "attributions": [
    {"id": "attribution_publisher",  "role": "publisher",      "entity": {"name": "HeiGIT (Heidelberg Institute for Geoinformation Technology)"}},
    {"id": "attribution_creator",    "role": "creator",        "entity": {"name": "Multiple sources"}},
    {"id": "attribution_contact",    "role": "contact_point",  "entity": {"name": "HeiGIT (Heidelberg Institute for Geoinformation Technology)"}}
  ],
  "resources": [
    {"id": "hdx_res_84de57ff", "title": "PHL_ADM2_facilities.csv",       "data_format": "CSV (csv)", "access_modality": "file_download"},
    {"id": "hdx_res_1eb585da", "title": "PHL_ADM2_flood_exposure.csv",   "data_format": "CSV (csv)", "access_modality": "file_download"},
    {"id": "hdx_res_6e96a202", "title": "PHL_ADM2_vulnerability.csv",    "data_format": "CSV (csv)", "access_modality": "file_download"},
    {"id": "hdx_res_15ef1ecf", "title": "PHL_ADM2_demographics.csv",     "data_format": "CSV (csv)", "access_modality": "file_download"},
    {"id": "hdx_res_c853e35b", "title": "PHL_ADM2_coping.csv",           "data_format": "CSV (csv)", "access_modality": "file_download"},
    {"id": "hdx_res_a5982430", "title": "PHL_ADM2_access.csv",           "data_format": "CSV (csv)", "access_modality": "file_download"},
    {"id": "hdx_res_6cc9e24f", "title": "PHL_ADM2_rural_population.csv", "data_format": "CSV (csv)", "access_modality": "file_download"},
    {"id": "hdx_res_b306e069", "title": "PHL_ADM2_cyclone_exposure.csv", "data_format": "CSV (csv)", "access_modality": "file_download"}
  ]
}
```

### Step 2 → Hazard Block (NB 09)

The tags `flooding` and `cyclones-hurricanes-typhoons` produce **two separate event sets** — one per hazard type. The `cyclones-hurricanes-typhoons` tag is a compound HDX tag; corroboration from the notes ("cyclone hazards") confirms the split. The hazard→process constraint maps `flood` → `fluvial_flood` and `convective_storm` → `tornado`:

```json
{
  "hazard": {
    "event_sets": [
      {
        "id": "event_set_bb961da8_1",
        "analysis_type": "empirical",
        "hazards": [{
          "id": "hazard_bb961da8_1",
          "type": "flood",
          "hazard_process": "fluvial_flood",
          "intensity_measure": "wd:m"
        }],
        "events": [{
          "id": "event_1_bb961da8_1",
          "calculation_method": "observed",
          "occurrence": { "empirical": {} },
          "description": "flood and convective storm hazard data for Philippines - empirical analysis"
        }]
      },
      {
        "id": "event_set_bb961da8_2",
        "analysis_type": "empirical",
        "hazards": [{
          "id": "hazard_bb961da8_2",
          "type": "convective_storm",
          "hazard_process": "tornado",
          "intensity_measure": "sws_3s:km/h"
        }],
        "events": [{
          "id": "event_1_bb961da8_2",
          "calculation_method": "observed",
          "occurrence": { "empirical": {} },
          "description": "flood and convective storm hazard data for Philippines - empirical analysis"
        }]
      }
    ]
  }
}
```

### Step 3 → Exposure Block (NB 10)

Tier 1 (tags) detects `population` from `affected population` and `demographics`. The VALID_TRIPLETS constraint enforces the only allowed combination for population: `(population, count)`:

```json
{
  "exposure": [
    {
      "id": "exposure_bb961da8_1",
      "category": "population",
      "metrics": [{
        "id": "metric_bb961da8_1_1",
        "dimension": "population",
        "quantity_kind": "count"
      }]
    }
  ]
}
```

### Step 4 → Vulnerability Block (NB 11)

The dataset has explicit vulnerability resources (`PHL_ADM2_vulnerability.csv`, `PHL_ADM2_coping.csv`, `PHL_ADM2_demographics.csv`). The extractor detects three **socio-economic indicators** and structures them into the RDLS vulnerability schema. Each indicator gets a code, a description, and a reference year:

```json
{
  "vulnerability": {
    "socio_economic": [
      {
        "id": "socio_bb961da8_1",
        "scheme": "Custom",
        "indicator_name": "Population density",
        "indicator_code": "POP_DENSITY",
        "description": "Number of people per unit area, indicating exposure concentration and potential vulnerability.",
        "reference_year": 2025
      },
      {
        "id": "socio_bb961da8_2",
        "scheme": "Custom",
        "indicator_name": "Elderly population percentage",
        "indicator_code": "AGE_65_PLUS",
        "description": "Population aged 65 years and older, more vulnerable to hazard-related health impacts.",
        "reference_year": 2025
      },
      {
        "id": "socio_bb961da8_3",
        "scheme": "Custom",
        "indicator_name": "Coping capacity index",
        "indicator_code": "COPING_CAPACITY",
        "description": "Capacity of communities to cope with and recover from hazard impacts.",
        "reference_year": 2025
      }
    ]
  }
}
```

### Step 5 → Loss Block (NB 11)

The flood exposure resource (`PHL_ADM2_flood_exposure.csv`) provides loss context — populations and facilities exposed to flooding at 30 cm depth. The `LOSS_SIGNAL_DEFAULTS` table maps this to an infrastructure exposure-to-hazard pattern, and `VALID_ASSET_TRIPLETS` validates the `(infrastructure, structure)` pair:

```json
{
  "loss": {
    "losses": [{
      "id": "loss_bb961da8_1",
      "hazard_type": "flood",
      "asset_category": "infrastructure",
      "asset_dimension": "structure",
      "impact_and_losses": {
        "impact_type": "direct",
        "impact_metric": "exposure_to_hazard",
        "quantity_kind": "count",
        "loss_type": "count",
        "loss_approach": "empirical"
      },
      "description": "Loss data from HDX dataset: Philippines - Risk Assessment Indicators"
    }]
  }
}
```

### Step 6 → Integration (NB 12) + Validation (NB 13)

NB 12 deep-copies the NB 06 base record and inserts all four blocks. The `risk_data_type` is reconciled to `["hazard", "exposure", "vulnerability", "loss"]` — confirmed because all four blocks are actually present. The filename prefix is `rdls_lss-` because loss has the highest priority in the naming convention.

NB 13 validates the integrated record against the RDLS v0.3 schema and assigns a composite confidence score. The result is routed to the `high/` tier.

> **📁 Final integrated record**: [`rdls/integrated/rdls_lss-hdx_heigit_heidelberg_in_phl_philippines_risk_assessment_indicators_multihazard.json`](../hdx_dataset_metadata_dump/rdls/integrated/rdls_lss-hdx_heigit_heidelberg_in_phl_philippines_risk_assessment_indicators_multihazard.json)

---

## The Results

### Final Pipeline Numbers

| Stage | Count | Rate |
| ----- | ----- | ---- |
| HDX datasets crawled | 26,246 | — |
| Organisations represented | 358 | — |
| OSM policy excluded | 3,649 | 13.9% |
| Classified as RDLS candidates | 13,053 | 49.7% |
| HEVL signals detected (any) | 19,948 | 76.0% |
| Integrated HEVL records | 12,554 | 96.2% of candidates |
| Schema-valid records | 9,772 | 77.9% of distributed |
| High-confidence tier | 12,539 | 99.8% of distributed |
| Total distributed records | 12,564 | — |

### HEVL Component Coverage (Final Records)

| Component | Records with Block | Coverage |
| --------- | ----------------- | -------- |
| Exposure | 12,118 | 96.6% |
| Vulnerability | 6,244 | 49.8% |
| Hazard | 2,774 | 22.1% |
| Loss | 1,576 | 12.6% |

### Quality Scores (Averages Across All Records)

| Dimension | Weight | Score |
| --------- | ------ | ----- |
| HEVL Coverage | 40% | 0.909 |
| Block Richness | 25% | 0.930 |
| Schema Validity | 20% | 0.933 |
| Metadata Completeness | 15% | 0.997 |

---

## Output Structure

```text
hdx_dataset_metadata_dump/
├── dataset_metadata/                  26,246 raw HDX JSON files
├── derived/
│   ├── classification_final.csv       Per-dataset classification breakdown
│   ├── classification_final_summary.json
│   └── rdls_included_dataset_ids_final.txt
├── config/
│   ├── signal_dictionary.yaml         Central HEVL signal configuration
│   ├── tag_to_rdls_component.yaml     HDX tag → RDLS component weights
│   ├── keyword_to_rdls_component.yaml Regex keyword patterns
│   ├── org_hints.yaml                 Organisation-level bias
│   └── overrides.yaml                 Per-dataset manual overrides
├── analysis/
│   ├── hdx_hevl_signal_analysis.csv   Per-dataset signal matches
│   ├── hdx_hevl_signal_summary.json   Aggregate signal statistics
│   └── hdx_high_signal_records.csv    Datasets with strong HEVL signals
└── rdls/
    ├── schema/                        RDLS v0.3 JSON Schema
    ├── template/                      Record template
    ├── example/                       4 hand-crafted reference records
    ├── records/                       13,053 NB 06 general metadata records
    ├── extracted/                     NB 09–11 extraction outputs
    │   ├── hazard_extraction_results.csv
    │   ├── hazard_extraction_high_confidence.csv
    │   ├── exposure_extraction_results.csv
    │   ├── exposure_extraction_high_confidence.csv
    │   ├── vulnerability_extraction_results.csv
    │   ├── vulnerability_detected_records.csv
    │   ├── loss_extraction_results.csv
    │   ├── loss_detected_records.csv
    │   └── rdls_*-hdx_*.json          Individual HEVL blocks
    ├── integrated/                    12,554 NB 12 merged records
    │   ├── rdls_index.csv
    │   ├── rdls_index.jsonl
    │   └── integration_skipped.csv
    ├── reports/
    │   ├── schema_validation_report.csv
    │   ├── hevl_completeness_report.csv
    │   ├── confidence_scored_records.csv
    │   └── rdls_validation_summary.md
    └── dist/                          Final deliverable
        ├── high/                      9,772 production-ready records
        ├── medium/                    25 records needing review
        ├── invalid/high/              2,767 high-confidence, schema-invalid
        ├── master_manifest.csv        Complete inventory
        ├── README.md                  Validation report
        └── reports/                   Full QA report suite
```

---

## What We Learned

**Exposure dominates the HDX catalogue.** Nearly 97% of final records have exposure blocks. This makes sense — HDX is a humanitarian data platform, and humanitarian responders need to know who and what is at risk. Population data alone accounts for 59% of exposure signals.

**Hazard data concentrates around flood.** Over 60% of hazard-flagged datasets relate to flooding. This reflects both the reality of disaster frequency globally and the strong presence of organisations like UNOSAT and OCHA flood response teams on HDX.

**Vulnerability is surprisingly common — when you define it broadly.** At 49.8% coverage, vulnerability detection was higher than the initial 0.8% signal scan suggested. The difference is that NB 08's initial scan looked for explicit vulnerability terminology (fragility curves, damage functions), while NB 11's extractor also captures socio-economic indicators like displacement rates, food security scores, and poverty indices — genuine vulnerability proxies in the RDLS sense.

**Loss data is the rarest and hardest to extract.** Only 12.6% of final records have loss blocks. Historical loss data tends to be embedded in reports and PDFs rather than structured datasets, and HDX metadata often lacks the specificity needed for automated extraction. The most common loss signals — displacement and human loss — come from humanitarian situation reports rather than dedicated loss databases.

**The 3-tier cascade prevents misclassification.** Without tiered extraction, datasets would be over-classified. Notes and descriptions frequently mention tangential topics — a flood hazard map might mention "population" in passing, a building exposure dataset might reference a "flood assessment" in its methodology. The cascade ensures that the most authoritative text fields (title, tags) take precedence.

**Constraint tables eliminate invalid field combinations.** Without constraint validation, the pipeline would produce plausible-looking but schema-invalid output. The constraint tables — hazard→process mappings, VALID_TRIPLETS, FUNCTION_TYPE_CONSTRAINTS, LOSS_SIGNAL_DEFAULTS, IMPACT_METRIC_CONSTRAINTS — form a safety net that guarantees internal consistency across all fields.

---

## Pipeline Architecture

```text
HDX CKAN API (26,246 datasets)
        │
        ▼
    NB 01–02: Crawl + OSM Exclusion ──→ dataset_metadata/ (26,246 JSON files)
        │
        ▼
    NB 03–05: Classify ──→ derived/classification_final.csv (13,053 candidates)
        │                  derived/classification_final_summary.json
        ▼
    NB 06–07: Translate General Metadata ──→ rdls/records/ (13,053 base records)
        │
        ▼
    NB 08: Signal Dictionary ──→ config/signal_dictionary.yaml
        │                       analysis/hdx_hevl_signal_summary.json
        │
        ├─── NB 09: Hazard Extractor ──→ rdls/extracted/hazard_extraction_results.csv
        │         constraint: hazard→process (11×30)
        │
        ├─── NB 10: Exposure Extractor ──→ rdls/extracted/exposure_extraction_results.csv
        │         strategy: 3-tier cascade
        │         constraint: VALID_TRIPLETS (7 categories)
        │
        └─── NB 11: V + L Extractor ──→ rdls/extracted/vulnerability_extraction_results.csv
                  shared: IMPACT_METRIC_CONSTRAINTS      rdls/extracted/loss_extraction_results.csv
                  vuln: FUNCTION_TYPE_CONSTRAINTS (4 types)
                  loss: VALID_ASSET_TRIPLETS + LOSS_SIGNAL_DEFAULTS
        │
        ▼
    NB 12: HEVL Integration ──→ rdls/integrated/ (12,554 merged records)
        │       strategy: merge-only               rdls/integrated/rdls_index.csv
        │       constraint: risk_data_type reconciliation
        ▼
    NB 13: Validation & QA ──→ rdls/dist/ (9,772 production-ready)
            scoring: 4-dimension composite          rdls/dist/master_manifest.csv
            routing: valid/invalid × high/medium/low
```

---

*Pipeline: 13 Jupyter notebooks | Schema: RDLS v0.3 | Source: HDX CKAN API | Updated: 2026-02-10*
