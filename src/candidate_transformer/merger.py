from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from candidate_transformer.normalizers.country import normalize_country
from candidate_transformer.normalizers.date import normalize_date
from candidate_transformer.normalizers.name import normalize_name
from candidate_transformer.normalizers.phone import normalize_phone
from candidate_transformer.schemas import (
    CandidateRecord,
    Education,
    Experience,
    Provenance,
    Skill,
)

SKILL_ALIASES = {
    "sql": "SQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "python": "Python",
    "aws": "AWS",
    "azure": "Azure",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "react": "React",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "spark": "Spark",
    "tableau": "Tableau",
    "api": "API",
    "rest": "REST",
    "graphql": "GraphQL",
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "ai": "AI",
    "etl": "ETL",
    "linux": "Linux",
    "git": "Git",
    "pytest": "Pytest",
}


def merge_candidates(
    csv_records: list[dict[str, Any]],
    ats_records: list[dict[str, Any]],
    resume_records: list[dict[str, Any]],
    default_country: str = "IN",
    date_formats: list[str] | None = None,
) -> list[CandidateRecord]:
    """Merge candidate records from multiple sources using deterministic priority rules."""

    merged: dict[str, CandidateRecord] = {}
    source_order = [
        ("ats", ats_records),
        ("csv", csv_records),
        ("resume", resume_records),
    ]

    for source_name, records in source_order:
        for raw_record in records:
            candidate = _normalize_source_record(
                raw_record, source_name, default_country, date_formats
            )
            key = _candidate_key(candidate)
            if key not in merged:
                merged[key] = CandidateRecord()
            merged[key] = _merge_record(merged[key], candidate, source_name)

    return sorted(merged.values(), key=lambda item: (item.full_name or "", item.candidate_id or ""))


def _normalize_source_record(
    raw_record: Mapping[str, Any],
    source_name: str,
    default_country: str,
    date_formats: list[str] | None,
) -> CandidateRecord:
    record = CandidateRecord()

    full_name = raw_record.get("full_name") or raw_record.get("name")
    if full_name:
        record.full_name = normalize_name(full_name)

    emails = _as_list(raw_record.get("emails") or raw_record.get("email"))
    if emails:
        record.emails = [email.strip().lower() for email in emails if email and str(email).strip()]

    phones = _as_list(raw_record.get("phones") or raw_record.get("phone"))
    if phones:
        normalized_phones: list[str] = []
        for phone in phones:
            normalized = normalize_phone(str(phone), default_country=default_country)
            if normalized:
                normalized_phones.append(normalized)
        record.phones = normalized_phones

    location_value = raw_record.get("location")
    if isinstance(location_value, str) and location_value:
        parts = [part.strip() for part in location_value.split(",") if part.strip()]
        if len(parts) >= 1:
            record.location.city = parts[0]
        if len(parts) >= 2:
            record.location.region = parts[1]
        if len(parts) >= 3:
            record.location.country = normalize_country(parts[2])
    elif isinstance(location_value, Mapping):
        record.location.city = str(location_value.get("city") or "") or None
        record.location.region = str(location_value.get("region") or "") or None
        record.location.country = normalize_country(
            str(location_value.get("country") or "") or None
        )

    links_value = raw_record.get("links")
    if isinstance(links_value, Mapping):
        record.links.linkedin = str(links_value.get("linkedin") or "") or None
        record.links.github = str(links_value.get("github") or "") or None
        record.links.portfolio = str(links_value.get("portfolio") or "") or None
        record.links.other = [str(item) for item in links_value.get("other", []) if item]
    elif isinstance(links_value, list):
        record.links.other = [str(item) for item in links_value if item]

    headline = raw_record.get("headline")
    if headline:
        record.headline = str(headline)

    years_experience = raw_record.get("years_experience")
    if years_experience is not None:
        try:
            record.years_experience = float(years_experience)
        except (TypeError, ValueError):
            record.years_experience = None

    skills_value = raw_record.get("skills")
    if skills_value:
        record.skills = [
            Skill(
                name=_canonical_skill_name(str(skill)),
                confidence=0.95 if source_name == "ats" else 0.9 if source_name == "csv" else 0.8,
                sources=[source_name],
            )
            for skill in _as_list(skills_value)
            if str(skill).strip()
        ]

    for experience in _as_list(raw_record.get("experience")):
        if isinstance(experience, Mapping):
            record.experience.append(
                Experience(
                    company=str(experience.get("company") or "") or None,
                    title=str(experience.get("title") or "") or None,
                    start=normalize_date(
                        str(experience.get("start") or "") or None, date_formats=date_formats
                    ),
                    end=normalize_date(
                        str(experience.get("end") or "") or None, date_formats=date_formats
                    ),
                    summary=str(experience.get("summary") or "") or None,
                )
            )

    for education in _as_list(raw_record.get("education")):
        if isinstance(education, Mapping):
            record.education.append(
                Education(
                    institution=str(education.get("institution") or "") or None,
                    degree=str(education.get("degree") or "") or None,
                    field=str(education.get("field") or "") or None,
                    end_year=education.get("end_year"),
                )
            )

    return _apply_provenance(record, source_name)


