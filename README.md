# NeuroNZ UOA Automation

Private automation repository for keeping the NeuroNZ Zotero collection, QA reports, and WordPress-facing cache up to date.

## What this repo does first

The first implementation is a safe read-only automation run:

1. fetches the tested NeuroNZ Zotero collections,
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

It does **not** write to Zotero yet. Write/update automation should be added only after these validation gates and review queues are stable.

External source automation currently starts candidate discovery with PubMed and data.govt.nz. Candidates are staged in CSV for review; they are not written into Zotero automatically yet.

## Repository secrets

Add this GitHub repository secret:

| Secret | Purpose |
|---|---|
| `ZOTERO_API_KEY` | Read-only Zotero API key for the NeuroNZ collection |

Do not commit API keys or WordPress credentials.

## Manual local run

```bash
export ZOTERO_API_KEY="your-read-only-key"
python3 -m neuronz_automation.run_phase2
```

Outputs are written to `outputs/`.

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
