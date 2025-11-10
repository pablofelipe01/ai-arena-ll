"""
OpenAI API Client for trading decisions.

Uses OpenAI API for GPT-4o and other models.
"""

from typing import Dict, Any
from decimal import Decimal

from openai import OpenAI

from src.clients.llm_client import BaseLLMClient
from src.utils.logger import app_logger
from src.utils.exceptions import LLMAPIError, LLMTimeoutError


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI API."""

    # OpenAI pricing per 1M tokens
    PRICING = {
        "gpt-4o": {
            "input": Decimal("2.50"),   # $2.50 per 1M input tokens
            "output": Decimal("10.00")  # $10 per 1M output tokens
        },
        "gpt-4-turbo": {
            "input": Decimal("10.00"),
            "output": Decimal("30.00")
        }
    }

    def __init__(
        self,
        llm_id: str,
        model: str,
        api_key: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        timeout: int = 30
    ):
        super().__init__(llm_id, "openai", model, api_key, temperature, max_tokens, timeout)

        self.client = OpenAI(api_key=api_key, timeout=timeout)

    def _make_api_call(self, system_prompt: str, user_prompt: str) -> tuple[str, Dict[str, Any]]:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            response_text = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens

            cost_usd = self.estimate_cost(input_tokens, output_tokens)

            metadata = {
                "tokens": {"prompt": input_tokens, "completion": output_tokens, "total": total_tokens},
                "cost_usd": float(cost_usd),
                "model": self.model,
                "provider": self.provider,
                "finish_reason": response.choices[0].finish_reason
            }

            return response_text, metadata

        except Exception as e:
            app_logger.error(f"{self.llm_id}: OpenAI API error: {e}")
            raise LLMAPIError(self.llm_id, f"OpenAI error: {str(e)}", self.provider)

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> Decimal:
        pricing = self.PRICING.get(self.model, {"input": Decimal("2.50"), "output": Decimal("10.00")})
        return (Decimal(prompt_tokens) / 1_000_000) * pricing["input"] + (Decimal(completion_tokens) / 1_000_000) * pricing["output"]
