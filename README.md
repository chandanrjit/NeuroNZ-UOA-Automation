# NeuroNZ UOA Automation

Private automation repository for keeping the NeuroNZ Zotero collection, QA reports, and WordPress-facing cache up to date.

## What this repo does first

The pipeline imports validated new PubMed evidence and refreshes monitoring outputs:

1. fetches group `6643086`, collection `PA2ESN45` and its descendants,
2. parses stable NeuroNZ IDs from Zotero `extra`,
3. generates a Zotero cache,
4. generates a WordPress-shaped catalogue JSON file,
5. generates a completeness report,
6. validates public-readiness quality gates,
7. creates a review queue for records needing attention,
8. monitors registered source pages,
9. discovers candidate records from PubMed and data.govt.nz,
10. checks catalogue primary links,
11. writes a run summary for dissertation/evaluation evidence.

GitHub Actions enables `ZOTERO_WRITE_ENABLED=true`. New PubMed papers with verified abstracts, clear NZ and neurological relevance, and no matching DOI, PMID, URL, or title in the group library are added to `02 Evidence Log`. Every created item is read back and logged with its Zotero key, evidence ID, `dateAdded`, and `dateModified` in `outputs/zotero_update_manifest.json`. Existing items are preserved. Concurrent pipeline runs are serialized.

Imports require a verified journal title, authors, and publication date in addition to title, abstract, PMID, and relevance checks. PubMed supplies journal abbreviation, ISSN, language, volume, issue, and pages when available. Missing optional source fields are listed in each write receipt; publisher identifiers are not substituted for page numbers. Existing phase2 articles in the target evidence collection with an exact PMID match can have missing bibliography filled using a version-guarded update. Existing populated fields are preserved, and readback verifies both the repair and the retained metadata. These repairs have status metadata_updated_verified in the manifest and run summary.

Candidates that fail relevance checks and data.govt.nz datasets that need catalogue metadata review remain in the review manifest. Source failures are logged and are never imported.

## Zotero target

Source: https://www.zotero.org/groups/6643086/nz_neuro_data_catalogue/collections/PA2ESN45/collection

The pipeline reads this collection and its descendants, deduplicates Zotero keys, and classifies records by their NeuroNZ IDs in `extra`. Evidence and condition IDs take precedence over catalogue references. Unclassified records enter catalogue validation so missing IDs remain visible. Attachments, notes, annotations, and descendant collections named `04 Excluded Sources` are excluded. Authenticated API checks confirmed access to `NeuroNZ_Shared_Collection` and all four child collections on 2 October 2026.

## Repository secrets

Add this GitHub repository secret:

| Secret | Purpose |
|---|---|
| `ZOTERO_API_KEY` | Zotero API key with read and write access to group `6643086` |

Do not commit API keys or WordPress credentials.

## Manual local run

```bash
export ZOTERO_API_KEY="your-read-only-key"
python3 -m neuronz_automation.run_phase2
```

Outputs are written to `outputs/`.
Local runs remain read-only unless `ZOTERO_WRITE_ENABLED=true` is explicitly set.

Main outputs:

| File | Purpose |
|---|---|
| `outputs/zotero_cache.json` | Normalised cache of Zotero catalogue, evidence, and taxonomy records. |
| `outputs/wordpress_neuro_resources.json` | WordPress-shaped catalogue records. |
| `outputs/catalogue_completeness_report.csv` | Field coverage report. |
| `outputs/validation_failures.csv` | Blocker/review issues from quality gates. |
| `outputs/review_queue.csv` | Records requiring human decision before public use. |
| `outputs/changed_records.csv` | New/changed/unchanged catalogue records compared with the previous committed output. |
| `outputs/candidate_records.csv` | New source candidates from PubMed and data.govt.nz for review. |
| `outputs/source_fetch_log.csv` | Status of registered source monitoring checks. |
| `outputs/catalogue_link_status.csv` | Status of primary catalogue URLs. |
| `outputs/latest_run_summary.json` | Top-level run summary for audit and dissertation evidence. |

## GitHub Actions

Workflow:

```text
.github/workflows/phase2-automation.yml
```

It supports:

1. manual runs through `workflow_dispatch`,
2. weekly scheduled runs,
3. artifact upload of generated outputs,
4. optional commit of changed output files.

## Documentation

Planning documents from the project repository are stored in `docs/`.
