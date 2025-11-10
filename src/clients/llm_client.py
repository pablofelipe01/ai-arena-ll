"""
Base class for LLM clients.

Defines the interface that all LLM clients (Claude, DeepSeek, OpenAI) must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from decimal import Decimal
import time

from src.utils.logger import app_logger
from src.utils.exceptions import LLMAPIError, LLMTimeoutError, LLMResponseParseError
from src.clients.prompts import build_trading_prompt, parse_llm_response


class BaseLLMClient(ABC):
    """
    Abstract base class for LLM clients.

    All LLM clients (Claude, DeepSeek, OpenAI) must inherit from this class
    and implement the abstract methods.
    """

    def __init__(
        self,
        llm_id: str,
        provider: str,
        model: str,
        api_key: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        timeout: int = 30
    ):
        """
        Initialize LLM client.

        Args:
            llm_id: ID del LLM ('LLM-A', 'LLM-B', 'LLM-C')
            provider: Provider name ('claude', 'deepseek', 'openai')
            model: Model name
            api_key: API key para el provider
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens en respuesta
            timeout: Request timeout en segundos
        """
        self.llm_id = llm_id
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        app_logger.info(f"Initialized {self.provider} client for {self.llm_id} with model {self.model}")

    @abstractmethod
    def _make_api_call(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> tuple[str, Dict[str, Any]]:
        """
        Make API call to LLM provider.

        This method must be implemented by each specific client.

        Args:
            system_prompt: System instructions
            user_prompt: User message/prompt

        Returns:
            Tuple of (response_text, metadata)
            metadata should include: tokens, cost, model, etc.

        Raises:
            LLMAPIError: If API call fails
            LLMTimeoutError: If API call times out
        """
        pass

    def get_trading_decision(
        self,
        account_info: Dict[str, Any],
        market_data: List[Dict[str, Any]],
        open_positions: List[Dict[str, Any]],
        recent_trades: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get trading decision from LLM.

        Args:
            account_info: Account information
            market_data: Current market data for all symbols
            open_positions: Currently open positions
            recent_trades: Recent trades history

        Returns:
            Dict with parsed decision and metadata:
            {
                "decision": {parsed decision},
                "raw_response": "...",
                "response_time_ms": 1234,
                "tokens": {...},
                "cost_usd": 0.001,
                ...
            }

        Raises:
            LLMAPIError: If API call fails
            LLMResponseParseError: If response cannot be parsed
        """
        start_time = time.time()

        try:
            # Build prompt
            full_prompt = build_trading_prompt(
                llm_id=self.llm_id,
                account_info=account_info,
                market_data=market_data,
                open_positions=open_positions,
                recent_trades=recent_trades
            )

            # Make API call
            app_logger.info(f"{self.llm_id}: Requesting trading decision from {self.provider}")

            response_text, metadata = self._make_api_call(
                system_prompt="",  # System prompt is in the full_prompt for compatibility
                user_prompt=full_prompt
            )

            # Parse response
            try:
                decision = parse_llm_response(response_text)
            except ValueError as e:
                app_logger.error(f"{self.llm_id}: Failed to parse LLM response: {e}")
                raise LLMResponseParseError(
                    llm_id=self.llm_id,
                    provider=self.provider,
                    raw_response=response_text,
                    error=str(e)
                )

            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)

            # Build result
            result = {
                "decision": decision,
                "raw_response": response_text,
                "response_time_ms": response_time_ms,
                **metadata
            }

            app_logger.info(
                f"{self.llm_id}: Decision received - "
                f"Action: {decision['action']}, "
                f"Symbol: {decision.get('symbol', 'N/A')}, "
                f"Confidence: {decision['confidence']}, "
                f"Time: {response_time_ms}ms"
            )

            return result

        except (LLMAPIError, LLMTimeoutError, LLMResponseParseError):
            # Re-raise these specific exceptions
            raise

        except Exception as e:
            # Catch any other unexpected errors
            app_logger.error(f"{self.llm_id}: Unexpected error getting decision: {e}")
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
        Estimate cost of API call.

        Args:
            prompt_tokens: Number of tokens in prompt
            completion_tokens: Number of tokens in completion

        Returns:
            Estimated cost in USD

        Note:
            This is a rough estimate. Actual costs may vary.
            Subclasses should override with provider-specific pricing.
        """
        # Default pricing (very rough estimates)
        # These should be overridden by specific clients
        cost_per_1k_prompt = Decimal("0.003")  # $0.003 per 1K prompt tokens
        cost_per_1k_completion = Decimal("0.015")  # $0.015 per 1K completion tokens

        prompt_cost = (Decimal(prompt_tokens) / 1000) * cost_per_1k_prompt
        completion_cost = (Decimal(completion_tokens) / 1000) * cost_per_1k_completion

        total_cost = prompt_cost + completion_cost

        return total_cost

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<{self.__class__.__name__} "
            f"llm_id={self.llm_id} "
            f"provider={self.provider} "
            f"model={self.model}>"
        )
