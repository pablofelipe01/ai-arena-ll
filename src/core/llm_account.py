"""
LLMAccount class - Manages virtual trading account for each LLM.

Each LLM has a virtual $100 USDT balance and can trade independently.
This class tracks balance, positions, trades, and performance metrics.
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime
import uuid

from src.utils.logger import app_logger


class Position:
    """Represents an open trading position."""

    def __init__(
        self,
        position_id: str,
        symbol: str,
        side: str,  # "LONG" or "SHORT"
        entry_price: Decimal,
        quantity: Decimal,
        leverage: int,
        stop_loss_pct: Optional[Decimal] = None,
        take_profit_pct: Optional[Decimal] = None,
        opened_at: Optional[datetime] = None
    ):
        """
        Initialize a position.

        Args:
            position_id: Unique position identifier
            symbol: Trading symbol (e.g., "ETHUSDT")
            side: "LONG" or "SHORT"
            entry_price: Entry price in USDT
            quantity: Position quantity (e.g., 0.01 ETH)
            leverage: Leverage used (1x-10x)
            stop_loss_pct: Stop loss percentage (optional)
            take_profit_pct: Take profit percentage (optional)
            opened_at: Position opening timestamp
        """
        self.position_id = position_id
        self.symbol = symbol
        self.side = side
        self.entry_price = entry_price
        self.quantity = quantity
        self.leverage = leverage
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.opened_at = opened_at or datetime.utcnow()

        # Calculate position value and margin
        self.position_value_usd = entry_price * quantity
        self.margin_used = self.position_value_usd / Decimal(leverage)

        # Calculate stop loss and take profit prices
        if stop_loss_pct:
            if side == "LONG":
                self.stop_loss_price = entry_price * (1 - stop_loss_pct / 100)
            else:  # SHORT
                self.stop_loss_price = entry_price * (1 + stop_loss_pct / 100)
        else:
            self.stop_loss_price = None

        if take_profit_pct:
            if side == "LONG":
                self.take_profit_price = entry_price * (1 + take_profit_pct / 100)
            else:  # SHORT
                self.take_profit_price = entry_price * (1 - take_profit_pct / 100)
        else:
            self.take_profit_price = None

    def calculate_pnl(self, current_price: Decimal) -> Dict[str, Decimal]:
        """
        Calculate current PnL for this position.

        Args:
            current_price: Current market price

        Returns:
            Dict with unrealized_pnl_usd, unrealized_pnl_pct, roi_pct
        """
        if self.side == "LONG":
            price_change = current_price - self.entry_price
        else:  # SHORT
            price_change = self.entry_price - current_price

        # PnL = price_change * quantity * leverage
        unrealized_pnl_usd = price_change * self.quantity * Decimal(self.leverage)

        # PnL percentage relative to margin used
        unrealized_pnl_pct = (unrealized_pnl_usd / self.margin_used) * 100

        # ROI relative to entry value
        roi_pct = (price_change / self.entry_price) * 100 * Decimal(self.leverage)

        return {
            "unrealized_pnl_usd": unrealized_pnl_usd,
            "unrealized_pnl_pct": unrealized_pnl_pct,
            "roi_pct": roi_pct
        }

    def calculate_liquidation_price(self) -> Decimal:
        """
        Calculate liquidation price for this position.

        Simplified calculation: assumes 100% loss of margin.
        """
        # Loss percentage that triggers liquidation (100% of margin)
        liquidation_loss_pct = Decimal("100") / Decimal(self.leverage)

        if self.side == "LONG":
            liquidation_price = self.entry_price * (1 - liquidation_loss_pct / 100)
        else:  # SHORT
            liquidation_price = self.entry_price * (1 + liquidation_loss_pct / 100)

        return liquidation_price

    def should_stop_loss(self, current_price: Decimal) -> bool:
        """Check if stop loss should trigger."""
        if not self.stop_loss_price:
            return False

        if self.side == "LONG":
            return current_price <= self.stop_loss_price
        else:  # SHORT
            return current_price >= self.stop_loss_price

    def should_take_profit(self, current_price: Decimal) -> bool:
        """Check if take profit should trigger."""
        if not self.take_profit_price:
            return False

        if self.side == "LONG":
            return current_price >= self.take_profit_price
        else:  # SHORT
            return current_price <= self.take_profit_price

    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary."""
        return {
            "position_id": self.position_id,
            "symbol": self.symbol,
            "side": self.side,
            "entry_price": float(self.entry_price),
            "quantity": float(self.quantity),
            "leverage": self.leverage,
            "position_value_usd": float(self.position_value_usd),
            "margin_used": float(self.margin_used),
            "stop_loss_pct": float(self.stop_loss_pct) if self.stop_loss_pct else None,
            "take_profit_pct": float(self.take_profit_pct) if self.take_profit_pct else None,
            "stop_loss_price": float(self.stop_loss_price) if self.stop_loss_price else None,
            "take_profit_price": float(self.take_profit_price) if self.take_profit_price else None,
            "liquidation_price": float(self.calculate_liquidation_price()),
            "opened_at": self.opened_at.isoformat()
        }


