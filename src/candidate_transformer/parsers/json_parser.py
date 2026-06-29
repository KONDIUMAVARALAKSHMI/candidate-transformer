from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def parse_json(path: str | Path) -> list[dict[str, Any]]:
    """Parse a JSON or JSONL file into a list of dictionaries."""

    json_path = Path(path)
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    if json_path.suffix.lower() == ".jsonl":
        records: list[dict[str, Any]] = []
        with json_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    records.append(payload)
        return records

    try:
        with json_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
        return []

    if isinstance(payload, dict):
        if isinstance(payload.get("candidates"), list):
            return [item for item in payload["candidates"] if isinstance(item, dict)]
        return [payload]

    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    return []
