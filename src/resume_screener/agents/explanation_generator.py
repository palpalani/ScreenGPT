"""Explanation generator agent."""

import structlog

from resume_screener.agents.base import BaseAgent
from resume_screener.models.candidate import CandidateProfile
from resume_screener.models.evaluation import EnhancedEvaluationResult
from resume_screener.models.explanation import HumanReadableExplanation
from resume_screener.models.job_description import JobRequirements
from resume_screener.prompts import GENERATE_EXPLANATION

logger = structlog.get_logger()


class ExplanationGeneratorAgent(BaseAgent):
    """Agent that generates human-readable explanations for hiring decisions."""

    async def execute(
        self,
        candidate: CandidateProfile,
        requirements: JobRequirements,
        evaluation: EnhancedEvaluationResult,
    ) -> HumanReadableExplanation:
        """Generate human-readable explanation of the evaluation."""
        logger.info("generating_explanation", candidate=candidate.name)

        prompt = GENERATE_EXPLANATION.format(
            candidate_json=candidate.model_dump_json(),
            jd_json=requirements.model_dump_json(),
            evaluation_json=evaluation.model_dump_json(),
        )

        response = await self._call_llm(prompt)
        result = self._parse_json_response(response, HumanReadableExplanation)

        logger.info(
            "explanation_generated",
            strength_count=len(result.strengths),
            gap_count=len(result.gaps),
        )

        return result
