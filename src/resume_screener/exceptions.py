"""Custom exceptions for resume screening."""


class ResumeScreenerError(Exception):
    """Base exception for resume screener."""


class PDFParseError(ResumeScreenerError):
    """Raised when PDF parsing fails."""


class LLMResponseError(ResumeScreenerError):
    """Raised when LLM response is invalid or cannot be parsed."""


class InvalidCandidateDataError(ResumeScreenerError):
    """Raised when candidate data is invalid or incomplete."""


class JobDescriptionNotFoundError(ResumeScreenerError):
    """Raised when job description file is not found."""


class SchemaValidationError(ResumeScreenerError):
    """Raised when agent output fails schema validation."""


class PipelineError(ResumeScreenerError):
    """Raised when the screening pipeline encounters a critical error."""

    def __init__(self, message: str, agent_name: str | None = None) -> None:
        self.agent_name = agent_name
        super().__init__(f"Pipeline error{f' in {agent_name}' if agent_name else ''}: {message}")
