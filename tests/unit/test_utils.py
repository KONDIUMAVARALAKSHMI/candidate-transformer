import pytest
from pydantic import ValidationError

from candidate_transformer.schemas import CandidateRecord, Experience
from candidate_transformer.utils.fuzzy import (
    calculate_fuzzy_similarity,
    fuzzy_match_names,
    fuzzy_match_skills,
)
from candidate_transformer.utils.logging import configure_logging
from candidate_transformer.validators.candidate import (
    validate_chronological_experience,
    validate_email_format,
    validate_phone_format,
)


def test_logging_configuration() -> None:
    # Test that configure_logging executes without error for both format types
    configure_logging(level="DEBUG", format_type="json")
    configure_logging(level="INFO", format_type="console")


def test_fuzzy_matching_similarity() -> None:
    assert calculate_fuzzy_similarity(None, "Python") == 0.0
    assert calculate_fuzzy_similarity("Python", None) == 0.0
    assert calculate_fuzzy_similarity("", "Python") == 0.0

    score = calculate_fuzzy_similarity("Ananya Reddy", "Ananya R")
    assert score > 50.0

    # exact match
    assert fuzzy_match_names("Ananya Reddy", "Ananya Reddy") is True
    # fuzzy name match
    assert fuzzy_match_names("Ananya Reddy", "Ananya R") is True
    assert fuzzy_match_names("Ananya Reddy", "Jane Doe") is False
    assert fuzzy_match_names(None, "Ananya Reddy") is False

    # skill matches
    assert fuzzy_match_skills("React JS", "React.js") is True
    assert fuzzy_match_skills("AWS", "Google Cloud") is False
    assert fuzzy_match_skills("Python", None) is False


def test_validators() -> None:
    # Email syntax
    assert validate_email_format("ananya.reddy@gmail.com") is True
    assert validate_email_format("invalid-email") is False
    assert validate_email_format("") is False

    # Phone formatting (E.164 checking)
    assert validate_phone_format("+919876543210") is True
    assert validate_phone_format("+14155550101") is True
    assert validate_phone_format("9876543210") is False  # Missing +
    assert validate_phone_format("+123") is False  # Too short
    assert validate_phone_format("") is False

    # Chronology validation
    valid_exp = [
        {"start": "2020-01", "end": "2021-06"},
        {"start": "2021-07", "end": "2023-12"},
    ]
    assert validate_chronological_experience(valid_exp) is True

    invalid_exp = [
        {"start": "2022-01", "end": "2020-12"},
    ]
    with pytest.raises(ValueError, match="has a start date.*after its end date"):
        validate_chronological_experience(invalid_exp)


def test_schema_level_validation_success() -> None:
    # Valid candidate model
    record = CandidateRecord(
        full_name="Ananya Reddy",
        emails=["ananya.reddy@gmail.com"],
        phones=["+919876543210"],
        experience=[Experience(company="Google", title="Intern", start="2022-05", end="2022-08")],
    )
    assert record.full_name == "Ananya Reddy"


def test_schema_level_validation_email_failure() -> None:
    with pytest.raises(ValidationError) as exc_info:
        CandidateRecord(
            full_name="Jane Doe",
            emails=["not-an-email"],
        )
    assert "Invalid email address syntax" in str(exc_info.value)


def test_schema_level_validation_phone_failure() -> None:
    with pytest.raises(ValidationError) as exc_info:
        CandidateRecord(
            full_name="Jane Doe",
            phones=["1234567890"],
        )
    assert "must be E.164-compliant" in str(exc_info.value)


def test_schema_level_validation_chronology_failure() -> None:
    with pytest.raises(ValidationError) as exc_info:
        CandidateRecord(
            full_name="Jane Doe",
            experience=[
                Experience(company="Acme", title="Engineer", start="2023-01", end="2022-12")
            ],
        )
    assert "has a start date '2023-01' that is after its end date '2022-12'" in str(exc_info.value)


def test_cli_help() -> None:
    from typer.testing import CliRunner

    from candidate_transformer.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Transform candidate records" in result.stdout


def test_cli_no_args() -> None:
    from typer.testing import CliRunner

    from candidate_transformer.cli import app

    runner = CliRunner()
    result = runner.invoke(app, [])
    assert result.exit_code == 2
    output = result.stderr or result.stdout
    assert "At least one of --csv, --ats, or --resume must be provided." in output
