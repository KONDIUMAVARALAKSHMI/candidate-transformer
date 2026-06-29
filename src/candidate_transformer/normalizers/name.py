from __future__ import annotations

import re


def normalize_name(value: str | None) -> str | None:
    """Clean and title-case a human name."""

    if not value:
        return None

    cleaned = re.sub(r"\s+", " ", str(value).strip())
    if not cleaned:
        return None

    parts = [part.strip() for part in cleaned.split(" ") if part.strip()]
    formatted_parts: list[str] = []
    for part in parts:
        if not part:
            continue
        formatted_parts.append("-".join(word.capitalize() for word in part.split("-")))

    return " ".join(formatted_parts)
