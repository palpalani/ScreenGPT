# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered resume screening system that evaluates candidates against job descriptions using OpenAI GPT-4. FastAPI backend with Streamlit UI. Uses an 8-agent pipeline for comprehensive candidate evaluation.

## Commands

### Setup (using uv)
```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Install with dev dependencies
uv sync --all-extras
```

### Run Backend (FastAPI)
```bash
uv run uvicorn resume_screener.main:app --reload
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Run Frontend (Streamlit)
```bash
uv run streamlit run ui/app.py
# UI: http://localhost:8501
```

### Run Tests
```bash
uv run pytest
uv run pytest --cov=resume_screener
```

### Lint & Format
```bash
uv run ruff check --fix .
uv run ruff format .
```

### Type Check
```bash
uv run mypy src/
```

## Architecture

### 8-Agent Pipeline (`POST /screening/`)

```
Resume PDF ──┐
             ├─► Phase 1: Parallel Extraction ─► Phase 2: Skill Normalization
JD PDF ──────┘                                           │
                                                         ▼
                                    Phase 3: Parallel Verification (Experience + Compliance)
                                                         │
                                                         ▼
                                    Phase 4: Enhanced Evaluation (0-100 scoring)
                                                         │
                                                         ▼
                                    Phase 5: Explanation Generation
                                                         │
                                                         ▼
                                    Phase 6: Final Aggregation → FinalRecommendation
```

**Agents:**
1. **ResumeExtractorAgent** - Extracts candidate info from resume
2. **JDExtractorAgent** - Extracts job requirements from JD
3. **SkillNormalizationAgent** - Normalizes and matches skills semantically
4. **ExperienceVerificationAgent** - Verifies work history, detects gaps/overlaps
5. **BiasComplianceAgent** - Checks for protected attributes, ensures fair evaluation
6. **EnhancedCandidateEvaluatorAgent** - Produces detailed 0-100 scoring
7. **ExplanationGeneratorAgent** - Creates human-readable decision explanations
8. **FinalAggregatorAgent** - Aggregates all signals into final recommendation

### Selection Criteria

- Skill match score: 0-100 based on normalized skill overlap
- Experience fit score: 0-100 based on range fit + verification confidence
- Overall fit score: skill_match * 0.6 + experience_fit * 0.4
- Recommendation levels: Strong Hire (≥85), Hire (70-84), Maybe (50-69), No Hire (30-49), Strong No Hire (<30)

## Project Structure

```
src/resume_screener/
├── main.py              # FastAPI app with /screening/ endpoint
├── config.py            # Pydantic settings configuration
├── exceptions.py        # Custom exception classes
├── prompts.py           # All LLM prompts (8 total)
├── models/
│   ├── candidate.py     # CandidateProfile model
│   ├── job_description.py  # JobRequirements model
│   ├── evaluation.py    # EnhancedEvaluationResult model
│   ├── normalization.py # SkillMapping, NormalizedSkillsResult models
│   ├── verification.py  # ExperienceEntry, ExperienceVerificationResult models
│   ├── compliance.py    # ProtectedAttributeFlag, BiasComplianceResult models
│   ├── explanation.py   # ScoreBreakdown, HumanReadableExplanation models
│   └── aggregation.py   # AgentSignal, FinalRecommendation models
├── agents/
│   ├── base.py          # Base agent with shared OpenAI client
│   ├── resume_extractor.py  # Async resume extraction
│   ├── jd_extractor.py  # Async JD extraction
│   ├── skill_normalizer.py  # Skill normalization agent
│   ├── experience_verifier.py  # Experience verification agent
│   ├── bias_compliance.py  # Bias compliance checking agent
│   ├── enhanced_evaluator.py  # Enhanced evaluation with scoring
│   ├── explanation_generator.py  # Human-readable explanation agent
│   └── final_aggregator.py  # Final recommendation aggregator
└── services/
    ├── pdf_parser.py    # PDF text extraction
    └── screening.py     # ScreeningService orchestration
```

## Key Files

- `src/resume_screener/main.py` - FastAPI app with `/screening/` endpoint
- `src/resume_screener/prompts.py` - All LLM prompts (modify evaluation logic here)
- `src/resume_screener/agents/` - Async agents calling OpenAI
- `src/resume_screener/services/screening.py` - Pipeline orchestration
- `src/resume_screener/services/pdf_parser.py` - PDF text extraction utility
- `resources/job_description.pdf` - Reference JD used for all evaluations
- `ui/app.py` - Streamlit frontend

## Environment Setup

Create `.env` file in project root (copy from `.env.example`):
```
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4
LOG_LEVEL=INFO
```

## API

**POST /screening/**
- Request: multipart form-data with `resume` file (PDF), optional `is_location_required` query param
- Response: `FinalRecommendation` with recommendation, overall_score, confidence, agent_signals, strengths, gaps, next_steps

**GET /health**
- Health check endpoint
- Response: `{ status: "healthy" }`

## Tech Stack

- **Python 3.12+** with modern type hints
- **uv** for dependency management
- **FastAPI** with async endpoints
- **Pydantic v2** for data validation
- **openai** async client
- **pypdf** for PDF parsing
- **structlog** for structured logging
- **pytest** + pytest-asyncio for testing
- **ruff** for linting and formatting
- **mypy** for type checking
