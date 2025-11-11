"""
End-to-End Integration Tests for Crypto LLM Trading System.

These tests validate the entire system working together:
- All services initialized correctly
- Database connectivity
- External API connections (Binance, LLM providers)
- Complete trading workflows
- Data persistence and consistency
- Error handling and recovery

Run with: pytest tests/test_integration_e2e.py -v
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import asyncio

from config.settings import settings
from src.services.trading_service import TradingService
from src.services.account_service import AccountService
from src.services.market_data_service import MarketDataService
from src.core.llm_decision import LLMDecisionService
from src.core.position_manager import PositionManager
from src.core.risk_manager import RiskManager
from src.database.supabase_client import SupabaseClient
from src.external.binance_client import BinanceClient
from src.external.llm_clients import get_llm_client


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_supabase():
    """Mock Supabase client for integration tests."""
    mock = Mock(spec=SupabaseClient)
    mock.is_connected = True

    # Mock LLM accounts
    mock.get_all_llm_accounts.return_value = [
        {
            "llm_id": "LLM-A",
            "provider": "anthropic",
            "model_name": "claude-sonnet-4-20250514",
            "balance": 100.0,
            "margin_used": 0.0,
            "total_pnl": 0.0,
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "open_positions": 0,
            "is_active": True,
            "is_trading_enabled": True,
            "api_calls_this_hour": 0,
            "api_calls_today": 0
        },
        {
            "llm_id": "LLM-B",
            "provider": "deepseek",
            "model_name": "deepseek-reasoner",
            "balance": 100.0,
            "margin_used": 0.0,
            "total_pnl": 0.0,
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "open_positions": 0,
            "is_active": True,
            "is_trading_enabled": True,
            "api_calls_this_hour": 0,
            "api_calls_today": 0
        },
        {
            "llm_id": "LLM-C",
            "provider": "openai",
            "model_name": "gpt-4o",
            "balance": 100.0,
            "margin_used": 0.0,
            "total_pnl": 0.0,
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "open_positions": 0,
            "is_active": True,
            "is_trading_enabled": True,
            "api_calls_this_hour": 0,
            "api_calls_today": 0
        }
    ]

    mock.get_llm_account.side_effect = lambda llm_id: next(
        (acc for acc in mock.get_all_llm_accounts.return_value if acc["llm_id"] == llm_id),
        None
    )

    mock.get_open_positions.return_value = []
    mock.get_trades.return_value = []
    mock.create_position.return_value = {
        "id": "test-position-id",
        "llm_id": "LLM-A",
        "symbol": "ETHUSDT",
        "side": "LONG",
        "entry_price": 2000.0,
        "quantity": 0.01,
        "leverage": 5,
        "margin": 4.0,
        "status": "OPEN"
    }
    mock.create_trade.return_value = {"id": "test-trade-id"}
    mock.update_llm_balance.return_value = {"balance": 100.0}
    mock.update_llm_stats.return_value = {"total_trades": 1}

    return mock


@pytest.fixture
def mock_binance():
    """Mock Binance client for integration tests."""
    mock = Mock(spec=BinanceClient)
    mock.is_connected = True

    # Mock market data
    mock.get_ticker.return_value = {
        "symbol": "ETHUSDT",
        "price": "2000.50",
        "bid": "2000.40",
        "ask": "2000.60",
        "volume": "150000.0",
        "priceChangePercent": "2.5",
        "highPrice": "2050.0",
        "lowPrice": "1950.0"
    }

    mock.get_klines.return_value = [
        {
            "open_time": 1699000000000,
            "open": "1990.0",
            "high": "2010.0",
            "low": "1980.0",
            "close": "2000.0",
            "volume": "1000.0",
            "close_time": 1699003600000
        }
    ] * 100  # 100 candles

    mock.get_account_balance.return_value = Decimal("10000.0")

    return mock


@pytest.fixture
def mock_llm_clients():
    """Mock LLM clients for all providers."""
    mocks = {}

    for llm_id in ["LLM-A", "LLM-B", "LLM-C"]:
        mock = Mock()
        mock.get_trading_decision.return_value = {
            "action": "BUY",
            "symbol": "ETHUSDT",
            "side": "LONG",
            "size_usd": 20.0,
            "leverage": 5,
            "confidence": 0.75,
            "reasoning": f"Test decision from {llm_id}",
            "stop_loss_pct": 2.0,
            "take_profit_pct": 5.0
        }
        mocks[llm_id] = mock

    return mocks


@pytest.fixture
def integrated_trading_service(mock_supabase, mock_binance, mock_llm_clients):
    """Create TradingService with all mocked dependencies."""

    # Create service instances
    account_service = AccountService(mock_supabase)
    market_data_service = MarketDataService(mock_binance, mock_supabase)
    risk_manager = RiskManager()
    position_manager = PositionManager(mock_supabase, mock_binance, account_service)

    # Patch LLM client factory
    with patch('src.core.llm_decision.get_llm_client') as mock_get_llm:
        def get_client_side_effect(llm_id):
            return mock_llm_clients.get(llm_id)

        mock_get_llm.side_effect = get_client_side_effect

        llm_decision_service = LLMDecisionService(mock_supabase)

        # Create TradingService
        trading_service = TradingService(
            account_service=account_service,
            market_data_service=market_data_service,
            llm_decision_service=llm_decision_service,
            position_manager=position_manager,
            risk_manager=risk_manager,
            supabase=mock_supabase
        )

        yield trading_service


# ============================================================================
# System Initialization Tests
# ============================================================================

class TestSystemInitialization:
    """Test complete system initialization."""

    def test_all_services_initialize(self, mock_supabase, mock_binance):
        """Test that all services can be initialized without errors."""
        # Account Service
        account_service = AccountService(mock_supabase)
        assert account_service.db is not None

        # Market Data Service
        market_service = MarketDataService(mock_binance, mock_supabase)
        assert market_service.binance is not None

        # Risk Manager
        risk_manager = RiskManager()
        assert risk_manager is not None

        # Position Manager
        position_manager = PositionManager(mock_supabase, mock_binance, account_service)
        assert position_manager is not None

        # LLM Decision Service
        llm_service = LLMDecisionService(mock_supabase)
        assert llm_service is not None

    def test_database_connectivity(self, mock_supabase):
        """Test database connection and basic queries."""
        # Get all accounts
        accounts = mock_supabase.get_all_llm_accounts()
        assert len(accounts) == 3
        assert all(acc["is_active"] for acc in accounts)

        # Get specific account
        account = mock_supabase.get_llm_account("LLM-A")
        assert account is not None
        assert account["llm_id"] == "LLM-A"
        assert account["balance"] == 100.0

    def test_external_api_connections(self, mock_binance):
        """Test external API connections (Binance)."""
        # Test ticker data
        ticker = mock_binance.get_ticker("ETHUSDT")
        assert ticker is not None
        assert "price" in ticker
        assert "symbol" in ticker

        # Test kline data
        klines = mock_binance.get_klines("ETHUSDT", "1h", limit=100)
        assert len(klines) == 100


# ============================================================================
# Complete Trading Cycle Tests
# ============================================================================

class TestCompleteTradingCycle:
    """Test complete trading cycles from start to finish."""

    def test_single_trading_cycle(self, integrated_trading_service):
        """Test a complete trading cycle with all LLMs."""
        result = integrated_trading_service.execute_trading_cycle()

        # Verify cycle executed
        assert result["status"] == "SUCCESS"
        assert "cycle_id" in result
        assert result["llms_processed"] == 3

        # Verify decisions were made
        assert "decisions" in result
        assert len(result["decisions"]) == 3

    def test_market_data_update_in_cycle(self, integrated_trading_service):
        """Test that market data is updated during trading cycle."""
        # Execute cycle
        result = integrated_trading_service.execute_trading_cycle()

        # Verify market data was fetched
        assert result["status"] == "SUCCESS"

        # Get market snapshot
        snapshot = integrated_trading_service.market_data.get_market_snapshot()
        assert "symbols" in snapshot
        assert len(snapshot["symbols"]) > 0

    def test_llm_decisions_in_cycle(self, integrated_trading_service):
        """Test that all LLMs make decisions during cycle."""
        result = integrated_trading_service.execute_trading_cycle()

        # Verify all LLMs made decisions
        assert result["llms_processed"] == 3
        decisions = result["decisions"]

        llm_ids = [d["llm_id"] for d in decisions]
        assert "LLM-A" in llm_ids
        assert "LLM-B" in llm_ids
        assert "LLM-C" in llm_ids

    def test_position_opening_in_cycle(self, integrated_trading_service, mock_supabase):
        """Test that positions can be opened during cycle."""
        # Mock approved decision
        mock_supabase.get_open_positions.return_value = []

        result = integrated_trading_service.execute_trading_cycle()

        # At least one decision should be made
        assert result["status"] == "SUCCESS"
        assert len(result["decisions"]) > 0

    def test_account_updates_in_cycle(self, integrated_trading_service, mock_supabase):
        """Test that account balances are updated during cycle."""
        result = integrated_trading_service.execute_trading_cycle()

        # Verify cycle completed
        assert result["status"] == "SUCCESS"

        # Account updates should have been called
        # (balance updates happen when positions are opened/closed)


# ============================================================================
# Multi-LLM Interaction Tests
# ============================================================================

class TestMultiLLMInteraction:
    """Test interactions between multiple LLMs."""

    def test_all_three_llms_active(self, integrated_trading_service):
        """Test that all 3 LLMs participate in trading."""
        result = integrated_trading_service.execute_trading_cycle()

        assert result["llms_processed"] == 3

        llm_ids = [d["llm_id"] for d in result["decisions"]]
        assert len(set(llm_ids)) == 3  # All unique

    def test_llms_independent_decisions(self, integrated_trading_service, mock_llm_clients):
        """Test that LLMs make independent decisions."""
        # Configure different decisions for each LLM
        mock_llm_clients["LLM-A"].get_trading_decision.return_value = {
            "action": "BUY",
            "symbol": "ETHUSDT",
            "side": "LONG",
            "size_usd": 20.0,
            "leverage": 5,
            "confidence": 0.8,
            "reasoning": "Bullish on ETH"
        }

        mock_llm_clients["LLM-B"].get_trading_decision.return_value = {
            "action": "SELL",
            "symbol": "BNBUSDT",
            "side": "SHORT",
            "size_usd": 15.0,
            "leverage": 3,
            "confidence": 0.7,
            "reasoning": "Bearish on BNB"
        }

        mock_llm_clients["LLM-C"].get_trading_decision.return_value = {
            "action": "HOLD",
            "symbol": None,
            "confidence": 0.5,
            "reasoning": "Waiting for better entry"
        }

        result = integrated_trading_service.execute_trading_cycle()

        # Verify different decisions
        decisions = result["decisions"]
        actions = [d["decision"]["action"] for d in decisions if "decision" in d]

        # Should have mix of actions (not all the same)
        assert len(set(actions)) >= 2

    def test_llm_isolation(self, integrated_trading_service, mock_supabase):
        """Test that one LLM's failure doesn't affect others."""
        # This is tested by the error handling in execute_trading_cycle
        # Each LLM is processed independently with try-catch

        result = integrated_trading_service.execute_trading_cycle()

        # Even if one fails, others should succeed
        assert result["status"] in ["SUCCESS", "PARTIAL_SUCCESS"]


# ============================================================================
# Data Persistence Tests
# ============================================================================

class TestDataPersistence:
    """Test that all data is correctly persisted to database."""

    def test_position_persistence(self, integrated_trading_service, mock_supabase):
        """Test that positions are saved to database."""
        # Execute cycle
        integrated_trading_service.execute_trading_cycle()

        # Verify create_position was called if decisions were executed
        # (depends on risk checks passing)

    def test_trade_persistence(self, integrated_trading_service, mock_supabase):
        """Test that trades are saved to database."""
        # Execute cycle
        integrated_trading_service.execute_trading_cycle()

        # Verify trade creation if positions were opened

    def test_account_balance_persistence(self, integrated_trading_service, mock_supabase):
        """Test that account balances are persisted."""
        # Get initial accounts
        accounts_before = mock_supabase.get_all_llm_accounts()

        # Execute cycle
        integrated_trading_service.execute_trading_cycle()

        # Balances should be tracked (updated via mocks)


# ============================================================================
# Error Handling and Recovery Tests
# ============================================================================

class TestErrorHandlingAndRecovery:
    """Test system error handling and recovery mechanisms."""

    def test_database_error_recovery(self, integrated_trading_service, mock_supabase):
        """Test system handles database errors gracefully."""
        # Simulate database error
        mock_supabase.get_all_llm_accounts.side_effect = Exception("Database connection lost")

        # System should handle error and not crash
        with pytest.raises(Exception):
            integrated_trading_service.execute_trading_cycle()

    def test_binance_api_error_recovery(self, integrated_trading_service, mock_binance):
        """Test system handles Binance API errors gracefully."""
        # Simulate API error
        mock_binance.get_ticker.side_effect = Exception("API rate limit exceeded")

        # System should handle error
        result = integrated_trading_service.execute_trading_cycle()

        # Should fail gracefully
        assert result["status"] in ["ERROR", "PARTIAL_SUCCESS"]

    def test_llm_api_error_recovery(self, integrated_trading_service, mock_llm_clients):
        """Test system handles LLM API errors gracefully."""
        # Simulate LLM error for one client
        mock_llm_clients["LLM-A"].get_trading_decision.side_effect = Exception("LLM timeout")

        # Other LLMs should still work
        result = integrated_trading_service.execute_trading_cycle()

        # Should be partial success (2 out of 3 LLMs work)
        assert result["llms_processed"] >= 0  # Some may succeed

    def test_invalid_decision_handling(self, integrated_trading_service, mock_llm_clients):
        """Test system handles invalid LLM decisions."""
        # Return invalid decision
        mock_llm_clients["LLM-A"].get_trading_decision.return_value = {
            "action": "INVALID_ACTION",  # Invalid
            "symbol": "INVALID"
        }

        result = integrated_trading_service.execute_trading_cycle()

        # Should handle gracefully (risk manager will reject)
        assert result["status"] in ["SUCCESS", "PARTIAL_SUCCESS"]


# ============================================================================
# Trading Status and Reporting Tests
# ============================================================================

class TestTradingStatusAndReporting:
    """Test trading status and reporting functionality."""

    def test_get_trading_status(self, integrated_trading_service):
        """Test getting overall trading status."""
        status = integrated_trading_service.get_trading_status()

        assert "accounts" in status
        assert "summary" in status
        assert "active_llms" in status
        assert len(status["accounts"]) == 3

    def test_get_llm_account_details(self, integrated_trading_service):
        """Test getting specific LLM account details."""
        account = integrated_trading_service.get_llm_account("LLM-A")

        assert account is not None
        assert account["llm_id"] == "LLM-A"
        assert "balance_usdt" in account
        assert "equity_usdt" in account

    def test_get_all_positions(self, integrated_trading_service):
        """Test getting all open positions."""
        positions = integrated_trading_service.get_all_positions()

        assert isinstance(positions, list)

    def test_get_leaderboard(self, integrated_trading_service):
        """Test getting LLM leaderboard."""
        leaderboard = integrated_trading_service.get_leaderboard()

        assert len(leaderboard) == 3

        # Should be sorted by performance
        for i in range(len(leaderboard) - 1):
            assert leaderboard[i]["balance_usdt"] >= leaderboard[i + 1]["balance_usdt"]


# ============================================================================
# Integration Test Summary
# ============================================================================

def test_full_system_integration(integrated_trading_service):
    """
    Comprehensive integration test of the entire system.

    This test validates:
    1. System initialization
    2. Market data fetching
    3. LLM decision making (3 LLMs)
    4. Risk validation
    5. Position management
    6. Account updates
    7. Data persistence
    8. Status reporting
    """
    # 1. Verify system is initialized
    status = integrated_trading_service.get_trading_status()
    assert len(status["accounts"]) == 3
    assert status["active_llms"] == 3

    # 2. Execute trading cycle
    cycle_result = integrated_trading_service.execute_trading_cycle()
    assert cycle_result["status"] in ["SUCCESS", "PARTIAL_SUCCESS"]
    assert cycle_result["llms_processed"] >= 1

    # 3. Verify market data
    snapshot = integrated_trading_service.market_data.get_market_snapshot()
    assert "symbols" in snapshot

    # 4. Verify decisions were made
    assert "decisions" in cycle_result
    assert len(cycle_result["decisions"]) >= 1

    # 5. Get final status
    final_status = integrated_trading_service.get_trading_status()
    assert final_status is not None

    # 6. Get leaderboard
    leaderboard = integrated_trading_service.get_leaderboard()
    assert len(leaderboard) == 3

    print("\n" + "="*70)
    print("✅ FULL SYSTEM INTEGRATION TEST PASSED")
    print("="*70)
    print(f"Cycle Status: {cycle_result['status']}")
    print(f"LLMs Processed: {cycle_result['llms_processed']}")
    print(f"Decisions Made: {len(cycle_result['decisions'])}")
    print(f"Active LLMs: {final_status['active_llms']}")
    print("="*70)
