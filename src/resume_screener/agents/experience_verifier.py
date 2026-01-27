"""Experience verification agent."""

import structlog

from resume_screener.agents.base import BaseAgent
from resume_screener.models.verification import ExperienceVerificationResult
from resume_screener.prompts import VERIFY_EXPERIENCE

logger = structlog.get_logger()


class ExperienceVerificationAgent(BaseAgent):
    """Agent that verifies and analyzes work experience from resume text."""

    async def execute(
        self,
        resume_text: str,
        min_experience: int | None,
        max_experience: int | None,
    ) -> ExperienceVerificationResult:
        """Verify work experience entries and calculate fit score."""
        logger.info(
            "verifying_experience",
            min_required=min_experience,
            max_required=max_experience,
        )

        prompt = VERIFY_EXPERIENCE.format(
            resume_text=resume_text,
            min_experience=min_experience if min_experience is not None else "null",
            max_experience=max_experience if max_experience is not None else "null",
        )

        response = await self._call_llm(prompt)
        result = self._parse_json_response(response, ExperienceVerificationResult)

        logger.info(
            "experience_verification_complete",
            total_years=result.total_experience_years,
            confidence=result.verification_confidence,
            fit_score=result.experience_fit_score,
        )

        return result
