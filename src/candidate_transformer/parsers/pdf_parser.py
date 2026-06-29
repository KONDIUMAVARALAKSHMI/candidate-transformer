from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any

try:
    import pdfplumber  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    pdfplumber = SimpleNamespace(open=None)


def parse_pdf(path: str | Path) -> list[dict[str, Any]]:
    """Extract a simple candidate profile from a PDF resume."""

    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if pdfplumber is None:
        text = pdf_path.read_text(encoding="utf-8", errors="ignore")
    else:
        try:
            with pdfplumber.open(pdf_path) as document:
                pages = [page.extract_text() or "" for page in document.pages]
            text = "\n".join(pages)
        except Exception:
            text = pdf_path.read_text(encoding="utf-8", errors="ignore")

    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phone_match = re.search(r"\+?\d[\d\s().-]{7,}\d", text)
    name_match = re.search(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", text, re.MULTILINE)
    skills = [token.strip() for token in re.findall(r"\b(Python|SQL|AWS|Java|Spark|Docker)\b", text, re.IGNORECASE)]

    return [
        {
            "full_name": name_match.group(1).strip() if name_match else None,
            "emails": [email_match.group(0).lower()] if email_match else [],
            "phones": [phone_match.group(0)] if phone_match else [],
            "skills": skills,
            "headline": "Resume-derived profile",
            "raw_text": text,
        }
    ]
