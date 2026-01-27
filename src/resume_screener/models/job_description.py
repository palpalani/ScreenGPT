"""Job description models."""

from pydantic import BaseModel, Field


class JobRequirements(BaseModel):
    """Extracted requirements from a job description."""

    min_work_experience: int | None = Field(
        default=None, description="Minimum years of experience required"
    )
    max_work_experience: int | None = Field(
        default=None, description="Maximum years of experience required"
    )
    skills: list[str] = Field(default_factory=list, description="Required skills for the position")

    model_config = {"extra": "ignore"}
