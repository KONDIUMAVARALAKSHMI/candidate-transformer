from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class Location(BaseModel):
    """Candidate location information."""

    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None


class Links(BaseModel):
    """External profile links."""

    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    other: List[str] = Field(default_factory=list)


class Skill(BaseModel):
    """Normalized skill."""

    name: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    sources: List[str] = Field(default_factory=list)


class Experience(BaseModel):
    """Employment history."""

    company: Optional[str] = None
    title: Optional[str] = None
    start: Optional[str] = None  # YYYY-MM
    end: Optional[str] = None
    summary: Optional[str] = None


class Education(BaseModel):
    """Education history."""

    institution: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    end_year: Optional[int] = None


class Provenance(BaseModel):
    """Tracks where a field originated."""

    field: str
    source: str
    method: str


class CandidateRecord(BaseModel):
    """
    Canonical candidate profile.
    """

    candidate_id: Optional[str] = None

    full_name: Optional[str] = None

    emails: List[str] = Field(default_factory=list)

    phones: List[str] = Field(default_factory=list)

    location: Location = Field(default_factory=Location)

    links: Links = Field(default_factory=Links)

    headline: Optional[str] = None

    years_experience: Optional[float] = None

    skills: List[Skill] = Field(default_factory=list)

    experience: List[Experience] = Field(default_factory=list)

    education: List[Education] = Field(default_factory=list)

    provenance: List[Provenance] = Field(default_factory=list)

    overall_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    @field_validator("emails")
    @classmethod
    def check_emails(cls, value: List[str]) -> List[str]:
        from candidate_transformer.validators.candidate import validate_email_format
        for email in value:
            if not validate_email_format(email):
                raise ValueError(f"Invalid email address syntax: {email}")
        return value

    @field_validator("phones")
    @classmethod
    def check_phones(cls, value: List[str]) -> List[str]:
        from candidate_transformer.validators.candidate import validate_phone_format
        for phone in value:
            if not validate_phone_format(phone):
                raise ValueError(f"Invalid phone number format (must be E.164-compliant): {phone}")
        return value

    @model_validator(mode="after")
    def check_chronology(self) -> CandidateRecord:
        from candidate_transformer.validators.candidate import validate_chronological_experience
        if self.experience:
            validate_chronological_experience(self.experience)
        return self