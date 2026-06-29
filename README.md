# Candidate Transformer

Candidate Transformer is a production-minded data refinement and profile consolidation pipeline. It ingests candidate data from heterogeneous recruiting sources—such as tabular Recruiter CSV files, nested Applicant Tracking System (ATS) JSON feeds, and plain-text/PDF resumes—then normalizes, matches, merges, validates, and projects them into a unified, canonical schema.

---

## 1. System Architecture

The pipeline follows a modular architecture that separates parsing, normalisation, stateful merging, validation, and viewing (projection).

```
                                  [CLI Input Command]
                                           │
                                           ▼
                            +──────────────────────────────+
                            │   pipeline.py (Orchestrator)  │
                            +──────────────┬───────────────+
                                           │
         ┌─────────────────────────────────┼────────────────────────────────┐
         ▼                                 ▼                                ▼
 +───────────────+                 +───────────────+                +───────────────+
 │  CSV Parser   │                 │  JSON Parser  │                │  PDF Parser   │
 +───────┬───────+                 +───────┬───────+                +───────┬───────+
         │                                 │                                │
         └─────────────────────────────────┼────────────────────────────────┘
                                           ▼
                           +────────────────────────────────+
                           │  merger.py (Entity Resolution) │
                           │  - Keys: Email, Phone, Socials │
                           │  - Priority: ATS > CSV > Resume│
                           +───────────────┬────────────────+
                                           │
                                           ▼
                           +────────────────────────────────+
                           │ confidence.py (Scoring Engine) │
                           │ - Field Lineage Weights        │
                           │ - Overall mean normalization   │
                           +───────────────┬────────────────+
                                           │
                                           ▼
                           +────────────────────────────────+
                           │     schemas.py & validators    │
                           │   (Pydantic & Business Rules)  │
                           +───────────────┬────────────────+
                                           │
                                           ▼
                           +────────────────────────────────+
                           │    projector.py (View Layer)   │
                           │ - Rename, mapping, projection  │
                           +───────────────┬────────────────+
                                           │
                                           ▼
                             [Canonical JSON/JSONL Output]
```

### Module Breakdown
- **Parser Layer (`parsers/`)**: Converts heterogeneous physical files (CSV, JSON, PDF) into structured dictionary streams.
- **Normalizer Layer (`normalizers/`)**: Standardizes values—such as phone numbers to **E.164** format, dates to **YYYY-MM**, and names to trimmed, proper case text.
- **Merger Layer (`merger.py`)**: Performs key-based candidate resolution and merges fields using deterministic source precedence rules (`ATS > CSV > Resume`).
- **Confidence Engine (`confidence.py`)**: Assigns confidence scores to fields depending on source reliability and calculates the average score for the profile.
- **Validator Layer (`validators/`, `schemas.py`)**: Enforces validation constraints, including email syntax verification, phone format checks, and chronological validation of experience.
- **Projector Layer (`projector.py`)**: Filters, renames, and maps nested keys to create a custom output format.

---

## 2. Ingestion Flow: Input → Processing → Output

```
[CSV, JSON, Resume Ingest] ──> [Parse & Standardize] ──> [Match & Resolve] ──> [Merge & Track Lineage] ──> [Score & Validate] ──> [Project JSON]
```

### Ingestion Stages
1. **Ingest**: File paths are passed to `run_pipeline`.
2. **Parse & Standardize**: Specialized parsers extract records, and normalizers standardize names, phone formats, and dates.
3. **Match & Resolve**: Records are matched using a hierarchical search keys strategy (checking emails, phones, social URLs, and name-company combinations).
4. **Merge & Track Lineage**: Values are merged using priority rules, and changes are recorded in the `provenance` metadata.
5. **Score & Validate**: The confidence engine calculates quality scores, and Pydantic enforces schema constraints.
6. **Project**: The final output is formatted according to the projection rules and serialized to disk.

---

## 3. Concrete Ingestion Examples

### 3.1 Recruiter CSV (Input)
```csv
full_name,email,phone,location,skills,headline,years_experience
Ananya Reddy,ananya.reddy@gmail.com,+91 98765 43210,"Hyderabad, Telangana, India","Python; SQL; AWS; Docker","Software Engineer",4
```

### 3.2 ATS JSON (Input)
```json
{
  "candidates": [
    {
      "candidate_id": "ATS-1024",
      "full_name": "Ananya Reddy",
      "emails": ["ananya.reddy@gmail.com"],
      "phones": ["+919876543210"],
      "headline": "Software Engineer",
      "years_experience": 4,
      "skills": ["Python", "SQL", "AWS", "Docker"]
    }
  ]
}
```

