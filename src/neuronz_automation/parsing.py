"""Parsing helpers for Zotero item metadata."""

from __future__ import annotations

import re
from typing import Any

DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
PMID_RE = re.compile(r"(?:pubmed\.ncbi\.nlm\.nih\.gov/|PMID:\s*)(\d+)", re.IGNORECASE)


def parse_extra(extra: str | None) -> dict[str, str]:
    """Parse Zotero newline-delimited key/value metadata from data.extra."""
    parsed: dict[str, str] = {}
    if not extra:
        return parsed

    for raw_line in extra.splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def extract_tags(data: dict[str, Any]) -> list[str]:
    tags = data.get("tags") or []
    return [tag["tag"] for tag in tags if isinstance(tag, dict) and tag.get("tag")]


def extract_doi(*values: str | None) -> str:
    for value in values:
        if not value:
            continue
        match = DOI_RE.search(value)
        if match:
            return match.group(0)
    return ""


def extract_pmid(*values: str | None) -> str:
    for value in values:
        if not value:
            continue
        match = PMID_RE.search(value)
        if match:
            return match.group(1)
    return ""

