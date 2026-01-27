"""FastAPI application for resume screening."""

import structlog
from fastapi import Depends, FastAPI, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI

from resume_screener.config import Settings, get_settings
from resume_screener.exceptions import (
    JobDescriptionNotFoundError,
    LLMResponseError,
    PDFParseError,
    PipelineError,
    ResumeScreenerError,
)
from resume_screener.models.aggregation import FinalRecommendation
from resume_screener.services.screening import ScreeningService

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

app = FastAPI(
    title="Resume Screener API",
    description="AI-powered resume screening system using OpenAI GPT-4 with 8-agent pipeline",
    version="2.0.0",
)


def get_openai_client(settings: Settings = Depends(get_settings)) -> AsyncOpenAI:
    """Get AsyncOpenAI client dependency."""
    return AsyncOpenAI(api_key=settings.openai_api_key)


def get_screening_service(
    settings: Settings = Depends(get_settings),
    client: AsyncOpenAI = Depends(get_openai_client),
) -> ScreeningService:
    """Get ScreeningService dependency."""
    return ScreeningService(settings, client)


@app.post("/screening/", response_model=FinalRecommendation)
async def screen_resume(
    resume: UploadFile,
    is_location_required: bool = Query(
        default=False, description="Whether location is required for the position"
    ),
    service: ScreeningService = Depends(get_screening_service),
) -> JSONResponse:
    """Screen a resume using the 8-agent pipeline.

    This endpoint provides comprehensive candidate evaluation with:
    - Skill normalization and semantic matching
    - Experience verification with confidence scoring
    - Bias compliance checking
    - Detailed scoring breakdown
    - Human-readable explanations
    - Final hiring recommendation with confidence level
    """
    logger.info("received_resume", filename=resume.filename)

    if not resume.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    try:
        result = await service.screen_resume(resume.file, resume.filename, is_location_required)
        return JSONResponse(content=result.model_dump())

    except PDFParseError as e:
        logger.error("pdf_parse_error", error=str(e))
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {e}") from e

    except JobDescriptionNotFoundError as e:
        logger.error("jd_not_found", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e

    except LLMResponseError as e:
        logger.error("llm_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"LLM processing error: {e}") from e

    except PipelineError as e:
        logger.error("pipeline_error", error=str(e), agent=e.agent_name)
        raise HTTPException(status_code=500, detail=str(e)) from e

    except ResumeScreenerError as e:
        logger.error("screening_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
