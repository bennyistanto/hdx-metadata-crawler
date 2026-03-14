# Known Limitations

This document describes known limitations of the HDX → RDLS metadata pipeline, their root causes, scale of impact, and references to ongoing work addressing them.

---

## Content-Blind Over-Classification

### The Problem

The pipeline classifies HEVL components based on **metadata signals** — title keywords, tags, resource names, and description text. This approach works well when metadata accurately describes the data content, but systematically fails for a common pattern:

> **Datasets that reference a hazard event in their title but contain entirely different data — typically loss/impact assessments, not hazard data.**

The pipeline sees "Earthquake" + "Health Facility" in the title and infers hazard (earthquake) + exposure (infrastructure). But the actual data columns tell a completely different story — the dataset may contain post-event facility status assessments (loss data), not seismic measurements (hazard data).

There is no mechanism in the pipeline to distinguish between:

| Pattern | Meaning | Pipeline Interpretation |
|---------|---------|------------------------|
| "Earthquake Health Facility **Status**" | A post-event damage assessment | hazard + exposure + vulnerability |
| "Earthquake **Shakemap**" | Actual seismic hazard data | hazard (correct) |
| "Drought Related **Key Figures**" | Humanitarian impact metrics | hazard + exposure + vulnerability + loss |
| "Drought **Forecast** Index" | Actual drought prediction model | hazard (correct) |

The word "earthquake" or "drought" in a title triggers a hazard classification regardless of whether the dataset **contains** hazard measurements or merely **references** a hazard event as context.

### Root Cause

The pipeline operates entirely on metadata text. It has no access to the actual data columns or content structure of the underlying datasets. This is an architectural boundary — the pipeline was designed for metadata-only processing, and extending it to inspect data content requires a fundamentally different approach (resource column caching, semantic classification, or both).

The fabricated hazard descriptions follow a telltale pattern: `"<hazard_type> hazard data for <country>"` — generic, template-generated text. The pipeline then assigns fabricated intensity measures (`PGA:g`, `SPI:-`, `wd:m`) that have no basis in the actual data content.

### Scale of Impact

| Metric | Count |
|--------|------:|
| Records with fabricated hazard blocks | **2,313** |
| % of all records with a hazard component | **82%** (2,313 / 2,813) |
| Records also misclassified with loss component | 613 |
| Records also fabricated exposure component | 480 |
| Records with genuinely authored hazard blocks | ~500 |

### Top Affected Publishers

| Publisher | Records | Typical Data Content |
|-----------|--------:|----------------------|
| UNOSAT | 276 | Satellite damage assessments |
| Philippine Space Agency | 72 | Building damage surveys |
| IDMC | 55 | Displacement monitoring |
| WFP ADAM | 46 | Disaster population estimates |
| IOM | 24 | Displacement tracking |

### Case Studies

The following examples demonstrate the gap between metadata-driven classification and actual data content.

#### Case 1: PNG Earthquake Health Facility Status

