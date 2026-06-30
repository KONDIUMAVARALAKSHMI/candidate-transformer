from __future__ import annotations

from typing import Optional

# Minimal alias map for quick lookups and to avoid an external dependency when possible.
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
    """Normalize a country value to ISO 3166-1 alpha-2 code when possible.

    Strategy:
    - empty -> None
    - check local alias map
    - accept 2-letter alpha codes and return uppercased
    - if pycountry is available, try a fuzzy lookup
    - fall back to original trimmed value
    """
    if not value:
        return None
    v = value.strip()
    if not v:
        return None
    lowered = v.lower()
    if lowered in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[lowered]

    # 2-letter alpha code
    if len(v) == 2 and v.isalpha():
        return v.upper()

    # Try pycountry if installed for broader name support
    try:
        import pycountry  # type: ignore

        try:
            country = pycountry.countries.lookup(v)
            return country.alpha_2
        except Exception:
            # fallback: attempt exact name / official_name matches
            for c in pycountry.countries:
                name = getattr(c, "name", "")
                official = getattr(c, "official_name", "")
                if name and name.lower() == lowered:
                    return c.alpha_2
                if official and official.lower() == lowered:
                    return c.alpha_2
    except Exception:
        # pycountry not available or lookup failed; continue
        pass

    return v.upper() if len(v) == 2 else v
