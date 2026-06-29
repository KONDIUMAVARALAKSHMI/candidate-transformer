# System Architecture

The Candidate Transformer is a high-throughput, deterministic profile consolidation and data refinement pipeline designed to ingest, clean, resolve, merge, score, and project candidate data from heterogeneous recruiting sources.

---

## 1. Pipeline Execution Flow

The system uses a modular, linear flow pattern that isolates data extraction from normalization and consolidation logic.

```
       +---------------------------------------------+
       |                Input Sources                |
       |  (Recruiter CSV, ATS JSON, Resume PDF/Text) |
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |                Parser Layer                 |
       |  (csv_parser.py, json_parser.py, pdf_parser)|
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |              Normalizer Layer               |
       |  (Standardizes Names, Phones E.164, Dates)  |
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |               Resolution & Merge            |
       |  (Computes identity keys & applies source   |
       |        priority: ATS > CSV > Resume)        |
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |              Confidence Scoring             |
       |  (Field-level & Overall confidence math)    |
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |             Validation (Pydantic)           |
       | (Enforces schema & business rules syntax)   |
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |             Projection Layer                |
       |  (Field selection, renames, path mapping)   |
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |               Canonical Output              |
       |            (Unified JSON/JSONL)             |
       +---------------------------------------------+
```

---

## 2. Module Breakdown

### 2.1 Parser Layer (`candidate_transformer.parsers`)
Ingests raw files and transforms them into standard Python list-of-dictionary structures:
- **`csv_parser.py`**: Reads tabular CSV exports. Implements custom delimiter splitting (`comma` and `semicolon`) for parsing skills and deduplicates them.
- **`json_parser.py`**: Supports both standard JSON payloads and JSON Lines (JSONL) format.
- **`pdf_parser.py`**: Extracts text from PDF resumes using `pdfplumber` with a safe fallback to standard text extraction if dependencies are unavailable. Utilizes regular expressions to extract name, phone, email, and skill keywords.

### 2.2 Normalizer Layer (`candidate_transformer.normalizers`)
Enforces standardization on raw strings prior to identity resolution and merging:
- **`name.py`**: Trims leading/trailing whitespace, eliminates double spaces, title-cases letters, and formats hyphenated double names (e.g. `Ananya-Reddy`).
- **`phone.py`**: Utilizes Google's `phonenumbers` port to validate number structures and output standard E.164 strings.
- **`date.py`**: Ingests varied date inputs, evaluates custom configuration formats, and leverages `dateutil.parser` to return normalized `YYYY-MM` formats.

### 2.3 Merger Layer (`candidate_transformer.merger`)
Performs entity resolution and profile merging:
- **Identity Resolution (`_candidate_key`)**: Computes a deterministic identity key to associate profiles. Key evaluation prioritizes:
  1. Emails (lowercased)
  2. Phone numbers (E.164 format)
  3. LinkedIn, GitHub, or Portfolio URLs
  4. Normalized Full Name + First Experience Employer
  5. Normalized Full Name only
- **Priority Rules**: Implements source precedence priority (`ATS > CSV > Resume`) when choosing scalar values.
- **Deduplication**: Merges multi-valued attributes (e.g. emails, phone numbers, external links) using union collections and consolidates skill matrices based on name similarity.
- **Provenance Tracking (`provenance`)**: Documents every write and merge operation per field, noting the source and method used ("source" or "merge").

### 2.4 Confidence Layer (`candidate_transformer.confidence`)
Determines data trust values based on ingestion lineage:
- **Lineage Weights**: Maps sources to a standard score scale (`ATS: 0.95`, `CSV: 0.90`, `Resume: 0.80`).
- **Field-level Confidence**: Assigns the maximum weight among all sources that contributed to that specific field.
- **Overall Confidence**: Calculates the mathematical mean of all resolved field-level confidences.

### 2.5 Validation Layer (`candidate_transformer.validators`)
- Runs during Pydantic schema validation (`CandidateRecord.model_validate()`).
- Validates structure compliance and syntax (such as checking email patterns, phone digits, and chronological coherence).

### 2.6 Projection Layer (`candidate_transformer.projector`)
- Acts as a views/representation layer.
- Dynamically selects, renames, and maps nested keys (using dot-notation path mappings) to create a custom runtime JSON payload for downstream services.
