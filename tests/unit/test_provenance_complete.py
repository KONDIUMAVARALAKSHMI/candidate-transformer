
from candidate_transformer.merger import _apply_provenance, _merge_record
from candidate_transformer.schemas import (
    CandidateRecord,
    Education,
    Experience,
    Links,
    Location,
    Skill,
)


def test_provenance_completeness() -> None:
    # Build a record containing every populated field type
    record = CandidateRecord(
        candidate_id="ATS-001",
        full_name="Jane Doe",
        emails=["jane@example.com"],
        phones=["+14155550101"],
        location=Location(city="San Francisco", region="CA", country="US"),
        links=Links(linkedin="linkedin.com/in/jane", github="github.com/jane"),
        headline="Senior Lead Engineer",
        years_experience=10.0,
        skills=[Skill(name="Python", confidence=0.9, sources=["ats"])],
        experience=[Experience(company="Acme", title="Engineer", start="2020-01", end="2021-01")],
        education=[Education(institution="Stanford", degree="MS", field="CS", end_year=2019)],
    )

    # Apply base provenance for the 'ats' source
    _apply_provenance(record, "ats")

    # Verify that every populated field has a corresponding provenance entry
    provenance_fields = {entry.field for entry in record.provenance}

    expected_fields = [
        "candidate_id",
        "full_name",
        "emails",
        "phones",
        "location",
        "links",
        "headline",
        "years_experience",
        "skills",
        "experience",
        "education",
    ]

    for field in expected_fields:
        assert any(
            f == field or f.startswith(f"{field}.") for f in provenance_fields
        ), f"Field '{field}' is missing a provenance entry."

    # Verify each provenance entry contains required fields, sources, and methods
    for entry in record.provenance:
        assert entry.field is not None and len(entry.field) > 0
        assert entry.source is not None and len(entry.source) > 0
        assert entry.method is not None and len(entry.method) > 0


def test_provenance_retains_history_after_merge() -> None:
    # Create existing record from CSV
    existing = CandidateRecord(
        full_name="Jane Doe",
        emails=["jane@example.com"],
    )
    _apply_provenance(existing, "csv")

    # Create incoming record from ATS
    incoming = CandidateRecord(
        full_name="Jane Doe",
        emails=["jane@example.com", "jane.doe@work.com"],
        headline="Staff Engineer",
    )
    _apply_provenance(incoming, "ats")

    # Merge records
    merged = _merge_record(existing, incoming, "ats")

    # We expect provenance to contain:
    # 1. Source entries from 'csv'
    # 2. Merge/Agreement/Conflict entries from 'ats'
    provenance_list = merged.provenance
    assert len(provenance_list) >= 3

    # Check for correct methods in merged provenance
    methods = {entry.method for entry in provenance_list}
    assert any(m in methods for m in ["source", "merge", "agreement", "conflict"])

    for entry in provenance_list:
        assert entry.field in [
            "full_name",
            "emails",
            "headline",
            "candidate_id",
        ] or entry.field.startswith("links.")
        assert entry.source in ["csv", "ats"]
