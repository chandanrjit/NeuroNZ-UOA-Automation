"""Classify against existing controlled conditions without inventing new IDs."""
from __future__ import annotations

import re
from typing import Any
from .parsing import parse_extra

# Reviewed aliases: broad neurological terms are deliberately not diagnoses.
ALIASES = {
    "Ataxia": ("sca27b", "spinocerebellar ataxia"),
    "Stroke": ("cerebrovascular", "endovascular thrombectomy", "code stroke"),
    "Epilepsy": ("epileptic", "epilepsies"),
    "Alzheimer's disease and other dementias": ("dementia", "alzheimer's disease", "alzheimers"),
    "Parkinson's disease": ("parkinson", "parkinson's"),
    "Neurological complications due to preterm birth": ("preterm", "prematurity"),
}


def phrase_match(text: str, phrase: str) -> bool:
    pattern = r"(?<!\w)" + re.escape(phrase.casefold()) + r"(?!\w)"
    for match in re.finditer(pattern, text.casefold()) if phrase else []:
        prefix = text[max(0, match.start() - 5):match.start()].casefold()
        suffix = text[match.end():match.end() + 5].casefold()
        if not prefix.endswith(("non-", "non ", "not ")) and not suffix.startswith("-like"):
            return True
    return False


def classify(title: str, taxonomy: list[dict[str, Any]]) -> list[dict[str, str]]:
    matches = []
    for item in taxonomy:
        data = item.get("data", {})
        extra = parse_extra(data.get("extra"))
        condition_id = extra.get("NeuroNZ Condition ID")
        name = extra.get("Public name") or data.get("title", "")
        if not condition_id or name == "Other neurological disorders":
            continue
        synonyms = [s.strip() for s in extra.get("Synonyms", "").split(";") if s.strip()]
        terms = [name, *synonyms, *ALIASES.get(name, ())]
        matched = next((term for term in terms if phrase_match(title, term)), None)
        if matched:
            matches.append({"condition_id": condition_id, "name": name, "matched_term": matched, "basis": "explicit_title"})
    return matches


def condition_patch(data: dict[str, Any], matches: list[dict[str, str]]) -> dict[str, Any]:
    if not matches:
        return {}
    curated = parse_extra(data.get("extra")).get("NeuroNZ Condition IDs")
    if curated:
        allowed = {value.strip() for value in curated.split(";")}
        matches = [match for match in matches if match["condition_id"] in allowed]
        if not matches:
            return {}
    tags = list(data.get("tags", []))
    existing_tags = {tag.get("tag") for tag in tags}
    for match in matches:
        tag = "nzneuro:condition:" + match["condition_id"]
        if tag not in existing_tags:
            tags.append({"tag": tag})
    patch = {}
    if tags != data.get("tags", []):
        patch["tags"] = tags
    extra = data.get("extra", "")
    if not parse_extra(extra).get("NeuroNZ Condition IDs"):
        patch["extra"] = extra.rstrip() + "\nNeuroNZ Condition IDs: " + "; ".join(m["condition_id"] for m in matches)
    return patch


def audit_items(items: list[dict[str, Any]], taxonomy: list[dict[str, Any]]) -> list[dict[str, Any]]:
    known = {parse_extra(x.get("data", {}).get("extra")).get("NeuroNZ Condition ID") for x in taxonomy}
    rows = []
    for item in items:
        data = item.get("data", {})
        extra = parse_extra(data.get("extra"))
        kind = "taxonomy" if extra.get("NeuroNZ Condition ID") else "evidence" if extra.get("NeuroNZ Evidence ID") else "catalogue"
        ids = [x.strip() for x in extra.get("NeuroNZ Condition IDs", "").split(";") if x.strip()]
        missing = []
        if kind != "taxonomy" and not ids:
            missing.append("condition_link_needs_review")
        if any(x not in known for x in ids):
            missing.append("unknown_condition_id")
        if kind == "taxonomy" and not extra.get("Synonyms"):
            missing.append("synonyms_not_recorded")
        if kind == "evidence" and data.get("itemType") == "journalArticle":
            missing += ["missing_" + field for field in ("title", "abstractNote", "publicationTitle", "creators", "date", "url") if not data.get(field)]
        if kind == "evidence" and not extra.get("NeuroNZ Record ID"):
            missing.append("catalogue_relationship_needs_review")
        rows.append({"zotero_key": item.get("key"), "kind": kind, "title": data.get("title"),
                     "condition_ids": ids, "suggested_matches": classify(data.get("title", ""), taxonomy) if kind != "taxonomy" else [],
                     "gaps": missing, "date_modified": data.get("dateModified")})
    return rows
