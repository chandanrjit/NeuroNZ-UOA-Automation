"""Source registry monitoring and lightweight URL checks."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def load_source_registry(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def check_url(url: str, timeout_seconds: int = 20) -> dict[str, Any]:
    """Check a URL with HEAD first and GET fallback for servers that reject HEAD."""
    if not url:
        return {"status": "missing_url", "status_code": "", "error_message": "No URL supplied"}

    for method in ("HEAD", "GET"):
        request = Request(
            url,
            method=method,
            headers={
                "User-Agent": "NeuroNZ-UOA-Automation/0.1 (+https://github.com/chandanrjit/NeuroNZ-UOA-Automation)"
            },
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                return {
                    "status": "ok",
                    "status_code": response.status,
                    "error_message": "",
                    "checked_method": method,
                }
        except HTTPError as exc:
            if method == "HEAD" and exc.code in {403, 405, 501}:
                continue
            return {
                "status": "http_error",
                "status_code": exc.code,
                "error_message": exc.reason,
                "checked_method": method,
            }
        except URLError as exc:
            return {
                "status": "url_error",
                "status_code": "",
                "error_message": str(exc.reason),
                "checked_method": method,
            }
        except TimeoutError:
            return {
                "status": "timeout",
                "status_code": "",
                "error_message": f"Timed out after {timeout_seconds}s",
                "checked_method": method,
            }

    return {"status": "failed", "status_code": "", "error_message": "URL check failed"}


def monitor_registered_sources(registry_path: Path) -> list[dict[str, Any]]:
    checked_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, Any]] = []
    for source in load_source_registry(registry_path):
        if source.get("source_type") == "Zotero API":
            rows.append(
                {
                    **source,
                    "checked_at": checked_at,
                    "status": "covered_by_zotero_client",
                    "status_code": "",
                    "error_message": "",
                    "checked_method": "ZoteroClient",
                }
            )
            continue

        result = check_url(source.get("primary_url", ""))
        rows.append({**source, "checked_at": checked_at, **result})
    return rows

