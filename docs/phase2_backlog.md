# Phase 2 Automation Backlog

## 1. Milestone A: Automation foundation

| Priority | Task | Output |
|---:|---|---|
| 1 | Create source registry and run-log structure | `source_registry.csv`, `runs/` convention |
| 2 | Add Zotero read/backfill script | Catalogue export with `zotero_key`, DOI, PMID where available |
| 3 | Add completeness report generator | Field coverage report after each run |
| 4 | Add secret scan to update workflow | Failed run if API keys appear in outputs |

## 2. Milestone B: Existing collection enrichment automation

| Priority | Task | Output |
|---:|---|---|
| 1 | Backfill Zotero item keys into catalogue export | 79/79 catalogue records have `zotero_key` |
| 2 | Extract DOI and PMID from Zotero items and source links | Dedicated DOI/PMID fields populated where available |
| 3 | Resolve public link gaps for `NZNEURO-043` and `NZNEURO-045` | 79/79 catalogue records have clean link handling |
| 4 | Fill blank `type_of_data` values | `NZNEURO-052`, `NZNEURO-053`, `NZNEURO-054`, `NZNEURO-077` completed |
| 5 | Fill blank `age_group` values | 9 known blank records completed |
| 6 | Convert public-risk `Verification pending` text into internal review flags | WordPress-safe display values |

## 3. Milestone C: Evidence relationship automation

| Priority | Task | Output |
|---:|---|---|
| 1 | Add explicit `record_id` field to evidence log | Evidence rows linked to catalogue records |
| 2 | Generate evidence coverage report by stable ID | Accurate coverage metrics |
| 3 | Flag catalogue records with weak/no evidence links | Review queue |
| 4 | Sync evidence IDs and links back into Zotero `extra` | Zotero and CSV stay aligned |

## 4. Milestone D: Source monitoring

| Priority | Task | Output |
|---:|---|---|
| 1 | Implement link checker for existing primary links | Broken-link report |
| 2 | Implement Zotero API refresh/cache | `zotero_cache.json` for WordPress sync support |
| 3 | Implement data.govt.nz monitor | Candidate records from NZ data catalogue |
| 4 | Implement PubMed saved-search monitor | Candidate evidence/publication records |
| 5 | Implement NZ public-source page monitors | Changed-source report |

## 5. Milestone E: WordPress sync support

| Priority | Task | Output |
|---:|---|---|
| 1 | Produce WordPress-shaped JSON from Zotero | Sync/cache file matching WordPress developer spec |
| 2 | Add created/updated/unchanged counts | `wordpress_sync_report.json` |
| 3 | Add blocked-record export | WordPress does not ingest failed-validation records |
| 4 | Document manual refresh and rollback process | WordPress admin runbook |

## 6. Milestone F: Dissertation evidence

| Priority | Task | Output |
|---:|---|---|
| 1 | Save automation run summaries | Dissertation methods/evaluation evidence |
| 2 | Compare manual vs automated update effort | Sustainability evaluation |
| 3 | Track completeness improvement across runs | Results chapter tables |
| 4 | Document limitations and governance | Dissertation discussion section |

## 7. First implementation recommendation

Start with the Zotero backfill and completeness report because they are low-risk, use the existing collection, and directly improve WordPress readiness:

1. read Zotero records from the tested API endpoints,
2. parse stable NeuroNZ IDs from `extra`,
3. match them to `catalogue_phase1_clean.csv`,
4. write `zotero_key`, DOI, and PMID where available,
5. regenerate a completeness report,
6. commit the updated exports and reports.

