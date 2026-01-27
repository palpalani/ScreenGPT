"""Job description extraction agent."""

import structlog

from resume_screener.agents.base import BaseAgent
from resume_screener.models.job_description import JobRequirements
from resume_screener.prompts import EXTRACT_JD_DETAILS

logger = structlog.get_logger()


class JDExtractorAgent(BaseAgent):
    """Agent for extracting requirements from job descriptions."""

    async def execute(self, jd_text: str) -> JobRequirements:
        """Extract job requirements from job description text."""
        logger.info("extracting_job_requirements")

        prompt = EXTRACT_JD_DETAILS.format(jd_text=jd_text)
        response = await self._call_llm(prompt)

        requirements = self._parse_json_response(response, JobRequirements)
        logger.info(
            "requirements_extracted",
            skills_count=len(requirements.skills),
            exp_range=f"{requirements.min_work_experience}-{requirements.max_work_experience}",
        )

        return requirements
