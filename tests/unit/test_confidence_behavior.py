import pytest

from candidate_transformer.confidence import (
    compute_field_confidences,
    compute_overall_confidence,
    apply_confidence,
)
from candidate_transformer.schemas import CandidateRecord, Provenance, Skill


def test_confidence_bounds() -> None:
    # Test that confidence is always between 0 and 1
    # Case A: empty provenance
    record = CandidateRecord()
    conf = compute_overall_confidence(record)
    assert conf == 0.0

    # Case B: low confidence provenance + heavy conflict penalties
    record2 = CandidateRecord(
        provenance=[
            Provenance(field="full_name", source="resume", method="source"),
            Provenance(field="full_name", source="csv", method="conflict"),
            Provenance(field="full_name", source="ats", method="conflict"),
        ]
    )
    field_confs = compute_field_confidences(record2)
    assert 0.0 <= field_confs["full_name"] <= 1.0

    # Case C: many agreement bonuses
    record3 = CandidateRecord(
        provenance=[
            Provenance(field="full_name", source="ats", method="source"),
            Provenance(field="full_name", source="csv", method="agreement"),
            Provenance(field="full_name", source="resume", method="agreement"),
            Provenance(field="full_name", source="ats-backup", method="agreement"),
        ]
    )
    field_confs = compute_field_confidences(record3)
    assert field_confs["full_name"] == 1.0


def test_confidence_increases_on_agreement() -> None:
    # Single source full_name
    record_single = CandidateRecord(
        provenance=[
            Provenance(field="full_name", source="csv", method="source"),
        ]
    )
    conf_single = compute_field_confidences(record_single)["full_name"]

    # Multiple sources agreeing on full_name
    record_agree = CandidateRecord(
        provenance=[
            Provenance(field="full_name", source="csv", method="source"),
            Provenance(field="full_name", source="ats", method="agreement"),
        ]
    )
    conf_agree = compute_field_confidences(record_agree)["full_name"]

    # Multiple sources agreeing should yield higher confidence than a single source
    assert conf_agree > conf_single


def test_confidence_decreases_on_conflict() -> None:
    # No conflict full_name
    record_no_conflict = CandidateRecord(
        provenance=[
            Provenance(field="full_name", source="ats", method="source"),
        ]
    )
    conf_no_conflict = compute_field_confidences(record_no_conflict)["full_name"]

    # Conflicting sources for full_name
    record_conflict = CandidateRecord(
        provenance=[
            Provenance(field="full_name", source="ats", method="source"),
            Provenance(field="full_name", source="csv", method="conflict"),
        ]
    )
    conf_conflict = compute_field_confidences(record_conflict)["full_name"]

    # Conflicting values should reduce confidence
    assert conf_conflict < conf_no_conflict


def test_skills_confidence_agreement() -> None:
    # Skill from single source
    skill_single = Skill(name="Python", confidence=0.8, sources=["resume"])
    record_single = CandidateRecord(skills=[skill_single])
    apply_confidence(record_single)
    conf_single = record_single.overall_confidence

    # Skill from multiple sources (agreement)
    skill_agree = Skill(name="Python", confidence=0.8, sources=["resume", "ats"])
    record_agree = CandidateRecord(skills=[skill_agree])
    apply_confidence(record_agree)
    conf_agree = record_agree.overall_confidence

    assert conf_agree > conf_single
