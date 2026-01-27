"""Base agent with shared OpenAI client."""

import json
from typing import TypeVar

import structlog
from openai import AsyncOpenAI
from pydantic import BaseModel

from resume_screener.config import Settings
from resume_screener.exceptions import LLMResponseError

logger = structlog.get_logger()

T = TypeVar("T", bound=BaseModel)


class BaseAgent:
    """Base class for LLM agents with shared OpenAI client.

    Provides common functionality for making OpenAI API calls and parsing JSON responses.
    Subclasses should implement their own `execute` method with appropriate signatures.
    """

    def __init__(self, client: AsyncOpenAI, settings: Settings) -> None:
        self.client = client
        self.settings = settings

    async def _call_llm(self, prompt: str) -> str:
        """Make an async call to the OpenAI API."""
        logger.debug("calling_llm", agent=self.__class__.__name__)

        response = await self.client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.choices[0].message.content
        if content is None:
            raise LLMResponseError("LLM returned empty response")

        logger.debug("llm_response_received", agent=self.__class__.__name__)
        return content

    def _parse_json_response(self, response: str, model_class: type[T]) -> T:
        """Parse JSON response and validate against Pydantic model."""
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
            return model_class.model_validate(data)
        except json.JSONDecodeError as e:
            raise LLMResponseError(f"Failed to parse JSON response: {e}") from e
        except Exception as e:
            raise LLMResponseError(f"Failed to validate response: {e}") from e
