from candidate_transformer.normalizers.date import normalize_date


def test_normalize_date_returns_year_month() -> None:
    assert normalize_date("12/03/2024") == "2024-03"
    assert normalize_date("2024-03-14") == "2024-03"
