import json
from pathlib import Path

from candidate_transformer.pipeline import run_pipeline
from candidate_transformer.projector import ProjectionConfig, project_record
from candidate_transformer.schemas import CandidateRecord, Provenance, Skill


def test_default_projection_uses_canonical_field_names() -> None:
    record = CandidateRecord(
        candidate_id="123",
        full_name="Jane Doe",
        emails=["jane@example.com"],
        phones=["+14155550101"],
        skills=[Skill(name="Python")],
        overall_confidence=0.91,
    )

    projected = project_record(record)

    assert set(projected.keys()) == {
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
        "provenance",
        "overall_confidence",
    }
    assert projected["overall_confidence"] == 0.91
    assert projected["provenance"] is None


def test_custom_projection_still_renames_fields() -> None:
    record = CandidateRecord(
        full_name="Jane Doe",
        emails=["jane@example.com"],
        skills=[Skill(name="Python")],
    )

    projected = project_record(
        record,
        ProjectionConfig(
            field_selection=["full_name", "emails", "skills"], field_rename={"full_name": "name"}
        ),
    )

    assert set(projected.keys()) == {"name", "emails", "skills"}
    assert projected["name"] == "Jane Doe"


def test_duplicate_merge_uses_same_candidate_profile(tmp_path: Path) -> None:
    csv_path = tmp_path / "recruiter.csv"
    csv_path.write_text(
        "full_name,email,phone,location,skills,headline,years_experience\n"
        "Jane Doe,jane@example.com,+1 415 555 0101,San Francisco, Python; SQL,Engineer,5\n",
        encoding="utf-8",
    )

    ats_path = tmp_path / "ats.json"
    ats_path.write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "full_name": "Jane Doe",
                        "emails": ["jane@example.com"],
                        "phones": ["+14155550101"],
                        "headline": "Senior Engineer",
                        "skills": ["Python", "AWS"],
                        "years_experience": 6,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    resume_path = tmp_path / "resume.txt"
    resume_path.write_text(
        "Jane Doe\njane@example.com\n+1 (415) 555-0101\nSkills: Python, SQL, AWS\n",
        encoding="utf-8",
    )

    output_path = tmp_path / "output.json"
    records = run_pipeline(
        csv_path=csv_path, ats_path=ats_path, resume_path=resume_path, output_path=output_path
    )

    assert len(records) == 1
    assert records[0].full_name == "Jane Doe"
    assert records[0].emails == ["jane@example.com"]
    assert records[0].phones == ["+14155550101"]


def test_projection_includes_field_level_provenance() -> None:
    record = CandidateRecord(
        full_name="Jane Doe",
        emails=["jane@example.com"],
        phones=["+14155550101"],
        skills=[Skill(name="Python")],
        provenance=[Provenance(field="full_name", source="ats", method="source")],
    )

    projected = project_record(
        record,
        ProjectionConfig(field_selection=["full_name", "emails"], include_provenance=True),
    )

    assert "field_provenance" in projected
    assert projected["field_provenance"]["full_name"][0]["source"] == "ats"


def test_malformed_source_does_not_abort_pipeline(tmp_path: Path) -> None:
    csv_path = tmp_path / "recruiter.csv"
    csv_path.write_text("full_name,email\nJane Doe,jane@example.com\n", encoding="utf-8")

    malformed_json = tmp_path / "ats.json"
    malformed_json.write_text('{"candidates": [', encoding="utf-8")

    output_path = tmp_path / "output.json"
    records = run_pipeline(csv_path=csv_path, ats_path=malformed_json, output_path=output_path)

    assert len(records) == 1
    assert records[0].full_name == "Jane Doe"
