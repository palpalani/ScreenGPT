"""Final aggregation models."""

from typing import Literal

from pydantic import BaseModel, Field


class AgentSignal(BaseModel):
    """Signal from an individual agent in the pipeline."""

    agent_name: str
    score: int | None = Field(default=None, ge=0, le=100)
    confidence: Literal["high", "medium", "low"]
    key_findings: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)


class FinalRecommendation(BaseModel):
    """Final hiring recommendation aggregated from all agents."""

    recommendation: Literal["Strong Hire", "Hire", "Maybe", "No Hire", "Strong No Hire"]
    overall_score: int = Field(ge=0, le=100)
    confidence: Literal["high", "medium", "low"]
    candidate_name: str
    candidate_email: str | None = None
    skill_match_score: int = Field(ge=0, le=100)
    experience_fit_score: int = Field(ge=0, le=100)
    agent_signals: list[AgentSignal] = Field(default_factory=list)
    summary: str = Field(description="Executive summary of the recommendation")
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    compliance_status: str = Field(description="Bias compliance status")
    next_steps: list[str] = Field(
        default_factory=list, description="Recommended next steps for hiring process"
    )
    reasoning: str = Field(description="Detailed reasoning for the recommendation")

    model_config = {"extra": "ignore"}
