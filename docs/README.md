# NeuroNZ Phase 2 Automation

**Date created:** 20 August 2026  
**Project:** NeuroNZ online neurological data/resource catalogue  
**Purpose:** Keep the NeuroNZ collection, Zotero library, exports, and WordPress-facing data updated through a repeatable automation workflow.

## 1. Phase 2 goal

Phase 2 adds the update pipeline on top of the completed Phase 1A collection. The goal is to reduce routine manual updating by automating:

1. source monitoring and discovery,
2. new/changed record detection,
3. metadata extraction and enrichment,
4. deduplication,
5. controlled-field validation,
6. Zotero updates,
7. export regeneration,
8. WordPress refresh support,
9. run logs and exception reports.

The pipeline should update the collection safely, but it should not publish low-confidence or failed-validation records directly to the public website.

## 2. Current baseline

| Asset | Current status |
|---|---|
| Zotero root collection | `NeuroNZ Collection` |
| Zotero user library ID | `21117133` |
| Catalogue collection | `01 Catalogue Sources`, key `VNEB8Z2T`, 79 items |
| Evidence collection | `02 Evidence Log`, key `CI4SRMX3`, 102 items |
| Condition taxonomy collection | `03 Condition Taxonomy`, key `Q3ZM44NE`, 79 items |
| Excluded sources collection | `04 Excluded Sources`, key `KICKW4WS`, 0 items |
| Local cleaned workbook | `NZ_Neuro_Data_Catalogue_Phase1A_Clean.xlsx` |
| Clean catalogue export | `NeuroNZ-Phase1-Collection/catalogue_phase1_clean.csv` |
| Clean evidence export | `NeuroNZ-Phase1-Collection/evidence_log_phase1_clean.csv` |
| Clean taxonomy export | `NeuroNZ-Phase1-Collection/condition_taxonomy_phase1_clean.csv` |
| WordPress developer handoff | `WordPress-Handoff/wordpress-integration.md` |
| Tested Zotero API spec | `WordPress-Handoff/zotero_api_spec.md` |

## 3. Phase 2 folder contents

| File | Purpose |
|---|---|
| `automation_architecture.md` | End-to-end architecture and data-flow design. |
| `update_runbook.md` | Operational workflow for scheduled and manual updates. |
| `source_registry.csv` | Initial list of real source families to monitor and the preferred automation method. |
| `quality_gates.md` | Validation gates before records update Zotero, exports, or WordPress. |
| `phase2_backlog.md` | Ordered work plan for implementing automation. |

## 4. Automation principle

Automation should do routine work, while review gates protect quality.

Records may be fetched, enriched, and staged automatically. Records should only be published to WordPress when they have:

1. a stable NeuroNZ ID,
2. a valid primary link,
3. required metadata fields,
4. duplicate checks completed,
5. source confidence recorded,
6. validation status recorded,
7. no unresolved public-display warnings.

## 5. Priority Phase 2 improvements

The first automation work should target the known remaining gaps:

1. backfill Zotero item keys into catalogue exports,
2. extract DOI and PMID where available,
3. add explicit `record_id` links in the evidence log,
4. monitor current source URLs for link breakage and content changes,
5. expand taxonomy synonyms for better search and classification,
6. generate an automated completeness report after every run,
7. produce a WordPress-ready sync/cache file from Zotero.

## 6. Security rule

Do not store Zotero API keys, WordPress credentials, GitHub tokens, or database credentials in this folder. Use environment variables, GitHub secrets, or WordPress secret/config storage.

