from __future__ import annotations

import re
from rapidfuzz import fuzz


def calculate_fuzzy_similarity(s1: str | None, s2: str | None) -> float:
    """
    Calculate the similarity ratio between two strings using rapidfuzz's WRatio.
    Returns a score between 0.0 and 100.0.
    """
    if s1 is None or s2 is None:
        return 0.0

    str1 = str(s1).strip()
    str2 = str(s2).strip()

    if not str1 or not str2:
        return 0.0

    return float(fuzz.WRatio(str1, str2))


def fuzzy_match_names(name1: str | None, name2: str | None, threshold: float = 88.0) -> bool:
    """
    Determine if two names match fuzzy-wise above a given threshold.
    """
    if name1 is None or name2 is None:
        return False

    n1 = name1.strip().lower()
    n2 = name2.strip().lower()

    if n1 == n2:
        return True

    score = calculate_fuzzy_similarity(n1, n2)
    return score >= threshold


def fuzzy_match_skills(skill1: str | None, skill2: str | None, threshold: float = 80.0) -> bool:
    """
    Determine if two skill names match fuzzy-wise.
    """
    if skill1 is None or skill2 is None:
        return False

    # Clean punctuation and normalize spacing to improve matching on patterns like React.js vs React JS
    s1 = re.sub(r"[^a-zA-Z0-9\s]", " ", skill1.strip().lower())
    s2 = re.sub(r"[^a-zA-Z0-9\s]", " ", skill2.strip().lower())

    s1 = re.sub(r"\s+", " ", s1).strip()
    s2 = re.sub(r"\s+", " ", s2).strip()

    if s1 == s2:
        return True

    # Use token sort ratio to handle word rearrangement
    score = float(fuzz.token_sort_ratio(s1, s2))
    return score >= threshold
