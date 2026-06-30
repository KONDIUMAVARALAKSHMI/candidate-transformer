from candidate_transformer.merger import merge_candidates


def test_merge_conflict_branches():
    csv = [{"full_name": "A", "emails": ["a@test.com"]}]
    ats = [{"full_name": "A different", "emails": ["a@test.com"]}]
    resume = []

    result = merge_candidates(csv, ats, resume)

    assert len(result) == 1
    assert result[0].full_name is not None


def test_merge_multi_source_skills():
    csv = [{"skills": ["Python"]}]
    ats = [{"skills": ["python"]}]
    resume = [{"skills": ["PYTHON"]}]

    result = merge_candidates(csv, ats, resume)

    assert result[0].skills
