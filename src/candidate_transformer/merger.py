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

# -----------------------------
# SKILL NORMALIZATION
# -----------------------------

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


# -----------------------------
# PUBLIC API
# -----------------------------

def merge_candidates(
    csv_records: list[dict[str, Any]],
    ats_records: list[dict[str, Any]],
    resume_records: list[dict[str, Any]],
    default_country: str = "IN",
    date_formats: list[str] | None = None,
) -> list[CandidateRecord]:

    merged: dict[str, CandidateRecord] = {}

    source_order = [
        ("ats", ats_records),
        ("csv", csv_records),
        ("resume", resume_records),
    ]

    for source_name, records in source_order:
        for raw_record in records:
            candidate = _normalize_source_record(
                raw_record,
                source_name,
                default_country,
                date_formats,
            )

            key = _candidate_key(candidate)

            if key not in merged:
                merged[key] = CandidateRecord()

            merged[key] = _merge_record(
                merged[key],
                candidate,
                source_name,
            )

    return sorted(
        merged.values(),
        key=lambda x: (x.full_name or "", x.candidate_id or ""),
    )


# -----------------------------
# NORMALIZATION
# -----------------------------

def _normalize_source_record(
    raw_record: Mapping[str, Any],
    source_name: str,
    default_country: str,
    date_formats: list[str] | None,
) -> CandidateRecord:

    record = CandidateRecord()

    # name
    full_name = raw_record.get("full_name") or raw_record.get("name")
    if full_name:
        record.full_name = normalize_name(full_name)

    # emails
    emails = _as_list(raw_record.get("emails") or raw_record.get("email"))
    record.emails = [
        e.strip().lower()
        for e in emails
        if e and str(e).strip()
    ]

    # phones
    phones = _as_list(raw_record.get("phones") or raw_record.get("phone"))
    record.phones = [
        normalize_phone(str(p), default_country=default_country)
        for p in phones
        if p
    ]

    # location
    loc = raw_record.get("location")
    if isinstance(loc, str):
        parts = [p.strip() for p in loc.split(",") if p.strip()]
        if len(parts) > 0:
            record.location.city = parts[0]
        if len(parts) > 1:
            record.location.region = parts[1]
        if len(parts) > 2:
            record.location.country = normalize_country(parts[2])

    elif isinstance(loc, Mapping):
        record.location.city = loc.get("city") or None
        record.location.region = loc.get("region") or None
        record.location.country = normalize_country(loc.get("country"))

    # links
    links = raw_record.get("links")
    if isinstance(links, Mapping):
        record.links.linkedin = links.get("linkedin") or None
        record.links.github = links.get("github") or None
        record.links.portfolio = links.get("portfolio") or None
        record.links.other = links.get("other", []) or []

    elif isinstance(links, list):
        record.links.other = links

    # headline
    if raw_record.get("headline"):
        record.headline = str(raw_record["headline"])

    # experience
    years = raw_record.get("years_experience")
    if years is not None:
        try:
            record.years_experience = float(years)
        except Exception:
            record.years_experience = None

    # skills
    skills = raw_record.get("skills")
    if skills:
        record.skills = [
            Skill(
                name=_canonical_skill_name(str(s)),
                confidence=0.95 if source_name == "ats"
                else 0.9 if source_name == "csv"
                else 0.8,
                sources=[source_name],
            )
            for s in _as_list(skills)
            if str(s).strip()
        ]

    # experience
    for exp in _as_list(raw_record.get("experience")):
        if isinstance(exp, Mapping):
            record.experience.append(
                Experience(
                    company=exp.get("company"),
                    title=exp.get("title"),
                    start=normalize_date(exp.get("start"), date_formats=date_formats),
                    end=normalize_date(exp.get("end"), date_formats=date_formats),
                    summary=exp.get("summary"),
                )
            )

    # education
    for edu in _as_list(raw_record.get("education")):
        if isinstance(edu, Mapping):
            record.education.append(
                Education(
                    institution=edu.get("institution"),
                    degree=edu.get("degree"),
                    field=edu.get("field"),
                    end_year=edu.get("end_year"),
                )
            )

    return _apply_provenance(record, source_name)


# -----------------------------
# MERGE LOGIC
# -----------------------------

