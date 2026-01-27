"""Bias compliance checking agent."""

import structlog

from resume_screener.agents.base import BaseAgent
from resume_screener.models.compliance import BiasComplianceResult
from resume_screener.prompts import CHECK_BIAS_COMPLIANCE

logger = structlog.get_logger()


class BiasComplianceAgent(BaseAgent):
    """Agent that checks resume for protected attributes and bias compliance."""

    async def execute(
        self,
        resume_text: str,
        is_location_required: bool = False,
    ) -> BiasComplianceResult:
        """Check resume for protected attributes and compliance issues."""
        logger.info("checking_bias_compliance", location_required=is_location_required)

        prompt = CHECK_BIAS_COMPLIANCE.format(
            resume_text=resume_text,
            is_location_required=str(is_location_required).lower(),
        )

        response = await self._call_llm(prompt)
        result = self._parse_json_response(response, BiasComplianceResult)

        logger.info(
            "bias_compliance_complete",
            is_compliant=result.is_compliant,
            risk_level=result.risk_level,
            flag_count=len(result.flags),
        )

        return result
