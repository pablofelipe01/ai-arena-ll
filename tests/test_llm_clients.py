"""
Tests for LLM clients (Claude, DeepSeek, OpenAI).

Tests cover:
- Prompt building and parsing
- All three LLM clients
- Response parsing and validation
- Error handling
- Cost estimation
"""

import json
import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

from src.clients.llm_client import BaseLLMClient
from src.clients.claude_client import ClaudeClient
from src.clients.deepseek_client import DeepSeekClient
from src.clients.openai_client import OpenAIClient
from src.clients.prompts import (
    build_trading_prompt,
    parse_llm_response,
    validate_decision,
    PERSONALITIES,
    ALLOWED_SYMBOLS
)
from src.utils.exceptions import LLMAPIError, LLMTimeoutError, LLMResponseParseError


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_account_info():
    """Sample account information."""
    return {
        "llm_id": "LLM-A",
        "balance_usdt": Decimal("95.50"),
        "equity_usdt": Decimal("100.00"),
        "unrealized_pnl": Decimal("4.50"),
        "available_balance": Decimal("70.00"),
        "total_margin_used": Decimal("25.00")
    }


@pytest.fixture
def sample_market_data():
    """Sample market data for multiple symbols."""
    return [
        {
            "symbol": "ETHUSDT",
            "price": Decimal("3500.00"),
            "price_change_pct_24h": Decimal("2.5"),
            "volume_24h": Decimal("1000000000"),
            "high_24h": Decimal("3550.00"),
            "low_24h": Decimal("3400.00")
        },
        {
            "symbol": "BNBUSDT",
            "price": Decimal("450.00"),
            "price_change_pct_24h": Decimal("-1.2"),
            "volume_24h": Decimal("500000000"),
            "high_24h": Decimal("460.00"),
            "low_24h": Decimal("445.00")
        }
    ]


@pytest.fixture
def sample_open_positions():
    """Sample open positions."""
    return [
        {
            "symbol": "ETHUSDT",
            "side": "LONG",
            "entry_price": Decimal("3400.00"),
            "current_price": Decimal("3500.00"),
            "quantity": Decimal("0.01"),
            "leverage": 3,
            "unrealized_pnl": Decimal("3.00"),
            "margin_used": Decimal("11.33")
        }
    ]


@pytest.fixture
def sample_recent_trades():
    """Sample recent trades history."""
    return [
        {
            "symbol": "ETHUSDT",
            "side": "BUY",
            "entry_price": Decimal("3400.00"),
            "exit_price": Decimal("3450.00"),
            "quantity": Decimal("0.01"),
            "pnl_usdt": Decimal("0.50"),
            "pnl_pct": Decimal("1.47"),
            "closed_at": "2025-01-10 10:00:00"
        }
    ]


@pytest.fixture
def sample_valid_decision():
    """Sample valid trading decision."""
    return {
        "action": "BUY",
        "symbol": "ETHUSDT",
        "quantity_usd": 20.0,
        "leverage": 3,
        "stop_loss_pct": 5.0,
        "take_profit_pct": 10.0,
        "reasoning": "ETH showing strong momentum",
        "confidence": 0.8,
        "strategy": "momentum"
    }


# ============================================================================
# Tests for prompts.py
# ============================================================================

