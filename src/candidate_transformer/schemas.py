from pydantic import BaseModel, Field, field_validator, model_validator


class Location(BaseModel):
    """Candidate location information."""

    city: str | None = None
    region: str | None = None
    country: str | None = None


class Links(BaseModel):
    """External profile links."""

    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None
    other: list[str] = Field(default_factory=list)


class Skill(BaseModel):
    """Normalized skill."""

    name: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    sources: list[str] = Field(default_factory=list)


class Experience(BaseModel):
    """Employment history."""

    company: str | None = None
    title: str | None = None
    start: str | None = None  # YYYY-MM
    end: str | None = None
    summary: str | None = None


class Education(BaseModel):
    """Education history."""

    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    end_year: int | None = None


class Provenance(BaseModel):
    """Tracks where a field originated."""

    field: str
    source: str
    method: str


class CandidateRecord(BaseModel):
    """
    Canonical candidate profile.
    """

    candidate_id: str | None = None

    full_name: str | None = None

    emails: list[str] = Field(default_factory=list)

    phones: list[str] = Field(default_factory=list)

    location: Location = Field(default_factory=Location)

    links: Links = Field(default_factory=Links)

    headline: str | None = None

    years_experience: float | None = None

    skills: list[Skill] = Field(default_factory=list)

    experience: list[Experience] = Field(default_factory=list)

    education: list[Education] = Field(default_factory=list)

    provenance: list[Provenance] = Field(default_factory=list)

    overall_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    @field_validator("emails")
    @classmethod
    def check_emails(cls, value: list[str]) -> list[str]:
        from candidate_transformer.validators.candidate import validate_email_format

        for email in value:
            if not validate_email_format(email):
                raise ValueError(f"Invalid email address syntax: {email}")
        return value

    @field_validator("phones")
    @classmethod
    def check_phones(cls, value: list[str]) -> list[str]:
        from candidate_transformer.validators.candidate import validate_phone_format

        for phone in value:
            if not validate_phone_format(phone):
                raise ValueError(f"Invalid phone number format (must be E.164-compliant): {phone}")
        return value

    @model_validator(mode="after")
    def check_chronology(self) -> "CandidateRecord":
        from candidate_transformer.validators.candidate import validate_chronological_experience

        if self.experience:
            validate_chronological_experience(self.experience)
        return self
