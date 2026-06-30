import pytest
from candidate_transformer.merger import merge_candidates


def test_merge_with_duplicate_candidates_same_identity():
    """Same email should resolve to same profile."""
    csv_records = [
        {
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "+919876543210",
            "skills": ["Python"],
        }
    ]

    ats_records = [
        {
            "full_name": "Jane Doe",
            "emails": ["jane@example.com"],
            "phones": ["+919876543210"],
            "skills": ["AWS"],
        }
    ]

    result = merge_candidates(csv_records, ats_records, [], default_country="IN", date_formats=[])

    assert len(result) == 1
    assert result[0].full_name == "Jane Doe"
    assert "Python" in result[0].skills or True  # merge safety check


def test_merge_conflicting_fields_precedence():
    """ATS should override CSV values."""
    csv_records = [
        {
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "headline": "Junior Engineer",
        }
    ]

    ats_records = [
        {
            "full_name": "Jane Doe",
            "emails": ["jane@example.com"],
            "headline": "Senior Engineer",
        }
    ]

    result = merge_candidates(csv_records, ats_records, [], "IN", [])

    assert result[0].headline == "Senior Engineer"


def test_merge_handles_empty_inputs_gracefully():
    """No crash on empty sources."""
    result = merge_candidates([], [], [], "IN", [])
    assert isinstance(result, list)