from __future__ import annotations

from datetime import datetime

from dateutil import parser


def normalize_date(value: str | None, date_formats: list[str] | None = None) -> str | None:
    """Normalize a date-like value to YYYY-MM."""

    if not value:
        return None

    candidate = str(value).strip()
    if not candidate:
        return None

    formats = date_formats or ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%B %d, %Y"]
    for fmt in formats:
        try:
            parsed = datetime.strptime(candidate, fmt)
            return parsed.strftime("%Y-%m")
        except ValueError:
            continue

    try:
        parsed = parser.parse(candidate)
    except (TypeError, ValueError):
        return None

    return parsed.strftime("%Y-%m")
