from candidate_transformer.normalizers.name import normalize_name


def test_normalize_name_title_cases_and_cleans() -> None:
    assert normalize_name("  jANe   doe  ") == "Jane Doe"
    assert normalize_name("maria-jo  perez") == "Maria-Jo Perez"