### 3.3 Resume Text (Input)
```text
Ananya Reddy
Email: ananya.reddy@gmail.com
Phone: +91 98765 43210
Location: Hyderabad, Telangana, India
Skills: Python, SQL, AWS, Docker
Experience: Software Engineer with 4 years of experience at Google.
```

### 3.4 Canonical Unified Output (Projected Output)
```json
{
  "candidate_id": "ATS-1024",
  "full_name": "Ananya Reddy",
  "emails": [
    "ananya.reddy@gmail.com"
  ],
  "phones": [
    "+919876543210"
  ],
  "location": {
    "city": "Hyderabad",
    "region": "Telangana",
    "country": "IN"
  },
  "headline": "Software Engineer",
  "years_experience": 4.0,
  "skills": [
    {
      "name": "Python",
      "confidence": 0.95,
      "sources": ["ats", "csv", "resume"]
    },
    {
      "name": "SQL",
      "confidence": 0.95,
      "sources": ["ats", "csv", "resume"]
    }
  ],
  "provenance": [
    {
      "field": "candidate_id",
      "source": "ats",
      "method": "source"
    },
    {
      "field": "full_name",
      "source": "ats",
      "method": "merge"
    }
  ],
  "overall_confidence": 0.95
}
```

---

## 4. Production CLI Usage

### 4.1 Installation
Initialize a virtual environment and install the required dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4.2 Standard Execution
Run the pipeline by providing the paths to your input files:
```bash
python -m candidate_transformer.cli run \
  --csv inputs/recruiter.csv \
  --ats inputs/ats.json \
  --resume inputs/resume.txt \
  --output output/candidate.json
```

### 4.3 Custom Settings Config
Inject configuration parameters (such as logging formats or date parameters) using a YAML config file:
```bash
python -m candidate_transformer.cli run \
  --csv inputs/recruiter.csv \
  --config configs/default.yaml \
  --output output/candidate.json
```

### 4.4 Custom Output Projection
Apply field mapping, renames, and lineage inclusion rules by providing a projection config file:
```bash
python -m candidate_transformer.cli run \
  --csv inputs/recruiter.csv \
  --ats inputs/ats.json \
  --projection-config inputs/projection_config.json \
  --output output/candidate.json
```

---

## 5. Core Design Decisions & Trade-offs

### 5.1 Identity Resolution: Key Hierarchy Strategy
Rather than using loose fuzzy matching at the ingestion layer, Candidate Transformer uses a deterministic key lookup hierarchy to link candidate records across different systems.
1. **Email Lookup**: Direct matching using the candidate's email address.
2. **Phone Lookup**: Matching using normalized phone numbers.
3. **Social/Portfolio URLs**: Matching using profile links (e.g. LinkedIn, GitHub).
4. **Name-Company Combination**: Matching using the candidate's name combined with their current employer.
5. **Name-Only Fallback**: Matching using the candidate's name as a last resort.

*Trade-off*: This deterministic key lookup priority prevents incorrect merges. However, it may fail to link records that contain spelling mistakes or outdated information.

### 5.2 Deterministic Conflict Precedence
When merging scalar values, the system resolves conflicts by prioritizing sources based on their reliability: `ATS (System of Record) > CSV (Structured Uploads) > Resume (Unstructured Extraction)`.
- If the ATS contains a value, it is retained.
- If the ATS field is empty, it is filled by the CSV value.
- The Resume value is only used as a fallback if no other source provides the data.

*Trade-off*: This approach prioritizes structural reliability. However, it may ignore more recent updates contained in a candidate's resume if the ATS record is outdated.

### 5.3 Provenance and Lineage Tracking
The system records all merge operations in the `provenance` metadata. Each change logs:
- `field`: The canonical field that was modified.
- `source`: The file source that provided the data (`ats`, `csv`, or `resume`).
- `method`: The operation performed (`source` for creation, `merge` for updates).

*Trade-off*: While this increases the size of the output payload, it ensures the data remains auditable and reproducible.

### 5.4 Lineage-Based Confidence Scoring
Confidence scores are calculated using source reliability weights: `ATS: 0.95`, `CSV: 0.90`, and `Resume: 0.80`.
- **Field-level Confidence**: The highest confidence score among all sources that contributed to that specific field.
- **Overall Confidence**: The mathematical average of all calculated field-level confidence scores.

