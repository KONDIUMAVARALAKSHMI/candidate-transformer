from __future__ import annotations

from candidate_transformer.schemas import CandidateRecord

SOURCE_WEIGHTS: dict[str, float] = {
    "ats": 0.95,
    "csv": 0.90,
    "resume": 0.80,
}


def compute_field_confidences(
    record: CandidateRecord, source_weights: dict[str, float] | None = None
) -> dict[str, float]:
    """Compute field-level confidence values from provenance entries."""

    weights = source_weights or SOURCE_WEIGHTS
    confidences: dict[str, float] = {}

    for field in {
        "candidate_id",
        "full_name",
        "emails",
        "phones",
        "location",
        "links",
        "headline",
        "years_experience",
        "skills",
        "experience",
        "education",
    }:
        matching = [entry for entry in record.provenance if entry.field == field]
        if matching:
            confidences[field] = max(weights.get(entry.source.lower(), 0.0) for entry in matching)

    if record.skills:
        confidences["skills"] = sum(skill.confidence for skill in record.skills) / max(
            1, len(record.skills)
        )

    return confidences


def compute_overall_confidence(
    record: CandidateRecord,
    source_weights: dict[str, float] | None = None,
) -> float:
    """Compute a single overall confidence score for the merged record."""

    field_confidences = compute_field_confidences(record, source_weights=source_weights)
    if not field_confidences:
        return 0.0

    return sum(field_confidences.values()) / len(field_confidences)


def apply_confidence(
    record: CandidateRecord, source_weights: dict[str, float] | None = None
) -> CandidateRecord:
    """Apply confidence values to the record in place and return it."""

    record.overall_confidence = compute_overall_confidence(record, source_weights=source_weights)
    return record
