"""Small Zotero Web API client using only the Python standard library."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import ZOTERO_API_BASE, ZOTERO_USER_ID


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
        path = f"/users/{ZOTERO_USER_ID}/collections/{collection_key}/items"
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

