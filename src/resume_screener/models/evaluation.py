"""Evaluation result models."""

from typing import Literal

from pydantic import BaseModel, Field


class EnhancedEvaluationResult(BaseModel):
    """Evaluation result with detailed scoring."""

    candidate_status: Literal["Selected", "Rejected"]
    recommendation: Literal["Strong Hire", "Hire", "Maybe", "No Hire", "Strong No Hire"]
    skill_match_score: float = Field(ge=0, le=100, description="Normalized skill match score")
    experience_fit_score: float = Field(ge=0, le=100, description="Experience fit score")
    overall_fit_score: float = Field(ge=0, le=100, description="Combined overall score")
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list, description="Required skills not found")
    experience_years: int | None = Field(default=None)
    experience_in_range: bool = Field(description="Whether experience is within JD range")
    scoring_breakdown: str = Field(description="Explanation of how scores were calculated")
    decision_reasoning: str = Field(description="Detailed reasoning for the decision")

    model_config = {"extra": "ignore"}
