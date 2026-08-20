"""Quality gates for WordPress-facing NeuroNZ records."""

from __future__ import annotations

from typing import Any

REQUIRED_PUBLIC_FIELDS = [
    "record_id",
    "title",
    "primary_link",
    "source_category",
    "availability_access",
]

RECOMMENDED_FILTER_FIELDS = [
    "type_of_data",
    "age_group",
    "available_in_idi",
]


def validation_rows(records: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen_ids: dict[str, int] = {}

    for record in records:
        record_id = str(record.get("record_id", "")).strip()
        seen_ids[record_id] = seen_ids.get(record_id, 0) + 1

        for field in REQUIRED_PUBLIC_FIELDS:
            if not str(record.get(field, "")).strip():
                rows.append(
                    {
                        "record_id": record_id,
                        "severity": "blocker",
                        "field": field,
                        "issue": "Required public field is blank",
                    }
                )

        for field in RECOMMENDED_FILTER_FIELDS:
            if not str(record.get(field, "")).strip():
                rows.append(
                    {
                        "record_id": record_id,
                        "severity": "review",
                        "field": field,
                        "issue": "Recommended filter/enrichment field is blank",
                    }
                )

        public_text = " ".join(
            str(record.get(field, ""))
            for field in ("summary", "availability_access", "all_source_links", "population_coverage")
        )
        if "verification pending" in public_text.lower():
            rows.append(
                {
                    "record_id": record_id,
                    "severity": "review",
                    "field": "public_text",
                    "issue": "Contains Verification pending text that should remain internal unless approved",
                }
            )

    for record_id, count in seen_ids.items():
        if record_id and count > 1:
            rows.append(
                {
                    "record_id": record_id,
                    "severity": "blocker",
                    "field": "record_id",
                    "issue": f"Duplicate stable ID appears {count} times",
                }
            )

    return rows


def review_queue_rows(validation: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in validation if row["severity"] in {"blocker", "review"}]


def changed_record_rows(
    previous_records: list[dict[str, Any]], current_records: list[dict[str, Any]]
) -> list[dict[str, str]]:
    previous_by_id = {
        str(record.get("record_id", "")).strip(): record
        for record in previous_records
        if str(record.get("record_id", "")).strip()
    }
    rows: list[dict[str, str]] = []

    for record in current_records:
        record_id = str(record.get("record_id", "")).strip()
        if not record_id:
            continue
        previous = previous_by_id.get(record_id)
        if previous is None:
            rows.append({"record_id": record_id, "change_status": "new", "changed_fields": ""})
            continue

        changed_fields = sorted(
            field
            for field, value in record.items()
            if field != "zotero_version" and previous.get(field) != value
        )
        rows.append(
            {
                "record_id": record_id,
                "change_status": "changed" if changed_fields else "unchanged",
                "changed_fields": "; ".join(changed_fields),
            }
        )

    return rows

