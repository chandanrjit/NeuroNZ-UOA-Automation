"""Report generation for Phase 2 automation outputs."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def completeness_rows(records: list[dict[str, Any]], fields: list[str]) -> list[dict[str, Any]]:
    total = len(records)
    rows: list[dict[str, Any]] = []
    for field in fields:
        populated = sum(1 for record in records if str(record.get(field, "")).strip())
        rows.append(
            {
                "field": field,
                "populated": populated,
                "total": total,
                "coverage_percent": round((populated / total) * 100, 2) if total else 0,
            }
        )
    return rows
