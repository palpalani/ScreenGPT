"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from resume_screener.models.aggregation import AgentSignal, FinalRecommendation
from resume_screener.models.candidate import CandidateProfile
from resume_screener.models.compliance import BiasComplianceResult, ProtectedAttributeFlag
from resume_screener.models.evaluation import EnhancedEvaluationResult
from resume_screener.models.explanation import HumanReadableExplanation, ScoreBreakdown
from resume_screener.models.job_description import JobRequirements
from resume_screener.models.normalization import NormalizedSkillsResult, SkillMapping
from resume_screener.models.verification import ExperienceEntry, ExperienceVerificationResult


class TestCandidateProfile:
    """Tests for CandidateProfile model."""

    def test_valid_candidate(self) -> None:
        """Test creating a valid candidate profile."""
        candidate = CandidateProfile(
            name="John Doe",
            email="john@example.com",
            phone="1234567890",
            education="BS Computer Science",
            work_experience=5,
            skills=["Python", "FastAPI"],
            certifications=["AWS"],
        )

        assert candidate.name == "John Doe"
        assert candidate.email == "john@example.com"
        assert candidate.work_experience == 5
        assert len(candidate.skills) == 2

    def test_minimal_candidate(self) -> None:
        """Test creating a candidate with minimal required fields."""
        candidate = CandidateProfile(
            name="Jane Doe",
            email="jane@example.com",
        )

        assert candidate.name == "Jane Doe"
        assert candidate.phone is None
        assert candidate.education is None
        assert candidate.work_experience is None
        assert candidate.skills == []
        assert candidate.certifications == []

    def test_invalid_email(self) -> None:
        """Test that invalid email raises validation error."""
        with pytest.raises(ValidationError):
            CandidateProfile(
                name="John Doe",
                email="invalid-email",
            )

    def test_extra_fields_ignored(self) -> None:
        """Test that extra fields are ignored."""
        candidate = CandidateProfile(
            name="John Doe",
            email="john@example.com",
            unknown_field="should be ignored",  # type: ignore[call-arg]
        )

        assert not hasattr(candidate, "unknown_field")


class TestJobRequirements:
    """Tests for JobRequirements model."""

    def test_valid_requirements(self) -> None:
        """Test creating valid job requirements."""
        requirements = JobRequirements(
            min_work_experience=3,
            max_work_experience=8,
            skills=["Python", "Docker"],
        )

        assert requirements.min_work_experience == 3
        assert requirements.max_work_experience == 8
        assert len(requirements.skills) == 2

    def test_defaults(self) -> None:
        """Test default values."""
        requirements = JobRequirements()

        assert requirements.min_work_experience is None
        assert requirements.max_work_experience is None
        assert requirements.skills == []


class TestEnhancedEvaluationResult:
    """Tests for EnhancedEvaluationResult model."""

    def test_selected_result(self) -> None:
        """Test creating a selected evaluation result."""
        result = EnhancedEvaluationResult(
            candidate_status="Selected",
            recommendation="Hire",
            skill_match_score=80,
            experience_fit_score=90,
            overall_fit_score=84,
            matched_skills=["Python", "FastAPI"],
            missing_skills=["Docker"],
            experience_years=5,
            experience_in_range=True,
            scoring_breakdown="80 * 0.6 + 90 * 0.4 = 84",
            decision_reasoning="Strong match with required skills.",
        )

        assert result.candidate_status == "Selected"
        assert result.recommendation == "Hire"
        assert result.overall_fit_score == 84

    def test_rejected_result(self) -> None:
        """Test creating a rejected evaluation result."""
        result = EnhancedEvaluationResult(
            candidate_status="Rejected",
            recommendation="No Hire",
            skill_match_score=20,
            experience_fit_score=40,
            overall_fit_score=28,
            matched_skills=["Python"],
            missing_skills=["FastAPI", "Docker", "Kubernetes"],
            experience_years=2,
            experience_in_range=False,
            scoring_breakdown="20 * 0.6 + 40 * 0.4 = 28",
            decision_reasoning="Insufficient skill match and experience.",
        )

        assert result.candidate_status == "Rejected"
        assert result.recommendation == "No Hire"
        assert result.overall_fit_score == 28

    def test_invalid_status(self) -> None:
        """Test that invalid status raises validation error."""
        with pytest.raises(ValidationError):
            EnhancedEvaluationResult(
                candidate_status="Maybe",  # type: ignore[arg-type]
                recommendation="Hire",
                skill_match_score=50,
                experience_fit_score=50,
                overall_fit_score=50,
                matched_skills=[],
                missing_skills=[],
                experience_years=3,
                experience_in_range=True,
                scoring_breakdown="50 * 0.6 + 50 * 0.4 = 50",
                decision_reasoning="Unknown",
            )

    def test_invalid_score(self) -> None:
        """Test that score must be 0-100."""
        with pytest.raises(ValidationError):
            EnhancedEvaluationResult(
                candidate_status="Selected",
                recommendation="Hire",
                skill_match_score=150,
                experience_fit_score=50,
                overall_fit_score=50,
                matched_skills=["Python"],
                missing_skills=[],
                experience_years=3,
                experience_in_range=True,
                scoring_breakdown="invalid",
                decision_reasoning="Good match",
            )


