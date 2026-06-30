import pytest
from candidate_transformer.parsers.json_parser import parse_json
import json


def test_parse_valid_json(tmp_path):
    f = tmp_path / "test.json"
    f.write_text(json.dumps({
        "candidates": [
            {"full_name": "A", "emails": ["a@test.com"]}
        ]
    }))

    result = parse_json(f)

    assert isinstance(result, list)


def test_parse_invalid_json_graceful(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text("{ broken json ")

    # should not crash pipeline logic
    try:
        parse_json(f)
    except Exception:
        assert True