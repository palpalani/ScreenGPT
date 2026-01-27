"""Shared test fixtures."""

from unittest.mock import AsyncMock

import pytest
from openai import AsyncOpenAI

from resume_screener.config import Settings
from resume_screener.models.candidate import CandidateProfile
from resume_screener.models.evaluation import EnhancedEvaluationResult
from resume_screener.models.job_description import JobRequirements


@pytest.fixture
def settings() -> Settings:
    """Create test settings."""
    return Settings(
        openai_api_key="test-api-key",
        openai_model="gpt-4",
        log_level="DEBUG",
        jd_file_path="resources/job_description.pdf",
    )


@pytest.fixture
def mock_openai_client() -> AsyncMock:
    """Create a mock AsyncOpenAI client."""
    client = AsyncMock(spec=AsyncOpenAI)
    return client


@pytest.fixture
def sample_candidate() -> CandidateProfile:
    """Create a sample candidate profile."""
    return CandidateProfile(
        name="John Doe",
        email="john.doe@example.com",
        phone="1234567890",
        education="Bachelor of Science in Computer Science",
        work_experience=5,
        skills=["Python", "FastAPI", "Machine Learning", "Docker"],
        certifications=["AWS Certified Developer"],
    )


@pytest.fixture
def sample_requirements() -> JobRequirements:
    """Create sample job requirements."""
    return JobRequirements(
        min_work_experience=3,
        max_work_experience=8,
        skills=["Python", "FastAPI", "Docker", "Kubernetes", "CI/CD"],
    )


@pytest.fixture
def sample_evaluation() -> EnhancedEvaluationResult:
    """Create a sample evaluation result."""
    return EnhancedEvaluationResult(
        candidate_status="Selected",
        recommendation="Hire",
        skill_match_score=60,
        experience_fit_score=100,
        overall_fit_score=76,
        matched_skills=["Python", "FastAPI", "Docker"],
        missing_skills=["Kubernetes", "CI/CD"],
        experience_years=5,
        experience_in_range=True,
        scoring_breakdown="60 * 0.6 + 100 * 0.4 = 76",
        decision_reasoning="Candidate has strong Python and FastAPI skills with 5 years of experience.",
    )


@pytest.fixture
def sample_resume_text() -> str:
    """Create sample resume text."""
    return """
    John Doe
    Email: john.doe@example.com
    Phone: 1234567890

    EDUCATION
    Bachelor of Science in Computer Science
    University of Technology, 2018

    EXPERIENCE
    Senior Software Engineer - Tech Corp (2019-Present)
    - Developed Python applications using FastAPI
    - Implemented Machine Learning pipelines
    - Managed Docker containers

    SKILLS
    Python, FastAPI, Machine Learning, Docker, Git

    CERTIFICATIONS
    AWS Certified Developer
    """


@pytest.fixture
def sample_jd_text() -> str:
    """Create sample job description text."""
    return """
    Senior Python Developer

    Requirements:
    - 3-8 years of experience in software development
    - Strong Python programming skills
    - Experience with FastAPI or similar frameworks
    - Docker and Kubernetes knowledge
    - CI/CD pipeline experience

    Responsibilities:
    - Design and develop scalable applications
    - Collaborate with cross-functional teams
    """
