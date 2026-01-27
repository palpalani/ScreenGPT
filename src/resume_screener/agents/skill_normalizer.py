"""Skill normalization agent."""

import structlog

from resume_screener.agents.base import BaseAgent
from resume_screener.models.normalization import NormalizedSkillsResult
from resume_screener.prompts import NORMALIZE_SKILLS

logger = structlog.get_logger()


class SkillNormalizationAgent(BaseAgent):
    """Agent that normalizes skills and identifies matches between candidate and JD."""

    async def execute(
        self,
        candidate_skills: list[str],
        jd_skills: list[str],
    ) -> NormalizedSkillsResult:
        """Normalize skills and identify matches."""
        logger.info(
            "normalizing_skills",
            candidate_skill_count=len(candidate_skills),
            jd_skill_count=len(jd_skills),
        )

        prompt = NORMALIZE_SKILLS.format(
            candidate_skills=", ".join(candidate_skills),
            jd_skills=", ".join(jd_skills),
        )

        response = await self._call_llm(prompt)
        result = self._parse_json_response(response, NormalizedSkillsResult)

        logger.info(
            "skill_normalization_complete",
            match_percentage=result.skill_match_percentage,
            matched_count=len(result.matched_pairs),
        )

        return result
