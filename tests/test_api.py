"""
Tests for FastAPI REST API endpoints.

Integration tests using FastAPI TestClient with mocked services.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient

from src.api.main import app
from src.core.llm_account import LLMAccount, Position
from src.services.market_data_service import MarketDataService
from src.services.indicator_service import IndicatorService
from src.services.account_service import AccountService
from src.services.trading_service import TradingService


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_services():
    """Mock all services for API tests."""
    # Mock accounts
    mock_account_a = Mock(spec=LLMAccount)
    mock_account_a.llm_id = "LLM-A"
    mock_account_a.balance_usdt = Decimal("100.00")
    mock_account_a.margin_used = Decimal("0.00")
    mock_account_a.unrealized_pnl = Decimal("0.00")
    mock_account_a.equity_usdt = Decimal("100.00")
    mock_account_a.total_trades = 0
    mock_account_a.winning_trades = 0
    mock_account_a.losing_trades = 0
    mock_account_a.win_rate = Decimal("0.00")
    mock_account_a.total_realized_pnl = Decimal("0.00")
    mock_account_a.total_pnl = Decimal("0.00")
    mock_account_a.total_pnl_pct = Decimal("0.00")
    mock_account_a.open_positions = {}
    mock_account_a.closed_trades = []

    # Mock account service
    mock_account_service = Mock(spec=AccountService)
    mock_account_service.get_account.return_value = mock_account_a
    mock_account_service.get_all_accounts.return_value = {
        "LLM-A": mock_account_a,
        "LLM-B": mock_account_a,
        "LLM-C": mock_account_a
    }
    mock_account_service.get_leaderboard.return_value = [
        {
            "llm_id": "LLM-A",
            "equity_usdt": 100.0,
            "total_pnl": 0.0,
            "total_pnl_pct": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "open_positions": 0,
            "balance_usdt": 100.0
        }
    ]
    mock_account_service.get_summary.return_value = {
        "total_equity_usdt": 300.0,
        "total_pnl": 0.0,
        "total_pnl_pct": 0.0,
        "total_trades": 0,
        "average_win_rate": 0.0
    }
    mock_account_service.get_all_open_positions.return_value = {
        "LLM-A": [],
        "LLM-B": [],
        "LLM-C": []
    }
    mock_account_service.get_recent_trades.return_value = []

    # Mock market data service
    mock_market_service = Mock(spec=MarketDataService)
    mock_market_service.get_current_prices.return_value = {
        "ETHUSDT": Decimal("3000.00"),
        "BNBUSDT": Decimal("500.00")
    }
    mock_market_service.get_market_snapshot.return_value = {
        "timestamp": datetime.utcnow(),
        "symbols": {
            "ETHUSDT": {
                "price": Decimal("3000.00"),
                "price_change_pct_24h": Decimal("5.0"),
                "volume_24h": Decimal("1000000.0"),
                "high_24h": Decimal("3100.00"),
                "low_24h": Decimal("2900.00")
            }
        },
        "summary": {
            "gainers": ["ETHUSDT"],
            "losers": [],
            "symbols_tracked": 6
        }
    }
    mock_market_service.get_ticker_24h.return_value = {
        "symbol": "ETHUSDT",
        "price": Decimal("3000.00"),
        "price_change_pct": Decimal("5.0"),
        "volume_24h": Decimal("1000000.0"),
        "high_24h": Decimal("3100.00"),
        "low_24h": Decimal("2900.00")
    }

    # Mock indicator service
    mock_indicator_service = Mock(spec=IndicatorService)
    mock_indicator_service.calculate_all_indicators.return_value = {
        "rsi": 65.0,
        "macd": 10.0,
        "macd_signal": 8.0,
        "macd_histogram": 2.0,
        "sma_20": 2950.0,
        "sma_50": 2900.0
    }
    mock_indicator_service.get_trading_signals.return_value = {
        "rsi_signal": "BUY",
        "macd_signal": "BUY",
        "overall_signal": "BUY"
    }
    mock_indicator_service.calculate_indicators_for_all_symbols.return_value = {
        "ETHUSDT": {
            "rsi": 65.0,
            "macd": 10.0,
            "macd_signal": 8.0,
            "macd_histogram": 2.0,
            "sma_20": 2950.0,
            "sma_50": 2900.0
        }
    }

    # Mock trading service
    mock_trading_service = Mock(spec=TradingService)
    mock_trading_service.get_trading_status.return_value = {
        "timestamp": datetime.utcnow().isoformat(),
        "llm_count": 3,
        "symbols_tracked": 6,
        "accounts": [],
        "open_positions": {
            "LLM-A": [],
            "LLM-B": [],
            "LLM-C": []
        },
        "recent_trades": [],
        "summary": {
            "total_equity_usdt": 300.0,
            "total_pnl": 0.0,
            "total_trades": 0,
            "average_win_rate": 0.0
        }
    }

    return {
        "account_service": mock_account_service,
        "market_service": mock_market_service,
        "indicator_service": mock_indicator_service,
        "trading_service": mock_trading_service
    }


@pytest.fixture
def client(mock_services):
    """FastAPI test client with mocked dependencies."""
    # Patch all dependency initialization functions before importing routes
    with patch("src.api.dependencies.get_binance_client"), \
         patch("src.api.dependencies.get_supabase_client"), \
         patch("src.api.dependencies.get_llm_clients"), \
         patch("src.api.dependencies.get_market_data_service", return_value=mock_services["market_service"]), \
         patch("src.api.dependencies.get_indicator_service", return_value=mock_services["indicator_service"]), \
         patch("src.api.dependencies.get_account_service", return_value=mock_services["account_service"]), \
         patch("src.api.dependencies.get_trading_service", return_value=mock_services["trading_service"]), \
         patch("src.api.dependencies.get_trading_service_dependency", return_value=mock_services["trading_service"]), \
         patch("src.api.dependencies.get_market_data_service_dependency", return_value=mock_services["market_service"]), \
         patch("src.api.dependencies.get_indicator_service_dependency", return_value=mock_services["indicator_service"]), \
         patch("src.api.dependencies.get_account_service_dependency", return_value=mock_services["account_service"]):

        # Create app without lifespan for testing
        from fastapi import FastAPI
        from src.api.routes import trading_router, market_router, health_router

        test_app = FastAPI()
        test_app.include_router(health_router)
        test_app.include_router(trading_router)
        test_app.include_router(market_router)

        with TestClient(test_app) as test_client:
            yield test_client


# ============================================================================
# Health Endpoint Tests
# ============================================================================

class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client):
        """Test /health endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "uptime_seconds" in data

    def test_root_endpoint(self, client):
        """Test / (root) endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Crypto LLM Trading API"
        assert "version" in data
        assert "endpoints" in data
        assert "trading" in data["endpoints"]
        assert "market" in data["endpoints"]


# ============================================================================
# Trading Endpoint Tests
# ============================================================================

class TestTradingEndpoints:
    """Tests for trading endpoints."""

    def test_get_trading_status(self, client):
        """Test GET /trading/status."""
        response = client.get("/trading/status")

        assert response.status_code == 200
        data = response.json()

        assert data["llm_count"] == 3
        assert data["symbols_tracked"] == 6
        assert "total_equity" in data
        assert "timestamp" in data

    def test_get_all_accounts(self, client):
        """Test GET /trading/accounts."""
        response = client.get("/trading/accounts")

        assert response.status_code == 200
        data = response.json()

        assert "accounts" in data
        assert len(data["accounts"]) == 3
        assert data["total_equity"] == 300.0

    def test_get_account(self, client):
        """Test GET /trading/accounts/{llm_id}."""
        response = client.get("/trading/accounts/LLM-A")

        assert response.status_code == 200
        data = response.json()

        assert data["llm_id"] == "LLM-A"
        assert "balance_usdt" in data
        assert "equity_usdt" in data
        assert "open_positions" in data

    def test_get_invalid_account(self, client, mock_services):
        """Test GET /trading/accounts/{llm_id} with invalid ID."""
        # Configure mock to raise ValueError
        mock_services["account_service"].get_account.side_effect = ValueError("Invalid LLM ID")

        response = client.get("/trading/accounts/LLM-Z")

        assert response.status_code == 404

    def test_get_all_positions(self, client):
        """Test GET /trading/positions."""
        response = client.get("/trading/positions")

        assert response.status_code == 200
        data = response.json()

        assert "positions" in data
        assert "total_count" in data
        assert "total_margin_used" in data

    def test_get_positions_by_llm(self, client):
        """Test GET /trading/positions/{llm_id}."""
        response = client.get("/trading/positions/LLM-A")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

    def test_get_trades(self, client):
        """Test GET /trading/trades."""
        response = client.get("/trading/trades?limit=5")

        assert response.status_code == 200
        data = response.json()

        assert "trades" in data
        assert "total_count" in data
        assert data["llm_id"] is None

    def test_get_trades_by_llm(self, client):
        """Test GET /trading/trades/{llm_id}."""
        response = client.get("/trading/trades/LLM-A?limit=10")

        assert response.status_code == 200
        data = response.json()

        assert "trades" in data
        assert data["llm_id"] == "LLM-A"

    def test_get_leaderboard(self, client):
        """Test GET /trading/leaderboard."""
        response = client.get("/trading/leaderboard")

        assert response.status_code == 200
        data = response.json()

        assert "leaderboard" in data
        assert "summary" in data
        assert len(data["leaderboard"]) == 1

        # Check rank
        assert data["leaderboard"][0]["rank"] == 1


# ============================================================================
# Market Data Endpoint Tests
# ============================================================================

class TestMarketEndpoints:
    """Tests for market data endpoints."""

    def test_get_market_snapshot(self, client):
        """Test GET /market/snapshot."""
        response = client.get("/market/snapshot")

        assert response.status_code == 200
        data = response.json()

        assert "symbols" in data
        assert "indicators" in data
        assert "summary" in data
        assert "timestamp" in data

    def test_get_current_prices(self, client):
        """Test GET /market/prices."""
        response = client.get("/market/prices")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, dict)
        assert "ETHUSDT" in data
        assert data["ETHUSDT"] == 3000.0

    def test_get_current_prices_no_cache(self, client):
        """Test GET /market/prices with use_cache=false."""
        response = client.get("/market/prices?use_cache=false")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, dict)

    def test_get_price_for_symbol(self, client):
        """Test GET /market/price/{symbol}."""
        response = client.get("/market/price/ETHUSDT")

        assert response.status_code == 200
        assert response.json() == 3000.0

    def test_get_ticker(self, client):
        """Test GET /market/ticker/{symbol}."""
        response = client.get("/market/ticker/ETHUSDT")

        assert response.status_code == 200
        data = response.json()

        assert data["symbol"] == "ETHUSDT"
        assert data["price"] == 3000.0
        assert "price_change_pct_24h" in data
        assert "volume_24h" in data

    def test_get_indicators(self, client):
        """Test GET /market/indicators/{symbol}."""
        response = client.get("/market/indicators/ETHUSDT")

        assert response.status_code == 200
        data = response.json()

        assert data["symbol"] == "ETHUSDT"
        assert "rsi" in data
        assert "macd" in data
        assert "trading_signal" in data
        assert data["trading_signal"] == "BUY"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
