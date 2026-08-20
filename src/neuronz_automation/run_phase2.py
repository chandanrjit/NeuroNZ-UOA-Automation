"""Run the first safe Phase 2 automation workflow."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import COLLECTIONS, OUTPUT_DIR
from .parsing import extract_doi, extract_pmid, extract_tags, parse_extra
from .reports import completeness_rows, write_csv, write_json
from .zotero_client import ZoteroClient


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


def run() -> None:
    started_at = datetime.now(timezone.utc).isoformat()
    output_dir = Path(OUTPUT_DIR)
    client = ZoteroClient(api_key=os.environ.get("ZOTERO_API_KEY"))

    cache: dict[str, list[dict[str, Any]]] = {}
    summary_collections: list[dict[str, Any]] = []

    for collection_type, config in COLLECTIONS.items():
        items = client.fetch_collection_items(config["key"])
        records = [normalise_zotero_item(item, config["stable_id_field"]) for item in items]
        cache[collection_type] = records
        summary_collections.append(
            {
                "collection_type": collection_type,
                "collection_name": config["name"],
                "collection_key": config["key"],
                "items_fetched": len(records),
                "records_with_stable_id": sum(1 for record in records if record["stable_id"]),
            }
        )

    catalogue_records = [wordpress_record(record) for record in cache["catalogue"]]
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

    write_json(output_dir / "zotero_cache.json", cache)
    write_json(output_dir / "wordpress_neuro_resources.json", catalogue_records)
    write_csv(
        output_dir / "catalogue_completeness_report.csv",
        completeness_rows(catalogue_records, completeness_fields),
        ["field", "populated", "total", "coverage_percent"],
    )

    finished_at = datetime.now(timezone.utc).isoformat()
    write_json(
        output_dir / "latest_run_summary.json",
        {
            "started_at": started_at,
            "finished_at": finished_at,
            "mode": "read_only",
            "collections": summary_collections,
            "outputs": [
                "outputs/zotero_cache.json",
                "outputs/wordpress_neuro_resources.json",
                "outputs/catalogue_completeness_report.csv",
            ],
        },
    )


if __name__ == "__main__":
    run()

