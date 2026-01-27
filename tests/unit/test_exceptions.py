"""Tests for custom exceptions."""


from resume_screener.exceptions import (
    InvalidCandidateDataError,
    JobDescriptionNotFoundError,
    LLMResponseError,
    PDFParseError,
    PipelineError,
    ResumeScreenerError,
    SchemaValidationError,
)


class TestExceptions:
    """Tests for custom exception classes."""

    def test_resume_screener_error(self) -> None:
        """Test base exception."""
        error = ResumeScreenerError("Test error")
        assert str(error) == "Test error"

    def test_pdf_parse_error(self) -> None:
        """Test PDF parse error."""
        error = PDFParseError("Failed to parse PDF")
        assert isinstance(error, ResumeScreenerError)
        assert "Failed to parse PDF" in str(error)

    def test_llm_response_error(self) -> None:
        """Test LLM response error."""
        error = LLMResponseError("Invalid JSON response")
        assert isinstance(error, ResumeScreenerError)
        assert "Invalid JSON response" in str(error)

    def test_invalid_candidate_data_error(self) -> None:
        """Test invalid candidate data error."""
        error = InvalidCandidateDataError("Missing email")
        assert isinstance(error, ResumeScreenerError)
        assert "Missing email" in str(error)

    def test_job_description_not_found_error(self) -> None:
        """Test job description not found error."""
        error = JobDescriptionNotFoundError("JD not found")
        assert isinstance(error, ResumeScreenerError)
        assert "JD not found" in str(error)

    def test_schema_validation_error(self) -> None:
        """Test schema validation error."""
        error = SchemaValidationError("Schema validation failed")
        assert isinstance(error, ResumeScreenerError)
        assert "Schema validation failed" in str(error)

    def test_pipeline_error_with_agent_name(self) -> None:
        """Test pipeline error with agent name."""
        error = PipelineError("Processing failed", agent_name="skill_normalizer")
        assert isinstance(error, ResumeScreenerError)
        assert "skill_normalizer" in str(error)
        assert "Processing failed" in str(error)
        assert error.agent_name == "skill_normalizer"

    def test_pipeline_error_without_agent_name(self) -> None:
        """Test pipeline error without agent name."""
        error = PipelineError("General pipeline error")
        assert isinstance(error, ResumeScreenerError)
        assert "General pipeline error" in str(error)
        assert error.agent_name is None
