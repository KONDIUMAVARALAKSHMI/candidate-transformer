from __future__ import annotations

import phonenumbers


def normalize_phone(value: str | None, default_country: str = "IN") -> str | None:
    """Normalize a phone number to E.164 format."""

    if not value:
        return None

    cleaned = str(value).strip()
    if not cleaned:
        return None

    try:
        parsed = phonenumbers.parse(cleaned, default_country.upper())
    except phonenumbers.NumberParseException:
        try:
            parsed = phonenumbers.parse(cleaned, None)
        except phonenumbers.NumberParseException:
            return None

    if not phonenumbers.is_valid_number(parsed):
        return None

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
