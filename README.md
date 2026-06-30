# Candidate Transformer

Candidate Transformer is a candidate profile consolidation and data refinement pipeline designed for the **Eightfold Engineering Intern (Jul-Dec 2026) Assignment**. 

The project ingests candidate profiles from heterogeneous recruiting sources—specifically structured tabular Recruiter CSV files, nested Applicant Tracking System (ATS) JSON feeds, and unstructured resume text or PDF documents—normalizes attributes to canonical structures, resolves duplicate identities, computes lineage-based confidence scores, validates compliance, and projects custom data views via configuration.

The pipeline outputs a unified, schema-validated JSON payload serialization representing consolidated, enriched candidate records.

---

## Features

The repository implements the following core features:

*   **Heterogeneous File Parsers**:
    *   **CSV Ingestion**: Parses tabular candidate lists. Implements delimiters (commas and semicolons) to split, clean, and deduplicate skills.
    *   **ATS JSON Ingestion**: Supports JSON candidate arrays, single JSON candidate objects, or line-delimited JSON Lines (JSONL).
    *   **Resume Ingestion**: Ingests plain text resumes and PDF resumes (using pdfplumber when available), extracting candidate name, email, phone, and skills via regular expression patterns.
*   **Canonical Validation Schema**: Enforces strict typing, nested structural constraints, and business logic validations via Pydantic model schemas.
*   **Attribute Normalization**:
    *   **Phone Numbers**: Parses and formats international numbers to standard **E.164** format using a port of Google's `phonenumbers` library.
    *   **Dates**: Standardizes diverse date expressions to **YYYY-MM** format utilizing `python-dateutil`.
    *   **Names**: Cleans excess whitespace, title-cases letters, and correctly formats hyphenated double names.
    *   **Countries**: Resolves locations to ISO 3166-1 alpha-2 codes using mapping aliases or `pycountry` library fallback lookups.
*   **Deterministic Merge Policy**: Links candidate profiles across systems using key-based entity resolution, resolving field conflicts using source precedence rules.
*   **Lineage-Based Confidence Scoring**: Assigns deterministic confidence metrics based on the trustworthiness of the source pipeline, featuring agreement bonuses and conflict penalties.
*   **Granular Provenance Tracking**: Appends audit logs detailing which source and method updated each field, supporting complete audibility.
*   **Runtime Configurable Projection**: Dynamically renames, maps, filters, or transforms canonical keys on serialization using a JSON projection configuration.
*   **Validation Verification**: Assures email regex validation, E.164 phone formats, and chronological employment verification.
*   **Command Line Interface**: Simple Typer command-line interface to execute the transformation pipeline end-to-end.
*   **Test Coverage**: Unit and integration tests covering the parser, merger, confidence engine, projection layer, and end-to-end pipeline.

---

## Assignment Requirements Covered

✔ Structured source (CSV)

✔ Structured source (ATS JSON)

✔ Unstructured source (Resume)

✔ Canonical normalization

✔ Deterministic merge policy

✔ Provenance tracking

✔ Confidence scoring

✔ Runtime configurable projection

✔ Output schema validation

✔ CLI interface

✔ Unit and integration tests

---

## Project Structure

```
candidate_transformer/
├── configs/                 # Pipeline and projection configurations
│   ├── default_config.yaml  # Default deduplication, normalization, and logging settings
│   ├── projection_config.json # Standard projection mapping, confidence, and provenance settings
│   └── projection_minimal.json # Minimal projection configuration without metadata
├── docs/                    # Design and data model documentation
│   ├── architecture.md      # Pipeline execution flow details
│   └── data_dictionary.md   # Canonical schemas and validation parameters
├── inputs/                  # Mock source inputs for development and validation
│   ├── ats.json             # Sample nested ATS JSON candidate profiles
│   ├── recruiter.csv        # Sample recruiter candidate spreadsheet
│   └── resume.txt           # Sample plain text resume profile
├── output/                  # Ingestion output directory
│   ├── candidate.json       # Generated standard output payload
│   └── candidate_minimal.json # Generated minimal output payload
├── src/                     # Core application source
│   └── candidate_transformer/
│       ├── normalizers/     # Text normalization modules (names, phones, dates, countries)
│       ├── parsers/         # Ingestion parsers (CSV, JSON, PDF/Text)
│       ├── utils/           # Helper libraries (fuzzy search, logging utilities)
│       ├── validators/      # Business logic validators (email patterns, experience order)
│       ├── cli.py           # Command-Line Interface module
│       ├── confidence.py    # Lineage-based confidence engine
│       ├── config.py        # Configuration loading module
│       ├── merger.py        # Entity resolution and deduplication logic
│       ├── pipeline.py      # Pipeline execution orchestrator
│       ├── projector.py     # Configuration-driven view projector
│       └── schemas.py       # Pydantic data schemas
├── tests/                   # Automated tests
│   ├── fixtures/            # Static test file fixtures
│   ├── integration/         # End-to-end pipeline execution tests
│   └── unit/                # Component unit tests
├── pyproject.toml           # Tool configs for Black, Ruff, Mypy, and Pytest
├── requirements.txt         # Runtime and development dependency requirements
└── README.md                # Project documentation
```

