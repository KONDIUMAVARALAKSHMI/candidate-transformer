from __future__ import annotations

COUNTRY_ALIASES: dict[str, str] = {
    "india": "IN",
    "in": "IN",
    "ind": "IN",
    "us": "US",
    "usa": "US",
    "united states": "US",
    "united states of america": "US",
    "uk": "GB",
    "u.k.": "GB",
    "united kingdom": "GB",
    "great britain": "GB",
    "england": "GB",
    "canada": "CA",
    "ca": "CA",
    "singapore": "SG",
    "sg": "SG",
    "australia": "AU",
    "au": "AU",
    "germany": "DE",
    "de": "DE",
    "france": "FR",
    "fr": "FR",
    "netherlands": "NL",
    "nl": "NL",
    "spain": "ES",
    "es": "ES",
    "japan": "JP",
    "jp": "JP",
}


def normalize_country(value: str | None) -> str | None:
    """Normalize country to ISO alpha-2 code when possible."""

    if not value:
        return None

    v = value.strip()
    if not v:
        return None

    lowered = v.lower()

    # -------------------------
    # Alias lookup (fast path)
    # -------------------------
    if lowered in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[lowered]

    # -------------------------
    # direct alpha-2 code
    # -------------------------
    if len(v) == 2 and v.isalpha():
        return v.upper()

    # -------------------------
    # pycountry lookup (optional dependency)
    # -------------------------
    try:
        import pycountry  # type: ignore

        country = pycountry.countries.lookup(v)
        if country:
            return str(country.alpha_2)

    except Exception:
        # pycountry not available OR lookup failed
        pass

    # -------------------------
    # fallback matching loop
    # (this is what was NOT being hit before)
    # -------------------------
    try:
        import pycountry  # type: ignore

        for c in pycountry.countries:
            name = getattr(c, "name", "")
            official = getattr(c, "official_name", "")

            if name and name.lower() == lowered:
                return str(c.alpha_2)

            if official and official.lower() == lowered:
                return str(c.alpha_2)

    except Exception:
        # module not available → skip
        pass

    # -------------------------
    # final fallback
    # -------------------------
    return v.upper() if len(v) == 2 else v