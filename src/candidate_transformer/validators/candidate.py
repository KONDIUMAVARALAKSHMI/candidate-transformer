from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime
from typing import Any


def validate_email_format(email: str) -> bool:
    """
    Validate basic syntax of an email address.
    """
    if not email:
        return False
    # Simple RFC 5322 regex for standard emails
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email.strip()))


def validate_phone_format(phone: str) -> bool:
    """
    Check if phone format is a valid E.164 structure (must start with + followed by 7 to 15 digits).
    """
    if not phone:
        return False
    # E.164 pattern: +[1-9]\d{1,14}
    pattern = r"^\+[1-9]\d{6,14}$"
    return bool(re.match(pattern, phone.strip()))


def validate_chronological_experience(experience: list[Any]) -> bool:
    """
    Verify chronological sequence consistency of employment history.
    Ensures that for each job record, the start date does not succeed the end date.
    Returns True if valid, raises ValueError or returns False if invalid.
    """
    for index, exp in enumerate(experience):
        start_str = None
        end_str = None

        if isinstance(exp, Mapping):
            start_str = exp.get("start")
            end_str = exp.get("end")
        elif hasattr(exp, "start") and hasattr(exp, "end"):
            start_str = exp.start
            end_str = exp.end

        if not start_str or not end_str:
            continue

        try:
            # Parse dates in YYYY-MM format
            start_date = datetime.strptime(start_str.strip(), "%Y-%m")
            end_date = datetime.strptime(end_str.strip(), "%Y-%m")

            if start_date > end_date:
                raise ValueError(
                    f"Job experience entry at index {index} has a start date '{start_str}' "
                    f"that is after its end date '{end_str}'."
                )
        except ValueError as exc:
            # Re-raise date order ValueError or propagate parse error
            if "has a start date" in str(exc):
                raise
            # If date string is malformed but not necessarily out of order, ignore or log
            continue
    return True
