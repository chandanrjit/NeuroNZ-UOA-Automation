"""Run the safe Phase 2 automation workflow."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .candidate_sources import discover_candidates
from .config import COLLECTIONS, OUTPUT_DIR, ZOTERO_COLLECTION_KEY, ZOTERO_LIBRARY_ID, ZOTERO_LIBRARY_TYPE
from .parsing import extract_doi, extract_pmid, extract_tags, parse_extra
from .quality import changed_record_rows, review_queue_rows, validation_rows
from .reports import completeness_rows, read_json, write_csv, write_json
from .source_monitor import check_url, monitor_registered_sources
from .zotero_client import ZoteroClient
from .zotero_updates import update_candidates


def normalise_zotero_item(item: dict[str, Any], stable_id_field: str) -> dict[str, Any]:
    data = item.get("data") or {}
    extra = parse_extra(data.get("extra"))
    url = data.get("url", "") or ""
    all_source_links = extra.get("All source links", "")
    doi = data.get("DOI", "") or extract_doi(url, all_source_links, data.get("extra"))
    pmid = extract_pmid(url, all_source_links, data.get("extra"))

    return {
        "stable_id": extra.get(stable_id_field, ""),
        "zotero_key": data.get("key", ""),
        "zotero_version": data.get("version", ""),
        "title": data.get("title", ""),
        "summary": data.get("abstractNote", ""),
        "source_organisation": data.get("websiteTitle", ""),
        "primary_link": url,
        "doi": doi,
        "pmid": pmid,
        "item_type": data.get("itemType", ""),
        "date": data.get("date", ""),
        "tags": extract_tags(data),
        "extra": extra,
    }


def wordpress_record(record: dict[str, Any]) -> dict[str, Any]:
    extra = record["extra"]
    return {
        "record_id": record["stable_id"],
        "zotero_key": record["zotero_key"],
        "zotero_version": record["zotero_version"],
        "title": record["title"],
        "summary": record["summary"],
        "source_organisation": record["source_organisation"],
        "primary_link": record["primary_link"],
        "source_category": extra.get("Source category", ""),
        "type_of_data": extra.get("Type of data", ""),
        "age_group": extra.get("Age group", ""),
        "data_period": extra.get("Data period", ""),
        "design_type": extra.get("Design type", ""),
        "population_coverage": extra.get("Population / Coverage", ""),
        "approx_sample_size": extra.get("Approx. sample size", ""),
        "available_in_idi": extra.get("Available in IDI", ""),
        "availability_access": extra.get("Availability / Access", ""),
        "all_source_links": extra.get("All source links", ""),
        "doi": record["doi"],
        "pmid": record["pmid"],
        "zotero_tags": record["tags"],
    }


def partition_items(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = {kind: [] for kind in COLLECTIONS}
    for item in items:
        data = item.get("data") or {}
        if data.get("itemType") in {"attachment", "note", "annotation"}:
            continue
        extra = parse_extra(data.get("extra"))
        # Evidence may also reference a catalogue ID; use its own ID first.
        for kind in ("evidence", "taxonomy", "catalogue"):
            if extra.get(COLLECTIONS[kind]["stable_id_field"]):
                buckets[kind].append(item)
                break
        else:
            # Keep unclassified records visible to the missing-ID quality gate.
            buckets["catalogue"].append(item)
    return buckets


def run() -> None:
    started_at = datetime.now(timezone.utc).isoformat()
    output_dir = Path(OUTPUT_DIR)
    api_key = os.environ.get("ZOTERO_API_KEY")
    if not api_key:
        raise SystemExit(
            "ZOTERO_API_KEY is required. Add it as a GitHub repository secret or export it locally before running."
        )
    client = ZoteroClient(api_key=api_key)
    source_registry_path = Path("docs/source_registry.csv")
    candidate_records = discover_candidates()
    write_enabled = os.environ.get("ZOTERO_WRITE_ENABLED", "false").lower() == "true"
    update_manifest = update_candidates(client, candidate_records, output_dir) if write_enabled else []

    cache: dict[str, list[dict[str, Any]]] = {}
    summary_collections: list[dict[str, Any]] = []
    items_by_type = partition_items(client.fetch_collection_tree_items(ZOTERO_COLLECTION_KEY))

    for collection_type, config in COLLECTIONS.items():
        items = items_by_type[collection_type]
        records = [normalise_zotero_item(item, config["stable_id_field"]) for item in items]
        cache[collection_type] = records
        summary_collections.append(
            {
                "collection_type": collection_type,
                "collection_name": config["name"],
                "collection_key": ZOTERO_COLLECTION_KEY,
                "items_fetched": len(records),
                "records_with_stable_id": sum(1 for record in records if record["stable_id"]),
            }
        )

    catalogue_records = [wordpress_record(record) for record in cache["catalogue"]]
    previous_catalogue_records = read_json(output_dir / "wordpress_neuro_resources.json", [])
    completeness_fields = [
        "record_id",
        "zotero_key",
        "title",
        "summary",
        "source_organisation",
        "primary_link",
        "source_category",
        "type_of_data",
        "age_group",
        "data_period",
        "design_type",
        "population_coverage",
        "available_in_idi",
        "availability_access",
        "doi",
        "pmid",
    ]
    validation = validation_rows(catalogue_records)
    review_queue = review_queue_rows(validation)
    changed_records = changed_record_rows(previous_catalogue_records, catalogue_records)
    source_fetch_log = monitor_registered_sources(source_registry_path)
    link_status_rows = [
        {
            "record_id": record["record_id"],
            "title": record["title"],
            "primary_link": record["primary_link"],
            **check_url(record["primary_link"]),
        }
        for record in catalogue_records
    ]

    write_json(output_dir / "zotero_cache.json", cache)
    write_json(output_dir / "wordpress_neuro_resources.json", catalogue_records)
    write_csv(
        output_dir / "catalogue_completeness_report.csv",
        completeness_rows(catalogue_records, completeness_fields),
        ["field", "populated", "total", "coverage_percent"],
    )
    write_csv(
        output_dir / "validation_failures.csv",
        validation,
        ["record_id", "severity", "field", "issue"],
    )
    write_csv(
        output_dir / "review_queue.csv",
        review_queue,
        ["record_id", "severity", "field", "issue"],
    )
    write_csv(
        output_dir / "changed_records.csv",
        changed_records,
        ["record_id", "change_status", "changed_fields"],
    )
    write_csv(
        output_dir / "candidate_records.csv",
        candidate_records,
        [
            "candidate_id",
            "source_id",
            "title",
            "url",
            "source_organisation",
            "candidate_type",
            "detected_at",
            "doi",
            "pmid",
            "summary",
            "bibliography",
            "condition_terms",
            "status",
            "error_message",
        ],
    )
    write_csv(
        output_dir / "source_fetch_log.csv",
        source_fetch_log,
        [
            "source_id",
            "source_name",
            "source_type",
            "primary_url",
            "automation_method",
            "phase2_priority",
            "notes",
            "checked_at",
            "status",
            "status_code",
            "error_message",
            "checked_method",
        ],
    )
    write_csv(
        output_dir / "catalogue_link_status.csv",
        link_status_rows,
        ["record_id", "title", "primary_link", "status", "status_code", "error_message", "checked_method"],
    )

    finished_at = datetime.now(timezone.utc).isoformat()
    blocker_count = sum(1 for row in validation if row["severity"] == "blocker")
    review_count = sum(1 for row in validation if row["severity"] == "review")
    write_json(
        output_dir / "latest_run_summary.json",
        {
            "started_at": started_at,
            "finished_at": finished_at,
            "mode": "validated_evidence_import" if write_enabled else "read_only_monitoring",
            "zotero_updates": {
                "created_verified": sum(row["status"] == "created_verified" for row in update_manifest),
                "metadata_updated_verified": sum(row["status"] == "metadata_updated_verified" for row in update_manifest),
                "duplicates": sum(row["status"] == "duplicate" for row in update_manifest),
                "review": sum(row["status"] == "review" for row in update_manifest),
                "manifest": "outputs/zotero_update_manifest.json" if write_enabled else None,
            },
            "zotero_library_type": ZOTERO_LIBRARY_TYPE,
            "zotero_library_id": ZOTERO_LIBRARY_ID,
            "zotero_collection_key": ZOTERO_COLLECTION_KEY,
            "collections": summary_collections,
            "quality": {
                "blocker_count": blocker_count,
                "review_count": review_count,
                "review_queue_count": len(review_queue),
                "source_monitor_count": len(source_fetch_log),
                "candidate_record_count": len(candidate_records),
                "catalogue_link_checks": len(link_status_rows),
            },
            "outputs": [
                "outputs/zotero_cache.json",
                "outputs/wordpress_neuro_resources.json",
                "outputs/catalogue_completeness_report.csv",
                "outputs/validation_failures.csv",
                "outputs/review_queue.csv",
                "outputs/changed_records.csv",
                "outputs/candidate_records.csv",
                "outputs/source_fetch_log.csv",
                "outputs/catalogue_link_status.csv",
            ],
        },
    )


if __name__ == "__main__":
    run()
