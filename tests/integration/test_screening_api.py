"""Integration tests for the screening API."""

import io
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from resume_screener.config import Settings
from resume_screener.exceptions import (
    LLMResponseError,
    ResumeScreenerError,
)
from resume_screener.main import app, get_openai_client, get_screening_service, get_settings


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings."""
    return Settings(
        openai_api_key="test-api-key",
        openai_model="gpt-4",
        log_level="DEBUG",
        jd_file_path="resources/job_description.pdf",
    )


@pytest.fixture
def mock_client() -> AsyncMock:
    """Create mock OpenAI client."""
    return AsyncMock()


@pytest.fixture
def client(test_settings: Settings, mock_client: AsyncMock) -> TestClient:
    """Create test client with dependency overrides."""
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_openai_client] = lambda: mock_client

    yield TestClient(app)

    app.dependency_overrides.clear()


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client: TestClient) -> None:
        """Test health check returns healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestScreeningEndpoint:
    """Tests for screening endpoint."""

    def test_screening_success(
        self,
        client: TestClient,
        mock_client: AsyncMock,
    ) -> None:
        """Test successful resume screening with 8-agent pipeline."""
        candidate_response = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "123456",
            "education": "BS CS",
            "work_experience": 5,
            "skills": ["Python", "FastAPI"],
            "certifications": [],
        }

        jd_response = {
            "min_work_experience": 3,
            "max_work_experience": 8,
            "skills": ["Python", "FastAPI", "Docker"],
        }

        skill_normalization_response = {
            "candidate_skills": [
                {
                    "raw_skill": "Python",
                    "normalized_skill": "Python",
                    "confidence": 1.0,
                    "category": "programming",
                },
                {
                    "raw_skill": "FastAPI",
                    "normalized_skill": "FastAPI",
                    "confidence": 1.0,
                    "category": "framework",
                },
            ],
            "jd_skills": [
                {
                    "raw_skill": "Python",
                    "normalized_skill": "Python",
                    "confidence": 1.0,
                    "category": "programming",
                },
                {
                    "raw_skill": "FastAPI",
                    "normalized_skill": "FastAPI",
                    "confidence": 1.0,
                    "category": "framework",
                },
                {
                    "raw_skill": "Docker",
                    "normalized_skill": "Docker",
                    "confidence": 1.0,
                    "category": "tool",
                },
            ],
            "matched_pairs": [["Python", "Python"], ["FastAPI", "FastAPI"]],
            "match_scores": {"Python:Python": 1.0, "FastAPI:FastAPI": 1.0},
            "skill_match_percentage": 67,
            "reasoning": "2 of 3 JD skills matched",
        }

        experience_verification_response = {
            "entries": [
                {
                    "company": "Tech Corp",
                    "role": "Software Engineer",
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
            "confidence_reason": "Clear dates and logical progression",
            "experience_fit_score": 100,
            "reasoning": "5 years experience within 3-8 year range",
        }

        compliance_response = {
            "is_compliant": True,
            "flags": [],
            "must_ignore_attributes": [],
            "location_relevant": False,
            "compliance_notes": "No protected attributes detected",
            "risk_level": "none",
        }

        evaluation_response = {
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
            "decision_reasoning": "Good skill match and perfect experience fit",
        }

        explanation_response = {
            "summary": "Strong candidate with good technical skills and experience.",
            "strengths": ["Python expertise", "FastAPI experience", "Solid experience level"],
            "gaps": ["Missing Docker experience"],
            "score_breakdown": {
                "skill_match_score": 67,
                "skill_match_weight": 0.6,
                "skill_match_details": "2 of 3 required skills matched",
                "experience_fit_score": 100,
                "experience_fit_weight": 0.4,
                "experience_fit_details": "5 years within 3-8 year range",
                "overall_fit_score": 80,
                "calculation_formula": "67 * 0.6 + 100 * 0.4 = 80",
            },
            "key_factors": ["Strong Python skills", "Appropriate experience level"],
            "recommendation_rationale": "Hire recommendation based on overall score of 80",
        }

        final_recommendation_response = {
            "recommendation": "Hire",
            "overall_score": 80,
            "confidence": "high",
            "candidate_name": "John Doe",
            "candidate_email": "john@example.com",
            "skill_match_score": 67,
            "experience_fit_score": 100,
            "agent_signals": [
                {
                    "agent_name": "SkillNormalizationAgent",
                    "score": 67,
                    "confidence": "high",
                    "key_findings": ["Good Python match"],
                    "concerns": ["Missing Docker"],
                }
            ],
            "summary": "Strong candidate recommended for hire",
            "strengths": ["Python expertise", "Good experience"],
            "gaps": ["Docker"],
            "compliance_status": "Compliant",
            "next_steps": ["Schedule technical interview", "Reference check"],
            "reasoning": "Overall score of 80 with high confidence",
        }

        responses = [
            candidate_response,
            jd_response,
            skill_normalization_response,
            experience_verification_response,
            compliance_response,
            evaluation_response,
            explanation_response,
            final_recommendation_response,
        ]
        call_count = 0

        async def mock_create(
            *_args: MagicMock,
            **_kwargs: MagicMock,
        ) -> MagicMock:
            nonlocal call_count
            mock_message = MagicMock()
            mock_message.content = json.dumps(responses[call_count])
            mock_choice = MagicMock()
            mock_choice.message = mock_message
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            call_count += 1
            return mock_response

        mock_client.chat.completions.create = mock_create

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample resume text"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with (
            patch("resume_screener.services.pdf_parser.PdfReader", return_value=mock_reader),
            patch("pathlib.Path.exists", return_value=True),
        ):
            response = client.post(
                "/screening/",
                files={"resume": ("test.pdf", io.BytesIO(b"fake pdf"), "application/pdf")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["recommendation"] == "Hire"
        assert data["overall_score"] == 80
        assert data["confidence"] == "high"
        assert data["candidate_name"] == "John Doe"

    def test_screening_with_location_required(
        self,
        client: TestClient,
        mock_client: AsyncMock,
    ) -> None:
        """Test screening with is_location_required parameter."""
        responses = [
            {
                "name": "John Doe",
                "email": "john@example.com",
                "skills": ["Python"],
                "work_experience": 5,
                "certifications": [],
            },
            {"min_work_experience": 3, "max_work_experience": 8, "skills": ["Python"]},
            {
                "candidate_skills": [],
                "jd_skills": [],
                "matched_pairs": [],
                "match_scores": {},
                "skill_match_percentage": 100,
                "reasoning": "Test",
            },
            {
                "entries": [],
                "total_experience_months": 60,
                "total_experience_years": 5,
                "has_gaps": False,
                "gap_details": [],
                "has_overlaps": False,
                "verification_confidence": "high",
                "confidence_reason": "Clear",
                "experience_fit_score": 100,
                "reasoning": "Good",
            },
            {
                "is_compliant": True,
                "flags": [],
                "must_ignore_attributes": [],
                "location_relevant": True,
                "compliance_notes": "Location relevant",
                "risk_level": "none",
            },
            {
                "candidate_status": "Selected",
                "recommendation": "Hire",
                "skill_match_score": 100,
                "experience_fit_score": 100,
                "overall_fit_score": 100,
                "matched_skills": ["Python"],
                "missing_skills": [],
                "experience_years": 5,
                "experience_in_range": True,
                "scoring_breakdown": "100",
                "decision_reasoning": "Good",
            },
            {
                "summary": "Good",
                "strengths": ["Python"],
                "gaps": [],
                "score_breakdown": {
                    "skill_match_score": 100,
                    "skill_match_weight": 0.6,
                    "skill_match_details": "All matched",
                    "experience_fit_score": 100,
                    "experience_fit_weight": 0.4,
                    "experience_fit_details": "Perfect fit",
                    "overall_fit_score": 100,
                    "calculation_formula": "100",
                },
                "key_factors": ["Skills"],
                "recommendation_rationale": "Strong hire",
            },
            {
                "recommendation": "Strong Hire",
                "overall_score": 100,
                "confidence": "high",
                "candidate_name": "John Doe",
                "candidate_email": "john@example.com",
                "skill_match_score": 100,
                "experience_fit_score": 100,
                "agent_signals": [],
                "summary": "Strong",
                "strengths": ["Python"],
                "gaps": [],
                "compliance_status": "Compliant",
                "next_steps": ["Interview"],
                "reasoning": "Perfect match",
            },
        ]
        call_count = 0

        async def mock_create(*_args: MagicMock, **_kwargs: MagicMock) -> MagicMock:
            nonlocal call_count
            mock_message = MagicMock()
            mock_message.content = json.dumps(responses[call_count])
            mock_choice = MagicMock()
            mock_choice.message = mock_message
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            call_count += 1
            return mock_response

        mock_client.chat.completions.create = mock_create

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample resume text"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with (
            patch("resume_screener.services.pdf_parser.PdfReader", return_value=mock_reader),
            patch("pathlib.Path.exists", return_value=True),
        ):
            response = client.post(
                "/screening/?is_location_required=true",
                files={"resume": ("test.pdf", io.BytesIO(b"fake pdf"), "application/pdf")},
            )

        assert response.status_code == 200

    def test_screening_no_file(self, client: TestClient) -> None:
        """Test screening without file returns error."""
        response = client.post("/screening/")

        assert response.status_code == 422

    def test_screening_invalid_pdf(
        self,
        client: TestClient,
    ) -> None:
        """Test screening with invalid PDF returns error."""
        with patch(
            "resume_screener.services.pdf_parser.PdfReader",
            side_effect=Exception("Invalid PDF"),
        ):
            response = client.post(
                "/screening/",
                files={"resume": ("test.pdf", io.BytesIO(b"not a pdf"), "application/pdf")},
            )

        assert response.status_code == 400
        assert "Failed to parse PDF" in response.json()["detail"]

    def test_screening_jd_not_found(
        self,
        client: TestClient,
    ) -> None:
        """Test screening with missing JD returns error."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample resume text"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with (
            patch("resume_screener.services.pdf_parser.PdfReader", return_value=mock_reader),
            patch("pathlib.Path.exists", return_value=False),
        ):
            response = client.post(
                "/screening/",
                files={"resume": ("test.pdf", io.BytesIO(b"fake pdf"), "application/pdf")},
            )

        assert response.status_code == 500
        assert "Job description not found" in response.json()["detail"]

    def test_screening_llm_error(
        self,
        client: TestClient,
        mock_client: AsyncMock,
    ) -> None:
        """Test screening with LLM error returns error."""
        mock_client.chat.completions.create = AsyncMock(
            side_effect=LLMResponseError("LLM returned empty response")
        )

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample resume text"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with (
            patch("resume_screener.services.pdf_parser.PdfReader", return_value=mock_reader),
            patch("pathlib.Path.exists", return_value=True),
        ):
            response = client.post(
                "/screening/",
                files={"resume": ("test.pdf", io.BytesIO(b"fake pdf"), "application/pdf")},
            )

        assert response.status_code == 500
        assert "Pipeline error" in response.json()["detail"]

    def test_screening_pipeline_error(
        self,
        client: TestClient,
        mock_client: AsyncMock,
    ) -> None:
        """Test screening with pipeline error returns error."""
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API connection failed")
        )

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample resume text"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with (
            patch("resume_screener.services.pdf_parser.PdfReader", return_value=mock_reader),
            patch("pathlib.Path.exists", return_value=True),
        ):
            response = client.post(
                "/screening/",
                files={"resume": ("test.pdf", io.BytesIO(b"fake pdf"), "application/pdf")},
            )

        assert response.status_code == 500
        assert "Pipeline error" in response.json()["detail"]

    def test_screening_no_filename(
        self,
        client: TestClient,
    ) -> None:
        """Test screening with empty filename returns validation error."""
        response = client.post(
            "/screening/",
            files={"resume": ("", io.BytesIO(b"fake pdf"), "application/pdf")},
        )

        # FastAPI validates the empty filename before our handler runs
        assert response.status_code == 422

    def test_screening_llm_response_error(
        self,
        client: TestClient,
        test_settings: Settings,
    ) -> None:
        """Test screening with direct LLMResponseError returns error."""
        from resume_screener.services.screening import ScreeningService

        async def mock_screen_resume(*_args, **_kwargs):
            raise LLMResponseError("LLM returned invalid response")

        mock_service = MagicMock(spec=ScreeningService)
        mock_service.screen_resume = mock_screen_resume

        app.dependency_overrides[get_settings] = lambda: test_settings
        # Override to return our mock service that raises LLMResponseError directly
        app.dependency_overrides[get_screening_service] = lambda: mock_service

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample resume text"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch("resume_screener.services.pdf_parser.PdfReader", return_value=mock_reader):
            response = client.post(
                "/screening/",
                files={"resume": ("test.pdf", io.BytesIO(b"fake pdf"), "application/pdf")},
            )

        assert response.status_code == 500
        assert "LLM processing error" in response.json()["detail"]
        app.dependency_overrides.clear()

    def test_screening_generic_error(
        self,
        client: TestClient,
        test_settings: Settings,
    ) -> None:
        """Test screening with generic ResumeScreenerError returns error."""
        from resume_screener.services.screening import ScreeningService

        async def mock_screen_resume(*_args, **_kwargs):
            raise ResumeScreenerError("Generic screening error occurred")

        mock_service = MagicMock(spec=ScreeningService)
        mock_service.screen_resume = mock_screen_resume

        app.dependency_overrides[get_settings] = lambda: test_settings
        app.dependency_overrides[get_screening_service] = lambda: mock_service

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample resume text"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch("resume_screener.services.pdf_parser.PdfReader", return_value=mock_reader):
            response = client.post(
                "/screening/",
                files={"resume": ("test.pdf", io.BytesIO(b"fake pdf"), "application/pdf")},
            )

        assert response.status_code == 500
        assert "Generic screening error occurred" in response.json()["detail"]
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_screening_with_none_filename(self) -> None:
        """Test screening with None filename returns error."""
        from fastapi import UploadFile

        from resume_screener.main import screen_resume
        from resume_screener.services.screening import ScreeningService

        # Create a mock UploadFile with None filename
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = None
        mock_file.file = io.BytesIO(b"fake pdf")

        mock_service = MagicMock(spec=ScreeningService)

        with pytest.raises(HTTPException) as exc_info:
            await screen_resume(mock_file, False, mock_service)

        assert exc_info.value.status_code == 400
        assert "No filename provided" in exc_info.value.detail


class TestDependencies:
    """Tests for FastAPI dependency functions."""

    def test_get_openai_client(self) -> None:
        """Test get_openai_client creates AsyncOpenAI instance."""
        from resume_screener.main import get_openai_client

        settings = Settings(openai_api_key="test-key-12345")
        client = get_openai_client(settings)

        from openai import AsyncOpenAI
        assert isinstance(client, AsyncOpenAI)
