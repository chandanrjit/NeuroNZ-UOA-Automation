"""Source-specific candidate discovery for Phase 2 automation."""

from __future__ import annotations

import json
from json import JSONDecodeError
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

USER_AGENT = "NeuroNZ-UOA-Automation/0.1 (+https://github.com/chandanrjit/NeuroNZ-UOA-Automation)"

PUBMED_QUERY = (
    '("New Zealand"[Title/Abstract] OR Aotearoa[Title/Abstract]) AND '
    "(stroke OR epilepsy OR dementia OR Parkinson OR neurological OR neurology)"
)

DATA_GOVT_QUERIES = [
    "neurological",
    "stroke",
    "dementia",
    "disability health",
]


def fetch_json(url: str, timeout_seconds: int = 30) -> dict[str, Any]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def candidate_error(source_id: str, message: str) -> dict[str, str]:
    return {
        "candidate_id": "",
        "source_id": source_id,
        "title": "",
        "url": "",
        "source_organisation": "",
        "candidate_type": "source_error",
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "doi": "",
        "pmid": "",
        "summary": "",
        "condition_terms": "",
        "status": "error",
        "error_message": message,
    }


def pubmed_metadata(xml: str) -> dict[str, dict[str, str]]:
    records = {}
    for article in ET.fromstring(xml).findall(".//PubmedArticle"):
        pmid = article.findtext(".//MedlineCitation/PMID", "")
        title = article.find(".//ArticleTitle")
        journal = article.find(".//Article/Journal")
        pubdate = journal.find("JournalIssue/PubDate") if journal is not None else None
        date = ""
        if pubdate is not None:
            date = pubdate.findtext("MedlineDate", "") or "-".join(
                pubdate.findtext(field, "") for field in ("Year", "Month", "Day") if pubdate.findtext(field)
            )
        creators = []
        for author in article.findall(".//Article/AuthorList/Author"):
            collective = author.findtext("CollectiveName")
            if collective:
                creators.append({"creatorType": "author", "name": collective})
            elif author.findtext("LastName"):
                creators.append({"creatorType": "author", "firstName": author.findtext("ForeName") or author.findtext("Initials", ""), "lastName": author.findtext("LastName")})
        bibliography = {
            "publicationTitle": journal.findtext("Title", "") if journal is not None else "",
            "journalAbbreviation": journal.findtext("ISOAbbreviation", "") if journal is not None else "",
            "volume": journal.findtext("JournalIssue/Volume", "") if journal is not None else "",
            "issue": journal.findtext("JournalIssue/Issue", "") if journal is not None else "",
            "ISSN": journal.findtext("ISSN", "") if journal is not None else "",
            "pages": article.findtext(".//Article/Pagination/MedlinePgn", "") or "-".join(
                article.findtext(".//Article/Pagination/" + field, "")
                for field in ("StartPage", "EndPage") if article.findtext(".//Article/Pagination/" + field)
            ),
            "date": date, "creators": creators,
            "language": "; ".join(e.text or "" for e in article.findall(".//Article/Language")),
            "PMID": pmid,
            "PMCID": next((e.text or "" for e in article.findall(".//PubmedData/ArticleIdList/ArticleId") if e.get("IdType") == "pmc"), ""),
            "rights": article.findtext(".//Article/Abstract/CopyrightInformation", ""),
            "libraryCatalog": "PubMed",
        }
        records[pmid] = {
            "title": "".join(title.itertext()) if title is not None else "",
            "summary": "\n".join("".join(e.itertext()) for e in article.findall(".//AbstractText")),
            "doi": next((e.text or "" for e in article.findall(".//PubmedData/ArticleIdList/ArticleId") if e.get("IdType") == "doi"), ""),
            "bibliography": json.dumps(bibliography, ensure_ascii=False),
        }
    return records


