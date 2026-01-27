"""Bias compliance models."""

from typing import Literal

from pydantic import BaseModel, Field


class ProtectedAttributeFlag(BaseModel):
    """A flag for a detected protected attribute in resume text."""

    attribute_type: Literal[
        "age", "gender", "ethnicity", "religion", "disability", "location", "other"
    ]
    detected_text: str = Field(description="The text that triggered the flag")
    is_relevant: bool = Field(
        description="Whether this attribute is job-relevant (e.g., location for on-site roles)"
    )
    recommendation: str = Field(description="How to handle this flag")


class BiasComplianceResult(BaseModel):
    """Result of bias compliance check."""

    is_compliant: bool = Field(description="Whether screening can proceed without bias concerns")
    flags: list[ProtectedAttributeFlag] = Field(default_factory=list)
    must_ignore_attributes: list[str] = Field(
        default_factory=list, description="Attributes that must be ignored in evaluation"
    )
    location_relevant: bool = Field(description="Whether location is relevant for this position")
    compliance_notes: str = Field(description="Summary of compliance status")
    risk_level: Literal["none", "low", "medium", "high"] = Field(
        description="Risk level of bias in evaluation"
    )

    model_config = {"extra": "ignore"}