---

## Architecture

The candidate transformation pipeline follows a modular sequence:

```
    [Input Sources] 
 (CSV, JSON, PDF/Text)
           │
           ▼
     [Parser Layer] ───> Converts files to dictionary streams
           │
           ▼
  [Normalizer Layer] ───> Standardizes phone (E.164), date (YYYY-MM), name, country
           │
           ▼
    [Merger Layer] ───> Entity resolution and source priority blending
           │
           ▼
  [Confidence Layer] ───> Calculates field and overall confidence scores
           │
           ▼
  [Validator Layer] ───> Pydantic schema validation & experience timeline check
           │
           ▼
  [Projector Layer] ───> Field selection, renaming, path mapping, metadata filters
           │
           ▼
    [Output JSON]
```

### Pipeline Flow Explanation
1. **Parsing**: Raw files are ingested and converted into list-of-dictionary records.
2. **Normalization**: Individual fields (phones, emails, names, countries, dates) are parsed and formatted into canonical structures.
3. **Merge**: Profiles are associated by identifying keys (email, phone, name) and merged according to source precedence. Lineage events are populated.
4. **Scoring**: Provenance logs are evaluated to assign deterministic confidence values.
5. **Validation**: The composite record is validated against Pydantic schema constraints.
6. **Projection**: The record is mapped to a customized format dictated by the projection config and written to the output file.

---

## Canonical Pipeline

*   **Parser**: Converts CSV, JSON, or PDF/Text into standard lists of dictionary structures.
*   **Normalizer**: Formats names (Title Case, trims spaces), phone numbers (E.164), dates (YYYY-MM), and countries (ISO alpha-2).
*   **Merger**: Groups profiles based on identifier keys, performs field merge logic, and writes metadata provenance records.
*   **Confidence**: Computes quality metrics using provenance events (source weighting, agreement bonuses, conflict penalties).
*   **Validator**: Enforces schema constraints, regex matches, and chronology validations using Pydantic.
*   **Projection**: Filters, maps, and renames canonical fields to serialize custom representations.

---

## Merge Strategy

The consolidation process resolves records into single profiles based on a deterministic merge strategy.

### 1. Identity Resolution Key Hierarchy
To determine whether candidate profiles from different sources represent the same person, the merger evaluates an identity key (`_candidate_key`) using a hierarchical priority:
1.  **Primary Email**: Exact match of the lowercased first email address.
2.  **Primary Phone**: Exact match of the normalized first E.164 phone number.
3.  **Name**: Exact match of the normalized, lowercased full name.
4.  **Fallback**: Falls back to `"unknown"` if no identity keys are present.

### 2. Source Precedence
When resolving conflicts for scalar values (such as `full_name`, `headline`, and geographic locations), the merger processes records in order of their reliability:
$$\text{ATS (System of Record)} > \text{CSV (Recruiter Input)} > \text{Resume (Unstructured Document)}$$

Because records are processed in this order (`ATS` $\rightarrow$ `CSV` $\rightarrow$ `Resume`), the first source that provides a value occupies the empty field. Subsequent sources do not overwrite already populated scalar values.

