from candidate_transformer.projector import ProjectionConfig, project_record
from candidate_transformer.schemas import CandidateRecord


def test_projector_missing_field_with_omit():
    record = CandidateRecord(full_name="Test User")

    config = ProjectionConfig(field_selection=["full_name", "headline"], on_missing="omit")

    output = project_record(record, config)

    assert "full_name" in output
    assert "headline" not in output


def test_projector_missing_field_with_null():
    record = CandidateRecord(full_name="Test User")

    config = ProjectionConfig(field_selection=["full_name", "headline"], on_missing="null")

    output = project_record(record, config)

    assert output["headline"] is None


def test_projector_nested_skill_projection():
    record = CandidateRecord(
        full_name="A", skills=[{"name": "Python", "confidence": 1.0, "sources": []}]
    )

    config = ProjectionConfig(field_selection=["skills[].name"])

    output = project_record(record, config)

    assert "skills" in output
