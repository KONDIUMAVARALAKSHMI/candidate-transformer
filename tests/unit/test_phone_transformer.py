from candidate_transformer.normalizers.phone import normalize_phone


def test_normalize_phone_formats_to_e164() -> None:
    assert normalize_phone("+91 98765 43210", default_country="IN") == "+919876543210"
    assert normalize_phone("9876543210", default_country="IN") == "+919876543210"
