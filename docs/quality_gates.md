# Phase 2 Quality Gates

## 1. Purpose

Quality gates prevent automated updates from lowering the quality of the NeuroNZ collection or publishing uncertain records to WordPress.

## 2. Required gates before Zotero update

| Gate | Pass rule | Fail action |
|---|---|---|
| Stable ID | Existing records have a stable NeuroNZ ID; new approved catalogue records receive the next available `NZNEURO` ID. | Send to review queue. |
| Title | Title is present and not only a source filename or generic page name. | Send to review queue. |
| Primary link | Public URL is present and resolves, or a documented access limitation is recorded. | Send to review queue. |
| Duplicate check | DOI, PMID, URL, Zotero key, and normalised title checks do not identify a conflict. | Mark possible duplicate. |
| NZ relevance | Record clearly relates to Aotearoa New Zealand, NZ data, NZ services, NZ research, or NZ comparator context. | Send to review queue. |
| Neurological relevance | Record maps to a NeuroNZ condition/category or clearly supports neurological data discovery. | Send to review queue. |
| Source category | Controlled source category is assigned. | Send to review queue. |
| Access status | Availability/access text is present and public-safe. | Send to review queue. |
| Review status | Internal review status is present. | Send to review queue. |
| Secret scan | Output files contain no API keys or credentials. | Stop run and clean outputs. |

## 3. Required gates before WordPress publication

| Gate | Pass rule |
|---|---|
| Public title | Title is clear for website users. |
| Public summary | Summary is understandable without workbook context. |
| Public link | Primary source link is usable. |
| Filter metadata | Source category and available controlled filters are populated. |
| Internal-only text | Raw cleanup notes, unresolved verification text, and private process notes are hidden. |
| Upsert key | WordPress uses stable NeuroNZ ID, not title. |

## 4. Current known gaps to monitor

These gaps should become automated completeness checks:

| Gap | Current affected records |
|---|---|
| Missing or unparsed public primary link | `NZNEURO-043`, `NZNEURO-045` |
| Blank `type_of_data` | `NZNEURO-052`, `NZNEURO-053`, `NZNEURO-054`, `NZNEURO-077` |
| Blank `age_group` | `NZNEURO-008`, `NZNEURO-017`, `NZNEURO-018`, `NZNEURO-019`, `NZNEURO-068`, `NZNEURO-076`, `NZNEURO-077`, `NZNEURO-078`, `NZNEURO-079` |
| Public-display risk text | Records containing `Verification pending` |
| Missing catalogue backfill | `zotero_key`, `doi`, and `pmid` fields in catalogue export |
| Weak evidence relationship | Evidence log should link to `record_id` rather than relying on title/name matching |
| Taxonomy search depth | Synonyms populated for only a minority of conditions |

## 5. Completeness scorecard

Each run should publish a scorecard with:

| Metric | Target before public launch |
|---|---:|
| Catalogue records with stable ID | 100% |
| Catalogue records with primary link | 100% or documented exception |
| Catalogue records with source category | 100% |
| Catalogue records with access/availability text | 100% |
| Catalogue records with `type_of_data` | 100% |
| Catalogue records with controlled age group or `Not age-specific` | 100% |
| Catalogue records with Zotero key backfilled | 100% |
| Evidence records linked to catalogue IDs where applicable | 90%+ |
| Taxonomy records with useful synonyms | 80%+ for launch-priority conditions |
| WordPress public records showing internal cleanup text | 0 |

