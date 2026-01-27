"""Tests for ScreeningService."""

import io
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from resume_screener.config import Settings
from resume_screener.exceptions import JobDescriptionNotFoundError, PipelineError
from resume_screener.services.screening import ScreeningService


class TestScreeningService:
    """Tests for ScreeningService."""

    @pytest.fixture
    def service(self, settings: Settings, mock_openai_client: AsyncMock) -> ScreeningService:
        """Create a screening service."""
        return ScreeningService(settings, mock_openai_client)

    def _create_mock_response(self, data: dict) -> MagicMock:
        """Create a mock OpenAI response."""
        mock_message = MagicMock()
        mock_message.content = json.dumps(data)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        return mock_response

    async def test_screen_resume_jd_not_found(
        self,
        service: ScreeningService,
    ) -> None:
        """Test screening with missing job description."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample resume text"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with (
            patch("resume_screener.services.pdf_parser.PdfReader", return_value=mock_reader),
            patch("pathlib.Path.exists", return_value=False),
            pytest.raises(JobDescriptionNotFoundError, match="Job description not found"),
        ):
            await service.screen_resume(
                io.BytesIO(b"fake pdf"),
                "test.pdf",
            )

    async def test_screen_resume_extraction_phase_error(
        self,
        service: ScreeningService,
        mock_openai_client: AsyncMock,
    ) -> None:
        """Test screening with extraction phase error."""
        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=Exception("Extraction failed")
        )

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample resume text"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with (
            patch("resume_screener.services.pdf_parser.PdfReader", return_value=mock_reader),
            patch("pathlib.Path.exists", return_value=True),
            pytest.raises(PipelineError, match="extraction_phase"),
        ):
            await service.screen_resume(
                io.BytesIO(b"fake pdf"),
                "test.pdf",
            )

    async def test_screen_resume_skill_normalizer_error(
        self,
        service: ScreeningService,
        mock_openai_client: AsyncMock,
    ) -> None:
        """Test screening with skill normalizer error."""
        candidate_response = self._create_mock_response({
            "name": "John Doe",
            "email": "john@example.com",
            "skills": ["Python"],
            "work_experience": 5,
            "certifications": [],
        })

        jd_response = self._create_mock_response({
            "min_work_experience": 3,
            "max_work_experience": 8,
            "skills": ["Python"],
        })

        call_count = 0

        async def mock_create(*_args: MagicMock, **_kwargs: MagicMock) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return candidate_response if call_count == 1 else jd_response
            raise Exception("Skill normalizer failed")

        mock_openai_client.chat.completions.create = mock_create

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample resume text"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with (
            patch("resume_screener.services.pdf_parser.PdfReader", return_value=mock_reader),
            patch("pathlib.Path.exists", return_value=True),
            pytest.raises(PipelineError, match="skill_normalizer"),
        ):
            await service.screen_resume(
                io.BytesIO(b"fake pdf"),
                "test.pdf",
            )

    async def test_screen_resume_verification_phase_error(
        self,
        service: ScreeningService,
        mock_openai_client: AsyncMock,
    ) -> None:
        """Test screening with verification phase error."""
        candidate_response = self._create_mock_response({
            "name": "John Doe",
            "email": "john@example.com",
            "skills": ["Python"],
            "work_experience": 5,
            "certifications": [],
        })

        jd_response = self._create_mock_response({
            "min_work_experience": 3,
            "max_work_experience": 8,
            "skills": ["Python"],
        })

        skill_response = self._create_mock_response({
            "candidate_skills": [],
            "jd_skills": [],
            "matched_pairs": [],
            "match_scores": {},
            "skill_match_percentage": 100,
            "reasoning": "Test",
        })

        call_count = 0

        async def mock_create(*_args: MagicMock, **_kwargs: MagicMock) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return candidate_response
            if call_count == 2:
                return jd_response
            if call_count == 3:
                return skill_response
            raise Exception("Verification failed")

        mock_openai_client.chat.completions.create = mock_create

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample resume text"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with (
            patch("resume_screener.services.pdf_parser.PdfReader", return_value=mock_reader),
            patch("pathlib.Path.exists", return_value=True),
            pytest.raises(PipelineError, match="verification_phase"),
        ):
            await service.screen_resume(
                io.BytesIO(b"fake pdf"),
                "test.pdf",
            )

    async def test_screen_resume_enhanced_evaluator_error(
        self,
        service: ScreeningService,
        mock_openai_client: AsyncMock,
    ) -> None:
        """Test screening with enhanced evaluator error."""
        responses = [
            self._create_mock_response({
                "name": "John",
                "email": "john@example.com",
                "skills": ["Python"],
                "work_experience": 5,
                "certifications": [],
            }),
            self._create_mock_response({
                "min_work_experience": 3,
                "max_work_experience": 8,
                "skills": ["Python"],
            }),
            self._create_mock_response({
                "candidate_skills": [],
                "jd_skills": [],
                "matched_pairs": [],
                "match_scores": {},
                "skill_match_percentage": 100,
                "reasoning": "Test",
            }),
            self._create_mock_response({
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
            }),
            self._create_mock_response({
                "is_compliant": True,
                "flags": [],
                "must_ignore_attributes": [],
                "location_relevant": False,
                "compliance_notes": "OK",
                "risk_level": "none",
            }),
        ]

        call_count = 0

        async def mock_create(*_args: MagicMock, **_kwargs: MagicMock) -> MagicMock:
            nonlocal call_count
            if call_count < len(responses):
                response = responses[call_count]
                call_count += 1
                return response
            raise Exception("Enhanced evaluator failed")

        mock_openai_client.chat.completions.create = mock_create

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample resume text"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with (
            patch("resume_screener.services.pdf_parser.PdfReader", return_value=mock_reader),
            patch("pathlib.Path.exists", return_value=True),
            pytest.raises(PipelineError, match="enhanced_evaluator"),
        ):
            await service.screen_resume(
                io.BytesIO(b"fake pdf"),
                "test.pdf",
            )

    async def test_screen_resume_explanation_generator_error(
        self,
        service: ScreeningService,
        mock_openai_client: AsyncMock,
    ) -> None:
        """Test screening with explanation generator error."""
        responses = [
            self._create_mock_response({
                "name": "John",
                "email": "john@example.com",
                "skills": ["Python"],
                "work_experience": 5,
                "certifications": [],
            }),
            self._create_mock_response({
                "min_work_experience": 3,
                "max_work_experience": 8,
                "skills": ["Python"],
            }),
            self._create_mock_response({
                "candidate_skills": [],
                "jd_skills": [],
                "matched_pairs": [],
                "match_scores": {},
                "skill_match_percentage": 100,
                "reasoning": "Test",
            }),
            self._create_mock_response({
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
            }),
            self._create_mock_response({
                "is_compliant": True,
                "flags": [],
                "must_ignore_attributes": [],
                "location_relevant": False,
                "compliance_notes": "OK",
                "risk_level": "none",
            }),
            self._create_mock_response({
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
            }),
        ]

        call_count = 0

        async def mock_create(*_args: MagicMock, **_kwargs: MagicMock) -> MagicMock:
            nonlocal call_count
            if call_count < len(responses):
                response = responses[call_count]
                call_count += 1
                return response
            raise Exception("Explanation generator failed")

        mock_openai_client.chat.completions.create = mock_create

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample resume text"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with (
            patch("resume_screener.services.pdf_parser.PdfReader", return_value=mock_reader),
            patch("pathlib.Path.exists", return_value=True),
            pytest.raises(PipelineError, match="explanation_generator"),
        ):
            await service.screen_resume(
                io.BytesIO(b"fake pdf"),
                "test.pdf",
            )

    async def test_screen_resume_final_aggregator_error(
        self,
        service: ScreeningService,
        mock_openai_client: AsyncMock,
    ) -> None:
        """Test screening with final aggregator error."""
        responses = [
            self._create_mock_response({
                "name": "John",
                "email": "john@example.com",
                "skills": ["Python"],
                "work_experience": 5,
                "certifications": [],
            }),
            self._create_mock_response({
                "min_work_experience": 3,
                "max_work_experience": 8,
                "skills": ["Python"],
            }),
            self._create_mock_response({
                "candidate_skills": [],
                "jd_skills": [],
                "matched_pairs": [],
                "match_scores": {},
                "skill_match_percentage": 100,
                "reasoning": "Test",
            }),
            self._create_mock_response({
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
            }),
            self._create_mock_response({
                "is_compliant": True,
                "flags": [],
                "must_ignore_attributes": [],
                "location_relevant": False,
                "compliance_notes": "OK",
                "risk_level": "none",
            }),
            self._create_mock_response({
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
            }),
            self._create_mock_response({
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
            }),
        ]

        call_count = 0

        async def mock_create(*_args: MagicMock, **_kwargs: MagicMock) -> MagicMock:
            nonlocal call_count
            if call_count < len(responses):
                response = responses[call_count]
                call_count += 1
                return response
            raise Exception("Final aggregator failed")

        mock_openai_client.chat.completions.create = mock_create

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample resume text"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with (
            patch("resume_screener.services.pdf_parser.PdfReader", return_value=mock_reader),
            patch("pathlib.Path.exists", return_value=True),
            pytest.raises(PipelineError, match="final_aggregator"),
        ):
            await service.screen_resume(
                io.BytesIO(b"fake pdf"),
                "test.pdf",
            )