def _merge_record(
    existing: CandidateRecord, incoming: CandidateRecord, source_name: str
) -> CandidateRecord:
    if incoming.candidate_id and not existing.candidate_id:
        existing.candidate_id = incoming.candidate_id
        _append_provenance(existing, "candidate_id", source_name, "merge")

    if incoming.full_name and not existing.full_name:
        existing.full_name = incoming.full_name
        _append_provenance(existing, "full_name", source_name, "merge")

    existing.emails = _merge_unique_strings(existing.emails, incoming.emails)
    if incoming.emails and existing.emails and existing.emails != incoming.emails:
        _append_provenance(existing, "emails", source_name, "merge")

    existing.phones = _merge_unique_strings(existing.phones, incoming.phones)
    if incoming.phones and existing.phones and existing.phones != incoming.phones:
        _append_provenance(existing, "phones", source_name, "merge")

    if incoming.location.city and not existing.location.city:
        existing.location.city = incoming.location.city
        _append_provenance(existing, "location.city", source_name, "merge")
    if incoming.location.region and not existing.location.region:
        existing.location.region = incoming.location.region
        _append_provenance(existing, "location.region", source_name, "merge")
    if incoming.location.country and not existing.location.country:
        existing.location.country = incoming.location.country
        _append_provenance(existing, "location.country", source_name, "merge")

    if incoming.links.linkedin and not existing.links.linkedin:
        existing.links.linkedin = incoming.links.linkedin
        _append_provenance(existing, "links.linkedin", source_name, "merge")
    if incoming.links.github and not existing.links.github:
        existing.links.github = incoming.links.github
        _append_provenance(existing, "links.github", source_name, "merge")
    if incoming.links.portfolio and not existing.links.portfolio:
        existing.links.portfolio = incoming.links.portfolio
        _append_provenance(existing, "links.portfolio", source_name, "merge")
    if incoming.links.other:
        existing.links.other = _merge_unique_strings(existing.links.other, incoming.links.other)
        if existing.links.other != [*existing.links.other]:
            _append_provenance(existing, "links.other", source_name, "merge")

    if incoming.headline and not existing.headline:
        existing.headline = incoming.headline
        _append_provenance(existing, "headline", source_name, "merge")

    if incoming.years_experience is not None and existing.years_experience is None:
        existing.years_experience = incoming.years_experience
        _append_provenance(existing, "years_experience", source_name, "merge")

    if incoming.skills:
        existing.skills = _merge_skills(existing.skills, incoming.skills, source_name)
        if existing.skills and incoming.skills:
            _append_provenance(existing, "skills", source_name, "merge")

    if incoming.experience:
        existing.experience.extend(
            [item for item in incoming.experience if item not in existing.experience]
        )
        if existing.experience:
            _append_provenance(existing, "experience", source_name, "merge")

    if incoming.education:
        existing.education.extend(
            [item for item in incoming.education if item not in existing.education]
        )
        if existing.education:
            _append_provenance(existing, "education", source_name, "merge")

    return existing


def _apply_provenance(record: CandidateRecord, source_name: str) -> CandidateRecord:
    if record.candidate_id:
        _append_provenance(record, "candidate_id", source_name, "source")
    if record.full_name:
        _append_provenance(record, "full_name", source_name, "source")
    if record.emails:
        _append_provenance(record, "emails", source_name, "source")
    if record.phones:
        _append_provenance(record, "phones", source_name, "source")
    if record.location.city or record.location.region or record.location.country:
        _append_provenance(record, "location", source_name, "source")
    if record.links.linkedin or record.links.github or record.links.portfolio or record.links.other:
        _append_provenance(record, "links", source_name, "source")
    if record.headline:
        _append_provenance(record, "headline", source_name, "source")
    if record.years_experience is not None:
        _append_provenance(record, "years_experience", source_name, "source")
    if record.skills:
        _append_provenance(record, "skills", source_name, "source")
    if record.experience:
        _append_provenance(record, "experience", source_name, "source")
    if record.education:
        _append_provenance(record, "education", source_name, "source")
    return record


def _append_provenance(record: CandidateRecord, field: str, source_name: str, method: str) -> None:
    record.provenance.append(Provenance(field=field, source=source_name, method=method))


def _merge_unique_strings(existing: list[str], incoming: list[str]) -> list[str]:
    combined = [item for item in existing if item]
    for item in incoming:
        if item and item not in combined:
            combined.append(item)
    return combined


def _merge_skills(existing: list[Skill], incoming: list[Skill], source_name: str) -> list[Skill]:
    combined = {skill.name.lower(): skill for skill in existing}
    for skill in incoming:
        normalized_name = skill.name.strip()
        key = normalized_name.lower()
        if key in combined:
            existing_skill = combined[key]
            existing_skill.confidence = max(existing_skill.confidence, skill.confidence)
            existing_skill.sources = _merge_unique_strings(existing_skill.sources, [source_name])
            continue
        combined[key] = Skill(
            name=normalized_name,
            confidence=max(skill.confidence, 0.8),
            sources=[source_name],
        )
    return list(combined.values())


def _candidate_key(candidate: CandidateRecord) -> str:
    if candidate.emails:
        return f"email:{candidate.emails[0].lower()}"
    if candidate.phones:
        return f"phone:{candidate.phones[0]}"
    if candidate.links.linkedin:
        return f"url:{candidate.links.linkedin.lower()}"
    if candidate.links.github:
        return f"url:{candidate.links.github.lower()}"
    if candidate.links.portfolio:
        return f"url:{candidate.links.portfolio.lower()}"
    if candidate.full_name:
        normalized_name = normalize_name(candidate.full_name).lower()
        if candidate.experience and candidate.experience[0].company:
            company_name = normalize_name(candidate.experience[0].company).lower()
            return f"name-company:{normalized_name}|{company_name}"
        return f"name:{normalized_name}"
    return "unknown"


# country normalization is handled by candidate_transformer.normalizers.country.normalize_country


def _canonical_skill_name(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return cleaned
    lowered = cleaned.lower()
    if lowered in SKILL_ALIASES:
        return SKILL_ALIASES[lowered]
    return cleaned


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]
