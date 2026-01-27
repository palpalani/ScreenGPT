# ScreenGPT

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-412991?logo=openai&logoColor=white)](https://openai.com/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue.svg)](http://mypy-lang.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

ScreenGPT is an open-source AI agent for automated resume screening. It parses resumes, matches skills and experience to job requirements, ranks candidates by fit, and generates clear screening rationales. Built for extensibility, auditability, and easy integration into HR workflows.

## Key Features

- **8-Agent Pipeline** - Enterprise-grade evaluation with skill normalization, experience verification, and bias compliance
- **Automated Resume Parsing** - Extracts candidate information from PDF resumes using AI
- **Intelligent Skill Matching** - Normalizes and compares skills semantically
- **Experience Verification** - Verifies work history, detects gaps and overlaps
- **Bias Compliance** - Checks for protected attributes to ensure fair evaluation
- **Detailed Scoring** - 0-100 scoring with recommendation levels (Strong Hire to Strong No Hire)
- **Human-Readable Explanations** - Clear reasoning for hiring decisions
- **Modern Web UI** - Clean Streamlit interface for easy resume uploads

## Table of Contents

- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Available Commands](#available-commands)
- [Testing](#testing)
- [How It Works](#how-it-works)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Tech Stack

| Category | Technology |
|----------|------------|
| **Language** | Python 3.12+ |
| **Package Manager** | [uv](https://github.com/astral-sh/uv) |
| **Backend Framework** | FastAPI |
| **Frontend** | Streamlit |
| **AI/LLM** | OpenAI GPT-4 |
| **Data Validation** | Pydantic v2 |
| **PDF Parsing** | pypdf |
| **HTTP Client** | httpx |
| **Logging** | structlog |
| **Testing** | pytest, pytest-asyncio |
| **Linting** | ruff |
| **Type Checking** | mypy |

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.12 or higher**
  ```bash
  python --version  # Should be 3.12+
  ```

- **uv package manager** (recommended)
  ```bash
  # Install uv
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- **OpenAI API Key**
  - Sign up at [OpenAI Platform](https://platform.openai.com/)
  - Create an API key in your account settings

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/palpalani/ScreenGPT.git
cd screengpt
```

### 2. Install Dependencies

Using uv (recommended):

```bash
# Install all dependencies including dev tools
uv sync --all-extras
```

<details>
<summary>Alternative: Using pip</summary>

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev,ui]"
```

</details>

### 3. Configure Environment

Copy the example environment file and add your OpenAI API key:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4
LOG_LEVEL=INFO
```

### 4. Add Job Description

Place your job description PDF in the `resources/` directory:

```bash
# The system looks for this file by default
resources/job_description.pdf
```

### 5. Start the Backend

```bash
uv run uvicorn resume_screener.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 6. Start the Frontend (Optional)

In a new terminal:

```bash
uv run streamlit run ui/app.py
```

The UI will be available at: http://localhost:8501

### 7. Test the System

1. Open the Streamlit UI at http://localhost:8501
2. Upload a PDF resume
3. Click "Process Resume"
4. View the evaluation results

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

| Phase | Agent | Purpose | Output |
|-------|-------|---------|--------|
| 1 | **ResumeExtractorAgent** | Extract candidate info | `CandidateProfile` |
| 1 | **JDExtractorAgent** | Extract job requirements | `JobRequirements` |
| 2 | **SkillNormalizationAgent** | Normalize and match skills | `NormalizedSkillsResult` |
| 3 | **ExperienceVerificationAgent** | Verify work history | `ExperienceVerificationResult` |
| 3 | **BiasComplianceAgent** | Check for bias/protected attributes | `BiasComplianceResult` |
| 4 | **EnhancedCandidateEvaluatorAgent** | Detailed 0-100 scoring | `EnhancedEvaluationResult` |
| 5 | **ExplanationGeneratorAgent** | Human-readable explanation | `HumanReadableExplanation` |
| 6 | **FinalAggregatorAgent** | Aggregate all signals | `FinalRecommendation` |

### Selection Criteria

- **Scoring Formula**: `overall_score = skill_match * 0.6 + experience_fit * 0.4`
- **Recommendation Levels**:
  - **Strong Hire**: overall_score ≥ 85, high confidence, no compliance issues
  - **Hire**: overall_score 70-84, good confidence
  - **Maybe**: overall_score 50-69 OR compliance flagged
  - **No Hire**: overall_score 30-49
  - **Strong No Hire**: overall_score < 30 OR compliance violations

## Project Structure

```
screengpt/
├── src/
│   └── resume_screener/
│       ├── __init__.py
│       ├── main.py              # FastAPI application entry point
│       ├── config.py            # Pydantic settings configuration
│       ├── exceptions.py        # Custom exception classes
│       ├── prompts.py           # LLM prompts for all agents (8 total)
│       ├── models/
│       │   ├── __init__.py
│       │   ├── candidate.py     # CandidateProfile model
│       │   ├── job_description.py  # JobRequirements model
│       │   ├── evaluation.py    # EnhancedEvaluationResult
│       │   ├── normalization.py # SkillMapping, NormalizedSkillsResult
│       │   ├── verification.py  # ExperienceEntry, ExperienceVerificationResult
│       │   ├── compliance.py    # ProtectedAttributeFlag, BiasComplianceResult
│       │   ├── explanation.py   # ScoreBreakdown, HumanReadableExplanation
│       │   └── aggregation.py   # AgentSignal, FinalRecommendation
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── base.py          # Base agent with OpenAI client
│       │   ├── resume_extractor.py  # Resume parsing agent
│       │   ├── jd_extractor.py  # Job description parsing agent
│       │   ├── skill_normalizer.py  # Skill normalization agent
│       │   ├── experience_verifier.py  # Experience verification agent
│       │   ├── bias_compliance.py  # Bias compliance checking agent
│       │   ├── enhanced_evaluator.py  # Enhanced evaluation with scoring
│       │   ├── explanation_generator.py  # Human-readable explanation agent
│       │   └── final_aggregator.py  # Final recommendation aggregator
│       └── services/
│           ├── __init__.py
│           ├── pdf_parser.py    # PDF text extraction
│           └── screening.py     # ScreeningService orchestration
├── ui/
│   └── app.py                   # Streamlit frontend
├── resources/
│   └── job_description.pdf      # Reference JD for evaluations
├── tests/
│   ├── conftest.py              # Shared test fixtures
│   ├── unit/
│   │   ├── test_models.py       # Pydantic model tests
│   │   ├── test_pdf_parser.py   # PDF parsing tests
│   │   └── test_agents.py       # Agent unit tests
│   └── integration/
│       └── test_screening_api.py  # API integration tests
├── pyproject.toml               # Project configuration
├── .env.example                 # Environment template
├── .gitignore
├── .editorconfig
└── README.md
```

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-abc123...` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `JD_FILE_PATH` | Path to job description PDF | `resources/job_description.pdf` |

## API Reference

### Screen Resume

Evaluate a resume using the 8-agent pipeline.

```http
POST /screening/
Content-Type: multipart/form-data
```

**Request:**
- `resume` (file, required): PDF resume file
- `is_location_required` (query, optional): Whether location is required for the position (default: false)

**Response:**
```json
{
  "recommendation": "Hire",
  "overall_score": 78,
  "confidence": "high",
  "candidate_name": "John Doe",
  "candidate_email": "john@example.com",
  "skill_match_score": 75,
  "experience_fit_score": 82,
  "agent_signals": [
    {
      "agent_name": "SkillNormalizationAgent",
      "score": 75,
      "confidence": "high",
      "key_findings": ["Strong Python expertise", "Modern framework knowledge"],
      "concerns": []
    }
  ],
  "summary": "Strong candidate with relevant technical skills and appropriate experience level.",
  "strengths": ["Python expertise", "FastAPI experience", "Cloud knowledge"],
  "gaps": ["No Kubernetes experience"],
  "compliance_status": "Compliant - no bias concerns detected",
  "next_steps": ["Schedule technical interview", "Reference check"],
  "reasoning": "Candidate demonstrates 75% skill match with verified 5 years experience..."
}
```

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy"
}
```

**Status Codes:**
| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Invalid PDF or missing file |
| 500 | Server error (LLM failure, missing JD, pipeline error) |

## Available Commands

| Command | Description |
|---------|-------------|
| `uv sync` | Install dependencies |
| `uv sync --all-extras` | Install all dependencies (including dev and UI) |
| `uv lock --upgrade` | Upgrade all dependencies to latest versions |
| `uv run uvicorn resume_screener.main:app --reload` | Start backend server |
| `uv run streamlit run ui/app.py` | Start frontend UI |
| `uv run pytest` | Run all tests |
| `uv run pytest --cov=resume_screener` | Run tests with coverage |
| `uv run ruff check .` | Run linter |
| `uv run ruff check --fix .` | Fix linting issues |
| `uv run ruff format .` | Format code |
| `uv run mypy src/` | Run type checker |

## Testing

### Run All Tests

```bash
uv run pytest
```

### Run with Coverage

```bash
uv run pytest --cov=resume_screener --cov-report=html
```

Open `htmlcov/index.html` in your browser to view the coverage report.

### Run Specific Test Categories

```bash
# Unit tests only
uv run pytest tests/unit/

# Integration tests only
uv run pytest tests/integration/

# Specific test file
uv run pytest tests/unit/test_models.py

# Tests matching a pattern
uv run pytest -k "candidate"
```

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures (settings, mock clients, sample data)
├── unit/
│   ├── test_models.py       # Pydantic model validation tests
│   ├── test_pdf_parser.py   # PDF parsing tests with mocked pypdf
│   └── test_agents.py       # Agent tests with mocked OpenAI responses
└── integration/
    └── test_screening_api.py  # Full API endpoint tests
```

## How It Works

### 1. Resume Upload

User uploads a PDF resume through the Streamlit UI or directly via the API.

### 2. Phase 1: Parallel Extraction

The `ResumeExtractorAgent` and `JDExtractorAgent` run concurrently:

```python
CandidateProfile(
    name="John Doe",
    email="john@example.com",
    skills=["Python", "FastAPI", "Docker"],
    work_experience=5
)

JobRequirements(
    min_work_experience=3,
    max_work_experience=8,
    skills=["Python", "FastAPI", "Docker", "Kubernetes"]
)
```

### 3. Phase 2: Skill Normalization

The `SkillNormalizationAgent` normalizes and matches skills semantically.

### 4. Phase 3: Parallel Verification

- `ExperienceVerificationAgent` verifies work history
- `BiasComplianceAgent` checks for protected attributes

### 5. Phase 4-6: Evaluation, Explanation, Aggregation

```python
FinalRecommendation(
    recommendation="Hire",
    overall_score=78,
    confidence="high",
    strengths=["Python expertise", "Relevant experience"],
    gaps=["No Kubernetes experience"],
    next_steps=["Schedule technical interview"]
)
```

## Customization

### Changing the OpenAI Model

Update your `.env` file:

```env
OPENAI_MODEL=gpt-4-turbo
# or
OPENAI_MODEL=gpt-3.5-turbo  # Faster, cheaper, less accurate
```

### Modifying Evaluation Criteria

Edit the prompts in `src/resume_screener/prompts.py`:

```python
ENHANCED_CANDIDATE_EVALUATION = """
# Modify the scoring formula
# Change recommendation thresholds
# Add custom evaluation criteria
"""
```

### Using a Different Job Description

Option 1: Replace the default file:
```bash
cp your-job-description.pdf resources/job_description.pdf
```

Option 2: Change the config:
```env
JD_FILE_PATH=path/to/your/job_description.pdf
```

## Troubleshooting

### OpenAI API Errors

**Error:** `openai.AuthenticationError`

**Solution:** Verify your API key is correct in `.env`:
```bash
cat .env | grep OPENAI_API_KEY
```

### PDF Parsing Failures

**Error:** `PDFParseError: No text could be extracted`

**Solutions:**
1. Ensure the PDF contains selectable text (not scanned images)
2. Try re-saving the PDF with a different tool
3. For scanned documents, use OCR first

### Connection Refused

**Error:** `Could not connect to API. Is the backend running?`

**Solution:** Start the backend server first:
```bash
uv run uvicorn resume_screener.main:app --reload
```

### Job Description Not Found

**Error:** `JobDescriptionNotFoundError`

**Solution:** Ensure the JD file exists:
```bash
ls -la resources/job_description.pdf
```

### Pipeline Errors

**Error:** `PipelineError in agent_name`

**Solution:** Check the logs for detailed error information:
```bash
LOG_LEVEL=DEBUG uv run uvicorn resume_screener.main:app --reload
```

### Type Check Failures

**Error:** `mypy` reports type errors

**Solution:** Run with the correct Python version:
```bash
uv run mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests and linting:
   ```bash
   uv run pytest
   uv run ruff check .
   uv run mypy src/
   ```
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Code Style

This project uses:
- **ruff** for linting and formatting (configured in `pyproject.toml`)
- **mypy** for strict type checking
- **Conventional Commits** for commit messages

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Built with [FastAPI](https://fastapi.tiangolo.com/), [Streamlit](https://streamlit.io/), and [OpenAI](https://openai.com/)
