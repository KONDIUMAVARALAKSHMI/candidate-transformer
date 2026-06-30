import pytest

from candidate_transformer.projector import ProjectionConfig, project_record
from candidate_transformer.schemas import CandidateRecord, Skill


def test_projection_on_missing_null() -> None:
    # Setup record with missing fields
    record = CandidateRecord(
        full_name="Ananya Reddy",
        emails=["ananya.reddy@gmail.com"],
        skills=[Skill(name="Python")],
    )

    # If missing, it should output null
    config = ProjectionConfig(
        field_selection=["full_name", "headline", "years_experience"],
        on_missing="null",
    )

    result = project_record(record, config)
    assert result["full_name"] == "Ananya Reddy"
    assert result["headline"] is None
    assert result["years_experience"] is None


def test_projection_on_missing_omit() -> None:
    record = CandidateRecord(
        full_name="Ananya Reddy",
        emails=["ananya.reddy@gmail.com"],
        skills=[Skill(name="Python")],
    )

    # If missing, it should not appear in output
    config = ProjectionConfig(
        field_selection=["full_name", "headline", "years_experience"],
        on_missing="omit",
    )

    result = project_record(record, config)
    assert result["full_name"] == "Ananya Reddy"
    assert "headline" not in result
    assert "years_experience" not in result


def test_projection_on_missing_error() -> None:
    record = CandidateRecord(
        full_name="Ananya Reddy",
        emails=["ananya.reddy@gmail.com"],
        skills=[Skill(name="Python")],
    )

    # If missing, it should raise a controlled error
    config = ProjectionConfig(
        field_selection=["full_name", "headline"],
        on_missing="error",
    )

    with pytest.raises(ValueError, match="Missing field for projection: headline"):
        project_record(record, config)


def test_projection_nested_mapping() -> None:
    record = CandidateRecord(
        full_name="Ananya Reddy",
        emails=["ananya.reddy@gmail.com", "secondary@domain.com"],
        skills=[Skill(name="Python"), Skill(name="SQL")],
    )

    # Test emails[0] and skills[].name
    config = ProjectionConfig(
        field_selection=["emails[0]", "skills[].name"],
    )

    result = project_record(record, config)
    assert result["emails[0]"] == "ananya.reddy@gmail.com"
    assert result["skills[]"]["name"] == ["Python", "SQL"]



def test_projection_nested_mapping_out_of_bounds() -> None:
    record = CandidateRecord(
        full_name="Ananya Reddy",
        emails=["ananya.reddy@gmail.com"],
    )

    config = ProjectionConfig(
        field_selection=["emails[5]"],
        on_missing="null",
    )

    result = project_record(record, config)
    assert result["emails[5]"] is None
