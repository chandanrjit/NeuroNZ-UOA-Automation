# Phase 2 Update Runbook

## 1. Purpose

This runbook defines how NeuroNZ collection updates should be performed once Phase 2 automation is implemented.

## 2. Safe update sequence

Run updates in this order:

1. fetch current Zotero records,
2. fetch registered external sources,
3. detect new and changed candidates,
4. deduplicate against existing NeuroNZ IDs, Zotero keys, DOI, PMID, URL, and title,
5. enrich metadata,
6. run validation gates,
7. stage low-confidence records for review,
8. update Zotero only for approved/pass records,
9. regenerate local exports,
10. generate completeness and run reports,
11. trigger or allow WordPress sync from Zotero.

## 3. Manual pre-run checks

Before running automation, confirm:

| Check | Expected result |
|---|---|
| Git working tree | No unrelated uncommitted edits that could be overwritten. |
| Zotero API key | Available through environment/secret storage only. |
| Root collection | `NeuroNZ Collection` exists. |
| Child collections | `01 Catalogue Sources`, `02 Evidence Log`, `03 Condition Taxonomy`, `04 Excluded Sources` exist. |
| Source registry | `source_registry.csv` has no disabled source accidentally marked active. |

## 4. Existing Zotero update command

Current safe update command for the Phase 1A cleaned collection:

```bash
ZOTERO_API_KEY="$ZOTERO_API_KEY" python3 scripts/zotero_phase1_import.py \
  --clean \
  --include-evidence \
  --include-conditions \
  --update-existing \
  --root-collection "NeuroNZ Collection"
```

Expected safe outcome for a no-change verification run:

```text
existing items detected
0 duplicate Zotero records created
```

## 5. Phase 2 run outputs

Each run should write to:

```text
Phase2-Automation/runs/YYYY-MM-DD-HHMM/
```

Required output files:

| File | Required? | Purpose |
|---|---:|---|
| `run_summary.json` | Yes | Single run result for audit and dissertation evidence. |
| `source_fetch_log.csv` | Yes | Source availability and counts. |
| `candidate_records.csv` | Yes | New or changed source records before validation. |
| `duplicate_matches.csv` | Yes | Deduplication evidence. |
| `validation_failures.csv` | Yes | Records blocked from Zotero/WordPress update. |
| `review_queue.csv` | Yes | Records needing human decision. |
| `zotero_update_manifest.csv` | Yes | Zotero create/update/skip actions. |
| `catalogue_completeness_report.csv` | Yes | Post-run metadata coverage. |

## 6. Review queue rules

Send records to review instead of publishing when:

1. no clean primary link exists,
2. DOI/PMID/title conflict with an existing record,
3. source category cannot be classified,
4. neurological relevance is uncertain,
5. Aotearoa New Zealand relevance is uncertain,
6. public display text still contains unresolved `Verification pending`,
7. source content is blocked, unavailable, or returns an error,
8. a record appears to describe sensitive or non-public data.

## 7. Post-run checks

After each run, verify:

| Check | Pass condition |
|---|---|
| Zotero item count | Expected increases only when approved new records exist. |
| Duplicate count | No duplicate stable NeuroNZ IDs. |
| Broken links | No public record has a missing primary URL. |
| Required fields | Catalogue records have title, stable ID, primary link, source category, access text, and review status. |
| WordPress sync | WordPress receives created/updated/unchanged counts and does not create title-based duplicates. |
| Secrets | No API keys appear in run logs or committed files. |

## 8. Failure handling

| Failure | Action |
|---|---|
| Zotero API authentication failure | Stop run, alert maintainer, do not update exports. |
| Source API shape changed | Mark source failed, save response sample outside public docs if needed, continue other sources. |
| Link checker outage | Do not mark all links broken; rerun link checker later. |
| Duplicate uncertainty | Place candidate in review queue. |
| WordPress sync failure | Keep Zotero/export updates, log WordPress failure, rerun WordPress sync after fix. |

## 9. Commit practice

Commit only:

1. source code,
2. documentation,
3. cleaned non-secret reports,
4. stable export files intended for version control.

Do not commit:

1. API keys,
2. raw private responses,
3. temporary credentials,
4. local Word/PowerPoint lock files,
5. sensitive logs.

