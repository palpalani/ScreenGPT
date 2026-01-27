"""Experience verification models."""

from typing import Literal

from pydantic import BaseModel, Field


class ExperienceEntry(BaseModel):
    """A single work experience entry extracted from resume."""

    company: str = Field(description="Company or organization name")
    role: str = Field(description="Job title or role")
    start_date: str = Field(description="Start date (YYYY-MM or 'unknown')")
    end_date: str = Field(description="End date (YYYY-MM, 'present', or 'unknown')")
    duration_months: int | None = Field(default=None, description="Calculated duration in months")
    is_verified: bool = Field(description="Whether dates could be verified from text")
    notes: str | None = Field(default=None, description="Any flags or concerns")


class ExperienceVerificationResult(BaseModel):
    """Result of experience verification analysis."""

    entries: list[ExperienceEntry] = Field(default_factory=list)
    total_experience_months: int = Field(description="Total calculated experience in months")
    total_experience_years: int = Field(description="Total experience rounded to years")
    has_gaps: bool = Field(description="Whether employment gaps were detected")
    gap_details: list[str] = Field(default_factory=list, description="Description of gaps if any")
    has_overlaps: bool = Field(description="Whether overlapping employment was detected")
    verification_confidence: Literal["high", "medium", "low"] = Field(
        description="Confidence in the verification"
    )
    confidence_reason: str = Field(description="Explanation of confidence level")
    experience_fit_score: int = Field(
        ge=0, le=100, description="Score based on experience range fit"
    )
    reasoning: str = Field(description="Explanation of experience analysis")

    model_config = {"extra": "ignore"}
