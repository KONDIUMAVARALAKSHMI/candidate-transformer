# Data Dictionary

This document details the canonical schemas and validation constraints enforced by the `Candidate Transformer` data pipeline. All outputs must comply with the `CandidateRecord` structure.

---

## 1. CandidateRecord Model (Root)

The core schema model defining a unified candidate profile.

| Field Name | Type | Description | Normalization & Validation Rules | Example |
| :--- | :--- | :--- | :--- | :--- |
| `candidate_id` | `Optional[str]` | Unique identifier from the source system (e.g., ATS). | Checked against alphanumeric structures. | `"ATS-1024"` |
| `full_name` | `Optional[str]` | The candidate's name. | Standardized to title case, spaces trimmed, and double spaces removed. | `"Ananya Reddy"` |
| `emails` | `List[str]` | List of unique email addresses. | Standardized to lowercase. Validated with standard RFC 5322 regex checks. | `["ananya.reddy@gmail.com"]` |
| `phones` | `List[str]` | List of unique phone numbers. | Formatted using Google's `phonenumbers` port to match E.164 standards (`+<country><number>`). | `["+919876543210"]` |
| `location` | `Location` | Nested geographical information. | Parses flat location strings or nested dictionary keys. | *See Location Model* |
| `links` | `Links` | Nested external profile links. | Maps specific fields for LinkedIn, GitHub, and Portfolio. | *See Links Model* |
| `headline` | `Optional[str]` | Professional title or summary line. | String trimmed of whitespace. | `"Software Engineer"` |
| `years_experience`| `Optional[float]`| Total years of career history. | Cast to float. Can be null if empty. | `4.0` |
| `skills` | `List[Skill]` | List of standardized skill objects. | Deduplicated and standardized using alias mapping (e.g. `JS` -> `JavaScript`). | *See Skill Model* |
| `experience` | `List[Experience]`| Employment history timeline. | Elements appended from all sources. Validated chronologically. | *See Experience Model* |
| `education` | `List[Education]` | Educational background records. | Appended sequentially from sources. | *See Education Model* |
| `provenance` | `List[Provenance]`| Metadata mapping field lineage. | Appended dynamically during merge. | *See Provenance Model* |
| `overall_confidence`| `float` | Quality score indicating pipeline trust. | Float value between `0.0` and `1.0`. Average of field-level confidences. | `0.95` |

---

## 2. Nested Sub-Models

### 2.1 Location Model
Geographic identifiers.
* **`city`** (`Optional[str]`): Name of the city. (e.g., `"Hyderabad"`)
* **`region`** (`Optional[str]`): Province, state, or region. (e.g., `"Telangana"`)
* **`country`** (`Optional[str]`): Upper-case ISO 3166-1 alpha-2 code where possible. (e.g., `"IN"`, `"US"`)

### 2.2 Links Model
Web presence coordinates.
* **`linkedin`** (`Optional[str]`): URL link to LinkedIn profile.
* **`github`** (`Optional[str]`): URL link to GitHub profile.
* **`portfolio`** (`Optional[str]`): URL link to personal website.
* **`other`** (`List[str]`): Secondary links or articles.

### 2.3 Skill Model
Skill indicators.
* **`name`** (`str`): Cleaned skill title (e.g., `"Python"`, `"Docker"`).
* **`confidence`** (`float`): Float indicating quality matching (ATS: `0.95`, CSV: `0.90`, Resume: `0.80`).
* **`sources`** (`List[str]`): List of ingestion pipelines containing this skill.

### 2.4 Experience Model
Employment history block.
* **`company`** (`Optional[str]`): Employer's name. (e.g., `"Google"`)
* **`title`** (`Optional[str]`): Job title. (e.g., `"Software Engineer"`)
* **`start`** (`Optional[str]`): Start date in YYYY-MM format. (e.g., `"2022-05"`)
* **`end`** (`Optional[str]`): End date in YYYY-MM format or `"Present"`. (e.g., `"2023-12"`)
* **`summary`** (`Optional[str]`): Description of duties.

### 2.5 Education Model
Degree details.
* **`institution`** (`Optional[str]`): University or academy.
* **`degree`** (`Optional[str]`): Level (e.g., `"Bachelor of Technology"`).
* **`field`** (`Optional[str]`): Field of study (e.g., `"Computer Science"`).
* **`end_year`** (`Optional[int]`): Graduation calendar year.

### 2.6 Provenance Model
Data lineage tracking.
* **`field`** (`str`): Canonical attribute identifier (e.g., `"full_name"`, `"location.city"`).
* **`source`** (`str`): Ingestion source key (`"ats"`, `"csv"`, `"resume"`).
* **`method`** (`str`): Execution context (`"source"` for first ingest, `"merge"` for reconciliation updates).
