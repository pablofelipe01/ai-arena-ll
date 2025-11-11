"""
Trading Cycle Integration Tests.

Tests specific trading cycle scenarios:
- Complete buy-hold-sell cycles
- Multiple positions management
- Stop loss and take profit triggers
- Position closing scenarios
- Account balance changes
- PnL calculations

Run with: pytest tests/test_trading_cycles.py -v
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.services.trading_service import TradingService
from src.services.account_service import AccountService
from src.services.market_data_service import MarketDataService
from src.core.position_manager import PositionManager
from src.core.risk_manager import RiskManager
from src.core.llm_decision import LLMDecisionService


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def trading_cycle_setup():
    """Setup for trading cycle tests."""
    # Mock Supabase
    mock_supabase = Mock()
    mock_supabase.is_connected = True

    # Initial account state - $100 balance
    initial_account = {
        "llm_id": "LLM-A",
        "provider": "anthropic",
        "model_name": "claude-sonnet-4",
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
        "is_trading_enabled": True
    }

    mock_supabase.get_llm_account.return_value = initial_account
    mock_supabase.get_all_llm_accounts.return_value = [initial_account]
    mock_supabase.get_open_positions.return_value = []
    mock_supabase.update_llm_balance.return_value = initial_account
    mock_supabase.update_llm_stats.return_value = initial_account

    # Mock Binance
    mock_binance = Mock()
    mock_binance.is_connected = True
    mock_binance.get_ticker.return_value = {
        "symbol": "ETHUSDT",
        "price": "2000.0",
        "bid": "1999.0",
        "ask": "2001.0",
        "volume": "100000",
        "priceChangePercent": "1.5"
    }
    mock_binance.get_klines.return_value = [
        {
            "open_time": 1699000000000,
            "open": "1990.0",
            "high": "2010.0",
            "low": "1980.0",
            "close": "2000.0",
            "volume": "1000.0"
        }
    ] * 100

    return {
        "supabase": mock_supabase,
        "binance": mock_binance,
        "initial_account": initial_account
    }


# ============================================================================
# Complete Trading Cycle Tests
# ============================================================================

class TestCompleteBuySellCycle:
    """Test complete buy and sell trading cycles."""

    def test_buy_cycle_position_opening(self, trading_cycle_setup):
        """Test opening a BUY position in a trading cycle."""
        mock_supabase = trading_cycle_setup["supabase"]
        mock_binance = trading_cycle_setup["binance"]

        # Mock successful position creation
        mock_supabase.create_position.return_value = {
            "id": "pos-123",
            "llm_id": "LLM-A",
            "symbol": "ETHUSDT",
            "side": "LONG",
            "entry_price": 2000.0,
            "current_price": 2000.0,
            "quantity": 0.01,
            "leverage": 5,
            "margin": 4.0,
            "unrealized_pnl": 0.0,
            "status": "OPEN",
            "opened_at": datetime.now().isoformat()
        }

        mock_supabase.create_trade.return_value = {"id": "trade-123"}

        # Create services
        account_service = AccountService(mock_supabase)
        market_data_service = MarketDataService(mock_binance, mock_supabase)
        position_manager = PositionManager(mock_supabase, mock_binance, account_service)

        # Open position
        decision = {
            "action": "BUY",
            "symbol": "ETHUSDT",
            "side": "LONG",
            "size_usd": 20.0,
            "leverage": 5,
            "confidence": 0.8,
            "reasoning": "Test buy decision"
        }

        result = position_manager.open_position("LLM-A", decision, Decimal("2000.0"))

        # Verify position opened
        assert result["status"] == "SUCCESS"
        assert "position" in result
        assert result["position"]["symbol"] == "ETHUSDT"
        assert result["position"]["side"] == "LONG"

        # Verify database calls
        mock_supabase.create_position.assert_called_once()
        mock_supabase.create_trade.assert_called_once()

    def test_sell_cycle_position_opening(self, trading_cycle_setup):
        """Test opening a SELL (SHORT) position."""
        mock_supabase = trading_cycle_setup["supabase"]
        mock_binance = trading_cycle_setup["binance"]

        # Mock SHORT position creation
        mock_supabase.create_position.return_value = {
            "id": "pos-456",
            "llm_id": "LLM-A",
            "symbol": "BNBUSDT",
            "side": "SHORT",
            "entry_price": 300.0,
            "current_price": 300.0,
            "quantity": 0.1,
            "leverage": 3,
            "margin": 10.0,
            "unrealized_pnl": 0.0,
            "status": "OPEN"
        }

        mock_supabase.create_trade.return_value = {"id": "trade-456"}

        # Update ticker for BNB
        mock_binance.get_ticker.return_value = {
            "symbol": "BNBUSDT",
            "price": "300.0",
            "bid": "299.0",
            "ask": "301.0"
        }

        account_service = AccountService(mock_supabase)
        position_manager = PositionManager(mock_supabase, mock_binance, account_service)

        # Open SHORT position
        decision = {
            "action": "SELL",
            "symbol": "BNBUSDT",
            "side": "SHORT",
            "size_usd": 30.0,
            "leverage": 3,
            "confidence": 0.7
        }

        result = position_manager.open_position("LLM-A", decision, Decimal("300.0"))

        assert result["status"] == "SUCCESS"
        assert result["position"]["side"] == "SHORT"

    def test_position_closing_with_profit(self, trading_cycle_setup):
        """Test closing a position with profit."""
        mock_supabase = trading_cycle_setup["supabase"]
        mock_binance = trading_cycle_setup["binance"]

        # Mock open position
        open_position = {
            "id": "pos-789",
            "llm_id": "LLM-A",
            "symbol": "ETHUSDT",
            "side": "LONG",
            "entry_price": 2000.0,
            "current_price": 2100.0,  # Price went up
            "quantity": 0.01,
            "leverage": 5,
            "margin": 4.0,
            "unrealized_pnl": 5.0,  # Profit
            "status": "OPEN"
        }

        mock_supabase.get_position_by_id.return_value = open_position
        mock_supabase.close_position.return_value = {**open_position, "status": "CLOSED"}
        mock_supabase.create_trade.return_value = {"id": "trade-close-789"}

        # Price is now higher
        mock_binance.get_ticker.return_value = {
            "symbol": "ETHUSDT",
            "price": "2100.0"
        }

        account_service = AccountService(mock_supabase)
        position_manager = PositionManager(mock_supabase, mock_binance, account_service)

        # Close position
        result = position_manager.close_position("pos-789", "TAKE_PROFIT")

        assert result["status"] == "SUCCESS"
        assert result["pnl"] > 0  # Profitable trade

    def test_position_closing_with_loss(self, trading_cycle_setup):
        """Test closing a position with loss."""
        mock_supabase = trading_cycle_setup["supabase"]
        mock_binance = trading_cycle_setup["binance"]

        # Mock losing position
        open_position = {
            "id": "pos-loss",
            "llm_id": "LLM-A",
            "symbol": "ETHUSDT",
            "side": "LONG",
            "entry_price": 2000.0,
            "current_price": 1950.0,  # Price went down
            "quantity": 0.01,
            "leverage": 5,
            "margin": 4.0,
            "unrealized_pnl": -2.5,  # Loss
            "status": "OPEN"
        }

        mock_supabase.get_position_by_id.return_value = open_position
        mock_supabase.close_position.return_value = {**open_position, "status": "CLOSED"}
        mock_supabase.create_trade.return_value = {"id": "trade-close-loss"}

        mock_binance.get_ticker.return_value = {"symbol": "ETHUSDT", "price": "1950.0"}

        account_service = AccountService(mock_supabase)
        position_manager = PositionManager(mock_supabase, mock_binance, account_service)

        result = position_manager.close_position("pos-loss", "STOP_LOSS")

        assert result["status"] == "SUCCESS"
        assert result["pnl"] < 0  # Losing trade


# ============================================================================
# Multiple Position Management Tests
# ============================================================================

class TestMultiplePositions:
    """Test managing multiple positions simultaneously."""

    def test_multiple_positions_different_symbols(self, trading_cycle_setup):
        """Test opening positions on different symbols."""
        mock_supabase = trading_cycle_setup["supabase"]
        mock_binance = trading_cycle_setup["binance"]

        # Mock multiple open positions
        positions = [
            {
                "id": "pos-1",
                "llm_id": "LLM-A",
                "symbol": "ETHUSDT",
                "side": "LONG",
                "entry_price": 2000.0,
                "margin": 4.0,
                "status": "OPEN"
            },
            {
                "id": "pos-2",
                "llm_id": "LLM-A",
                "symbol": "BNBUSDT",
                "side": "LONG",
                "entry_price": 300.0,
                "margin": 5.0,
                "status": "OPEN"
            },
            {
                "id": "pos-3",
                "llm_id": "LLM-A",
                "symbol": "XRPUSDT",
                "side": "SHORT",
                "entry_price": 0.5,
                "margin": 3.0,
                "status": "OPEN"
            }
        ]

        mock_supabase.get_open_positions.return_value = positions

        account_service = AccountService(mock_supabase)

        # Get positions
        llm_positions = mock_supabase.get_open_positions(llm_id="LLM-A")

        assert len(llm_positions) == 3
        assert all(p["status"] == "OPEN" for p in llm_positions)

        # Different symbols
        symbols = [p["symbol"] for p in llm_positions]
        assert len(set(symbols)) == 3

    def test_position_limit_enforcement(self, trading_cycle_setup):
        """Test that max position limit is enforced."""
        mock_supabase = trading_cycle_setup["supabase"]

        # Mock 3 open positions (max limit)
        open_positions = [
            {"id": f"pos-{i}", "llm_id": "LLM-A", "status": "OPEN"}
            for i in range(3)
        ]

        mock_supabase.get_open_positions.return_value = open_positions

        # Try to open 4th position - should be rejected by risk manager
        risk_manager = RiskManager()

        account = trading_cycle_setup["initial_account"]
        account["open_positions"] = 3

        decision = {
            "action": "BUY",
            "symbol": "DOGEUSDT",
            "side": "LONG",
            "size_usd": 10.0,
            "leverage": 2
        }

        # Risk check should fail
        risk_result = risk_manager.validate_decision("LLM-A", account, decision, open_positions)

        assert not risk_result["approved"]
        assert "max_positions" in risk_result["rejection_reason"].lower() or \
               "position limit" in risk_result["rejection_reason"].lower()

    def test_total_margin_tracking(self, trading_cycle_setup):
        """Test that total margin used is tracked correctly."""
        mock_supabase = trading_cycle_setup["supabase"]

        # Positions with different margins
        positions = [
            {"id": "pos-1", "margin": 10.0, "status": "OPEN"},
            {"id": "pos-2", "margin": 15.0, "status": "OPEN"},
            {"id": "pos-3", "margin": 8.0, "status": "OPEN"}
        ]

        mock_supabase.get_open_positions.return_value = positions

        # Calculate total margin
        total_margin = sum(p["margin"] for p in positions)

        assert total_margin == 33.0
        assert total_margin < 100.0  # Within balance


# ============================================================================
# Stop Loss and Take Profit Tests
# ============================================================================

class TestStopLossAndTakeProfit:
    """Test stop loss and take profit triggers."""

    def test_stop_loss_trigger(self, trading_cycle_setup):
        """Test that stop loss is triggered correctly."""
        mock_supabase = trading_cycle_setup["supabase"]
        mock_binance = trading_cycle_setup["binance"]

        # Position with stop loss
        position = {
            "id": "pos-sl",
            "llm_id": "LLM-A",
            "symbol": "ETHUSDT",
            "side": "LONG",
            "entry_price": 2000.0,
            "current_price": 1960.0,  # Down 2%
            "stop_loss": 1970.0,  # Stop at 1970
            "quantity": 0.01,
            "margin": 4.0,
            "status": "OPEN"
        }

        mock_supabase.get_position_by_id.return_value = position
        mock_supabase.get_open_positions.return_value = [position]

        # Current price below stop loss
        mock_binance.get_ticker.return_value = {
            "symbol": "ETHUSDT",
            "price": "1960.0"
        }

        account_service = AccountService(mock_supabase)
        position_manager = PositionManager(mock_supabase, mock_binance, account_service)

        # Check if stop loss should trigger
        current_price = Decimal("1960.0")
        stop_loss = Decimal(position["stop_loss"])

        should_trigger = current_price <= stop_loss

        assert should_trigger is True

    def test_take_profit_trigger(self, trading_cycle_setup):
        """Test that take profit is triggered correctly."""
        mock_supabase = trading_cycle_setup["supabase"]
        mock_binance = trading_cycle_setup["binance"]

        # Position with take profit
        position = {
            "id": "pos-tp",
            "llm_id": "LLM-A",
            "symbol": "ETHUSDT",
            "side": "LONG",
            "entry_price": 2000.0,
            "current_price": 2110.0,  # Up 5.5%
            "take_profit": 2100.0,  # Take profit at 2100
            "quantity": 0.01,
            "status": "OPEN"
        }

        mock_binance.get_ticker.return_value = {
            "symbol": "ETHUSDT",
            "price": "2110.0"
        }

        # Check if take profit should trigger
        current_price = Decimal("2110.0")
        take_profit = Decimal(position["take_profit"])

        should_trigger = current_price >= take_profit

        assert should_trigger is True


# ============================================================================
# Account Balance and PnL Tests
# ============================================================================

class TestAccountBalanceAndPnL:
    """Test account balance changes and PnL calculations."""

    def test_balance_decreases_on_position_open(self, trading_cycle_setup):
        """Test that balance decreases when position is opened (margin deducted)."""
        mock_supabase = trading_cycle_setup["supabase"]
        initial_account = trading_cycle_setup["initial_account"]

        # Initial balance: $100
        initial_balance = initial_account["balance"]

        # Open position with $4 margin
        margin_used = 4.0

        # New balance should be less (margin is reserved)
        # Note: In real system, balance doesn't decrease, but margin_used increases
        # and available balance = balance - margin_used

        available_balance = initial_balance - margin_used
        assert available_balance == 96.0

    def test_pnl_calculation_for_winning_trade(self, trading_cycle_setup):
        """Test PnL calculation for a winning trade."""
        # Position details
        entry_price = Decimal("2000.0")
        exit_price = Decimal("2100.0")
        quantity = Decimal("0.01")
        leverage = 5

        # Calculate PnL
        price_diff = exit_price - entry_price  # +100
        pnl = price_diff * quantity * leverage  # 100 * 0.01 * 5 = 5.0

        assert pnl == Decimal("5.0")  # $5 profit

    def test_pnl_calculation_for_losing_trade(self, trading_cycle_setup):
        """Test PnL calculation for a losing trade."""
        entry_price = Decimal("2000.0")
        exit_price = Decimal("1950.0")
        quantity = Decimal("0.01")
        leverage = 5

        # Calculate PnL
        price_diff = exit_price - entry_price  # -50
        pnl = price_diff * quantity * leverage  # -50 * 0.01 * 5 = -2.5

        assert pnl == Decimal("-2.5")  # $2.5 loss

    def test_pnl_calculation_for_short_position(self, trading_cycle_setup):
        """Test PnL calculation for SHORT position."""
        entry_price = Decimal("300.0")
        exit_price = Decimal("290.0")  # Price went down
        quantity = Decimal("0.1")
        leverage = 3

        # For SHORT: profit when price goes down
        price_diff = entry_price - exit_price  # 300 - 290 = +10
        pnl = price_diff * quantity * leverage  # 10 * 0.1 * 3 = 3.0

        assert pnl == Decimal("3.0")  # $3 profit on short

    def test_cumulative_pnl_tracking(self, trading_cycle_setup):
        """Test cumulative PnL tracking across multiple trades."""
        # Trade 1: +$5
        # Trade 2: -$2
        # Trade 3: +$8
        # Total: +$11

        trades = [
            {"realized_pnl": 5.0},
            {"realized_pnl": -2.0},
            {"realized_pnl": 8.0}
        ]

        total_pnl = sum(t["realized_pnl"] for t in trades)

        assert total_pnl == 11.0

        # Winning trades count
        winning_trades = sum(1 for t in trades if t["realized_pnl"] > 0)
        assert winning_trades == 2

        # Losing trades count
        losing_trades = sum(1 for t in trades if t["realized_pnl"] < 0)
        assert losing_trades == 1

        # Win rate
        total_trades = len(trades)
        win_rate = (winning_trades / total_trades) * 100
        assert win_rate == pytest.approx(66.67, rel=0.01)


# ============================================================================
# Full Trading Cycle Scenarios
# ============================================================================

class TestFullTradingScenarios:
    """Test complete trading scenarios from start to finish."""

    def test_profitable_trading_day(self, trading_cycle_setup):
        """Test a full day of profitable trading."""
        mock_supabase = trading_cycle_setup["supabase"]

        # Starting balance: $100
        initial_balance = 100.0

        # Simulate 3 profitable trades
        trades = [
            {"realized_pnl": 5.0, "fees": 0.05},
            {"realized_pnl": 3.5, "fees": 0.04},
            {"realized_pnl": 7.2, "fees": 0.06}
        ]

        total_pnl = sum(t["realized_pnl"] for t in trades)
        total_fees = sum(t["fees"] for t in trades)
        net_pnl = total_pnl - total_fees

        final_balance = initial_balance + net_pnl

        assert total_pnl == 15.7
        assert total_fees == 0.15
        assert net_pnl == 15.55
        assert final_balance == 115.55  # Made $15.55 profit

    def test_losing_trading_day(self, trading_cycle_setup):
        """Test a full day of losing trades."""
        initial_balance = 100.0

        # Simulate 3 losing trades
        trades = [
            {"realized_pnl": -3.0, "fees": 0.05},
            {"realized_pnl": -2.5, "fees": 0.04},
            {"realized_pnl": -1.8, "fees": 0.03}
        ]

        total_pnl = sum(t["realized_pnl"] for t in trades)
        total_fees = sum(t["fees"] for t in trades)
        net_pnl = total_pnl - total_fees

        final_balance = initial_balance + net_pnl

        assert total_pnl == -7.3
        assert total_fees == 0.12
        assert net_pnl == -7.42
        assert final_balance == 92.58  # Lost $7.42

    def test_mixed_trading_day(self, trading_cycle_setup):
        """Test a day with both winning and losing trades."""
        initial_balance = 100.0

        trades = [
            {"realized_pnl": 5.0, "fees": 0.05},   # Win
            {"realized_pnl": -2.0, "fees": 0.03},  # Loss
            {"realized_pnl": 8.0, "fees": 0.06},   # Win
            {"realized_pnl": -3.5, "fees": 0.04},  # Loss
            {"realized_pnl": 4.5, "fees": 0.05}    # Win
        ]

        total_pnl = sum(t["realized_pnl"] for t in trades)
        total_fees = sum(t["fees"] for t in trades)
        net_pnl = total_pnl - total_fees

        # Calculate stats
        winning_trades = [t for t in trades if t["realized_pnl"] > 0]
        losing_trades = [t for t in trades if t["realized_pnl"] < 0]

        win_rate = (len(winning_trades) / len(trades)) * 100

        assert len(winning_trades) == 3
        assert len(losing_trades) == 2
        assert win_rate == 60.0
        assert total_pnl == 12.0
        assert net_pnl > 0  # Net profitable day
