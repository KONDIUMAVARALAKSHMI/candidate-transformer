import json

from candidate_transformer.parsers import pdf_parser
from candidate_transformer.pipeline import run_pipeline


def test_pipeline_merges_and_projects_candidates(tmp_path, monkeypatch) -> None:
    csv_path = tmp_path / "candidates.csv"
    csv_path.write_text(
        "full_name,email,phone,location,skills,headline,years_experience\n"
        "Jane Doe,jane@example.com,+919876543210,Bengaluru, IN,Python; SQL,Engineer,5\n",
        encoding="utf-8",
    )

    ats_path = tmp_path / "ats.json"
    ats_path.write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "full_name": "Jane Doe",
                        "emails": ["jane@example.com"],
                        "phones": ["+919876543210"],
                        "headline": "Senior Engineer",
                        "skills": ["Python", "AWS"],
                        "years_experience": 6,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    class FakePage:
        def extract_text(self) -> str:
            return "Jane Doe\njane@example.com\n+91 98765 43210\nPython\nSQL"

    class FakePdf:
        def __init__(self, path: str) -> None:
            self.pages = [FakePage()]

        def __enter__(self) -> "FakePdf":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    monkeypatch.setattr(pdf_parser.pdfplumber, "open", lambda path: FakePdf(path))
    resume_path = tmp_path / "resume.pdf"
    resume_path.write_bytes(b"%PDF-1.4")

    output_path = tmp_path / "output.jsonl"
    result = run_pipeline(
        csv_path=csv_path,
        ats_path=ats_path,
        resume_path=resume_path,
        output_path=output_path,
    )

    assert output_path.exists()
    assert len(result) == 1
    assert result[0].full_name == "Jane Doe"
    assert result[0].overall_confidence > 0.0
    assert result[0].emails[0] == "jane@example.com"
    assert any(item.field == "full_name" for item in result[0].provenance)
