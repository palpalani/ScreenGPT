"""Tests for LLM agents."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from resume_screener.agents.base import BaseAgent
from resume_screener.agents.bias_compliance import BiasComplianceAgent
from resume_screener.agents.enhanced_evaluator import EnhancedCandidateEvaluatorAgent
from resume_screener.agents.experience_verifier import ExperienceVerificationAgent
from resume_screener.agents.explanation_generator import ExplanationGeneratorAgent
from resume_screener.agents.final_aggregator import FinalAggregatorAgent
from resume_screener.agents.jd_extractor import JDExtractorAgent
from resume_screener.agents.resume_extractor import ResumeExtractorAgent
from resume_screener.agents.skill_normalizer import SkillNormalizationAgent
from resume_screener.config import Settings
from resume_screener.exceptions import LLMResponseError
from resume_screener.models.candidate import CandidateProfile
from resume_screener.models.compliance import BiasComplianceResult
from resume_screener.models.evaluation import EnhancedEvaluationResult
from resume_screener.models.explanation import HumanReadableExplanation
from resume_screener.models.job_description import JobRequirements
from resume_screener.models.normalization import NormalizedSkillsResult
from resume_screener.models.verification import ExperienceVerificationResult


class TestBaseAgent:
    """Tests for BaseAgent."""

    @pytest.fixture
    def agent(self, settings: Settings, mock_openai_client: AsyncMock) -> BaseAgent:
        """Create a base agent."""
        return BaseAgent(mock_openai_client, settings)

    async def test_call_llm_empty_response(
        self,
        agent: BaseAgent,
        mock_openai_client: AsyncMock,
    ) -> None:
        """Test handling empty LLM response."""
        mock_message = MagicMock()
        mock_message.content = None
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with pytest.raises(LLMResponseError, match="LLM returned empty response"):
            await agent._call_llm("test prompt")

    def test_parse_json_with_plain_code_block(
        self,
        agent: BaseAgent,
    ) -> None:
        """Test parsing JSON wrapped in plain code block."""
        response = "```\n{\"name\": \"test\"}\n```"

        class SimpleModel:
            @classmethod
            def model_validate(cls, _data: dict) -> "SimpleModel":
                return cls()

        result = agent._parse_json_response(response, SimpleModel)
        assert result is not None

    def test_parse_json_validation_error(
        self,
        agent: BaseAgent,
    ) -> None:
        """Test handling validation error."""
        response = '{"name": "test"}'

        class FailingModel:
            @classmethod
            def model_validate(cls, _data: dict) -> "FailingModel":
                raise ValueError("Validation failed")

        with pytest.raises(LLMResponseError, match="Failed to validate response"):
            agent._parse_json_response(response, FailingModel)


class TestResumeExtractorAgent:
    """Tests for ResumeExtractorAgent."""

    @pytest.fixture
    def agent(self, settings: Settings, mock_openai_client: AsyncMock) -> ResumeExtractorAgent:
        """Create a resume extractor agent."""
        return ResumeExtractorAgent(mock_openai_client, settings)

    async def test_extract_candidate(
        self,
        agent: ResumeExtractorAgent,
        mock_openai_client: AsyncMock,
        sample_resume_text: str,
    ) -> None:
        """Test extracting candidate from resume."""
        response_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "1234567890",
            "education": "BS Computer Science",
            "work_experience": 5,
            "skills": ["Python", "FastAPI"],
            "certifications": ["AWS"],
        }

        mock_message = MagicMock()
        mock_message.content = json.dumps(response_data)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await agent.execute(sample_resume_text)

        assert isinstance(result, CandidateProfile)
        assert result.name == "John Doe"
        assert result.email == "john.doe@example.com"
        assert result.work_experience == 5

    async def test_extract_with_json_code_block(
        self,
        agent: ResumeExtractorAgent,
        mock_openai_client: AsyncMock,
        sample_resume_text: str,
    ) -> None:
        """Test extracting from response wrapped in code block."""
        response_data = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": None,
            "education": None,
            "work_experience": None,
            "skills": [],
            "certifications": [],
        }

        mock_message = MagicMock()
        mock_message.content = f"```json\n{json.dumps(response_data)}\n```"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await agent.execute(sample_resume_text)

        assert result.name == "Jane Doe"

    async def test_invalid_json_response(
        self,
        agent: ResumeExtractorAgent,
        mock_openai_client: AsyncMock,
        sample_resume_text: str,
    ) -> None:
        """Test handling invalid JSON response."""
        mock_message = MagicMock()
        mock_message.content = "Not valid JSON"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with pytest.raises(LLMResponseError, match="Failed to parse JSON"):
            await agent.execute(sample_resume_text)


class TestJDExtractorAgent:
    """Tests for JDExtractorAgent."""

    @pytest.fixture
    def agent(self, settings: Settings, mock_openai_client: AsyncMock) -> JDExtractorAgent:
        """Create a JD extractor agent."""
        return JDExtractorAgent(mock_openai_client, settings)

    async def test_extract_requirements(
        self,
        agent: JDExtractorAgent,
        mock_openai_client: AsyncMock,
        sample_jd_text: str,
    ) -> None:
        """Test extracting requirements from job description."""
        response_data = {
            "min_work_experience": 3,
            "max_work_experience": 8,
            "skills": ["Python", "FastAPI", "Docker"],
        }

        mock_message = MagicMock()
        mock_message.content = json.dumps(response_data)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await agent.execute(sample_jd_text)

        assert isinstance(result, JobRequirements)
        assert result.min_work_experience == 3
        assert result.max_work_experience == 8
        assert "Python" in result.skills


class TestSkillNormalizationAgent:
    """Tests for SkillNormalizationAgent."""

    @pytest.fixture
    def agent(
        self,
        settings: Settings,
        mock_openai_client: AsyncMock,
    ) -> SkillNormalizationAgent:
        """Create a skill normalization agent."""
        return SkillNormalizationAgent(mock_openai_client, settings)

    async def test_normalize_skills(
        self,
        agent: SkillNormalizationAgent,
        mock_openai_client: AsyncMock,
    ) -> None:
        """Test skill normalization."""
        response_data = {
            "candidate_skills": [
                {"raw_skill": "Python", "normalized_skill": "Python", "confidence": 1.0, "category": "programming"},
            ],
            "jd_skills": [
                {"raw_skill": "Python", "normalized_skill": "Python", "confidence": 1.0, "category": "programming"},
            ],
            "matched_pairs": [["Python", "Python"]],
            "match_scores": {"Python:Python": 1.0},
            "skill_match_percentage": 100,
            "reasoning": "Perfect match",
        }

        mock_message = MagicMock()
        mock_message.content = json.dumps(response_data)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await agent.execute(["Python"], ["Python"])

        assert isinstance(result, NormalizedSkillsResult)
        assert result.skill_match_percentage == 100


class TestExperienceVerificationAgent:
    """Tests for ExperienceVerificationAgent."""

    @pytest.fixture
    def agent(
        self,
        settings: Settings,
        mock_openai_client: AsyncMock,
    ) -> ExperienceVerificationAgent:
        """Create an experience verification agent."""
        return ExperienceVerificationAgent(mock_openai_client, settings)

    async def test_verify_experience(
        self,
        agent: ExperienceVerificationAgent,
        mock_openai_client: AsyncMock,
        sample_resume_text: str,
    ) -> None:
        """Test experience verification."""
        response_data = {
            "entries": [
                {
                    "company": "Tech Corp",
                    "role": "Engineer",
                    "start_date": "2020-01",
                    "end_date": "present",
                    "duration_months": 60,
                    "is_verified": True,
                    "notes": None,
                }
            ],
            "total_experience_months": 60,
            "total_experience_years": 5,
            "has_gaps": False,
            "gap_details": [],
            "has_overlaps": False,
            "verification_confidence": "high",
            "confidence_reason": "Clear dates",
            "experience_fit_score": 100,
            "reasoning": "Good fit",
        }

        mock_message = MagicMock()
        mock_message.content = json.dumps(response_data)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await agent.execute(sample_resume_text, 3, 8)

        assert isinstance(result, ExperienceVerificationResult)
        assert result.total_experience_years == 5
        assert result.verification_confidence == "high"

    async def test_verify_experience_null_requirements(
        self,
        agent: ExperienceVerificationAgent,
        mock_openai_client: AsyncMock,
        sample_resume_text: str,
    ) -> None:
        """Test experience verification with null requirements."""
        response_data = {
            "entries": [],
            "total_experience_months": 0,
            "total_experience_years": 0,
            "has_gaps": False,
            "gap_details": [],
            "has_overlaps": False,
            "verification_confidence": "low",
            "confidence_reason": "No experience found",
            "experience_fit_score": 30,
            "reasoning": "Unknown experience",
        }

        mock_message = MagicMock()
        mock_message.content = json.dumps(response_data)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await agent.execute(sample_resume_text, None, None)

        assert isinstance(result, ExperienceVerificationResult)


class TestBiasComplianceAgent:
    """Tests for BiasComplianceAgent."""

    @pytest.fixture
    def agent(
        self,
        settings: Settings,
        mock_openai_client: AsyncMock,
    ) -> BiasComplianceAgent:
        """Create a bias compliance agent."""
        return BiasComplianceAgent(mock_openai_client, settings)

    async def test_check_compliance(
        self,
        agent: BiasComplianceAgent,
        mock_openai_client: AsyncMock,
        sample_resume_text: str,
    ) -> None:
        """Test bias compliance check."""
        response_data = {
            "is_compliant": True,
            "flags": [],
            "must_ignore_attributes": [],
            "location_relevant": False,
            "compliance_notes": "No issues",
            "risk_level": "none",
        }

        mock_message = MagicMock()
        mock_message.content = json.dumps(response_data)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await agent.execute(sample_resume_text, False)

        assert isinstance(result, BiasComplianceResult)
        assert result.is_compliant is True

    async def test_check_compliance_location_required(
        self,
        agent: BiasComplianceAgent,
        mock_openai_client: AsyncMock,
        sample_resume_text: str,
    ) -> None:
        """Test bias compliance check with location required."""
        response_data = {
            "is_compliant": True,
            "flags": [
                {
                    "attribute_type": "location",
                    "detected_text": "San Francisco",
                    "is_relevant": True,
                    "recommendation": "Consider location",
                }
            ],
            "must_ignore_attributes": [],
            "location_relevant": True,
            "compliance_notes": "Location relevant for role",
            "risk_level": "low",
        }

        mock_message = MagicMock()
        mock_message.content = json.dumps(response_data)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await agent.execute(sample_resume_text, True)

        assert result.location_relevant is True


class TestEnhancedCandidateEvaluatorAgent:
    """Tests for EnhancedCandidateEvaluatorAgent."""

    @pytest.fixture
    def agent(
        self,
        settings: Settings,
        mock_openai_client: AsyncMock,
    ) -> EnhancedCandidateEvaluatorAgent:
        """Create an enhanced evaluator agent."""
        return EnhancedCandidateEvaluatorAgent(mock_openai_client, settings)

    async def test_evaluate_selected(
        self,
        agent: EnhancedCandidateEvaluatorAgent,
        mock_openai_client: AsyncMock,
        sample_candidate: CandidateProfile,
        sample_requirements: JobRequirements,
    ) -> None:
        """Test evaluating a selected candidate."""
        response_data = {
            "candidate_status": "Selected",
            "recommendation": "Hire",
            "skill_match_score": 67,
            "experience_fit_score": 100,
            "overall_fit_score": 80,
            "matched_skills": ["Python", "FastAPI"],
            "missing_skills": ["Docker"],
            "experience_years": 5,
            "experience_in_range": True,
            "scoring_breakdown": "67 * 0.6 + 100 * 0.4 = 80",
            "decision_reasoning": "Good skill match and experience fit.",
        }

        mock_message = MagicMock()
        mock_message.content = json.dumps(response_data)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await agent.execute(
            candidate=sample_candidate,
            requirements=sample_requirements,
            skill_match_percentage=67,
            matched_skills=["Python", "FastAPI"],
            experience_years=5,
            experience_fit_score=100,
            verification_confidence="high",
            is_compliant=True,
            risk_level="none",
        )

        assert isinstance(result, EnhancedEvaluationResult)
        assert result.candidate_status == "Selected"
        assert result.recommendation == "Hire"
        assert result.overall_fit_score == 80

    async def test_evaluate_rejected(
        self,
        agent: EnhancedCandidateEvaluatorAgent,
        mock_openai_client: AsyncMock,
        sample_candidate: CandidateProfile,
        sample_requirements: JobRequirements,
    ) -> None:
        """Test evaluating a rejected candidate."""
        response_data = {
            "candidate_status": "Rejected",
            "recommendation": "No Hire",
            "skill_match_score": 20,
            "experience_fit_score": 40,
            "overall_fit_score": 28,
            "matched_skills": ["Python"],
            "missing_skills": ["FastAPI", "Docker", "Kubernetes"],
            "experience_years": 2,
            "experience_in_range": False,
            "scoring_breakdown": "20 * 0.6 + 40 * 0.4 = 28",
            "decision_reasoning": "Insufficient skill match and experience.",
        }

        mock_message = MagicMock()
        mock_message.content = json.dumps(response_data)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await agent.execute(
            candidate=sample_candidate,
            requirements=sample_requirements,
            skill_match_percentage=20,
            matched_skills=["Python"],
            experience_years=2,
            experience_fit_score=40,
            verification_confidence="medium",
            is_compliant=True,
            risk_level="none",
        )

        assert result.candidate_status == "Rejected"
        assert result.recommendation == "No Hire"


class TestExplanationGeneratorAgent:
    """Tests for ExplanationGeneratorAgent."""

    @pytest.fixture
    def agent(
        self,
        settings: Settings,
        mock_openai_client: AsyncMock,
    ) -> ExplanationGeneratorAgent:
        """Create an explanation generator agent."""
        return ExplanationGeneratorAgent(mock_openai_client, settings)

    async def test_generate_explanation(
        self,
        agent: ExplanationGeneratorAgent,
        mock_openai_client: AsyncMock,
        sample_candidate: CandidateProfile,
        sample_requirements: JobRequirements,
        sample_evaluation: EnhancedEvaluationResult,
    ) -> None:
        """Test generating explanation."""
        response_data = {
            "summary": "Strong candidate with good fit.",
            "strengths": ["Python expertise", "Good experience"],
            "gaps": ["Missing Docker"],
            "score_breakdown": {
                "skill_match_score": 60,
                "skill_match_weight": 0.6,
                "skill_match_details": "3 of 5 skills matched",
                "experience_fit_score": 100,
                "experience_fit_weight": 0.4,
                "experience_fit_details": "5 years in range",
                "overall_fit_score": 76,
                "calculation_formula": "60 * 0.6 + 100 * 0.4 = 76",
            },
            "key_factors": ["Python skills", "Experience level"],
            "recommendation_rationale": "Hire based on overall score of 76",
        }

        mock_message = MagicMock()
        mock_message.content = json.dumps(response_data)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await agent.execute(sample_candidate, sample_requirements, sample_evaluation)

        assert isinstance(result, HumanReadableExplanation)
        assert len(result.strengths) > 0


class TestFinalAggregatorAgent:
    """Tests for FinalAggregatorAgent."""

    @pytest.fixture
    def agent(
        self,
        settings: Settings,
        mock_openai_client: AsyncMock,
    ) -> FinalAggregatorAgent:
        """Create a final aggregator agent."""
        return FinalAggregatorAgent(mock_openai_client, settings)

    async def test_aggregate_final_recommendation(
        self,
        agent: FinalAggregatorAgent,
        mock_openai_client: AsyncMock,
        sample_candidate: CandidateProfile,
    ) -> None:
        """Test aggregating final recommendation."""
        response_data = {
            "recommendation": "Hire",
            "overall_score": 80,
            "confidence": "high",
            "candidate_name": "John Doe",
            "candidate_email": "john@example.com",
            "skill_match_score": 75,
            "experience_fit_score": 88,
            "agent_signals": [
                {
                    "agent_name": "SkillNormalizationAgent",
                    "score": 75,
                    "confidence": "high",
                    "key_findings": ["Good Python match"],
                    "concerns": [],
                }
            ],
            "summary": "Strong candidate recommended for hire",
            "strengths": ["Python expertise", "Good experience"],
            "gaps": ["Missing Docker"],
            "compliance_status": "Compliant",
            "next_steps": ["Schedule interview", "Reference check"],
            "reasoning": "Overall score of 80 with high confidence",
        }

        mock_message = MagicMock()
        mock_message.content = json.dumps(response_data)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        skill_normalization = NormalizedSkillsResult(
            candidate_skills=[],
            jd_skills=[],
            matched_pairs=[],
            match_scores={},
            skill_match_percentage=75,
            reasoning="Test",
        )

        experience_verification = ExperienceVerificationResult(
            entries=[],
            total_experience_months=60,
            total_experience_years=5,
            has_gaps=False,
            gap_details=[],
            has_overlaps=False,
            verification_confidence="high",
            confidence_reason="Clear dates",
            experience_fit_score=88,
            reasoning="Good fit",
        )

        compliance = BiasComplianceResult(
            is_compliant=True,
            flags=[],
            must_ignore_attributes=[],
            location_relevant=False,
            compliance_notes="No issues",
            risk_level="none",
        )

        evaluation = EnhancedEvaluationResult(
            candidate_status="Selected",
            recommendation="Hire",
            skill_match_score=75,
            experience_fit_score=88,
            overall_fit_score=80,
            matched_skills=["Python"],
            missing_skills=["Docker"],
            experience_years=5,
            experience_in_range=True,
            scoring_breakdown="75 * 0.6 + 88 * 0.4 = 80",
            decision_reasoning="Good overall fit",
        )

        explanation = HumanReadableExplanation(
            summary="Strong candidate",
            strengths=["Python"],
            gaps=["Docker"],
            score_breakdown={
                "skill_match_score": 75,
                "skill_match_weight": 0.6,
                "skill_match_details": "Good",
                "experience_fit_score": 88,
                "experience_fit_weight": 0.4,
                "experience_fit_details": "Good",
                "overall_fit_score": 80,
                "calculation_formula": "75 * 0.6 + 88 * 0.4 = 80",
            },
            key_factors=["Python"],
            recommendation_rationale="Good fit",
        )

        from resume_screener.models.aggregation import FinalRecommendation

        result = await agent.execute(
            candidate=sample_candidate,
            skill_normalization=skill_normalization,
            experience_verification=experience_verification,
            compliance=compliance,
            evaluation=evaluation,
            explanation=explanation,
        )

        assert isinstance(result, FinalRecommendation)
        assert result.recommendation == "Hire"
        assert result.overall_score == 80
