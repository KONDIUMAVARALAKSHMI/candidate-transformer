from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from candidate_transformer.confidence import compute_field_confidences
from candidate_transformer.schemas import CandidateRecord

CANONICAL_FIELDS = [
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
    "provenance",
    "overall_confidence",
]


class ProjectionConfig(BaseModel):
    """Runtime projection configuration for output formatting."""

    field_selection: list[str] | None = None
    field_rename: dict[str, str] = Field(default_factory=dict)
    canonical_path_mapping: dict[str, str] = Field(default_factory=dict)
    normalize: bool = True
    include_confidence: bool = False
    include_provenance: bool = False
    on_missing: Literal["null", "omit", "error"] = "null"


def load_projection_config(config_path: str | Path | None = None) -> ProjectionConfig:
    """Load projection settings from a JSON file when provided."""

    if config_path is None:
        return ProjectionConfig()

    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Projection config file not found: {config_file}")

    with config_file.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, dict):
        return ProjectionConfig(**payload)

    raise ValueError("Projection configuration must be a JSON object.")


def project_record(
    record: CandidateRecord, config: ProjectionConfig | None = None
) -> dict[str, Any]:
    """Project a canonical candidate record into a runtime-friendly dictionary."""

    projection_config = config or ProjectionConfig()
    selected_fields = projection_config.field_selection or CANONICAL_FIELDS

    output: dict[str, Any] = {}
    for field_name in selected_fields:
        value = _resolve_field(record, field_name)
        if value is None or value == [] or value == {}:
            if projection_config.on_missing == "error":
                raise ValueError(f"Missing field for projection: {field_name}")
            if projection_config.on_missing == "omit":
                continue
            _set_nested_value(output, field_name, None)
            continue

        if projection_config.normalize:
            value = _normalize_for_projection(field_name, value)

        output_key = projection_config.field_rename.get(field_name, field_name)
        output_key = projection_config.canonical_path_mapping.get(field_name, output_key)
        _set_nested_value(output, output_key, value)

    if projection_config.include_confidence:
        output["confidence"] = {
            "overall": record.overall_confidence,
            "fields": compute_field_confidences(record),
        }

    if projection_config.include_provenance:
        output["provenance"] = [item.model_dump() for item in record.provenance]
        output["field_provenance"] = {
            field_name: _matching_provenance(record, field_name)
            for field_name in selected_fields
            if _matching_provenance(record, field_name)
        }

    return output


def _resolve_field(record: CandidateRecord, field_name: str) -> Any:
    # Handle list attribute projection (e.g., skills[].name)
    if "[]" in field_name:
        parts = field_name.split("[]")
        base = parts[0]
        rest = parts[1].lstrip(".")
        base_val = _resolve_field(record, base)
        if isinstance(base_val, list):
            res = []
            for item in base_val:
                if isinstance(item, dict) and rest in item:
                    res.append(item[rest])
                elif hasattr(item, "dict") and rest in item.dict():
                    res.append(item.dict()[rest])
                elif hasattr(item, "model_dump") and rest in item.model_dump():
                    res.append(item.model_dump()[rest])
                elif hasattr(item, rest):
                    res.append(getattr(item, rest))
                else:
                    res.append(None)
            return res
        return None

    # Handle array index lookup (e.g., emails[0])
    import re

    match = re.match(r"^(\w+)\[(\d+)\]$", field_name)
    if match:
        base = match.group(1)
        index = int(match.group(2))
        base_val = _resolve_field(record, base)
        if isinstance(base_val, list) and 0 <= index < len(base_val):
            return base_val[index]
        return None

    if field_name == "candidate_id":
        return record.candidate_id
    if field_name == "full_name":
        return record.full_name
    if field_name == "emails":
        return record.emails
    if field_name == "phones":
        return record.phones
    if field_name == "location":
        return record.location.model_dump()
    if field_name == "links":
        return record.links.model_dump()
    if field_name == "headline":
        return record.headline
    if field_name == "years_experience":
        return record.years_experience
    if field_name == "skills":
        return [skill.model_dump() for skill in record.skills]
    if field_name == "provenance":
        return [item.model_dump() for item in record.provenance]
    if field_name == "overall_confidence":
        return record.overall_confidence
    if field_name == "experience":
        return [item.model_dump() for item in record.experience]
    if field_name == "education":
        return [item.model_dump() for item in record.education]
    return None


def _normalize_for_projection(field_name: str, value: Any) -> Any:
    if field_name == "full_name" and isinstance(value, str):
        from candidate_transformer.normalizers.name import normalize_name

        return normalize_name(value)
    if field_name in {"phones", "phone"} and isinstance(value, list):
        from candidate_transformer.normalizers.phone import normalize_phone

        return [normalize_phone(item, default_country="IN") for item in value]
    if field_name in {"experience", "education"} and isinstance(value, list):
        return value
    return value


def _matching_provenance(record: CandidateRecord, field_name: str) -> list[dict[str, Any]]:
    matching: list[dict[str, Any]] = []
    for item in record.provenance:
        if item.field == field_name or item.field.startswith(f"{field_name}."):
            matching.append(item.model_dump())
    return matching


def _set_nested_value(payload: dict[str, Any], path: str, value: Any) -> None:
    parts = [part for part in path.split(".") if part]
    if not parts:
        return

    current: dict[str, Any] = payload
    for part in parts[:-1]:
        next_value = current.get(part)
        if not isinstance(next_value, dict):
            next_value = {}
            current[part] = next_value
        current = next_value

    current[parts[-1]] = value
