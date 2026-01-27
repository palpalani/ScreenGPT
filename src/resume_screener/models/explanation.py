"""Human-readable explanation models."""

from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    """Breakdown of how the final score was calculated."""

    skill_match_score: int = Field(ge=0, le=100)
    skill_match_weight: float = Field(default=0.6)
    skill_match_details: str = Field(description="Explanation of skill matching")
    experience_fit_score: int = Field(ge=0, le=100)
    experience_fit_weight: float = Field(default=0.4)
    experience_fit_details: str = Field(description="Explanation of experience fit")
    overall_fit_score: int = Field(ge=0, le=100)
    calculation_formula: str = Field(description="Formula used for calculation")


class HumanReadableExplanation(BaseModel):
    """Human-readable explanation of the evaluation decision."""

    summary: str = Field(description="One-paragraph summary of the decision")
    strengths: list[str] = Field(default_factory=list, description="Candidate's key strengths")
    gaps: list[str] = Field(default_factory=list, description="Areas where candidate falls short")
    score_breakdown: ScoreBreakdown
    key_factors: list[str] = Field(
        default_factory=list, description="Top 3-5 factors that influenced the decision"
    )
    recommendation_rationale: str = Field(description="Why this recommendation level was chosen")

    model_config = {"extra": "ignore"}