def discover_pubmed_candidates(retmax: int = 20, existing_pmids: list[str] | None = None) -> list[dict[str, str]]:
    detected_at = datetime.now(timezone.utc).isoformat()
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urlencode(
        {
            "db": "pubmed",
            "term": PUBMED_QUERY,
            "retmode": "json",
            "retmax": retmax,
            "sort": "pub date",
            "tool": "neuronz_uoa_automation",
        }
    )

    try:
        search = fetch_json(search_url)
        pmids = list(dict.fromkeys(search.get("esearchresult", {}).get("idlist", []) + (existing_pmids or [])))
        if not pmids:
            return []

        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + urlencode(
            {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "json",
                "tool": "neuronz_uoa_automation",
            }
        )
        summary = fetch_json(summary_url)
        full_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urlencode(
            {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml", "tool": "neuronz_uoa_automation"}
        )
        request = Request(full_url, headers={"User-Agent": USER_AGENT})
        with urlopen(request, timeout=30) as response:
            full_records = pubmed_metadata(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, RuntimeError, JSONDecodeError, ET.ParseError) as exc:
        return [candidate_error("pubmed", str(exc))]

    result = summary.get("result", {})
    rows: list[dict[str, str]] = []
    for pmid in pmids:
        item = result.get(pmid, {})
        if not item:
            continue
        rows.append(
            {
                "candidate_id": f"pubmed:{pmid}",
                "source_id": "pubmed",
                "title": full_records.get(pmid, {}).get("title", ""),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "source_organisation": "PubMed/MEDLINE",
                "candidate_type": "bibliographic_record",
                "detected_at": detected_at,
                "doi": full_records.get(pmid, {}).get("doi", ""),
                "pmid": pmid,
                "summary": full_records.get(pmid, {}).get("summary", ""),
                "bibliography": json.dumps(dict(json.loads(full_records.get(pmid, {}).get("bibliography", "{}")), accessDate=datetime.fromisoformat(detected_at).strftime("%Y-%m-%d %H:%M:%S"))),
                "condition_terms": "",
                "status": "candidate",
                "error_message": "",
            }
        )
    return rows


def discover_data_govt_candidates(rows_per_query: int = 10) -> list[dict[str, str]]:
    detected_at = datetime.now(timezone.utc).isoformat()
    rows_by_url: dict[str, dict[str, str]] = {}

    for query in DATA_GOVT_QUERIES:
        url = "https://catalogue.data.govt.nz/api/3/action/package_search?" + urlencode(
            {"q": query, "rows": rows_per_query}
        )
        try:
            payload = fetch_json(url)
        except (HTTPError, URLError, TimeoutError, RuntimeError, JSONDecodeError) as exc:
            rows_by_url[f"error:{query}"] = candidate_error("data-govt-nz", f"{query}: {exc}")
            continue

        if payload.get("success") is not True:
            rows_by_url[f"error:{query}"] = candidate_error("data-govt-nz", f"{query}: CKAN returned success=false")
            continue
        for package in payload.get("result", {}).get("results", []):
            package_name = package.get("name", "")
            page_url = f"https://catalogue.data.govt.nz/dataset/{package_name}" if package_name else ""
            if not page_url or page_url in rows_by_url:
                continue
            rows_by_url[page_url] = {
                "candidate_id": f"data-govt-nz:{package.get('id', package_name)}",
                "source_id": "data-govt-nz",
                "title": package.get("title") or package_name,
                "url": page_url,
                "source_organisation": package.get("organization", {}).get("title", "data.govt.nz"),
                "candidate_type": "dataset_or_catalogue_record",
                "detected_at": detected_at,
                "doi": "",
                "pmid": "",
                "summary": package.get("notes") or "",
                "condition_terms": "",
                "bibliography": json.dumps({"websiteTitle": "data.govt.nz", "date": package.get("metadata_modified", "")[:10],
                    "accessDate": datetime.fromisoformat(detected_at).strftime("%Y-%m-%d %H:%M:%S"), "libraryCatalog": "data.govt.nz"}),
                "dataset_metadata": json.dumps({"private": package.get("private"), "license": package.get("license_title") or package.get("license_id", ""),
                    "resources": [r["url"] for r in package.get("resources", []) if r.get("url", "").startswith("https://")],
                    "language": package.get("language", "")}),
                "status": "candidate",
                "error_message": "",
            }

    return list(rows_by_url.values())


def discover_candidates(existing_pmids: list[str] | None = None) -> list[dict[str, str]]:
    return discover_pubmed_candidates(existing_pmids=existing_pmids) + discover_data_govt_candidates()
