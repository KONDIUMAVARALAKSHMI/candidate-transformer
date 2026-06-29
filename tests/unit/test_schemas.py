from candidate_transformer.schemas import CandidateRecord, Location, Skill


def test_candidate_record_validation() -> None:
    record = CandidateRecord(
        full_name="Jane Doe",
        emails=["jane@example.com"],
        phones=["+919876543210"],
        location=Location(city="Bengaluru", country="IN"),
        skills=[Skill(name="Python")],
    )

    assert record.full_name == "Jane Doe"
    assert record.emails == ["jane@example.com"]
    assert record.location.country == "IN"
    assert record.skills[0].name == "Python"