class Trade:
    """Represents a completed trade."""

    def __init__(
        self,
        trade_id: str,
        symbol: str,
        side: str,
        entry_price: Decimal,
        exit_price: Decimal,
        quantity: Decimal,
        leverage: int,
        pnl_usd: Decimal,
        pnl_pct: Decimal,
        opened_at: datetime,
        closed_at: datetime,
        exit_reason: str  # "MANUAL", "STOP_LOSS", "TAKE_PROFIT", "LIQUIDATION"
    ):
        """Initialize a completed trade."""
        self.trade_id = trade_id
        self.symbol = symbol
        self.side = side
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.quantity = quantity
        self.leverage = leverage
        self.pnl_usd = pnl_usd
        self.pnl_pct = pnl_pct
        self.opened_at = opened_at
        self.closed_at = closed_at
        self.exit_reason = exit_reason
        self.duration_seconds = (closed_at - opened_at).total_seconds()

    def is_winner(self) -> bool:
        """Check if trade was profitable."""
        return self.pnl_usd > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert trade to dictionary."""
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "side": self.side,
            "entry_price": float(self.entry_price),
            "exit_price": float(self.exit_price),
            "quantity": float(self.quantity),
            "leverage": self.leverage,
            "pnl_usd": float(self.pnl_usd),
            "pnl_pct": float(self.pnl_pct),
            "opened_at": self.opened_at.isoformat(),
            "closed_at": self.closed_at.isoformat(),
            "exit_reason": self.exit_reason,
            "duration_seconds": self.duration_seconds,
            "is_winner": self.is_winner()
        }


class LLMAccount:
    """
    Virtual trading account for an LLM.

    Each LLM starts with $100 USDT and trades independently.
    Tracks balance, positions, trades, and performance.
    """

    def __init__(
        self,
        llm_id: str,
        initial_balance: Decimal = Decimal("100.00"),
        max_positions: int = 3
    ):
        """
        Initialize LLM account.

        Args:
            llm_id: LLM identifier ("LLM-A", "LLM-B", "LLM-C")
            initial_balance: Starting balance in USDT
            max_positions: Maximum simultaneous positions
        """
        self.llm_id = llm_id
        self.initial_balance = initial_balance
        self.max_positions = max_positions

        # Account balances
        self.balance_usdt = initial_balance  # Available balance
        self.margin_used = Decimal("0")  # Margin locked in positions
        self.unrealized_pnl = Decimal("0")  # Unrealized PnL from open positions

        # Positions and trades
        self.open_positions: Dict[str, Position] = {}  # position_id -> Position
        self.closed_trades: List[Trade] = []

        # Performance metrics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_realized_pnl = Decimal("0")

        app_logger.info(f"{llm_id}: Account initialized with ${initial_balance} USDT")

    @property
    def equity_usdt(self) -> Decimal:
        """Total equity = balance + margin_used + unrealized_pnl."""
        return self.balance_usdt + self.margin_used + self.unrealized_pnl

    @property
    def available_balance(self) -> Decimal:
        """Balance available for new trades."""
        return self.balance_usdt

    @property
    def total_pnl(self) -> Decimal:
        """Total PnL = realized + unrealized."""
        return self.total_realized_pnl + self.unrealized_pnl

    @property
    def total_pnl_pct(self) -> Decimal:
        """Total PnL as percentage of initial balance."""
        return (self.total_pnl / self.initial_balance) * 100

    @property
    def win_rate(self) -> Decimal:
        """Win rate percentage."""
        if self.total_trades == 0:
            return Decimal("0")
        return (Decimal(self.winning_trades) / Decimal(self.total_trades)) * 100

    def can_open_position(self) -> bool:
        """Check if can open a new position."""
        return len(self.open_positions) < self.max_positions

    def has_position_for_symbol(self, symbol: str) -> bool:
        """Check if already has an open position for this symbol."""
        return any(pos.symbol == symbol for pos in self.open_positions.values())

    def get_position_by_symbol(self, symbol: str) -> Optional[Position]:
        """Get open position for a symbol."""
        for pos in self.open_positions.values():
            if pos.symbol == symbol:
                return pos
        return None

    def open_position(
        self,
        symbol: str,
        side: str,
        entry_price: Decimal,
        quantity_usd: Decimal,
        leverage: int,
        stop_loss_pct: Optional[Decimal] = None,
        take_profit_pct: Optional[Decimal] = None
    ) -> Position:
        """
        Open a new position.

        Args:
            symbol: Trading symbol
            side: "LONG" or "SHORT"
            entry_price: Entry price
            quantity_usd: Position size in USD
            leverage: Leverage to use
            stop_loss_pct: Stop loss percentage (optional)
            take_profit_pct: Take profit percentage (optional)

        Returns:
            Opened Position

        Raises:
            ValueError: If cannot open position
        """
        # Validate
        if not self.can_open_position():
            raise ValueError(f"Maximum positions ({self.max_positions}) reached")

        if self.has_position_for_symbol(symbol):
            raise ValueError(f"Already have open position for {symbol}")

        # Calculate margin required
        margin_required = quantity_usd / Decimal(leverage)

        if margin_required > self.available_balance:
            raise ValueError(
                f"Insufficient balance: need ${margin_required}, have ${self.available_balance}"
            )

        # Calculate quantity (amount of crypto)
        quantity = quantity_usd / entry_price

        # Create position
        position_id = str(uuid.uuid4())
        position = Position(
            position_id=position_id,
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            leverage=leverage,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct
        )

        # Update account state
        self.open_positions[position_id] = position
        self.balance_usdt -= margin_required
        self.margin_used += margin_required

        app_logger.info(
            f"{self.llm_id}: Opened {side} position - "
            f"{symbol} @ ${entry_price}, "
            f"Size: ${quantity_usd}, "
            f"Leverage: {leverage}x, "
            f"Margin: ${margin_required}"
        )

        return position

    def close_position(
        self,
        position_id: str,
        exit_price: Decimal,
        exit_reason: str = "MANUAL"
    ) -> Trade:
        """
        Close an open position.

        Args:
            position_id: Position to close
            exit_price: Exit price
            exit_reason: Reason for closing

        Returns:
            Completed Trade

        Raises:
            ValueError: If position not found
        """
        if position_id not in self.open_positions:
            raise ValueError(f"Position {position_id} not found")

        position = self.open_positions[position_id]

        # Calculate PnL
        pnl_data = position.calculate_pnl(exit_price)
        pnl_usd = pnl_data["unrealized_pnl_usd"]
        pnl_pct = pnl_data["unrealized_pnl_pct"]

        # Create trade record
        trade = Trade(
            trade_id=position_id,
            symbol=position.symbol,
            side=position.side,
            entry_price=position.entry_price,
            exit_price=exit_price,
            quantity=position.quantity,
            leverage=position.leverage,
            pnl_usd=pnl_usd,
            pnl_pct=pnl_pct,
            opened_at=position.opened_at,
            closed_at=datetime.utcnow(),
            exit_reason=exit_reason
        )

        # Update account state
        returned_margin = position.margin_used
        self.balance_usdt += returned_margin + pnl_usd
        self.margin_used -= returned_margin

        # Update metrics
        self.total_trades += 1
        self.total_realized_pnl += pnl_usd

        if trade.is_winner():
            self.winning_trades += 1
        else:
            self.losing_trades += 1

        # Store trade and remove position
        self.closed_trades.append(trade)
        del self.open_positions[position_id]

        app_logger.info(
            f"{self.llm_id}: Closed {position.side} position - "
            f"{position.symbol}, "
            f"PnL: ${pnl_usd:.2f} ({pnl_pct:.2f}%), "
            f"Reason: {exit_reason}"
        )

        return trade

    def update_unrealized_pnl(self, market_prices: Dict[str, Decimal]) -> None:
        """
        Update unrealized PnL for all open positions.

        Args:
            market_prices: Dict of symbol -> current_price
        """
        total_unrealized = Decimal("0")

        for position in self.open_positions.values():
            if position.symbol in market_prices:
                current_price = market_prices[position.symbol]
                pnl_data = position.calculate_pnl(current_price)
                total_unrealized += pnl_data["unrealized_pnl_usd"]

        self.unrealized_pnl = total_unrealized

    def get_recent_trades(self, limit: int = 5) -> List[Trade]:
        """Get most recent trades."""
        return self.closed_trades[-limit:]

    def to_dict(self) -> Dict[str, Any]:
        """Convert account to dictionary."""
        return {
            "llm_id": self.llm_id,
            "balance_usdt": float(self.balance_usdt),
            "margin_used": float(self.margin_used),
            "unrealized_pnl": float(self.unrealized_pnl),
            "equity_usdt": float(self.equity_usdt),
            "available_balance": float(self.available_balance),
            "total_pnl": float(self.total_pnl),
            "total_pnl_pct": float(self.total_pnl_pct),
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": float(self.win_rate),
            "open_positions": len(self.open_positions),
            "max_positions": self.max_positions,
            "can_open_position": self.can_open_position()
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<LLMAccount {self.llm_id} "
            f"equity=${self.equity_usdt:.2f} "
            f"pnl=${self.total_pnl:.2f} "
            f"positions={len(self.open_positions)}/{self.max_positions}>"
        )
