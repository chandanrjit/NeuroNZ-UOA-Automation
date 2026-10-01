"""Small Zotero Web API client using only the Python standard library."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import ZOTERO_API_BASE, ZOTERO_LIBRARY_ID, ZOTERO_LIBRARY_TYPE


@dataclass(frozen=True)
class ZoteroClient:
    api_key: str | None = None
    timeout_seconds: int = 60

    def _headers(self) -> dict[str, str]:
        headers = {"Zotero-API-Version": "3"}
        if self.api_key:
            headers["Zotero-API-Key"] = self.api_key
        return headers

    def _get_json(self, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        query = urlencode(params)
        url = f"{ZOTERO_API_BASE}{path}?{query}"
        request = Request(url, headers=self._headers())
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Zotero API request failed with HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Zotero API request failed: {exc.reason}") from exc

    def fetch_collection_items(self, collection_key: str, limit: int = 100) -> list[dict[str, Any]]:
        path = f"/{ZOTERO_LIBRARY_TYPE}/{ZOTERO_LIBRARY_ID}/collections/{collection_key}/items"
        return self._get_all(path, limit)

    def _get_all(self, path: str, limit: int = 100) -> list[dict[str, Any]]:
        all_items: list[dict[str, Any]] = []
        start = 0

        while True:
            batch = self._get_json(
                path,
                {
                    "format": "json",
                    "include": "data",
                    "limit": limit,
                    "start": start,
                },
            )
            all_items.extend(batch)
            if len(batch) < limit:
                return all_items
            start += limit

    def fetch_collection_tree_items(self, collection_key: str) -> list[dict[str, Any]]:
        """Read the selected collection and descendants; Zotero item reads are not recursive."""
        prefix = f"/{ZOTERO_LIBRARY_TYPE}/{ZOTERO_LIBRARY_ID}/collections"
        pending = [collection_key]
        visited: set[str] = set()
        items_by_key: dict[str, dict[str, Any]] = {}
        while pending:
            key = pending.pop()
            if key in visited:
                continue
            visited.add(key)
            for item in self.fetch_collection_items(key):
                items_by_key[item["key"]] = item
            for child in self._get_all(f"{prefix}/{key}/collections"):
                if child["data"].get("name") != "04 Excluded Sources":
                    pending.append(child["key"])
        return list(items_by_key.values())
