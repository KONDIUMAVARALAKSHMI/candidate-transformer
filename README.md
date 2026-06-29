# Candidate Transformer

Candidate Transformer is a Python CLI project for consolidating candidate profile data from recruiter CSV exports, ATS JSON feeds, and resume text/PDF sources into a single normalized and validated output.

## Assignment Objective

The goal of this assignment is to build a small but production-minded data transformation pipeline that can:

- ingest heterogeneous candidate source data,
- normalize and merge records deterministically,
- attach confidence and provenance metadata,
- project the canonical record into a runtime-friendly JSON shape,
- and produce a final validated output for downstream use.

## Features

- Supports recruiter CSV, ATS JSON, and resume PDF/text ingestion
- Normalizes phone numbers to E.164 format
- Normalizes dates to YYYY-MM
- Cleans and standardizes human names
- Merges records with deterministic priority rules: ATS > CSV > Resume
- Deduplicates emails, phones, skills, and links
- Tracks provenance for each selected field
- Computes field-level and overall confidence scores
- Supports runtime projection configuration for field selection, renaming, path mapping, normalization, and missing-field behavior
- Validates output with Pydantic before writing the final JSON

## Supported Input Sources

### Recruiter CSV

A flat CSV file containing candidate fields such as full name, email, phone, location, skills, and headline.

### ATS JSON

A JSON or JSONL document containing candidate objects, typically with arrays of emails, phones, skills, and experience.

### Resume PDF

A PDF or plain-text resume that is parsed into a lightweight profile structure. If pdfplumber is unavailable, the parser falls back to plain text extraction.

## Canonical Output Schema

The canonical schema is defined by the Pydantic model in [src/candidate_transformer/schemas.py](src/candidate_transformer/schemas.py). It includes fields such as:

- full_name
- emails
- phones
- location
- links
- headline
- years_experience
- skills
- experience
- education
- provenance
- overall_confidence

## Runtime Projection Configuration

The runtime projection layer is configurable through JSON. It supports:

- field selection
- field renaming
- canonical path mapping
- normalization
- include_confidence
- include_provenance
- on_missing with values: null, omit, error

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

Run the pipeline with the CLI:

```bash
python -m candidate_transformer.cli run --csv inputs/recruiter.csv --ats inputs/ats.json --resume inputs/resume.txt --config configs/default.yaml --output output/candidate.json --projection-config inputs/projection_config.json
```

## CLI Examples

### Basic run

```bash
python -m candidate_transformer.cli run --csv inputs/recruiter.csv --ats inputs/ats.json --resume inputs/resume.txt --output output/candidate.json
```

### With custom projection

```bash
python -m candidate_transformer.cli run --csv inputs/recruiter.csv --ats inputs/ats.json --resume inputs/resume.txt --projection-config inputs/projection_config.json --output output/candidate.json
```

## Example Default Output

The repository includes a sample output at [output/candidate.json](output/candidate.json).

## Example Custom Projection

The sample projection configuration is available at [inputs/projection_config.json](inputs/projection_config.json). It demonstrates:

- renaming fields such as full_name to name
- remapping skills to capabilities
- including confidence and provenance in the output

## Folder Structure

```text
candidate_transformer/
├── configs/
├── docs/
├── inputs/
├── output/
├── src/candidate_transformer/
├── tests/
├── README.md
├── pyproject.toml
├── requirements.txt
```

## Assumptions

- The CSV, JSON, and resume sources represent the same candidate or closely related records.
- Resume parsing is lightweight and intended for demonstration quality rather than full OCR-level extraction.
- The project is designed for a coding assignment and uses simple, deterministic merge logic.

## Limitations

- Resume parsing is heuristic and may not capture every formatting variation.
- The merge strategy is deterministic but intentionally simple for interview-ready clarity.
- The projection layer is flexible but focuses on the core assignment requirements.

## Future Improvements

- Add real PDF OCR and structured resume parsing
- Introduce fuzzy identity matching across records
- Support richer validation and rejection logging
- Add more examples and integration tests for edge cases

## Running Tests

```bash
pytest -q
```

## License

MIT