### 3. Conflict and Agreement Handling
*   **Conflict**: If a subsequent source provides a different value for an existing scalar field, the value is **not** overwritten. However, a `conflict` event is appended to the field's provenance log.
*   **Agreement**: If a subsequent source provides the same value for an existing scalar field, an `agreement` event is appended to the provenance log.
*   **Lists**: Fields like `emails` and `phones` collect all unique values across all sources using union sets.
*   **Skills**: Consolidated by lowercase name. If the same skill is found in multiple sources, the final skill keeps the maximum confidence score (`max(existing_conf, incoming_conf)`) and aggregates all unique sources.
*   **Experience & Education**: Consolidated by simply appending/extending the arrays in order.
*   *Note*: The `years_experience` field is parsed during normalization but is not currently merged in `_merge_record`. Consequently, it remains `null` in merged output records unless it is populated by the first matching record in the ingestion order.

---

## Confidence

Confidence is computed deterministically using lineage analysis. No machine learning or statistical inferences are used.

### Ingestion Source Weights
Each ingestion source is assigned a static reliability weight:
*   **ATS**: $0.95$
*   **CSV**: $0.90$
*   **Resume**: $0.80$

### Field-Level Confidence Calculation
For each of the 11 canonical fields, confidence is evaluated based on its provenance history:
1.  **Base Confidence**: The maximum weight among all unique sources that successfully contributed to the field (excluding sources that resulted in a `conflict`).
2.  **Agreement Bonus**: An increase of $+0.05$ for each additional unique agreeing source:
    $$\text{Bonus} = 0.05 \times (\text{number of unique agreeing/merging sources} - 1)$$
3.  **Conflict Penalty**: A deduction of $-0.10$ for every conflicting entry recorded:
    $$\text{Penalty} = 0.10 \times \text{number of conflict entries}$$
4.  **Skills Field Confidence**: The average confidence score of all individual skills, where each skill's confidence is its base confidence plus an agreement bonus ($0.05 \times (\text{number of sources} - 1)$).
5.  **Clipping**: Calculated confidence scores are strictly clipped to the range $[0.0, 1.0]$. If only conflicts exist, the base confidence is set to $0.5$ before applying penalties.

### Overall Confidence Score
The final candidate record is assigned an `overall_confidence` score, calculated as the simple arithmetic mean of all calculated field-level confidence scores.

---

## Provenance

Provenance provides a detailed metadata log tracking the lineage of every attribute. 

Each operation updates a global `provenance` list containing:
*   `field`: The canonical field name or path (e.g., `"full_name"`, `"location.city"`).
*   `source`: The source system that provided the data (`"ats"`, `"csv"`, or `"resume"`).
*   `method`: The context of the operation:
    *   `"source"`: Initial field value assignment.
    *   `"merge"`: Value merged into a previously empty field.
    *   `"agreement"`: Submitting a matching value from an additional source.
    *   `"conflict"`: Submitting a conflicting value from an additional source.

When projection is configured to include provenance, it serializes both the flat event log (`provenance`) and a structured dictionary mapping selected fields to their history (`field_provenance`).

---

## Runtime Projection

The projection layer defines how candidate records are structured, renamed, and filtered before serialization. It is driven entirely through a JSON configuration file.

Supported configuration parameters:
*   **`field_selection`**: A list of specific fields or nested paths to output.
    *   Supports array index lookups (e.g., `emails[0]`).
    *   Supports nested attribute projections from lists (e.g., `skills[].name`).
*   **`field_rename`**: Key-value mapping to rename output fields (e.g., `"full_name": "name"`).
*   **`canonical_path_mapping`**: Key-value mapping to nest or redirect fields (e.g., `"skills": "capabilities"`).
*   **`normalize`**: A boolean flag (default `true`) that triggers name/phone cleaning during projection.
*   **`include_confidence`**: A boolean flag (default `false`) that appends the `overall_confidence` and field-level confidence breakdowns.
*   **`include_provenance`**: A boolean flag (default `false`) that appends the global `provenance` list and a `field_provenance` dictionary mapping history to selected fields.
*   **`on_missing`**: Defines behavior when a requested field is absent from the merged profile:
    *   `"null"` (default): Sets the output value to `null`.
    *   `"omit"`: Excludes the field from the serialized output.
    *   `"error"`: Raises a `ValueError` halting execution.

---

## Requirements

