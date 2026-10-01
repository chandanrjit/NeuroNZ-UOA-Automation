"""Add verified new research evidence and retain a receipt after each write."""

from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Any

from .config import ZOTERO_COLLECTION_KEY
from .parsing import extract_doi, extract_pmid, parse_extra
from .reports import write_json
from .taxonomy import classify, condition_patch
from .dataset_updates import dataset_issue, dataset_item


def normal_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]", "", title.casefold())


BIBLIOGRAPHY_FIELDS = ("publicationTitle", "creators", "date", "volume", "issue", "pages", "ISSN", "journalAbbreviation", "language", "PMID", "PMCID", "rights", "libraryCatalog", "accessDate")


def bibliography(candidate: dict[str, str]) -> dict[str, Any]:
    source = json.loads(candidate.get("bibliography") or "{}")
    return {field: source[field] for field in BIBLIOGRAPHY_FIELDS if source.get(field)}


def verify_fields(data: dict[str, Any], fields: dict[str, Any]) -> None:
    if any(data.get(field) != value for field, value in fields.items()):
        raise RuntimeError("Zotero bibliography readback did not match the verified source")


def duplicate_tokens(data: dict[str, Any]) -> set[str]:
    extra = data.get("extra", "")
    url = str(data.get("url", "")).rstrip("/")
    doi = data.get("DOI") or extract_doi(url, extra)
    pmid = extract_pmid(url, extra)
    tokens = set()
    if doi:
        tokens.add("doi:" + doi.casefold().removeprefix("https://doi.org/"))
    if pmid:
        tokens.add("pmid:" + pmid)
    if url:
        tokens.add("url:" + url.casefold())
    if data.get("title"):
        tokens.add("title:" + normal_title(data["title"]))
    return tokens


def relevance_issue(candidate: dict[str, str]) -> str:
    if candidate.get("status") != "candidate":
        return "Source discovery error"
    if candidate.get("source_id") != "pubmed":
        return "Dataset requires catalogue metadata review before import"
    title = candidate.get("title", "")
    abstract = candidate.get("summary", "")
    if not title or not abstract or not candidate.get("pmid"):
        return "Missing verified PubMed title, abstract, or PMID"
    if not re.search(r"new zealand|aotearoa", abstract, re.I):
        return "NZ study context not established in abstract"
    if re.search(r"new zealand (?:white|rabbits?)", abstract, re.I):
        return "Animal breed match does not establish NZ relevance"
    if re.search(r"popular press|historical|history of", title, re.I):
        return "Historical commentary requires data relevance review"
    if not re.search(r"stroke|cerebrovascular|endovascular thrombectomy|epilep|dementia|parkinson|neurolog|neurodevelop|brain injury|ataxia|sca27b|migraine|acquired communication disorders", title, re.I):
        return "Neurological study focus requires review"
    if candidate.get("url") != f"https://pubmed.ncbi.nlm.nih.gov/{candidate['pmid']}/":
        return "Unexpected PubMed source URL"
    return ""