class TestSkillMapping:
    """Tests for SkillMapping model."""

    def test_valid_skill_mapping(self) -> None:
        """Test creating a valid skill mapping."""
        mapping = SkillMapping(
            raw_skill="JS",
            normalized_skill="JavaScript",
            confidence=0.95,
            category="programming",
        )

        assert mapping.raw_skill == "JS"
        assert mapping.normalized_skill == "JavaScript"
        assert mapping.confidence == 0.95

    def test_invalid_confidence(self) -> None:
        """Test that confidence must be 0-1."""
        with pytest.raises(ValidationError):
            SkillMapping(
                raw_skill="JS",
                normalized_skill="JavaScript",
                confidence=1.5,
                category="programming",
            )


class TestNormalizedSkillsResult:
    """Tests for NormalizedSkillsResult model."""

    def test_valid_result(self) -> None:
        """Test creating a valid normalized skills result."""
        result = NormalizedSkillsResult(
            candidate_skills=[
                SkillMapping(
                    raw_skill="Python",
                    normalized_skill="Python",
                    confidence=1.0,
                    category="programming",
                )
            ],
            jd_skills=[
                SkillMapping(
                    raw_skill="Python",
                    normalized_skill="Python",
                    confidence=1.0,
                    category="programming",
                )
            ],
            matched_pairs=[("Python", "Python")],
            match_scores={"Python:Python": 1.0},
            skill_match_percentage=100,
            reasoning="Perfect match",
        )

        assert result.skill_match_percentage == 100
        assert len(result.matched_pairs) == 1


class TestExperienceEntry:
    """Tests for ExperienceEntry model."""

    def test_valid_entry(self) -> None:
        """Test creating a valid experience entry."""
        entry = ExperienceEntry(
            company="Tech Corp",
            role="Software Engineer",
            start_date="2020-01",
            end_date="present",
            duration_months=60,
            is_verified=True,
            notes=None,
        )

        assert entry.company == "Tech Corp"
        assert entry.is_verified is True


class TestExperienceVerificationResult:
    """Tests for ExperienceVerificationResult model."""

    def test_valid_result(self) -> None:
        """Test creating a valid verification result."""
        result = ExperienceVerificationResult(
            entries=[],
            total_experience_months=60,
            total_experience_years=5,
            has_gaps=False,
            gap_details=[],
            has_overlaps=False,
            verification_confidence="high",
            confidence_reason="Clear dates",
            experience_fit_score=100,
            reasoning="Good fit",
        )

        assert result.total_experience_years == 5
        assert result.verification_confidence == "high"


class TestProtectedAttributeFlag:
    """Tests for ProtectedAttributeFlag model."""

    def test_valid_flag(self) -> None:
        """Test creating a valid protected attribute flag."""
        flag = ProtectedAttributeFlag(
            attribute_type="location",
            detected_text="San Francisco",
            is_relevant=True,
            recommendation="Consider for on-site role",
        )

        assert flag.attribute_type == "location"
        assert flag.is_relevant is True


