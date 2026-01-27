"""Final aggregation agent."""

import structlog

from resume_screener.agents.base import BaseAgent
from resume_screener.models.aggregation import FinalRecommendation
from resume_screener.models.candidate import CandidateProfile
from resume_screener.models.compliance import BiasComplianceResult
from resume_screener.models.evaluation import EnhancedEvaluationResult
from resume_screener.models.explanation import HumanReadableExplanation
from resume_screener.models.normalization import NormalizedSkillsResult
from resume_screener.models.verification import ExperienceVerificationResult
from resume_screener.prompts import AGGREGATE_FINAL_RECOMMENDATION

logger = structlog.get_logger()


class FinalAggregatorAgent(BaseAgent):
    """Agent that aggregates all signals into a final hiring recommendation."""

    async def execute(
        self,
        candidate: CandidateProfile,
        skill_normalization: NormalizedSkillsResult,
        experience_verification: ExperienceVerificationResult,
        compliance: BiasComplianceResult,
        evaluation: EnhancedEvaluationResult,
        explanation: HumanReadableExplanation,
    ) -> FinalRecommendation:
        """Aggregate all agent signals into final recommendation."""
        logger.info("aggregating_final_recommendation", candidate=candidate.name)

        prompt = AGGREGATE_FINAL_RECOMMENDATION.format(
            candidate_json=candidate.model_dump_json(),
            skill_normalization_json=skill_normalization.model_dump_json(),
            experience_verification_json=experience_verification.model_dump_json(),
            compliance_json=compliance.model_dump_json(),
            evaluation_json=evaluation.model_dump_json(),
            explanation_json=explanation.model_dump_json(),
        )

        response = await self._call_llm(prompt)
        result = self._parse_json_response(response, FinalRecommendation)

        logger.info(
            "final_recommendation_complete",
            recommendation=result.recommendation,
            overall_score=result.overall_score,
            confidence=result.confidence,
        )

        return result