def update_candidates(client: Any, candidates: list[dict[str, str]], output_dir: Path) -> list[dict[str, Any]]:
    children = client.fetch_child_collections(ZOTERO_COLLECTION_KEY)
    evidence = [c for c in children if c["data"]["name"] == "02 Evidence Log"]
    if len(evidence) != 1:
        raise RuntimeError("Expected exactly one 02 Evidence Log child under the selected collection")
    target = evidence[0]["key"]
    existing = client.fetch_library_items()
    taxonomy_keys = {c["key"] for c in children if c["data"]["name"] == "03 Condition Taxonomy"}
    taxonomy = [item for item in existing if taxonomy_keys.intersection(item.get("data", {}).get("collections", []))]
    seen: set[str] = set()
    evidence_numbers = []
    for item in existing:
        data = item.get("data") or {}
        seen.update(duplicate_tokens(data))
        eid = parse_extra(data.get("extra")).get("NeuroNZ Evidence ID", "")
        match = re.fullmatch(r"E(\d+)", eid)
        if match:
            evidence_numbers.append(int(match[1]))
    next_id = max(evidence_numbers, default=0) + 1
    catalogue_keys = [c["key"] for c in children if c["data"]["name"] == "01 Catalogue Sources"]
    catalogue_numbers = [int(match[1]) for item in existing
        if (match := re.fullmatch(r"NZNEURO-(\d+)", parse_extra(item.get("data", {}).get("extra")).get("NeuroNZ Record ID", "")))]
    next_catalogue_id = max(catalogue_numbers, default=0) + 1
    manifest: list[dict[str, Any]] = []
    receipt_path = output_dir / "zotero_update_manifest.json"
    for candidate in candidates:
        row = {"candidate_id": candidate.get("candidate_id", ""), "title": candidate.get("title", ""), "collection_key": target}
        reason = relevance_issue(candidate)
        condition_matches = classify(candidate.get("title", ""), taxonomy)
        row["condition_matches"] = condition_matches
        row["relationship_status"] = "catalogue linkage pending review"
        candidate["condition_terms"] = "; ".join(m["name"] for m in condition_matches)
        fields = bibliography(candidate)
        tokens = duplicate_tokens({"title": candidate.get("title", ""), "url": candidate.get("url", ""), "DOI": candidate.get("doi", "")})
        if candidate.get("source_id") == "data-govt-nz":
            reason = dataset_issue(candidate, condition_matches)
            if reason or seen.intersection(tokens) or len(catalogue_keys) != 1:
                row.update(status="review" if reason or len(catalogue_keys) != 1 else "duplicate",
                    reason=reason or ("Catalogue collection unavailable" if len(catalogue_keys) != 1 else "Existing dataset in library"))
                manifest.append(row)
                write_json(receipt_path, manifest)
                continue
            record_id = f"NZNEURO-{next_catalogue_id:03d}"
            item = dataset_item(candidate, catalogue_keys[0], record_id, condition_matches)
            row.update(status="write_pending", record_id=record_id, collection_key=catalogue_keys[0], relationship_status="dataset condition verified")
            manifest.append(row)
            write_json(receipt_path, manifest)
            created = client.create_item(item)
            row.update(status="created_unverified", zotero_key=created["key"])
            write_json(receipt_path, manifest)
            verified = client.fetch_item(created["key"])
            verify_fields(verified["data"], item)
            row.update(status="created_verified", date_added=verified["data"]["dateAdded"], date_modified=verified["data"]["dateModified"], zotero_version=verified["version"])
            write_json(receipt_path, manifest)
            seen.update(tokens)
            next_catalogue_id += 1
            continue
        matched_items = [item for item in existing if duplicate_tokens(item.get("data", {})).intersection(tokens)]
        row["duplicate_zotero_keys"] = [item.get("key") for item in matched_items]
        # Repair only our own imported evidence with the exact PMID in this collection.
        matches = [item for item in existing if target in item.get("data", {}).get("collections", [])
                   and item.get("data", {}).get("itemType") == "journalArticle"
                   and any(tag.get("tag") == "nzneuro:phase2" for tag in item.get("data", {}).get("tags", []))
                   and extract_pmid(item["data"].get("url", ""), item["data"].get("extra", "")) == candidate.get("pmid")]
        if not reason and len(matches) == 1:
            current = client.fetch_item(matches[0]["key"])
            data = current["data"]
            enrichment = dict(fields, DOI=candidate.get("doi", ""))
            if data.get("DOI") and candidate.get("doi") and data["DOI"].casefold() != candidate["doi"].casefold():
                row.update(status="review", reason="Exact PMID matched but DOI conflicts with source")
                manifest.append(row)
                write_json(receipt_path, manifest)
                continue
            patch = {field: value for field, value in enrichment.items() if value and not data.get(field)}
            patch.update(condition_patch(data, condition_matches))
            row.update(zotero_key=current["key"], evidence_id=parse_extra(data.get("extra")).get("NeuroNZ Evidence ID"),
                       source_unavailable_fields=[field for field in BIBLIOGRAPHY_FIELDS if field not in fields])
            if patch:
                row.update(status="metadata_write_pending", changed_fields=sorted(patch), previous_date_modified=data["dateModified"])
                manifest.append(row)
                write_json(receipt_path, manifest)
                try:
                    client.patch_item(current["key"], current["version"], patch)
                except Exception as exc:
                    row.update(status="metadata_write_failed", reason=str(exc))
                    write_json(receipt_path, manifest)
                    raise
                row["status"] = "metadata_updated_unverified"
                write_json(receipt_path, manifest)
                verified = client.fetch_item(current["key"])
                try:
                    verify_fields(verified["data"], patch)
                except Exception as exc:
                    row["reason"] = str(exc)
                    write_json(receipt_path, manifest)
                    raise
                preserved = {field: value for field, value in data.items() if field not in patch and field not in ("version", "dateModified")}
                verify_fields(verified["data"], preserved)
                row.update(status="metadata_updated_verified", date_added=verified["data"]["dateAdded"],
                           date_modified=verified["data"]["dateModified"], zotero_version=verified["version"])
                write_json(receipt_path, manifest)
                continue
        if not reason and not seen.intersection(tokens):
            missing = [field for field in ("publicationTitle", "creators", "date") if not fields.get(field)]
            if missing:
                reason = "Missing required PubMed bibliography: " + ", ".join(missing)
            elif taxonomy and not condition_matches:
                reason = "No verified controlled condition match; taxonomy review required"
        if reason or seen.intersection(tokens):
            row.update(status="review" if reason else "duplicate", reason=reason or "Existing DOI, PMID, URL, or title in group library")
            manifest.append(row)
            write_json(receipt_path, manifest)
            continue
        eid = f"E{next_id:03d}"
        item = {
            **fields,
            "itemType": "journalArticle", "title": candidate["title"],
            "abstractNote": candidate["summary"], "url": candidate["url"],
            "DOI": candidate.get("doi", ""), "collections": [target],
            "tags": [{"tag": "nzneuro:phase2"}, {"tag": "type:evidence"}],
            "extra": "\n".join([
                f"NeuroNZ Evidence ID: {eid}", f"PMID: {candidate['pmid']}",
                f"Source candidate ID: {candidate['candidate_id']}",
                "Source category: Published research",
                "Availability / Access: Public PubMed abstract; full-text access varies by publisher",
                "Review status: Automated source and relevance checks passed; catalogue linkage pending review",
                f"All evidence URLs: {candidate['url']}",
            ]),
        }
        item.update(condition_patch(item, condition_matches))
        row.update(status="write_pending", evidence_id=eid)
        manifest.append(row)
        write_json(receipt_path, manifest)
        try:
            created = client.create_item(item)
            row.update(status="created_unverified", zotero_key=created["key"])
            write_json(receipt_path, manifest)
            verified = client.fetch_item(created["key"])
            data = verified["data"]
            verify_fields(data, fields)
            if (target not in data.get("collections", [])
                    or parse_extra(data.get("extra")).get("NeuroNZ Evidence ID") != eid
                    or data.get("title") != item["title"]
                    or data.get("url") != item["url"]):
                raise RuntimeError("Created item did not match intended collection and evidence ID")
            row.update(status="created_verified", date_added=data["dateAdded"], date_modified=data["dateModified"], zotero_version=verified["version"],
                       source_unavailable_fields=[field for field in BIBLIOGRAPHY_FIELDS if field not in fields])
            write_json(receipt_path, manifest)
        except Exception:
            row["reason"] = "Write or readback incomplete; inspect group library before retrying"
            write_json(receipt_path, manifest)
            raise
        seen.update(tokens)
        next_id += 1
    write_json(receipt_path, manifest)
    return manifest
