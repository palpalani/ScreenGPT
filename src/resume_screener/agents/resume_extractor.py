"""Resume extraction agent."""

import structlog

from resume_screener.agents.base import BaseAgent
from resume_screener.models.candidate import CandidateProfile
from resume_screener.prompts import EXTRACT_CANDIDATE_DETAILS

logger = structlog.get_logger()


class ResumeExtractorAgent(BaseAgent):
    """Agent for extracting candidate information from resumes."""

    async def execute(self, resume_text: str) -> CandidateProfile:
        """Extract candidate details from resume text."""
        logger.info("extracting_candidate_details")

        prompt = EXTRACT_CANDIDATE_DETAILS.format(resume_text=resume_text)
        response = await self._call_llm(prompt)

        candidate = self._parse_json_response(response, CandidateProfile)
        logger.info("candidate_extracted", name=candidate.name, skills_count=len(candidate.skills))

        return candidate
