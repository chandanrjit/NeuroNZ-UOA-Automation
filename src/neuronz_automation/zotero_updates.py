"""Add verified new research evidence and retain a receipt after each write."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .config import ZOTERO_COLLECTION_KEY
from .parsing import extract_doi, extract_pmid, parse_extra
from .reports import write_json


def normal_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]", "", title.casefold())


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
    manifest: list[dict[str, Any]] = []
    receipt_path = output_dir / "zotero_update_manifest.json"
    for candidate in candidates:
        row = {"candidate_id": candidate.get("candidate_id", ""), "title": candidate.get("title", ""), "collection_key": target}
        reason = relevance_issue(candidate)
        tokens = duplicate_tokens({"title": candidate.get("title", ""), "url": candidate.get("url", ""), "DOI": candidate.get("doi", "")})
        if reason or seen.intersection(tokens):
            row.update(status="review" if reason else "duplicate", reason=reason or "Existing DOI, PMID, URL, or title in group library")
            manifest.append(row)
            write_json(receipt_path, manifest)
            continue
        eid = f"E{next_id:03d}"
        item = {
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
        row.update(status="write_pending", evidence_id=eid)
        manifest.append(row)
        write_json(receipt_path, manifest)
        try:
            created = client.create_item(item)
            row.update(status="created_unverified", zotero_key=created["key"])
            write_json(receipt_path, manifest)
            verified = client.fetch_item(created["key"])
            data = verified["data"]
            if (target not in data.get("collections", [])
                    or parse_extra(data.get("extra")).get("NeuroNZ Evidence ID") != eid
                    or data.get("title") != item["title"]
                    or data.get("url") != item["url"]):
                raise RuntimeError("Created item did not match intended collection and evidence ID")
            row.update(status="created_verified", date_added=data["dateAdded"], date_modified=data["dateModified"], zotero_version=verified["version"])
            write_json(receipt_path, manifest)
        except Exception:
            row["reason"] = "Write or readback incomplete; inspect group library before retrying"
            write_json(receipt_path, manifest)
            raise
        seen.update(tokens)
        next_id += 1
    write_json(receipt_path, manifest)
    return manifest
