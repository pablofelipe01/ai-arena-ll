"""
Tests for services layer (MarketDataService, IndicatorService, AccountService, TradingService).

Basic integration tests focusing on key workflows.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch

from src.services.market_data_service import MarketDataService, MarketDataCache
from src.services.indicator_service import IndicatorService
from src.services.account_service import AccountService
from src.services.trading_service import TradingService
from src.clients.binance_client import BinanceClient
from src.core import RiskManager, TradeExecutor
from src.database.supabase_client import SupabaseClient


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_binance():
    """Mock Binance client."""
    mock = Mock()

    # Mock ticker price
    mock.get_ticker_price = Mock(return_value={"price": "3000.00"})

    # Mock 24h ticker
    mock.get_ticker_24h = Mock(return_value={
        "symbol": "ETHUSDT",
        "lastPrice": "3000.00",
        "priceChange": "150.00",
        "priceChangePercent": "5.26",
        "volume": "1000000",
        "quoteVolume": "3000000000",
        "highPrice": "3100.00",
        "lowPrice": "2900.00",
        "openPrice": "2850.00",
        "closeTime": 1700000000000
    })

    # Mock klines
    mock.get_klines = Mock(return_value=[
        [1700000000000, "2900", "3000", "2850", "2950", "100", 1700003600000, "290000", 100],
        [1700003600000, "2950", "3050", "2940", "3000", "110", 1700007200000, "330000", 110],
    ])

    return mock


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    mock = Mock(spec=SupabaseClient)
    mock.upsert_llm_account = Mock()
    mock.upsert_position = Mock()
    mock.update_position_status = Mock()
    mock.insert_trade = Mock()
    mock.insert_llm_decision = Mock()
    mock.insert_market_data = Mock()
    return mock


@pytest.fixture
def market_data_service(mock_binance):
    """Market data service instance."""
    return MarketDataService(
        binance_client=mock_binance,
        cache_ttl=60
    )


@pytest.fixture
def indicator_service(market_data_service):
    """Indicator service instance."""
    return IndicatorService(market_data_service)


@pytest.fixture
def account_service(mock_supabase):
    """Account service instance."""
    return AccountService(
        supabase_client=mock_supabase,
        initial_balance=Decimal("100.00")
    )


# ============================================================================
# MarketDataService Tests
# ============================================================================

class TestMarketDataService:
    """Tests for MarketDataService."""

    def test_initialization(self, market_data_service):
        """Test service initialization."""
        assert market_data_service is not None
        assert len(market_data_service.symbols) == 6  # ALLOWED_SYMBOLS

    def test_get_current_prices(self, market_data_service):
        """Test fetching current prices."""
        prices = market_data_service.get_current_prices(use_cache=False)

        assert "ETHUSDT" in prices
        assert prices["ETHUSDT"] == Decimal("3000.00")

    def test_get_ticker_24h(self, market_data_service):
        """Test fetching 24h ticker."""
        ticker = market_data_service.get_ticker_24h("ETHUSDT", use_cache=False)

        assert ticker["symbol"] == "ETHUSDT"
        assert ticker["price"] == Decimal("3000.00")
        assert ticker["price_change_pct"] == Decimal("5.26")

    def test_cache_functionality(self, market_data_service):
        """Test data caching."""
        # First call - should hit API
        prices1 = market_data_service.get_current_prices(use_cache=True)

        # Second call - should use cache
        prices2 = market_data_service.get_current_prices(use_cache=True)

        assert prices1 == prices2

        # Clear cache
        market_data_service.clear_cache()

        # Third call - should hit API again
        prices3 = market_data_service.get_current_prices(use_cache=False)

        assert prices3 == prices1


# ============================================================================
# IndicatorService Tests
# ============================================================================

class TestIndicatorService:
    """Tests for IndicatorService."""

    def test_calculate_rsi(self, indicator_service):
        """Test RSI calculation."""
        rsi = indicator_service.calculate_rsi("ETHUSDT")

        assert 0 <= rsi <= 100
        assert isinstance(rsi, float)

    def test_calculate_macd(self, indicator_service):
        """Test MACD calculation."""
        macd = indicator_service.calculate_macd("ETHUSDT")

        assert "macd" in macd
        assert "signal" in macd
        assert "histogram" in macd

    def test_calculate_all_indicators(self, indicator_service):
        """Test calculating all indicators."""
        indicators = indicator_service.calculate_all_indicators("ETHUSDT")

        assert "rsi" in indicators
        assert "macd" in indicators
        assert "sma_20" in indicators

    def test_get_trading_signals(self, indicator_service):
        """Test trading signal generation."""
        signals = indicator_service.get_trading_signals("ETHUSDT")

        assert "rsi_signal" in signals
        assert "macd_signal" in signals
        assert "overall_signal" in signals


# ============================================================================
# AccountService Tests
# ============================================================================

class TestAccountService:
    """Tests for AccountService."""

    def test_initialization(self, account_service):
        """Test service initialization."""
        assert len(account_service.accounts) == 3
        assert "LLM-A" in account_service.accounts
        assert "LLM-B" in account_service.accounts
        assert "LLM-C" in account_service.accounts

    def test_get_account(self, account_service):
        """Test getting an account."""
        account = account_service.get_account("LLM-A")

        assert account.llm_id == "LLM-A"
        assert account.balance_usdt == Decimal("100.00")

    def test_invalid_llm_id(self, account_service):
        """Test getting invalid account."""
        with pytest.raises(ValueError, match="Invalid LLM ID"):
            account_service.get_account("LLM-Z")

    def test_get_leaderboard(self, account_service):
        """Test leaderboard generation."""
        leaderboard = account_service.get_leaderboard()

        assert len(leaderboard) == 3
        assert all("llm_id" in entry for entry in leaderboard)
        assert all("total_pnl" in entry for entry in leaderboard)

    def test_get_summary(self, account_service):
        """Test summary statistics."""
        summary = account_service.get_summary()

        assert summary["total_equity_usdt"] == 300.0  # 3 x $100
        assert summary["active_llms"] == 3
        assert "leaderboard" in summary

    def test_sync_account_to_db(self, account_service, mock_supabase):
        """Test syncing account to database."""
        account_service.sync_account_to_db("LLM-A")

        # Verify DB call was made
        mock_supabase.upsert_llm_account.assert_called_once()

        # Check call arguments
        call_args = mock_supabase.upsert_llm_account.call_args[0][0]
        assert call_args["llm_id"] == "LLM-A"
        assert call_args["balance_usdt"] == 100.0


# ============================================================================
# TradingService Tests
# ============================================================================

class TestTradingService:
    """Tests for TradingService (basic integration tests)."""

    @pytest.fixture
    def trading_service(self, market_data_service, indicator_service, account_service, mock_supabase):
        """Trading service instance."""
        risk_manager = RiskManager()

        mock_trade_executor = Mock(spec=TradeExecutor)
        mock_trade_executor.auto_close_triggers.return_value = []
        mock_trade_executor.execute_decision.return_value = {
            "status": "SUCCESS",
            "action": "HOLD",
            "message": "No action taken"
        }

        # Mock LLM clients
        mock_llm_clients = {}
        for llm_id in ["LLM-A", "LLM-B", "LLM-C"]:
            mock_llm = Mock()
            mock_llm.get_trading_decision.return_value = {
                "decision": {
                    "action": "HOLD",
                    "reasoning": "Testing",
                    "confidence": 0.5,
                    "strategy": "wait"
                },
                "raw_response": "{}",
                "response_time_ms": 100,
                "tokens": {"total": 1000},
                "cost_usd": 0.01
            }
            mock_llm_clients[llm_id] = mock_llm

        return TradingService(
            market_data_service=market_data_service,
            indicator_service=indicator_service,
            account_service=account_service,
            risk_manager=risk_manager,
            trade_executor=mock_trade_executor,
            llm_clients=mock_llm_clients,
            supabase_client=mock_supabase
        )

    def test_initialization(self, trading_service):
        """Test trading service initialization."""
        assert trading_service is not None
        assert len(trading_service.llm_clients) == 3

    def test_get_trading_status(self, trading_service):
        """Test getting trading status."""
        status = trading_service.get_trading_status()

        assert "timestamp" in status
        assert "llm_count" in status
        assert status["llm_count"] == 3
        assert "accounts" in status
        assert "summary" in status

    def test_execute_trading_cycle(self, trading_service):
        """Test executing a complete trading cycle."""
        results = trading_service.execute_trading_cycle()

        assert results["success"] is True
        assert "market_data" in results
        assert "decisions" in results
        assert "accounts" in results
        assert "summary" in results

        # Check that all 3 LLMs made decisions
        assert len(results["decisions"]) == 3
        assert "LLM-A" in results["decisions"]
        assert "LLM-B" in results["decisions"]
        assert "LLM-C" in results["decisions"]


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