class TestBiasComplianceResult:
    """Tests for BiasComplianceResult model."""

    def test_valid_result(self) -> None:
        """Test creating a valid compliance result."""
        result = BiasComplianceResult(
            is_compliant=True,
            flags=[],
            must_ignore_attributes=[],
            location_relevant=False,
            compliance_notes="No issues",
            risk_level="none",
        )

        assert result.is_compliant is True
        assert result.risk_level == "none"


class TestScoreBreakdown:
    """Tests for ScoreBreakdown model."""

    def test_valid_breakdown(self) -> None:
        """Test creating a valid score breakdown."""
        breakdown = ScoreBreakdown(
            skill_match_score=80,
            skill_match_weight=0.6,
            skill_match_details="4 of 5 skills matched",
            experience_fit_score=100,
            experience_fit_weight=0.4,
            experience_fit_details="5 years in 3-8 range",
            overall_fit_score=88,
            calculation_formula="80 * 0.6 + 100 * 0.4 = 88",
        )

        assert breakdown.overall_fit_score == 88


class TestHumanReadableExplanation:
    """Tests for HumanReadableExplanation model."""

    def test_valid_explanation(self) -> None:
        """Test creating a valid explanation."""
        explanation = HumanReadableExplanation(
            summary="Strong candidate with good fit.",
            strengths=["Python expertise", "Good experience"],
            gaps=["Missing Docker"],
            score_breakdown=ScoreBreakdown(
                skill_match_score=80,
                skill_match_weight=0.6,
                skill_match_details="4 of 5 skills matched",
                experience_fit_score=100,
                experience_fit_weight=0.4,
                experience_fit_details="5 years in range",
                overall_fit_score=88,
                calculation_formula="80 * 0.6 + 100 * 0.4 = 88",
            ),
            key_factors=["Strong Python skills"],
            recommendation_rationale="Hire based on overall score of 88",
        )

        assert len(explanation.strengths) == 2
        assert explanation.score_breakdown.overall_fit_score == 88


class TestAgentSignal:
    """Tests for AgentSignal model."""

    def test_valid_signal(self) -> None:
        """Test creating a valid agent signal."""
        signal = AgentSignal(
            agent_name="SkillNormalizationAgent",
            score=80,
            confidence="high",
            key_findings=["Strong Python match"],
            concerns=["Missing Docker"],
        )

        assert signal.agent_name == "SkillNormalizationAgent"
        assert signal.score == 80

    def test_signal_with_null_score(self) -> None:
        """Test creating a signal with null score."""
        signal = AgentSignal(
            agent_name="BiasComplianceAgent",
            score=None,
            confidence="high",
            key_findings=["No bias detected"],
            concerns=[],
        )

        assert signal.score is None


class TestFinalRecommendation:
    """Tests for FinalRecommendation model."""

    def test_valid_recommendation(self) -> None:
        """Test creating a valid final recommendation."""
        recommendation = FinalRecommendation(
            recommendation="Hire",
            overall_score=80,
            confidence="high",
            candidate_name="John Doe",
            candidate_email="john@example.com",
            skill_match_score=75,
            experience_fit_score=88,
            agent_signals=[
                AgentSignal(
                    agent_name="SkillNormalizationAgent",
                    score=75,
                    confidence="high",
                    key_findings=["Good match"],
                    concerns=[],
                )
            ],
            summary="Strong candidate",
            strengths=["Python skills"],
            gaps=["Docker"],
            compliance_status="Compliant",
            next_steps=["Interview"],
            reasoning="Good overall fit",
        )

        assert recommendation.recommendation == "Hire"
        assert recommendation.overall_score == 80
        assert len(recommendation.agent_signals) == 1

    def test_recommendation_invalid_level(self) -> None:
        """Test that invalid recommendation level raises error."""
        with pytest.raises(ValidationError):
            FinalRecommendation(
                recommendation="Excellent",  # type: ignore[arg-type]
                overall_score=80,
                confidence="high",
                candidate_name="John Doe",
                skill_match_score=75,
                experience_fit_score=88,
                agent_signals=[],
                summary="Strong",
                strengths=[],
                gaps=[],
                compliance_status="OK",
                next_steps=[],
                reasoning="Good",
            )