**Source**: [HDX Dataset](https://data.humdata.org/dataset/3f3b4b2f-60c8-4d03-ac74-aa7fd606b0d7)

**Pipeline classification**: `risk_data_type: ["hazard", "exposure", "vulnerability"]`
- Hazard block: `"earthquake hazard data for Papua New Guinea"` with `intensity_measure: "PGA:g"` — **fabricated**
- Exposure block: `category: "infrastructure"`, `dimension: "structure"` — **fabricated**
- Vulnerability block: `indicator_code: "HEALTH_ACCESS"` — **fabricated**
- Loss: **completely missing** despite being a post-earthquake damage assessment

**Actual data columns** (from the XLSX file):
```
WHO FACILITY NAME, TYPE, LLG_Pcode, Dis_Pcode, Prov_Pcode,
Status Post Earthquake (Open/Closed), Status Date,
Power Functioning (solar or generator or mains) Y/N, Water Supply Y/N,
Health Facility Building Damaged (Severe/Moderate/Minor),
Clinical Staff Present (Y/N), Surgical services functional (Y/N)
```

**Correct classification**: `["exposure", "loss"]` — the dataset contains a spatial registry of health facilities (exposure) and post-event operational status assessments (loss). There are zero seismic measurements — no ShakeMap, no PAGER. The earthquake is a triggering event context, not the data content.

#### Case 2: Kenya Drought Related Key Figures

**Source**: [HDX Dataset](https://data.humdata.org/dataset/c7e5d29e-f5e8-4d8b-a437-f784fcfd6103)

**Pipeline classification**: `risk_data_type: ["hazard", "exposure", "vulnerability", "loss"]` — all four components

**Actual data columns**:
```
Country, Date, Total Affected, Total Targeted, Targeted %,
Total Reached, Reached %, Food Insecurity, Malnutrition,
SAM, MAM, GAM, PLW, Internal Displacement, School Dropout,
Livestock Deaths, Water Insecurity, Diseases: AWD/Cholera,
Diseases: Measles, Source
```

**Correct classification**: `["loss"]` only — the dataset contains post-event humanitarian key figures (affected populations, malnutrition cases, livestock deaths, displacement). There are no drought indices (SPI, PDSI), no exposure inventories, and no vulnerability functions.

#### Case 3: Colombia HungerMap Data (WFP)

**Source**: [HDX Dataset](https://data.humdata.org/dataset/9a8b705d-1679-4554-95de-9fc6343e57c8)

**Pipeline classification**: `risk_data_type: ["hazard", "exposure", "vulnerability"]` — with **earthquake** as the hazard type for a **food security** dataset

**Correct classification**: `["loss"]` only — FCS (Food Consumption Score) and RCSI (Reduced Coping Strategy Index) are food security outcome measures, not hazard models or exposure inventories. The pipeline assigned `earthquake` as the hazard type because the description mentions "hazards" as one of many WFP data inputs, triggering a false keyword match.

#### Case 4: Burkina Faso Internal Displacements (IDMC)

**Source**: [HDX Dataset](https://data.humdata.org/dataset/5110aba6-f927-4dd2-80ec-5e7f56684895)

**Pipeline classification**: `risk_data_type: ["hazard", "exposure", "loss"]` — with `flood` as the only hazard type and `wd:m` (water depth) as intensity measure

**Correct classification**: `["loss"]` only — the dataset tracks displacement events. The coordinates are post-event displacement flow locations, not pre-event exposure inventories. There are no flood depth measurements.

### Summary

In all four cases, the datasets are primarily **loss/impact data**. The pipeline over-classifies them by:
1. Treating hazard event references in titles as hazard data
2. Fabricating intensity measures that have no basis in the actual data
3. Missing the loss component that is the dataset's primary content
4. Assigning exposure/vulnerability based on incidental keyword matches

### Addressing This Limitation

This limitation is architectural — resolving it requires access to the actual data content (column headers, data types) and semantic classification that can distinguish "dataset ABOUT earthquakes" from "dataset CONTAINING earthquake measurements."

Work on a content-driven classification approach is tracked separately in the [`to-rdls`](https://github.com/GFDRR/to-rdls) pipeline repository, which implements resource column caching and LLM-assisted review to address this gap.

---

## Occurrence Schema Gap

### The Problem

The RDLS v0.3 schema requires `hazard.event_sets[].events[].occurrence` to have at least one property (`minProperties: 1`). However, many HDX datasets lack event-specific temporal information, resulting in empty `occurrence: {}` blocks that fail schema validation.

### Scale of Impact

| Metric | Count |
|--------|------:|
| Records blocked by this issue | **2,690** |
| % of RDLS-relevant records blocked | 30.5% |
| Other validation errors on these records | None (sole blocker) |

### Status

This is a schema-level constraint issue. The RDLS schema team is aware and considering a revision to allow empty occurrence blocks for datasets where event timing is genuinely unknown. Once the schema is updated, these 2,690 records would pass validation, raising the valid record count from 6,132 to approximately 8,822 (99.8% of RDLS-relevant records).

---

## Kosovo Country Code (XKX)

### The Problem

Three records reference Kosovo using the code `XKX`, which is not in the ISO 3166-1 alpha-3 codelist. While `XKX` is widely used as a provisional code for Kosovo (including by the EU, World Bank, and HDX itself), it is not part of the official ISO standard and fails schema validation.

### Current Handling

These records are routed to `not_rdls/` during sanitization. A future schema revision or country code alias mechanism could re-include them.

---

[← Back to README](../README.md) | [Architecture →](ARCHITECTURE.md)