class TestPrompts:
    """Tests for prompt building and parsing functions."""

    def test_build_trading_prompt_structure(
        self,
        sample_account_info,
        sample_market_data,
        sample_open_positions,
        sample_recent_trades
    ):
        """Test that build_trading_prompt returns a well-structured prompt."""
        prompt = build_trading_prompt(
            llm_id="LLM-A",
            account_info=sample_account_info,
            market_data=sample_market_data,
            open_positions=sample_open_positions,
            recent_trades=sample_recent_trades
        )

        # Check prompt contains expected sections
        assert "CURRENT MARKET DATA" in prompt
        assert "YOUR ACCOUNT STATUS" in prompt
        assert "OPEN POSITIONS" in prompt
        assert "RECENT TRADES" in prompt
        assert "RESPONSE FORMAT" in prompt
        assert "MAKE YOUR DECISION" in prompt

        # Check personality is included
        assert PERSONALITIES["LLM-A"] in prompt

        # Check account data is included
        assert "LLM-A" in prompt  # LLM ID
        assert "70.00" in prompt  # available balance

        # Check market data is included
        assert "ETHUSDT" in prompt
        assert "3500.00" in prompt
        assert "BNBUSDT" in prompt
        assert "450.00" in prompt

    def test_build_trading_prompt_different_personalities(self, sample_account_info, sample_market_data, sample_open_positions, sample_recent_trades):
        """Test that different LLM IDs get different personalities."""
        prompt_a = build_trading_prompt("LLM-A", sample_account_info, sample_market_data, sample_open_positions, sample_recent_trades)
        prompt_b = build_trading_prompt("LLM-B", sample_account_info, sample_market_data, sample_open_positions, sample_recent_trades)
        prompt_c = build_trading_prompt("LLM-C", sample_account_info, sample_market_data, sample_open_positions, sample_recent_trades)

        assert "CONSERVATIVE" in prompt_a
        assert "BALANCED" in prompt_b
        assert "AGGRESSIVE" in prompt_c

        # Verify different strategies
        assert "1x-3x" in prompt_a  # Low leverage for conservative
        assert "3x-7x" in prompt_b  # Medium leverage for balanced
        assert "7x-10x" in prompt_c  # High leverage for aggressive

    def test_parse_llm_response_valid_json(self, sample_valid_decision):
        """Test parsing a valid JSON response."""
        response_text = json.dumps(sample_valid_decision)

        decision = parse_llm_response(response_text)

        assert decision["action"] == "BUY"
        assert decision["symbol"] == "ETHUSDT"
        assert decision["quantity_usd"] == 20.0
        assert decision["leverage"] == 3
        assert decision["confidence"] == 0.8

    def test_parse_llm_response_with_markdown(self, sample_valid_decision):
        """Test parsing JSON wrapped in markdown code blocks."""
        response_text = f"""Here's my trading decision:

```json
{json.dumps(sample_valid_decision)}
```

This is my reasoning.
"""

        decision = parse_llm_response(response_text)

        assert decision["action"] == "BUY"
        assert decision["symbol"] == "ETHUSDT"

    def test_parse_llm_response_with_markdown_no_json_tag(self, sample_valid_decision):
        """Test parsing JSON wrapped in markdown without 'json' tag."""
        response_text = f"""```
{json.dumps(sample_valid_decision)}
```"""

        decision = parse_llm_response(response_text)

        assert decision["action"] == "BUY"

    def test_parse_llm_response_missing_required_field(self):
        """Test parsing fails when required fields are missing."""
        invalid_decision = {
            "action": "BUY",
            # Missing symbol
            "quantity_usd": 20.0
        }
        response_text = json.dumps(invalid_decision)

        with pytest.raises(ValueError, match="Missing required field"):
            parse_llm_response(response_text)

    def test_parse_llm_response_invalid_json(self):
        """Test parsing fails with invalid JSON."""
        response_text = "This is not valid JSON at all"

        with pytest.raises(ValueError, match="No JSON object found"):
            parse_llm_response(response_text)

    def test_validate_decision_valid(self, sample_valid_decision):
        """Test validating a valid decision."""
        is_valid, error = validate_decision(
            decision=sample_valid_decision,
            available_balance=Decimal("70.00"),
            max_positions=3,
            current_positions=1,
            allowed_symbols=ALLOWED_SYMBOLS
        )

        assert is_valid is True
        assert error == ""

    def test_validate_decision_invalid_symbol(self, sample_valid_decision):
        """Test validation fails for invalid symbol."""
        sample_valid_decision["symbol"] = "INVALID"

        is_valid, error = validate_decision(
            decision=sample_valid_decision,
            available_balance=Decimal("70.00"),
            max_positions=3,
            current_positions=1,
            allowed_symbols=ALLOWED_SYMBOLS
        )

        assert is_valid is False
        assert "not allowed" in error

    def test_validate_decision_max_positions_reached(self, sample_valid_decision):
        """Test validation fails when max positions reached."""
        is_valid, error = validate_decision(
            decision=sample_valid_decision,
            available_balance=Decimal("70.00"),
            max_positions=3,
            current_positions=3,  # Already at max
            allowed_symbols=ALLOWED_SYMBOLS
        )

        assert is_valid is False
        assert "Maximum positions" in error

    def test_validate_decision_insufficient_balance(self, sample_valid_decision):
        """Test validation fails with insufficient balance."""
        # sample_valid_decision has quantity_usd=20.0, leverage=3
        # Required margin = 20.0 / 3 = 6.67
        # So we need balance < 6.67 to fail
        is_valid, error = validate_decision(
            decision=sample_valid_decision,
            available_balance=Decimal("5.00"),  # Not enough (need 6.67)
            max_positions=3,
            current_positions=0,
            allowed_symbols=ALLOWED_SYMBOLS
        )

        assert is_valid is False
        assert "Insufficient balance" in error

    def test_validate_decision_hold_action(self):
        """Test HOLD action is always valid."""
        hold_decision = {
            "action": "HOLD",
            "symbol": None,
            "quantity_usd": 0,
            "leverage": 1,
            "stop_loss_pct": 0,
            "take_profit_pct": 0,
            "reasoning": "Waiting for better opportunities",
            "confidence": 0.9,
            "strategy": "wait"
        }

        is_valid, error = validate_decision(
            decision=hold_decision,
            available_balance=Decimal("0.00"),  # Even with no balance
            max_positions=3,
            current_positions=3,  # Even at max positions
            allowed_symbols=ALLOWED_SYMBOLS
        )

        assert is_valid is True