*   **Python Version**: `>=3.11` (specifically tested on Python 3.11/3.14)
*   **Core Dependencies**:
    *   `typer==0.16.0` (CLI framework)
    *   `pydantic==2.7.1` (Schema validations)
    *   `pandas==2.2.2` (CSV parsing)
    *   `pdfplumber==0.11.1` (PDF resume parsing)
    *   `phonenumbers==8.13.37` (E.164 phone parsing)
    *   `python-dateutil==2.9.0.post0` (Date parsing)
    *   `rapidfuzz==3.9.3` (Fuzzy matching utilities)
    *   `PyYAML==6.0.1` (YAML configuration)
    *   `structlog==24.2.0` (Structured JSON logs)
*   **Development Dependencies**:
    *   `pytest==8.2.1` / `pytest-cov==5.0.0`
    *   `ruff==0.4.7` (Linting and formatting)
    *   `mypy==1.10.0` (Static type checking)

---

## Installation

1.  Clone the repository and navigate to the project directory:
    ```bash
    cd candidate_transformer
    ```

2.  Initialize a virtual environment:
    ```bash
    python -m venv .venv
    ```

3.  Activate the virtual environment:
    *   **Windows**:
        ```powershell
        .venv\Scripts\activate
        ```
    *   **Linux/macOS**:
        ```bash
        source .venv/bin/activate
        ```

4.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

---

## Running the Project

Run the ingestion pipeline command by executing the CLI module.

**PowerShell**:
```powershell
$env:PYTHONPATH="src"

python -m candidate_transformer.cli \
  --csv inputs/recruiter.csv \
  --ats inputs/ats.json \
  --resume inputs/resume.txt \
  --config configs/default_config.yaml \
  --projection-config configs/projection_config.json \
  --output output/candidate.json
```

**Bash / Linux / macOS**:
```bash
PYTHONPATH=src python -m candidate_transformer.cli \
  --csv inputs/recruiter.csv \
  --ats inputs/ats.json \
  --resume inputs/resume.txt \
  --config configs/default_config.yaml \
  --projection-config configs/projection_config.json \
  --output output/candidate.json
```

---

## Running with Minimal Projection

To output a simplified profile layout without metadata logs (confidence and provenance), use the minimal projection configuration:

**PowerShell**:
```powershell
$env:PYTHONPATH="src"

python -m candidate_transformer.cli \
  --csv inputs/recruiter.csv \
  --ats inputs/ats.json \
  --resume inputs/resume.txt \
  --config configs/default_config.yaml \
  --projection-config configs/projection_minimal.json \
  --output output/candidate_minimal.json
```

**Bash / Linux / macOS**:
```bash
PYTHONPATH=src python -m candidate_transformer.cli \
  --csv inputs/recruiter.csv \
  --ats inputs/ats.json \
  --resume inputs/resume.txt \
  --config configs/default_config.yaml \
  --projection-config configs/projection_minimal.json \
  --output output/candidate_minimal.json
```

---

## Sample Output

### 1. Standard Output (`output/candidate.json`)
Consolidated using `configs/projection_config.json`. Generates structured attributes alongside confidence scores and detailed field-level provenance logs:

```json
{
  "name": "Ananya Reddy",
  "email_addresses": [
    "ananya.reddy@gmail.com"
  ],
  "phone_numbers": [
    "+919876543210"
  ],
  "headline": "Software Engineer",
  "years_experience": null,
  "capabilities": [
    {
      "name": "Python",
      "confidence": 0.95,
      "sources": ["ats", "csv", "resume"]
    }
  ],
  "confidence": {
    "overall": 0.9416666666666668,
    "fields": {
      "location": 0.9,
      "full_name": 0.9,
      "headline": 0.95,
      "phones": 0.95,
      "emails": 0.95,
      "skills": 1.0
    }
  },
  "provenance": [
    {
      "field": "full_name",
      "source": "ats",
      "method": "merge"
    },
    {
      "field": "full_name",
      "source": "resume",
      "method": "conflict"
    }
  ],
  "field_provenance": {
    "full_name": [
      {
        "field": "full_name",
        "source": "ats",
        "method": "merge"
      },
      {
        "field": "full_name",
        "source": "resume",
        "method": "conflict"
      }
    ]
  }
}
```

### 2. Minimal Output (`output/candidate_minimal.json`)
Consolidated using `configs/projection_minimal.json`. Omits all metadata schemas and provides clean arrays:

