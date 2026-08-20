# NeuroNZ Phase 2 Automation

Private automation repository for keeping the NeuroNZ Zotero collection, QA reports, and WordPress-facing cache up to date.

## What this repo does first

The first implementation is a safe read-only automation run:

1. fetches the tested NeuroNZ Zotero collections,
2. parses stable NeuroNZ IDs from Zotero `extra`,
3. generates a Zotero cache,
4. generates a WordPress-shaped catalogue JSON file,
5. generates a completeness report,
6. writes a run summary for dissertation/evaluation evidence.

It does **not** write to Zotero yet. Write/update automation should be added only after validation gates and review queues are working.

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

