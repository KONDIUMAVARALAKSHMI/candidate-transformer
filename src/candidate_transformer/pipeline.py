from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog
from pydantic import ValidationError

from candidate_transformer.confidence import apply_confidence
from candidate_transformer.config import AppConfig, load_config
from candidate_transformer.merger import merge_candidates
from candidate_transformer.parsers.csv_parser import parse_csv
from candidate_transformer.parsers.json_parser import parse_json
from candidate_transformer.parsers.pdf_parser import parse_pdf
from candidate_transformer.projector import ProjectionConfig, load_projection_config, project_record
from candidate_transformer.schemas import CandidateRecord
from candidate_transformer.utils.logging import configure_logging


def run_pipeline(
    csv_path: str | Path | None = None,
    ats_path: str | Path | None = None,
    resume_path: str | Path | None = None,
    output_path: str | Path | None = None,
    config: AppConfig | str | Path | None = None,
    projection_config: ProjectionConfig | str | Path | None = None,
) -> list[CandidateRecord]:
    """Run the transformation pipeline from source files to validated JSONL output."""

    settings = load_config(config) if isinstance(config, (str, Path)) or config is None else config
    if not isinstance(settings, AppConfig):
        settings = load_config(config)

    # Initialize structured logger
    configure_logging(level=settings.log_level, format_type=settings.log_format)
    logger = structlog.get_logger("candidate_transformer.pipeline")

    logger.info(
        "Starting candidate transformation pipeline",
        csv_path=str(csv_path) if csv_path else None,
        ats_path=str(ats_path) if ats_path else None,
        resume_path=str(resume_path) if resume_path else None,
    )

    csv_records: list[dict[str, Any]] = []
    if csv_path:
        csv_records = parse_csv(csv_path)
        logger.debug("Parsed CSV records", count=len(csv_records))

    ats_records: list[dict[str, Any]] = []
    if ats_path:
        ats_records = parse_json(ats_path)
        logger.debug("Parsed ATS JSON records", count=len(ats_records))

    resume_records: list[dict[str, Any]] = []
    if resume_path:
        resume_records = parse_pdf(resume_path)
        logger.debug("Parsed resume records", count=len(resume_records))

    logger.info(
        "Merging profiles from all sources",
        csv_count=len(csv_records),
        ats_count=len(ats_records),
        resume_count=len(resume_records),
    )

    merged = merge_candidates(
        csv_records=csv_records,
        ats_records=ats_records,
        resume_records=resume_records,
        default_country=settings.default_country,
        date_formats=settings.date_formats,
    )
    logger.info("Successfully merged source candidate profiles", merged_count=len(merged))

    runtime_projection_config = (
        load_projection_config(projection_config)
        if isinstance(projection_config, (str, Path))
        else projection_config
    )
    if runtime_projection_config is None:
        runtime_projection_config = ProjectionConfig(
            field_selection=settings.projection_fields,
            field_rename=settings.field_rename,
            canonical_path_mapping=settings.canonical_path_mapping,
            normalize=True,
            include_confidence=settings.include_confidence,
            include_provenance=settings.include_provenance,
            on_missing=settings.on_missing,
        )

    output = (
        Path(output_path) if output_path else Path(settings.output_dir) / settings.output_filename
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    validated_records: list[CandidateRecord] = []
    projected_rows: list[dict[str, Any]] = []
    for record in merged:
        try:
            candidate = apply_confidence(record)
            candidate = CandidateRecord.model_validate(candidate.model_dump())
            projected = project_record(candidate, runtime_projection_config)
            logger.debug(
                "Validated and projected candidate record",
                name=candidate.full_name,
                confidence=candidate.overall_confidence,
            )
        except (ValidationError, ValueError) as exc:
            logger.error(
                "Candidate record validation failed",
                name=record.full_name or "unknown",
                error=str(exc),
            )
            raise ValueError(
                f"Validation failed for candidate {record.full_name or 'unknown'}: {exc}"
            ) from exc

        validated_records.append(candidate)
        projected_rows.append(projected)

    payload: Any = projected_rows[0] if len(projected_rows) == 1 else projected_rows
    with output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    logger.info("Wrote unified candidate output file", output_path=str(output))
    return validated_records
