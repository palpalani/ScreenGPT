"""Skill normalization models."""

from pydantic import BaseModel, Field


class SkillMapping(BaseModel):
    """Maps a raw skill to its normalized form."""

    raw_skill: str = Field(description="Original skill as it appeared")
    normalized_skill: str = Field(description="Standardized skill name")
    confidence: float = Field(ge=0, le=1, description="Normalization confidence score")
    category: str = Field(description="Skill category (e.g., 'programming', 'framework', 'tool')")


class NormalizedSkillsResult(BaseModel):
    """Result of skill normalization for both candidate and JD skills."""

    candidate_skills: list[SkillMapping] = Field(default_factory=list)
    jd_skills: list[SkillMapping] = Field(default_factory=list)
    matched_pairs: list[tuple[str, str]] = Field(
        default_factory=list, description="Pairs of (candidate_skill, jd_skill) that match"
    )
    match_scores: dict[str, float] = Field(
        default_factory=dict, description="Similarity scores for matched pairs"
    )
    skill_match_percentage: int = Field(ge=0, le=100)
    reasoning: str = Field(description="Explanation of normalization and matching logic")

    model_config = {"extra": "ignore"}
