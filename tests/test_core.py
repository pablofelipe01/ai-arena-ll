"""
Tests for core logic (LLMAccount, RiskManager, TradeExecutor).

Tests cover:
- Position calculations (PnL, liquidation, triggers)
- LLMAccount balance management
- Trade tracking and metrics
- Risk validation
- Trade execution
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

from src.core.llm_account import LLMAccount, Position, Trade
from src.core.risk_manager import RiskManager
from src.core.trade_executor import TradeExecutor
from src.clients.binance_client import BinanceClient


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_position_long():
    """Sample LONG position."""
    return Position(
        position_id="pos-123",
        symbol="ETHUSDT",
        side="LONG",
        entry_price=Decimal("3000.00"),
        quantity=Decimal("0.01"),
        leverage=5,
        stop_loss_pct=Decimal("5.0"),
        take_profit_pct=Decimal("10.0")
    )


@pytest.fixture
def sample_position_short():
    """Sample SHORT position."""
    return Position(
        position_id="pos-456",
        symbol="BNBUSDT",
        side="SHORT",
        entry_price=Decimal("500.00"),
        quantity=Decimal("0.05"),
        leverage=3,
        stop_loss_pct=Decimal("8.0"),
        take_profit_pct=Decimal("15.0")
    )


@pytest.fixture
def llm_account():
    """Fresh LLM account."""
    return LLMAccount(llm_id="LLM-A", initial_balance=Decimal("100.00"))


@pytest.fixture
def risk_manager():
    """Risk manager instance."""
    return RiskManager()


@pytest.fixture
def mock_binance():
    """Mock Binance client."""
    mock = Mock(spec=BinanceClient)
    mock.get_ticker_price = Mock(return_value={"price": "3000.00"})
    mock.round_step_size = Mock(side_effect=lambda symbol, qty: qty)
    mock.set_leverage = Mock()
    mock.create_market_order = Mock(return_value={"orderId": "12345"})
    return mock


@pytest.fixture
def trade_executor(mock_binance, risk_manager):
    """Trade executor with mocked Binance."""
    return TradeExecutor(
        binance_client=mock_binance,
        risk_manager=risk_manager,
        simulate=True
    )


# ============================================================================
# Position Tests
# ============================================================================

class TestPosition:
    """Tests for Position class."""

    def test_initialization(self, sample_position_long):
        """Test position initialization."""
        pos = sample_position_long

        assert pos.position_id == "pos-123"
        assert pos.symbol == "ETHUSDT"
        assert pos.side == "LONG"
        assert pos.entry_price == Decimal("3000.00")
        assert pos.quantity == Decimal("0.01")
        assert pos.leverage == 5

        # Check calculated values
        assert pos.position_value_usd == Decimal("30.00")  # 3000 * 0.01
        assert pos.margin_used == Decimal("6.00")  # 30 / 5

    def test_stop_loss_calculation_long(self, sample_position_long):
        """Test stop loss price for LONG position."""
        pos = sample_position_long

        # 5% stop loss on LONG at $3000 = $2850
        expected_sl = Decimal("3000") * (1 - Decimal("5.0") / 100)
        assert pos.stop_loss_price == expected_sl

    def test_take_profit_calculation_long(self, sample_position_long):
        """Test take profit price for LONG position."""
        pos = sample_position_long

        # 10% take profit on LONG at $3000 = $3300
        expected_tp = Decimal("3000") * (1 + Decimal("10.0") / 100)
        assert pos.take_profit_price == expected_tp

    def test_stop_loss_calculation_short(self, sample_position_short):
        """Test stop loss price for SHORT position."""
        pos = sample_position_short

        # 8% stop loss on SHORT at $500 = $540
        expected_sl = Decimal("500") * (1 + Decimal("8.0") / 100)
        assert pos.stop_loss_price == expected_sl

    def test_pnl_long_profit(self, sample_position_long):
        """Test PnL calculation for LONG position in profit."""
        pos = sample_position_long

        # Price goes from $3000 to $3300 (+10%)
        pnl = pos.calculate_pnl(Decimal("3300.00"))

        # Price change: +$300
        # PnL = $300 * 0.01 * 5x = $15
        assert pnl["unrealized_pnl_usd"] == Decimal("15.00")

        # PnL% = $15 / $6 margin = 250%
        assert pnl["unrealized_pnl_pct"] == Decimal("250.00")

        # ROI = 10% price change * 5x = 50%
        assert pnl["roi_pct"] == Decimal("50.00")

    def test_pnl_long_loss(self, sample_position_long):
        """Test PnL calculation for LONG position in loss."""
        pos = sample_position_long

        # Price drops from $3000 to $2700 (-10%)
        pnl = pos.calculate_pnl(Decimal("2700.00"))

        # Price change: -$300
        # PnL = -$300 * 0.01 * 5x = -$15
        assert pnl["unrealized_pnl_usd"] == Decimal("-15.00")

    def test_pnl_short_profit(self, sample_position_short):
        """Test PnL calculation for SHORT position in profit."""
        pos = sample_position_short

        # Price drops from $500 to $400 (-20%)
        pnl = pos.calculate_pnl(Decimal("400.00"))

        # Price change: +$100 (profit for SHORT)
        # PnL = $100 * 0.05 * 3x = $15
        assert pnl["unrealized_pnl_usd"] == Decimal("15.00")

    def test_liquidation_price_long(self, sample_position_long):
        """Test liquidation price for LONG position."""
        pos = sample_position_long

        liq_price = pos.calculate_liquidation_price()

        # 5x leverage = 20% drop triggers liquidation
        # $3000 * 0.80 = $2400
        assert liq_price == Decimal("2400.00")

    def test_liquidation_price_short(self, sample_position_short):
        """Test liquidation price for SHORT position."""
        pos = sample_position_short

        liq_price = pos.calculate_liquidation_price()

        # 3x leverage = 33.33% rise triggers liquidation
        # $500 * 1.3333 = $666.65
        expected = Decimal("500") * (1 + Decimal("100") / Decimal("3") / 100)
        assert abs(liq_price - expected) < Decimal("0.01")

    def test_should_stop_loss_trigger(self, sample_position_long):
        """Test stop loss trigger detection."""
        pos = sample_position_long

        # Should not trigger above stop loss
        assert pos.should_stop_loss(Decimal("2900.00")) is False

        # Should trigger at stop loss
        assert pos.should_stop_loss(pos.stop_loss_price) is True

        # Should trigger below stop loss
        assert pos.should_stop_loss(Decimal("2800.00")) is True

    def test_should_take_profit_trigger(self, sample_position_long):
        """Test take profit trigger detection."""
        pos = sample_position_long

        # Should not trigger below take profit
        assert pos.should_take_profit(Decimal("3200.00")) is False

        # Should trigger at take profit
        assert pos.should_take_profit(pos.take_profit_price) is True

        # Should trigger above take profit
        assert pos.should_take_profit(Decimal("3400.00")) is True


# ============================================================================
# LLMAccount Tests
# ============================================================================

class TestLLMAccount:
    """Tests for LLMAccount class."""

    def test_initialization(self):
        """Test account initialization."""
        account = LLMAccount(llm_id="LLM-A", initial_balance=Decimal("100.00"))

        assert account.llm_id == "LLM-A"
        assert account.balance_usdt == Decimal("100.00")
        assert account.margin_used == Decimal("0")
        assert account.unrealized_pnl == Decimal("0")
        assert account.equity_usdt == Decimal("100.00")
        assert len(account.open_positions) == 0
        assert len(account.closed_trades) == 0

    def test_can_open_position(self, llm_account):
        """Test position limit checking."""
        assert llm_account.can_open_position() is True

        # Open 3 positions (max)
        for i in range(3):
            llm_account.open_position(
                symbol=f"ETH{i}USDT",
                side="LONG",
                entry_price=Decimal("3000.00"),
                quantity_usd=Decimal("10.00"),
                leverage=1
            )

        # Should not be able to open more
        assert llm_account.can_open_position() is False

    def test_open_position_success(self, llm_account):
        """Test successful position opening."""
        position = llm_account.open_position(
            symbol="ETHUSDT",
            side="LONG",
            entry_price=Decimal("3000.00"),
            quantity_usd=Decimal("30.00"),
            leverage=5
        )

        assert position.symbol == "ETHUSDT"
        assert position.side == "LONG"
        assert position.leverage == 5

        # Check margin calculation: $30 / 5x = $6
        assert position.margin_used == Decimal("6.00")

        # Check account state
        assert llm_account.balance_usdt == Decimal("94.00")  # 100 - 6
        assert llm_account.margin_used == Decimal("6.00")
        assert len(llm_account.open_positions) == 1

    def test_open_position_insufficient_balance(self, llm_account):
        """Test opening position with insufficient balance."""
        with pytest.raises(ValueError, match="Insufficient balance"):
            llm_account.open_position(
                symbol="ETHUSDT",
                side="LONG",
                entry_price=Decimal("3000.00"),
                quantity_usd=Decimal("300.00"),  # Too large
                leverage=2
            )

    def test_open_position_max_reached(self, llm_account):
        """Test opening position when max reached."""
        # Open 3 positions
        for i in range(3):
            llm_account.open_position(
                symbol=f"ETH{i}USDT",
                side="LONG",
                entry_price=Decimal("3000.00"),
                quantity_usd=Decimal("10.00"),
                leverage=1
            )

        # Try to open 4th
        with pytest.raises(ValueError, match="Maximum positions"):
            llm_account.open_position(
                symbol="BTCUSDT",
                side="LONG",
                entry_price=Decimal("50000.00"),
                quantity_usd=Decimal("10.00"),
                leverage=1
            )

    def test_close_position_profit(self, llm_account):
        """Test closing position with profit."""
        # Open position
        position = llm_account.open_position(
            symbol="ETHUSDT",
            side="LONG",
            entry_price=Decimal("3000.00"),
            quantity_usd=Decimal("30.00"),
            leverage=5
        )

        balance_before = llm_account.balance_usdt

        # Close with profit: entry $3000, exit $3300
        trade = llm_account.close_position(
            position_id=position.position_id,
            exit_price=Decimal("3300.00")
        )

        # PnL = +$300 * 0.01 * 5x = +$15
        assert trade.pnl_usd == Decimal("15.00")

        # Check account state
        assert len(llm_account.open_positions) == 0
        assert len(llm_account.closed_trades) == 1

        # Balance = before + margin_returned + pnl
        # = 94 + 6 + 15 = 115
        assert llm_account.balance_usdt == Decimal("115.00")
        assert llm_account.margin_used == Decimal("0")
        assert llm_account.total_realized_pnl == Decimal("15.00")

    def test_close_position_loss(self, llm_account):
        """Test closing position with loss."""
        # Open position
        position = llm_account.open_position(
            symbol="ETHUSDT",
            side="LONG",
            entry_price=Decimal("3000.00"),
            quantity_usd=Decimal("30.00"),
            leverage=5
        )

        # Close with loss: entry $3000, exit $2700
        trade = llm_account.close_position(
            position_id=position.position_id,
            exit_price=Decimal("2700.00")
        )

        # PnL = -$300 * 0.01 * 5x = -$15
        assert trade.pnl_usd == Decimal("-15.00")

        # Balance = 94 + 6 - 15 = 85
        assert llm_account.balance_usdt == Decimal("85.00")
        assert llm_account.total_realized_pnl == Decimal("-15.00")

    def test_update_unrealized_pnl(self, llm_account):
        """Test unrealized PnL calculation."""
        # Open 2 positions
        pos1 = llm_account.open_position(
            symbol="ETHUSDT",
            side="LONG",
            entry_price=Decimal("3000.00"),
            quantity_usd=Decimal("30.00"),
            leverage=5
        )

        pos2 = llm_account.open_position(
            symbol="BNBUSDT",
            side="SHORT",
            entry_price=Decimal("500.00"),
            quantity_usd=Decimal("25.00"),
            leverage=5
        )

        # Update with current prices
        market_prices = {
            "ETHUSDT": Decimal("3300.00"),  # +10% for LONG
            "BNBUSDT": Decimal("450.00")     # -10% for SHORT
        }

        llm_account.update_unrealized_pnl(market_prices)

        # ETH PnL = +$300 * 0.01 * 5x = +$15
        # BNB PnL = +$50 * 0.05 * 5x = +$12.50
        # Total = $27.50
        assert llm_account.unrealized_pnl == Decimal("27.50")

    def test_performance_metrics(self, llm_account):
        """Test performance metric calculations."""
        # Open and close 3 trades: 2 wins, 1 loss
        trades = [
            ("LONG", 3000, 3300),   # Win: +300 * 0.01 * 5 = +15
            ("LONG", 500, 550),     # Win: +50 * 0.06 * 5 = +15
            ("LONG", 400, 380)      # Loss: -20 * 0.075 * 5 = -7.5
        ]

        for i, (side, entry, exit) in enumerate(trades):
            pos = llm_account.open_position(
                symbol=f"ETH{i}USDT",
                side=side,
                entry_price=Decimal(str(entry)),
                quantity_usd=Decimal("30.00"),
                leverage=5
            )

            llm_account.close_position(
                position_id=pos.position_id,
                exit_price=Decimal(str(exit))
            )

        # Check metrics
        assert llm_account.total_trades == 3
        assert llm_account.winning_trades == 2
        assert llm_account.losing_trades == 1
        # Check win rate is approximately 66.67% (2/3)
        assert abs(llm_account.win_rate - Decimal("66.67")) < Decimal("0.01")


# ============================================================================
# RiskManager Tests
# ============================================================================

class TestRiskManager:
    """Tests for RiskManager class."""

    def test_validate_hold(self, risk_manager, llm_account):
        """Test HOLD validation (always valid)."""
        decision = {"action": "HOLD"}

        is_valid, error = risk_manager.validate_decision(
            decision,
            llm_account,
            {}
        )

        assert is_valid is True
        assert error == ""

    def test_validate_invalid_symbol(self, risk_manager, llm_account):
        """Test invalid symbol rejection."""
        decision = {
            "action": "BUY",
            "symbol": "INVALID",
            "quantity_usd": 20,
            "leverage": 3
        }

        is_valid, error = risk_manager.validate_decision(
            decision,
            llm_account,
            {"INVALID": Decimal("100")}
        )

        assert is_valid is False
        assert "not in allowed list" in error

    def test_validate_max_positions(self, risk_manager, llm_account):
        """Test max positions limit."""
        # Fill account to max positions
        for i in range(3):
            llm_account.open_position(
                symbol=f"ETH{i}USDT",
                side="LONG",
                entry_price=Decimal("3000"),
                quantity_usd=Decimal("10"),
                leverage=1
            )

        decision = {
            "action": "BUY",
            "symbol": "BNBUSDT",
            "quantity_usd": 20,
            "leverage": 3
        }

        is_valid, error = risk_manager.validate_decision(
            decision,
            llm_account,
            {"BNBUSDT": Decimal("500")}
        )

        assert is_valid is False
        assert "Maximum positions reached" in error

    def test_validate_insufficient_balance(self, risk_manager, llm_account):
        """Test insufficient balance rejection."""
        # Use valid trade size (40) but leverage that requires more margin than available
        decision = {
            "action": "BUY",
            "symbol": "ETHUSDT",
            "quantity_usd": 40,  # Max trade size (valid)
            "leverage": 1  # Requires $40 margin, but only $30 available after opening first position
        }

        # Open a position to reduce available balance
        llm_account.open_position(
            symbol="BNBUSDT",
            side="LONG",
            entry_price=Decimal("500"),
            quantity_usd=Decimal("30"),
            leverage=1  # Uses $30 margin, leaving $70 available
        )

        # Now try to open $40 position with 1x leverage (needs $40, have $70)
        # This should fail if we use 2x the initial balance
        llm_account.balance_usdt = Decimal("30")  # Manually reduce to test

        is_valid, error = risk_manager.validate_decision(
            decision,
            llm_account,
            {"ETHUSDT": Decimal("3000")}
        )

        assert is_valid is False
        assert "Insufficient balance" in error

    def test_validate_leverage_limits(self, risk_manager, llm_account):
        """Test leverage limit enforcement."""
        decision = {
            "action": "BUY",
            "symbol": "ETHUSDT",
            "quantity_usd": 20,
            "leverage": 15  # Above max of 10
        }

        is_valid, error = risk_manager.validate_decision(
            decision,
            llm_account,
            {"ETHUSDT": Decimal("3000")}
        )

        assert is_valid is False
        assert "Leverage" in error
        assert "10x" in error


# ============================================================================
# TradeExecutor Tests
# ============================================================================

class TestTradeExecutor:
    """Tests for TradeExecutor class."""

    def test_execute_hold(self, trade_executor, llm_account):
        """Test HOLD execution."""
        decision = {
            "action": "HOLD",
            "reasoning": "Waiting for better opportunities"
        }

        result = trade_executor.execute_decision(
            decision,
            llm_account,
            {}
        )

        assert result["status"] == "SUCCESS"
        assert result["action"] == "HOLD"

    def test_execute_buy_success(self, trade_executor, llm_account):
        """Test successful BUY execution."""
        decision = {
            "action": "BUY",
            "symbol": "ETHUSDT",
            "quantity_usd": 30.0,
            "leverage": 5,
            "stop_loss_pct": 5.0,
            "take_profit_pct": 10.0,
            "reasoning": "Strong uptrend",
            "confidence": 0.8
        }

        prices = {"ETHUSDT": Decimal("3000.00")}

        result = trade_executor.execute_decision(
            decision,
            llm_account,
            prices
        )

        assert result["status"] == "SUCCESS"
        assert result["action"] == "BUY"
        assert result["symbol"] == "ETHUSDT"
        assert result["side"] == "LONG"
        assert len(llm_account.open_positions) == 1

    def test_execute_rejected(self, trade_executor, llm_account):
        """Test rejected execution."""
        decision = {
            "action": "BUY",
            "symbol": "INVALID",
            "quantity_usd": 30.0,
            "leverage": 5
        }

        prices = {"ETHUSDT": Decimal("3000.00")}

        result = trade_executor.execute_decision(
            decision,
            llm_account,
            prices
        )

        assert result["status"] == "REJECTED"
        assert "not in allowed list" in result["reason"]


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