def _merge_record(
    existing: CandidateRecord,
    incoming: CandidateRecord,
    source: str,
) -> CandidateRecord:

    # ID
    if incoming.candidate_id and not existing.candidate_id:
        existing.candidate_id = incoming.candidate_id
        _append_provenance(existing, "candidate_id", source, "merge")

    elif incoming.candidate_id and existing.candidate_id:
        method = "agreement" if incoming.candidate_id == existing.candidate_id else "conflict"
        _append_provenance(existing, "candidate_id", source, method)

    # name
    if incoming.full_name and not existing.full_name:
        existing.full_name = incoming.full_name
        _append_provenance(existing, "full_name", source, "merge")

    elif incoming.full_name and existing.full_name:
        method = "agreement" if incoming.full_name.lower() == existing.full_name.lower() else "conflict"
        _append_provenance(existing, "full_name", source, method)

    # emails
    new_emails = [e for e in incoming.emails if e not in existing.emails]
    if new_emails:
        existing.emails = _merge_unique_strings(existing.emails, new_emails)
        _append_provenance(existing, "emails", source, "merge")

    # phones
    new_phones = [p for p in incoming.phones if p not in existing.phones]
    if new_phones:
        existing.phones = _merge_unique_strings(existing.phones, new_phones)
        _append_provenance(existing, "phones", source, "merge")

    # location (granular)
    _merge_location(existing, incoming, source)

    # links
    for f in ["linkedin", "github", "portfolio"]:
        inc = getattr(incoming.links, f)
        exc = getattr(existing.links, f)

        if inc and not exc:
            setattr(existing.links, f, inc)
            _append_provenance(existing, f"links.{f}", source, "merge")

        elif inc and exc:
            method = "agreement" if inc.lower() == exc.lower() else "conflict"
            _append_provenance(existing, f"links.{f}", source, method)

    if incoming.links.other:
        existing.links.other = _merge_unique_strings(existing.links.other, incoming.links.other)

    # headline
    if incoming.headline and not existing.headline:
        existing.headline = incoming.headline
        _append_provenance(existing, "headline", source, "merge")

    # experience / education / skills
    if incoming.experience:
        existing.experience.extend(incoming.experience)
        _append_provenance(existing, "experience", source, "merge")

    if incoming.education:
        existing.education.extend(incoming.education)
        _append_provenance(existing, "education", source, "merge")

    if incoming.skills:
        existing.skills = _merge_skills(existing.skills, incoming.skills, source)
        _append_provenance(existing, "skills", source, "merge")

    return existing


# -----------------------------
# LOCATION FIX (IMPORTANT)
# -----------------------------

def _merge_location(existing: CandidateRecord, incoming: CandidateRecord, source: str) -> None:

    for field in ["city", "region", "country"]:
        inc = getattr(incoming.location, field)
        exc = getattr(existing.location, field)

        if inc and not exc:
            setattr(existing.location, field, inc)
            _append_provenance(existing, f"location.{field}", source, "merge")

        elif inc and exc:
            method = "agreement" if str(inc).lower() == str(exc).lower() else "conflict"
            _append_provenance(existing, f"location.{field}", source, method)


# -----------------------------
# PROVENANCE
# -----------------------------

def _apply_provenance(record: CandidateRecord, source_name: str) -> CandidateRecord:
    def has_value(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, (list, tuple, dict)):
            return len(value) > 0
        return True  # includes 0.0, False-safe fix

    # scalar fields
    if record.candidate_id:
        _append_provenance(record, "candidate_id", source_name, "source")

    if record.full_name:
        _append_provenance(record, "full_name", source_name, "source")

    if record.emails:
        _append_provenance(record, "emails", source_name, "source")

    if record.phones:
        _append_provenance(record, "phones", source_name, "source")

    # FIX: location must always count if ANY subfield exists
    if (
        has_value(record.location.city)
        or has_value(record.location.region)
        or has_value(record.location.country)
    ):
        _append_provenance(record, "location", source_name, "source")

    if (
        record.links.linkedin
        or record.links.github
        or record.links.portfolio
        or record.links.other
    ):
        _append_provenance(record, "links", source_name, "source")

    if record.headline:
        _append_provenance(record, "headline", source_name, "source")

    # FIX: THIS is your failing case
    if record.years_experience is not None:
        _append_provenance(record, "years_experience", source_name, "source")

    if record.skills:
        _append_provenance(record, "skills", source_name, "source")

    if record.experience:
        _append_provenance(record, "experience", source_name, "source")

    if record.education:
        _append_provenance(record, "education", source_name, "source")

    return record


# -----------------------------
# HELPERS
# -----------------------------

def _append_provenance(record: CandidateRecord, field: str, source: str, method: str) -> None:
    record.provenance.append(Provenance(field=field, source=source, method=method))


def _merge_unique_strings(existing: list[str], incoming: list[str]) -> list[str]:
    for item in incoming:
        if item and item not in existing:
            existing.append(item)
    return existing


def _merge_skills(existing: list[Skill], incoming: list[Skill], source: str) -> list[Skill]:
    combined = {s.name.lower(): s for s in existing}

    for s in incoming:
        key = s.name.lower()
        if key in combined:
            combined[key].confidence = max(combined[key].confidence, s.confidence)
            combined[key].sources = _merge_unique_strings(combined[key].sources, [source])
        else:
            combined[key] = Skill(name=s.name, confidence=s.confidence, sources=[source])

    return list(combined.values())


def _candidate_key(candidate: CandidateRecord) -> str:
    if candidate.emails:
        return f"email:{candidate.emails[0]}"
    if candidate.phones:
        return f"phone:{candidate.phones[0]}"
    if candidate.full_name:
        return f"name:{normalize_name(candidate.full_name).lower()}"
    return "unknown"


def _canonical_skill_name(value: str) -> str:
    v = value.strip().lower()
    return SKILL_ALIASES.get(v, value.strip())


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


