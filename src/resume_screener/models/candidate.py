"""Candidate profile models."""

from pydantic import BaseModel, EmailStr, Field


class CandidateProfile(BaseModel):
    """Extracted candidate information from a resume."""

    name: str
    email: EmailStr
    phone: str | None = None
    education: str | None = None
    work_experience: int | None = Field(default=None, description="Years of work experience")
    skills: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)

    model_config = {"extra": "ignore"}
