"""Enhanced candidate evaluator agent."""

import structlog

from resume_screener.agents.base import BaseAgent
from resume_screener.models.candidate import CandidateProfile
from resume_screener.models.evaluation import EnhancedEvaluationResult
from resume_screener.models.job_description import JobRequirements
from resume_screener.prompts import ENHANCED_CANDIDATE_EVALUATION

logger = structlog.get_logger()


class EnhancedCandidateEvaluatorAgent(BaseAgent):
    """Agent that evaluates candidates with detailed scoring based on normalized data."""

    async def execute(
        self,
        candidate: CandidateProfile,
        requirements: JobRequirements,
        skill_match_percentage: int,
        matched_skills: list[str],
        experience_years: int | None,
        experience_fit_score: int,
        verification_confidence: str,
        is_compliant: bool,
        risk_level: str,
    ) -> EnhancedEvaluationResult:
        """Evaluate candidate with enhanced scoring."""
        logger.info(
            "enhanced_evaluation_starting",
            candidate=candidate.name,
            skill_match=skill_match_percentage,
            experience_fit=experience_fit_score,
        )

        prompt = ENHANCED_CANDIDATE_EVALUATION.format(
            candidate_json=candidate.model_dump_json(),
            jd_json=requirements.model_dump_json(),
            skill_match_percentage=skill_match_percentage,
            matched_skills=", ".join(matched_skills),
            experience_years=experience_years if experience_years is not None else "null",
            experience_fit_score=experience_fit_score,
            verification_confidence=verification_confidence,
            is_compliant=str(is_compliant).lower(),
            risk_level=risk_level,
        )

        response = await self._call_llm(prompt)
        result = self._parse_json_response(response, EnhancedEvaluationResult)

        logger.info(
            "enhanced_evaluation_complete",
            status=result.candidate_status,
            recommendation=result.recommendation,
            overall_score=result.overall_fit_score,
        )

        return result
