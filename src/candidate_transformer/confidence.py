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
        matching = [
            entry
            for entry in record.provenance
            if entry.field == field or entry.field.startswith(f"{field}.")
        ]
        if matching:
            valid_matching = [entry for entry in matching if entry.method != "conflict"]
            if valid_matching:
                base_conf = max(weights.get(entry.source.lower(), 0.0) for entry in valid_matching)
            else:
                base_conf = 0.5

            # Agreement: number of unique sources that agreed or merged
            unique_sources = {entry.source.lower() for entry in valid_matching}
            agreement_bonus = 0.05 * (len(unique_sources) - 1)

            # Conflict: check if there are any conflict method entries
            conflict_entries = [entry for entry in matching if entry.method == "conflict"]
            conflict_penalty = 0.10 * len(conflict_entries)

            conf = base_conf + agreement_bonus - conflict_penalty
            conf = max(0.0, min(1.0, conf))
            confidences[field] = conf

    if record.skills:
        skill_confs = []
        for skill in record.skills:
            s_base = skill.confidence
            s_agreement = 0.05 * (len(skill.sources) - 1)
            s_conf = max(0.0, min(1.0, s_base + s_agreement))
            skill_confs.append(s_conf)
        confidences["skills"] = sum(skill_confs) / max(1, len(record.skills))

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
