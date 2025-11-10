"""
Claude (Anthropic) API Client for trading decisions.

Uses the Anthropic API to get trading decisions from Claude models.
"""

from typing import Dict, Any
from decimal import Decimal

import anthropic

from src.clients.llm_client import BaseLLMClient
from src.utils.logger import app_logger
from src.utils.exceptions import LLMAPIError, LLMTimeoutError


class ClaudeClient(BaseLLMClient):
    """
    Client for Claude (Anthropic) API.

    Supports Claude Sonnet 4 and other Claude models.
    """

    # Pricing per 1M tokens (as of Jan 2025)
    PRICING = {
        "claude-sonnet-4-20250514": {
            "input": Decimal("3.00"),   # $3 per 1M input tokens
            "output": Decimal("15.00")  # $15 per 1M output tokens
        },
        "claude-3-5-sonnet-20241022": {
            "input": Decimal("3.00"),
            "output": Decimal("15.00")
        },
        "claude-3-opus-20240229": {
            "input": Decimal("15.00"),
            "output": Decimal("75.00")
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
        """
        Initialize Claude client.

        Args:
            llm_id: ID del LLM ('LLM-A', 'LLM-B', 'LLM-C')
            model: Claude model name (e.g., 'claude-sonnet-4-20250514')
            api_key: Anthropic API key
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
        """
        super().__init__(
            llm_id=llm_id,
            provider="claude",
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )

        # Initialize Anthropic client
        self.client = anthropic.Anthropic(
            api_key=api_key,
            timeout=timeout
        )

    def _make_api_call(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> tuple[str, Dict[str, Any]]:
        """
        Make API call to Claude.

        Args:
            system_prompt: System instructions (not used, included in user_prompt)
            user_prompt: User message/prompt

        Returns:
            Tuple of (response_text, metadata)

        Raises:
            LLMAPIError: If API call fails
            LLMTimeoutError: If API call times out
        """
        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            # Extract response text
            response_text = response.content[0].text

            # Extract token usage
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens = input_tokens + output_tokens

            # Calculate cost
            cost_usd = self.estimate_cost(input_tokens, output_tokens)

            # Build metadata
            metadata = {
                "tokens": {
                    "prompt": input_tokens,
                    "completion": output_tokens,
                    "total": total_tokens
                },
                "cost_usd": float(cost_usd),
                "model": self.model,
                "provider": self.provider,
                "stop_reason": response.stop_reason
            }

            return response_text, metadata

        except anthropic.APITimeoutError as e:
            app_logger.error(f"{self.llm_id}: Claude API timeout: {e}")
            raise LLMTimeoutError(
                llm_id=self.llm_id,
                provider=self.provider,
                timeout_seconds=self.timeout
            )

        except anthropic.APIConnectionError as e:
            app_logger.error(f"{self.llm_id}: Claude API connection error: {e}")
            raise LLMAPIError(
                llm_id=self.llm_id,
                message=f"Connection error: {str(e)}",
                provider=self.provider
            )

        except anthropic.RateLimitError as e:
            app_logger.error(f"{self.llm_id}: Claude API rate limit: {e}")
            raise LLMAPIError(
                llm_id=self.llm_id,
                message="Rate limit exceeded",
                provider=self.provider
            )

        except anthropic.APIStatusError as e:
            app_logger.error(f"{self.llm_id}: Claude API error: {e.status_code} - {e.message}")
            raise LLMAPIError(
                llm_id=self.llm_id,
                message=f"API error: {e.message}",
                provider=self.provider
            )

        except Exception as e:
            app_logger.error(f"{self.llm_id}: Unexpected Claude error: {e}")
            raise LLMAPIError(
                llm_id=self.llm_id,
                message=f"Unexpected error: {str(e)}",
                provider=self.provider
            )

    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int
    ) -> Decimal:
        """
        Estimate cost of API call using Claude pricing.

        Args:
            prompt_tokens: Number of tokens in prompt
            completion_tokens: Number of tokens in completion

        Returns:
            Estimated cost in USD
        """
        # Get pricing for this model
        pricing = self.PRICING.get(self.model, {
            "input": Decimal("3.00"),
            "output": Decimal("15.00")
        })

        # Calculate cost (pricing is per 1M tokens)
        input_cost = (Decimal(prompt_tokens) / 1_000_000) * pricing["input"]
        output_cost = (Decimal(completion_tokens) / 1_000_000) * pricing["output"]

        total_cost = input_cost + output_cost

        return total_cost