# ============================================================================
# Tests for ClaudeClient
# ============================================================================

class TestClaudeClient:
    """Tests for Claude (Anthropic) API client."""

    def test_initialization(self):
        """Test Claude client initialization."""
        client = ClaudeClient(
            llm_id="LLM-A",
            model="claude-sonnet-4-20250514",
            api_key="test-key",
            temperature=0.5,
            max_tokens=1000,
            timeout=30
        )

        assert client.llm_id == "LLM-A"
        assert client.provider == "claude"
        assert client.model == "claude-sonnet-4-20250514"
        assert client.temperature == 0.5
        assert client.max_tokens == 1000
        assert client.timeout == 30

    def test_estimate_cost(self):
        """Test cost estimation for Claude API."""
        client = ClaudeClient(
            llm_id="LLM-A",
            model="claude-sonnet-4-20250514",
            api_key="test-key"
        )

        # Test with 10,000 input tokens and 5,000 output tokens
        cost = client.estimate_cost(10000, 5000)

        # Expected: (10000/1000000)*3.00 + (5000/1000000)*15.00
        # = 0.03 + 0.075 = 0.105
        expected_cost = Decimal("0.105")
        assert cost == expected_cost

    @patch('anthropic.Anthropic')
    def test_make_api_call_success(self, mock_anthropic_class):
        """Test successful API call to Claude."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"action": "HOLD"}')]
        mock_response.usage = MagicMock(
            input_tokens=1000,
            output_tokens=500
        )
        mock_response.stop_reason = "end_turn"

        mock_client.messages.create.return_value = mock_response

        # Create client and make call
        client = ClaudeClient(
            llm_id="LLM-A",
            model="claude-sonnet-4-20250514",
            api_key="test-key"
        )

        response_text, metadata = client._make_api_call("system", "user prompt")

        # Verify response
        assert response_text == '{"action": "HOLD"}'
        assert metadata["tokens"]["prompt"] == 1000
        assert metadata["tokens"]["completion"] == 500
        assert metadata["model"] == "claude-sonnet-4-20250514"
        assert metadata["provider"] == "claude"
        assert "cost_usd" in metadata

    @patch('anthropic.Anthropic')
    def test_make_api_call_timeout(self, mock_anthropic_class):
        """Test API timeout error."""
        import anthropic

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Simulate timeout
        mock_client.messages.create.side_effect = anthropic.APITimeoutError(request=MagicMock())

        client = ClaudeClient(
            llm_id="LLM-A",
            model="claude-sonnet-4-20250514",
            api_key="test-key"
        )

        with pytest.raises(LLMTimeoutError):
            client._make_api_call("system", "user prompt")

    @patch('anthropic.Anthropic')
    def test_make_api_call_rate_limit(self, mock_anthropic_class):
        """Test rate limit error."""
        import anthropic

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Simulate rate limit
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_client.messages.create.side_effect = anthropic.RateLimitError(
            "Rate limit exceeded",
            response=mock_response,
            body=None
        )

        client = ClaudeClient(
            llm_id="LLM-A",
            model="claude-sonnet-4-20250514",
            api_key="test-key"
        )

        with pytest.raises(LLMAPIError, match="Rate limit"):
            client._make_api_call("system", "user prompt")


# ============================================================================
# Tests for DeepSeekClient
# ============================================================================

class TestDeepSeekClient:
    """Tests for DeepSeek API client."""

    def test_initialization(self):
        """Test DeepSeek client initialization."""
        client = DeepSeekClient(
            llm_id="LLM-B",
            model="deepseek-chat",
            api_key="test-key",
            temperature=0.7,
            max_tokens=1000,
            timeout=30
        )

        assert client.llm_id == "LLM-B"
        assert client.provider == "deepseek"
        assert client.model == "deepseek-chat"
        assert client.temperature == 0.7

    def test_estimate_cost(self):
        """Test cost estimation for DeepSeek API."""
        client = DeepSeekClient(
            llm_id="LLM-B",
            model="deepseek-chat",
            api_key="test-key"
        )

        # Test with 10,000 input tokens and 5,000 output tokens
        cost = client.estimate_cost(10000, 5000)

        # Expected: (10000/1000000)*0.14 + (5000/1000000)*0.28
        # = 0.0014 + 0.0014 = 0.0028
        expected_cost = Decimal("0.0028")
        assert cost == expected_cost

    @patch('src.clients.deepseek_client.OpenAI')
    def test_make_api_call_success(self, mock_openai_class):
        """Test successful API call to DeepSeek."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(
            message=MagicMock(content='{"action": "BUY"}'),
            finish_reason="stop"
        )]
        mock_response.usage = MagicMock(
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500
        )

        mock_client.chat.completions.create.return_value = mock_response

        # Create client and make call
        client = DeepSeekClient(
            llm_id="LLM-B",
            model="deepseek-chat",
            api_key="test-key"
        )

        response_text, metadata = client._make_api_call("system", "user prompt")

        # Verify response
        assert response_text == '{"action": "BUY"}'
        assert metadata["tokens"]["prompt"] == 1000
        assert metadata["tokens"]["completion"] == 500
        assert metadata["model"] == "deepseek-chat"
        assert metadata["provider"] == "deepseek"

    @patch('src.clients.deepseek_client.OpenAI')
    def test_make_api_call_error(self, mock_openai_class):
        """Test API error handling."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Simulate error
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        client = DeepSeekClient(
            llm_id="LLM-B",
            model="deepseek-chat",
            api_key="test-key"
        )

        with pytest.raises(LLMAPIError, match="DeepSeek error"):
            client._make_api_call("system", "user prompt")


# ============================================================================
# Tests for OpenAIClient
# ============================================================================

class TestOpenAIClient:
    """Tests for OpenAI API client."""

    def test_initialization(self):
        """Test OpenAI client initialization."""
        client = OpenAIClient(
            llm_id="LLM-C",
            model="gpt-4o",
            api_key="test-key",
            temperature=0.9,
            max_tokens=1000,
            timeout=30
        )

        assert client.llm_id == "LLM-C"
        assert client.provider == "openai"
        assert client.model == "gpt-4o"
        assert client.temperature == 0.9

    def test_estimate_cost(self):
        """Test cost estimation for OpenAI API."""
        client = OpenAIClient(
            llm_id="LLM-C",
            model="gpt-4o",
            api_key="test-key"
        )

        # Test with 10,000 input tokens and 5,000 output tokens
        cost = client.estimate_cost(10000, 5000)

        # Expected: (10000/1000000)*2.50 + (5000/1000000)*10.00
        # = 0.025 + 0.05 = 0.075
        expected_cost = Decimal("0.075")
        assert cost == expected_cost

    @patch('src.clients.openai_client.OpenAI')
    def test_make_api_call_success(self, mock_openai_class):
        """Test successful API call to OpenAI."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(
            message=MagicMock(content='{"action": "SELL"}'),
            finish_reason="stop"
        )]
        mock_response.usage = MagicMock(
            prompt_tokens=1200,
            completion_tokens=600,
            total_tokens=1800
        )

        mock_client.chat.completions.create.return_value = mock_response

        # Create client and make call
        client = OpenAIClient(
            llm_id="LLM-C",
            model="gpt-4o",
            api_key="test-key"
        )

        response_text, metadata = client._make_api_call("system", "user prompt")

        # Verify response
        assert response_text == '{"action": "SELL"}'
        assert metadata["tokens"]["prompt"] == 1200
        assert metadata["tokens"]["completion"] == 600
        assert metadata["model"] == "gpt-4o"
        assert metadata["provider"] == "openai"

    @patch('src.clients.openai_client.OpenAI')
    def test_make_api_call_error(self, mock_openai_class):
        """Test API error handling."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Simulate error
        mock_client.chat.completions.create.side_effect = Exception("OpenAI API Error")

        client = OpenAIClient(
            llm_id="LLM-C",
            model="gpt-4o",
            api_key="test-key"
        )

        with pytest.raises(LLMAPIError, match="OpenAI error"):
            client._make_api_call("system", "user prompt")


# ============================================================================
# Integration Tests for get_trading_decision
# ============================================================================

class TestGetTradingDecision:
    """Integration tests for get_trading_decision method."""

    @patch('anthropic.Anthropic')
    def test_get_trading_decision_success(
        self,
        mock_anthropic_class,
        sample_account_info,
        sample_market_data,
        sample_open_positions,
        sample_recent_trades,
        sample_valid_decision
    ):
        """Test complete flow of getting a trading decision."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Return valid JSON response
        response_json = json.dumps(sample_valid_decision)
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=response_json)]
        mock_response.usage = MagicMock(
            input_tokens=2000,
            output_tokens=200
        )
        mock_response.stop_reason = "end_turn"

        mock_client.messages.create.return_value = mock_response

        # Create client
        client = ClaudeClient(
            llm_id="LLM-A",
            model="claude-sonnet-4-20250514",
            api_key="test-key"
        )

        # Get decision
        result = client.get_trading_decision(
            account_info=sample_account_info,
            market_data=sample_market_data,
            open_positions=sample_open_positions,
            recent_trades=sample_recent_trades
        )

        # Verify result structure
        assert "decision" in result
        assert "raw_response" in result
        assert "response_time_ms" in result
        assert "tokens" in result
        assert "cost_usd" in result

        # Verify decision
        assert result["decision"]["action"] == "BUY"
        assert result["decision"]["symbol"] == "ETHUSDT"
        assert result["decision"]["confidence"] == 0.8

    @patch('anthropic.Anthropic')
    def test_get_trading_decision_parse_error(
        self,
        mock_anthropic_class,
        sample_account_info,
        sample_market_data,
        sample_open_positions,
        sample_recent_trades
    ):
        """Test handling of unparseable LLM response."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Return invalid response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="This is not valid JSON")]
        mock_response.usage = MagicMock(
            input_tokens=2000,
            output_tokens=200
        )
        mock_response.stop_reason = "end_turn"

        mock_client.messages.create.return_value = mock_response

        # Create client
        client = ClaudeClient(
            llm_id="LLM-A",
            model="claude-sonnet-4-20250514",
            api_key="test-key"
        )

        # Should raise LLMResponseParseError
        with pytest.raises(LLMResponseParseError):
            client.get_trading_decision(
                account_info=sample_account_info,
                market_data=sample_market_data,
                open_positions=sample_open_positions,
                recent_trades=sample_recent_trades
            )


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