*Trade-off*: While this calculation is straightforward and fast, it does not evaluate the semantic accuracy of the data.

---

## 6. System Limitations & Engineering Roadmap

### 6.1 Unstructured Resume Ingestion
- *Limitation*: The current resume parser uses regular expressions to extract information, which may fail on complex or non-standard document layouts.
- *Roadmap*: Integrate OCR engines (e.g. `Tesseract`) and Named Entity Recognition (NER) models to extract structured information from unstructured text.

### 6.2 Scalability and In-Memory Execution
- *Limitation*: The merging process runs entirely in-memory, which restricts the pipeline's ability to process very large datasets.
- *Roadmap*: Port the merge logic to distributed processing frameworks (e.g. `Apache Spark` or `Ray`) to enable horizontal scaling.

### 6.3 Exact Match Constraints
- *Limitation*: The system relies on exact string matches for identity resolution, which can result in duplicate profiles if name variations exist.
- *Roadmap*: Implement fuzzy matching models (e.g. Bi-Encoder representations) to resolve profiles based on semantic similarity.

---

## 7. Interview Story: Engineering Presentation

### 7.1 How to present this project in an interview
"I developed **Candidate Transformer** to address a common data integration challenge: consolidating messy, multi-source candidate profiles into a single, validated database. The pipeline ingests recruiter CSVs, ATS JSON feeds, and unstructured resume text, normalizes the data, and merges matching profiles.

To ensure reliability, I implemented a deterministic key lookup hierarchy that resolves identities using unique identifiers (like emails, phone numbers, and social profiles) before falling back to name-company combinations. I also designed a multi-source precedence merge strategy (`ATS > CSV > Resume`) and built a metadata-driven provenance model to track the lineage of every field.

To ensure the output is production-ready, the pipeline validates all consolidated profiles against a Pydantic schema and uses a runtime projection layer to format the data for downstream services. Finally, I integrated structured logging using `structlog` for observability and configured a CI/CD pipeline using GitHub Actions to enforce linting, type-safety, and test coverage."

---

## 8. GitHub Repository Best Practices

- **`.gitignore` Configuration**: The `.gitignore` file is configured to exclude temporary files, virtual environments (`.venv`), output JSON/JSONL files, and log files, ensuring only source code and configuration templates are tracked.
- **Directory Structure**: The project follows a standard python package structure:
  - `src/candidate_transformer/`: Core source code modules (parsers, normalizers, merger, projector, schemas).
  - `configs/`: YAML configuration templates.
  - `tests/`: Organized into separate `unit` and `integration` test folders.
- **Pre-commit Hooks**: Enforces styling rules and code quality checks using `ruff` and `mypy` before changes are committed to the repository.

---

## 9. Resume Bullet Points (Senior/Intern SWE/MLE Standard)

- **Designed and implemented** a multi-source data integration pipeline that consolidates candidate profiles from CSV, JSON, and PDF formats, resolving schema conflicts using a deterministic merge hierarchy.
- **Integrated Google's `phonenumbers` port** and custom regex parsers to normalize candidate fields (names, phones, and dates) and enforce data validation using Pydantic schemas.
- **Built a metadata-driven provenance model** that tracks data lineage and calculates quality confidence scores for consolidated candidate records.
- **Improved codebase quality** by writing unit and integration tests to achieve **81% test coverage**, and configured a CI/CD workflow using GitHub Actions to automate linting, type-checking, and testing.
- **Developed a runtime projection layer** that dynamically filters, renames, and maps nested keys to format data payloads for downstream microservices.

---

## 10. DevOps & Observability features

### 10.1 GitHub Actions CI Pipeline
The repository includes a CI workflow (`.github/workflows/ci.yml`) that runs on every push and pull request. It automates:
1. **Linting**: Running code quality checks using `ruff check`.
2. **Formatting**: Verifying code style formatting using `ruff format`.
3. **Type Safety**: Enforcing static type safety using `mypy`.
4. **Testing**: Running unit and integration tests using `pytest` and generating coverage reports.

### 10.2 Structured Logging & Observability
Observability is implemented using structured JSON logs (`structlog`), which capture key pipeline events:
- Ingestion start, file types, and counts.
- Profile merging and identity resolution events.
- Schema validation failures.
- File serialization paths.

You can configure the log format and severity level in `configs/default.yaml`:
```yaml
log_level: "INFO"           # DEBUG | INFO | WARNING | ERROR
log_format: "json"          # json (for production) | pretty (for local development)
```
