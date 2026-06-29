from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def parse_csv(path: str | Path) -> list[dict[str, Any]]:
    """Parse a CSV file into a list of dictionaries."""

    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        rows: list[dict[str, Any]] = []
        headers = next(reader, None)
        if not headers:
            return rows

        normalized_headers = [str(header).strip() for header in headers]
        for row in reader:
            cleaned_row: dict[str, Any] = {}
            for index, key in enumerate(normalized_headers):
                if index >= len(row):
                    cleaned_value = None
                else:
                    cleaned_value = str(row[index]).strip()

                if key.lower() == "skills" and cleaned_value:
                    if index == len(normalized_headers) - 1 and len(row) > len(normalized_headers):
                        combined = ", ".join(str(item).strip() for item in row[index:] if str(item).strip())
                        cleaned_value = _split_skills(combined)
                    else:
                        cleaned_value = _split_skills(cleaned_value)

                cleaned_row[str(key)] = cleaned_value
            rows.append(cleaned_row)
    return rows


def _split_skills(value: str) -> list[str]:
    if not value:
        return []

    parts = []
    for raw_part in value.replace(";", ",").split(","):
        cleaned = raw_part.strip()
        if not cleaned:
            continue
        canonical = _canonical_skill_name(cleaned)
        if canonical and canonical.lower() not in {part.lower() for part in parts}:
            parts.append(canonical)
    return parts


def _canonical_skill_name(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        return ""

    aliases = {
        "python": "Python",
        "sql": "SQL",
        "aws": "AWS",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "react": "React",
        "pandas": "Pandas",
        "numpy": "NumPy",
        "spark": "Spark",
        "tableau": "Tableau",
        "linux": "Linux",
        "git": "Git",
        "pytest": "Pytest",
        "api": "API",
        "rest": "REST",
        "graphql": "GraphQL",
    }
    lowered = normalized.lower()
    return aliases.get(lowered, normalized)
