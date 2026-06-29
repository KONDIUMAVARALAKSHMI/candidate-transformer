from pathlib import Path

from candidate_transformer.parsers.csv_parser import parse_csv


def test_parse_csv_reads_rows() -> None:
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "sample.csv"

    rows = parse_csv(fixture_path)

    assert len(rows) == 1
    assert rows[0]["full_name"] == "Jane Doe"
    assert rows[0]["email"] == "jane@example.com"


def test_parse_csv_splits_skill_values_with_semicolons(tmp_path: Path) -> None:
    csv_path = tmp_path / "skills.csv"
    csv_path.write_text(
        "full_name,email,skills\nJane Doe,jane@example.com,Python; SQL; AWS\n",
        encoding="utf-8",
    )

    rows = parse_csv(csv_path)

    assert rows[0]["skills"] == ["Python", "SQL", "AWS"]


def test_parse_csv_splits_skill_values_with_commas(tmp_path: Path) -> None:
    csv_path = tmp_path / "skills.csv"
    csv_path.write_text(
        "full_name,email,skills\nJane Doe,jane@example.com,Python, SQL ,AWS,, Docker\n",
        encoding="utf-8",
    )

    rows = parse_csv(csv_path)

    assert rows[0]["skills"] == ["Python", "SQL", "AWS", "Docker"]


def test_parse_csv_splits_mixed_separators_and_deduplicates(tmp_path: Path) -> None:
    csv_path = tmp_path / "skills.csv"
    csv_path.write_text(
        "full_name,email,skills\nJane Doe,jane@example.com,Python; SQL, AWS,python\n",
        encoding="utf-8",
    )

    rows = parse_csv(csv_path)

    assert rows[0]["skills"] == ["Python", "SQL", "AWS"]
