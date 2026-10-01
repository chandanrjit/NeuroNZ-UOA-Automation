"""Import public NZ dataset descriptions only when controlled metadata is verified."""
from __future__ import annotations
import json
import re
from typing import Any
from .taxonomy import condition_patch


def dataset_issue(candidate: dict[str, str], matches: list[dict[str, str]]) -> str:
    if candidate.get("status") != "candidate":
        return "Dataset source discovery failed: " + candidate.get("error_message", "")
    if not all(candidate.get(field) for field in ("title", "summary", "source_organisation", "url")):
        return "Missing dataset title, description, organisation, or URL"
    if not re.search(r"new zealand|aotearoa", candidate["summary"], re.I):
        return "NZ dataset context not explicitly established in description"
    if not matches:
        return "No controlled condition match for dataset title"
    metadata = json.loads(candidate.get("dataset_metadata") or "{}")
    if metadata.get("private") is not False or not metadata.get("resources"):
        return "Public dataset status and downloadable resources not verified"
    if not metadata.get("license"):
        return "Dataset access licence not provided by source"
    if not candidate["url"].startswith("https://catalogue.data.govt.nz/dataset/"):
        return "Unexpected dataset source URL"
    return ""


def dataset_item(candidate: dict[str, str], target: str, record_id: str, matches: list[dict[str, str]]) -> dict[str, Any]:
    metadata = json.loads(candidate["dataset_metadata"])
    bibliography = json.loads(candidate.get("bibliography") or "{}")
    item = {"itemType": "webpage", "title": candidate["title"], "abstractNote": candidate["summary"],
            "websiteTitle": candidate["source_organisation"], "url": candidate["url"],
            "date": bibliography.get("date", ""), "accessDate": bibliography.get("accessDate", ""),
            "language": metadata.get("language", ""), "rights": metadata["license"],
            "collections": [target], "tags": [{"tag": "nzneuro:phase2"}, {"tag": "type:dataset"}, {"tag": "category:Dataset"}],
            "extra": "\n".join([f"NeuroNZ Record ID: {record_id}", f"Source candidate ID: {candidate['candidate_id']}",
                "Source category: Dataset", "Availability / Access: Public resource links listed in data.govt.nz; licence: " + metadata["license"],
                "Review status: Automated source and condition checks passed; detailed dataset filters pending review",
                "All source links: " + "; ".join([candidate["url"], *metadata["resources"]])])}
    item.update(condition_patch(item, matches))
    return item
