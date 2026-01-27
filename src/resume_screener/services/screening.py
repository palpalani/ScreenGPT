"""Screening orchestration service."""

import asyncio
from pathlib import Path
from typing import BinaryIO

import structlog
from openai import AsyncOpenAI

from resume_screener.agents.bias_compliance import BiasComplianceAgent
from resume_screener.agents.enhanced_evaluator import EnhancedCandidateEvaluatorAgent
from resume_screener.agents.experience_verifier import ExperienceVerificationAgent
from resume_screener.agents.explanation_generator import ExplanationGeneratorAgent
from resume_screener.agents.final_aggregator import FinalAggregatorAgent
from resume_screener.agents.jd_extractor import JDExtractorAgent
from resume_screener.agents.resume_extractor import ResumeExtractorAgent
from resume_screener.agents.skill_normalizer import SkillNormalizationAgent
from resume_screener.config import Settings
from resume_screener.exceptions import JobDescriptionNotFoundError, PipelineError
from resume_screener.models.aggregation import FinalRecommendation
from resume_screener.models.candidate import CandidateProfile
from resume_screener.models.job_description import JobRequirements
from resume_screener.services.pdf_parser import PDFParser

logger = structlog.get_logger()


class ScreeningService:
    """Orchestrates the 8-agent resume screening pipeline.

    Pipeline Phases:
    1. Parallel Extraction: Resume + JD parsing (concurrent)
    2. Skill Normalization: Normalize and match skills
    3. Parallel Verification: Experience verification + Bias compliance (concurrent)
    4. Enhanced Evaluation: Score calculation with all inputs
    5. Explanation Generation: Human-readable explanation
    6. Final Aggregation: Aggregate all signals into recommendation
    """

    def __init__(self, settings: Settings, client: AsyncOpenAI) -> None:
        self.settings = settings
        self.client = client
        self.pdf_parser = PDFParser()

        self.resume_extractor = ResumeExtractorAgent(client, settings)
        self.jd_extractor = JDExtractorAgent(client, settings)
        self.skill_normalizer = SkillNormalizationAgent(client, settings)
        self.experience_verifier = ExperienceVerificationAgent(client, settings)
        self.bias_compliance = BiasComplianceAgent(client, settings)
        self.enhanced_evaluator = EnhancedCandidateEvaluatorAgent(client, settings)
        self.explanation_generator = ExplanationGeneratorAgent(client, settings)
        self.final_aggregator = FinalAggregatorAgent(client, settings)

    async def _extract_phase(
        self,
        resume_text: str,
        jd_text: str,
    ) -> tuple[CandidateProfile, JobRequirements]:
        """Phase 1: Parallel extraction of candidate and JD data."""
        logger.info("phase_1_extraction_starting")

        try:
            candidate, requirements = await asyncio.gather(
                self.resume_extractor.execute(resume_text),
                self.jd_extractor.execute(jd_text),
            )
        except Exception as e:
            raise PipelineError(str(e), agent_name="extraction_phase") from e

        logger.info(
            "phase_1_extraction_complete",
            candidate=candidate.name,
            jd_skills=len(requirements.skills),
        )

        return candidate, requirements

    async def screen_resume(
        self,
        resume_file: BinaryIO,
        filename: str,
        is_location_required: bool = False,
    ) -> FinalRecommendation:
        """Screen a resume using the 8-agent pipeline."""
        logger.info("screening_starting", filename=filename)

        resume_text = self.pdf_parser.parse(resume_file)

        jd_path = Path(self.settings.jd_file_path)
        if not jd_path.exists():
            raise JobDescriptionNotFoundError(f"Job description not found: {jd_path}")

        jd_text = self.pdf_parser.parse_file(jd_path)

        candidate, requirements = await self._extract_phase(resume_text, jd_text)

        logger.info("phase_2_skill_normalization_starting")
        try:
            skill_normalization = await self.skill_normalizer.execute(
                candidate_skills=candidate.skills,
                jd_skills=requirements.skills,
            )
        except Exception as e:
            raise PipelineError(str(e), agent_name="skill_normalizer") from e

        logger.info(
            "phase_2_skill_normalization_complete",
            match_percentage=skill_normalization.skill_match_percentage,
        )

        logger.info("phase_3_verification_starting")
        try:
            experience_verification, compliance = await asyncio.gather(
                self.experience_verifier.execute(
                    resume_text=resume_text,
                    min_experience=requirements.min_work_experience,
                    max_experience=requirements.max_work_experience,
                ),
                self.bias_compliance.execute(
                    resume_text=resume_text,
                    is_location_required=is_location_required,
                ),
            )
        except Exception as e:
            raise PipelineError(str(e), agent_name="verification_phase") from e

        logger.info(
            "phase_3_verification_complete",
            experience_years=experience_verification.total_experience_years,
            compliance_status=compliance.is_compliant,
        )

        logger.info("phase_4_enhanced_evaluation_starting")
        matched_skill_names = [pair[0] for pair in skill_normalization.matched_pairs]
        try:
            evaluation = await self.enhanced_evaluator.execute(
                candidate=candidate,
                requirements=requirements,
                skill_match_percentage=skill_normalization.skill_match_percentage,
                matched_skills=matched_skill_names,
                experience_years=experience_verification.total_experience_years,
                experience_fit_score=experience_verification.experience_fit_score,
                verification_confidence=experience_verification.verification_confidence,
                is_compliant=compliance.is_compliant,
                risk_level=compliance.risk_level,
            )
        except Exception as e:
            raise PipelineError(str(e), agent_name="enhanced_evaluator") from e

        logger.info(
            "phase_4_enhanced_evaluation_complete",
            recommendation=evaluation.recommendation,
            overall_score=evaluation.overall_fit_score,
        )

        logger.info("phase_5_explanation_generation_starting")
        try:
            explanation = await self.explanation_generator.execute(
                candidate=candidate,
                requirements=requirements,
                evaluation=evaluation,
            )
        except Exception as e:
            raise PipelineError(str(e), agent_name="explanation_generator") from e

        logger.info("phase_5_explanation_generation_complete")

        logger.info("phase_6_final_aggregation_starting")
        try:
            final_recommendation = await self.final_aggregator.execute(
                candidate=candidate,
                skill_normalization=skill_normalization,
                experience_verification=experience_verification,
                compliance=compliance,
                evaluation=evaluation,
                explanation=explanation,
            )
        except Exception as e:
            raise PipelineError(str(e), agent_name="final_aggregator") from e

        logger.info(
            "screening_complete",
            filename=filename,
            recommendation=final_recommendation.recommendation,
            overall_score=final_recommendation.overall_score,
            confidence=final_recommendation.confidence,
        )

        return final_recommendation