```json
{
  "name": "Ananya Reddy",
  "email_addresses": [
    "ananya.reddy@gmail.com"
  ],
  "phone_numbers": [
    "+919876543210"
  ],
  "capabilities": [
    {
      "name": "Python",
      "confidence": 0.95,
      "sources": ["ats", "csv", "resume"]
    }
  ]
}
```

---

## Output Files

The pipeline generates:

- `output/candidate.json` – Default projected candidate profile including confidence and provenance.
- `output/candidate_minimal.json` – Minimal projected candidate profile without confidence and provenance.

---

## Running Tests

Execute the full testing suite using `pytest`:

```bash
pytest -v
```

To run tests with code coverage analysis:

```bash
pytest --cov=src/candidate_transformer --cov-report=term-missing
```

---

## Assumptions

The candidate transformer operates under the following functional assumptions:
1.  **Deduplication Keys**: Candidates are identical if they share a primary email address, normalized phone number, or matching full name.
2.  **Source Reliability Hierarchy**: System-of-record ATS data is inherently more accurate than CSV uploads, which are more accurate than unstructured resumes (`ATS > CSV > Resume`).
3.  **Country Target Format**: Geographical locations can be mapped directly to ISO 3166-1 alpha-2 standards (defaulting fallback to `"IN"`).
4.  **Employment Chronology**: Validated job experience must present end dates that do not precede start dates in `YYYY-MM` formatting.

---

## Edge Cases Handled

The system handles the following edge cases:
*   **Missing Fields**: Projector configuration handles absent values dynamically (outputs `null`, skips fields, or raises controlled exceptions).
*   **Conflicting Profile Values**: Keeps values based on source precedence and records mismatches as `conflict` method logs in the provenance metadata.
*   **Empty Ingestion Sources**: Gracefully handles empty CSV tables, JSON listings, or plain text files without pipeline failure.
*   **Duplicate Candidates**: Links duplicates across multiple datasets using identity key comparisons and builds a unified record.
*   **Invalid Phone Formats**: Filters out and flags numbers that do not conform to E.164 structures using parsed validations.
*   **Out of Bounds Projections**: Mapping index values (e.g., `emails[5]`) resolving past available array bounds outputs `null` instead of raising errors.
*   **Chronological Discrepancies**: Checks employment records, raising a validation error if a job's start date is chronologically after its end date.

---

## Future Improvements

Planned future developments include:
*   **Complete Merging for Experience Years**: Implementing full merge logic for the `years_experience` field to properly resolve and aggregate experience years across sources.
*   **Advanced Resume NER**: Integrating Named Entity Recognition models to parse unstructured resumes, replacing regex heuristics.
*   **Horizontal Scalability**: Migrating data ingestion pipelines to distributed systems (e.g., Apache Spark or Ray) for heavy workloads.
*   **Probabilistic Entity Matching**: Introducing fuzzy entity resolution weights to identify candidates with minor name spelling variations.

---

## Assignment Mapping

| Requirement | Status | Verification & Location |
| :--- | :--- | :--- |
| **Structured source** | ✓ | CSV and JSON parses resolved in `src/candidate_transformer/parsers/` |
| **Unstructured source** | ✓ | PDF/Text resume parsing in `src/candidate_transformer/parsers/pdf_parser.py` |
| **Normalization** | ✓ | Standardized names, phones, dates, and countries under `normalizers/` |
| **Merge** | ✓ | Deterministic merging and conflict tracking in `src/candidate_transformer/merger.py` |
| **Confidence** | ✓ | Provenance-based confidence engine in `src/candidate_transformer/confidence.py` |
| **Provenance** | ✓ | Detailed lineage metadata schemas tracking state updates in `schemas.py` |
| **Projection** | ✓ | Configurable projection mappings managed in `src/candidate_transformer/projector.py` |
| **Validation** | ✓ | RFC email, E.164 phone, and chronological validation checks in `validators/` |
| **CLI** | ✓ | Command-line control options defined in `src/candidate_transformer/cli.py` |
| **Tests** | ✓ | Comprehensive unit and integration coverage under `tests/` |
| **Output JSON** | ✓ | Writes formatted output targets to the `output/` directory |
