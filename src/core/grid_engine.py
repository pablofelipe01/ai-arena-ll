"""
Grid Trading Engine - Executes automated grid trading strategies.

Implements geometric and arithmetic grid spacing for capturing volatility
in sideways markets through systematic buy low / sell high cycles.
"""

from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime
import uuid

from src.utils.logger import app_logger
from src.utils.exceptions import TradingError


class GridLevel:
    """Represents a single level in the grid."""

    def __init__(
        self,
        level_id: str,
        price: Decimal,
        side: str,  # "BUY" or "SELL"
        quantity: Decimal,
        status: str = "PENDING"  # PENDING, FILLED, CANCELLED
    ):
        self.level_id = level_id
        self.price = price
        self.side = side
        self.quantity = quantity
        self.status = status
        self.order_id: Optional[str] = None
        self.filled_at: Optional[datetime] = None
        self.filled_price: Optional[Decimal] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level_id": self.level_id,
            "price": float(self.price),
            "side": self.side,
            "quantity": float(self.quantity),
            "status": self.status,
            "order_id": self.order_id,
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
            "filled_price": float(self.filled_price) if self.filled_price else None
        }


class GridConfig:
    """Configuration for a grid trading strategy."""

    def __init__(
        self,
        symbol: str,
        upper_limit: Decimal,
        lower_limit: Decimal,
        grid_levels: int,
        spacing_type: str,  # "arithmetic" or "geometric"
        leverage: int,
        investment_usd: Decimal,
        stop_loss_pct: Decimal
    ):
        self.symbol = symbol
        self.upper_limit = upper_limit
        self.lower_limit = lower_limit
        self.grid_levels = grid_levels
        self.spacing_type = spacing_type
        self.leverage = leverage
        self.investment_usd = investment_usd
        self.stop_loss_pct = stop_loss_pct

        # Validate
        if upper_limit <= lower_limit:
            raise ValueError("Upper limit must be greater than lower limit")
        if grid_levels < 5:
            raise ValueError("Minimum 5 grid levels required")
        if grid_levels > 50:
            raise ValueError("Maximum 50 grid levels allowed")
        if spacing_type not in ["arithmetic", "geometric"]:
            raise ValueError("Spacing type must be 'arithmetic' or 'geometric'")
        if leverage < 1 or leverage > 5:
            raise ValueError("Leverage must be between 1x and 5x")
        if investment_usd < Decimal("5"):
            raise ValueError("Minimum investment $5")
        if investment_usd > Decimal("10"):
            raise ValueError("Maximum investment $10 per grid")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "upper_limit": float(self.upper_limit),
            "lower_limit": float(self.lower_limit),
            "grid_levels": self.grid_levels,
            "spacing_type": self.spacing_type,
            "leverage": self.leverage,
            "investment_usd": float(self.investment_usd),
            "stop_loss_pct": float(self.stop_loss_pct)
        }


class GridInstance:
    """Active grid trading instance for a symbol."""

    def __init__(
        self,
        grid_id: str,
        llm_id: str,
        config: GridConfig,
        created_at: datetime
    ):
        self.grid_id = grid_id
        self.llm_id = llm_id
        self.config = config
        self.created_at = created_at
        self.status = "ACTIVE"  # ACTIVE, PAUSED, STOPPED

        # Grid levels
        self.buy_levels: List[GridLevel] = []
        self.sell_levels: List[GridLevel] = []

        # Performance tracking
        self.cycles_completed = 0
        self.total_profit_usdt = Decimal("0")
        self.total_fees_usdt = Decimal("0")
        self.last_update = created_at

        # Generate grid levels
        self._generate_grid_levels()

    def _generate_grid_levels(self):
        """Generate buy and sell grid levels based on configuration."""
        config = self.config

        if config.spacing_type == "arithmetic":
            # Arithmetic spacing: equal dollar intervals
            spacing = (config.upper_limit - config.lower_limit) / Decimal(str(config.grid_levels - 1))
            prices = [
                config.lower_limit + (spacing * Decimal(str(i)))
                for i in range(config.grid_levels)
            ]
        else:
            # Geometric spacing: equal percentage intervals
            ratio = (config.upper_limit / config.lower_limit) ** (Decimal("1") / Decimal(str(config.grid_levels - 1)))
            prices = [
                config.lower_limit * (ratio ** Decimal(str(i)))
                for i in range(config.grid_levels)
            ]

        # Calculate quantity per level
        # Total investment split across all levels
        investment_per_level = config.investment_usd / Decimal(str(config.grid_levels))

        # Generate buy and sell levels
        for i, price in enumerate(prices):
            quantity = investment_per_level / price

            # Create buy level (except at upper limit)
            if i < len(prices) - 1:
                buy_level = GridLevel(
                    level_id=f"{self.grid_id}_BUY_{i}",
                    price=price,
                    side="BUY",
                    quantity=quantity
                )
                self.buy_levels.append(buy_level)

            # Create sell level (except at lower limit)
            if i > 0:
                sell_level = GridLevel(
                    level_id=f"{self.grid_id}_SELL_{i}",
                    price=price,
                    side="SELL",
                    quantity=quantity
                )
                self.sell_levels.append(sell_level)

        app_logger.info(
            f"[{self.llm_id}] Grid {self.grid_id} generated: "
            f"{len(self.buy_levels)} buy levels, {len(self.sell_levels)} sell levels"
        )

    def get_pending_orders(self) -> List[GridLevel]:
        """Get all pending grid orders."""
        pending = []
        for level in self.buy_levels + self.sell_levels:
            if level.status == "PENDING":
                pending.append(level)
        return pending

    def get_filled_orders(self) -> List[GridLevel]:
        """Get all filled grid orders."""
        filled = []
        for level in self.buy_levels + self.sell_levels:
            if level.status == "FILLED":
                filled.append(level)
        return filled

    def mark_level_filled(
        self,
        level_id: str,
        order_id: str,
        filled_price: Decimal,
        filled_at: datetime
    ):
        """Mark a grid level as filled."""
        for level in self.buy_levels + self.sell_levels:
            if level.level_id == level_id:
                level.status = "FILLED"
                level.order_id = order_id
                level.filled_price = filled_price
                level.filled_at = filled_at
                app_logger.info(
                    f"[{self.llm_id}] Grid level filled: {level_id} @ ${filled_price}"
                )
                return

        app_logger.warning(f"[{self.llm_id}] Level {level_id} not found in grid {self.grid_id}")

    def calculate_cycle_profit(
        self,
        buy_price: Decimal,
        sell_price: Decimal,
        quantity: Decimal,
        fee_rate: Decimal = Decimal("0.0005")  # 0.05% Binance taker fee
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Calculate profit for a completed grid cycle.

        Returns:
            (gross_profit, total_fees, net_profit)
        """
        # Gross profit
        gross_profit = (sell_price - buy_price) * quantity

        # Fees (buy + sell)
        buy_fee = buy_price * quantity * fee_rate
        sell_fee = sell_price * quantity * fee_rate
        total_fees = buy_fee + sell_fee

        # Net profit
        net_profit = gross_profit - total_fees

        return gross_profit, total_fees, net_profit

    def record_completed_cycle(
        self,
        buy_price: Decimal,
        sell_price: Decimal,
        quantity: Decimal
    ):
        """Record a completed buy-sell cycle."""
        gross, fees, net = self.calculate_cycle_profit(buy_price, sell_price, quantity)

        self.cycles_completed += 1
        self.total_profit_usdt += net
        self.total_fees_usdt += fees
        self.last_update = datetime.utcnow()

        app_logger.info(
            f"[{self.llm_id}] Grid cycle completed: "
            f"Buy @ ${buy_price}, Sell @ ${sell_price}, "
            f"Net profit: ${net:.2f} (Cycle #{self.cycles_completed})"
        )

    def check_stop_loss(self, current_price: Decimal) -> bool:
        """Check if stop loss is triggered."""
        stop_loss_price = self.config.lower_limit * (Decimal("1") - self.config.stop_loss_pct / Decimal("100"))

        if current_price <= stop_loss_price:
            app_logger.warning(
                f"[{self.llm_id}] STOP LOSS TRIGGERED for grid {self.grid_id}: "
                f"Price ${current_price} <= Stop ${stop_loss_price}"
            )
            return True

        return False

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for this grid."""
        return {
            "grid_id": self.grid_id,
            "llm_id": self.llm_id,
            "symbol": self.config.symbol,
            "status": self.status,
            "cycles_completed": self.cycles_completed,
            "total_profit_usdt": float(self.total_profit_usdt),
            "total_fees_usdt": float(self.total_fees_usdt),
            "net_profit_usdt": float(self.total_profit_usdt - self.total_fees_usdt),
            "roi_pct": float((self.total_profit_usdt / self.config.investment_usd) * Decimal("100")) if self.config.investment_usd > 0 else 0,
            "avg_profit_per_cycle": float(self.total_profit_usdt / Decimal(str(self.cycles_completed))) if self.cycles_completed > 0 else 0,
            "created_at": self.created_at.isoformat(),
            "last_update": self.last_update.isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            **self.get_performance_metrics(),
            "config": self.config.to_dict(),
            "buy_levels": [level.to_dict() for level in self.buy_levels],
            "sell_levels": [level.to_dict() for level in self.sell_levels]
        }


class GridEngine:
    """
    Grid Trading Engine.

    Manages multiple active grids for different LLMs and symbols,
    executes grid orders, tracks performance, and handles lifecycle.
    """

    def __init__(self):
        """Initialize Grid Engine."""
        self.active_grids: Dict[str, GridInstance] = {}  # grid_id -> GridInstance
        self.grids_by_llm: Dict[str, List[str]] = {}  # llm_id -> [grid_ids]

        app_logger.info("GridEngine initialized")

    def create_grid(
        self,
        llm_id: str,
        config: GridConfig
    ) -> GridInstance:
        """
        Create a new grid trading instance.

        Args:
            llm_id: LLM identifier
            config: Grid configuration

        Returns:
            GridInstance
        """
        grid_id = f"GRID_{llm_id}_{config.symbol}_{uuid.uuid4().hex[:8]}"

        grid = GridInstance(
            grid_id=grid_id,
            llm_id=llm_id,
            config=config,
            created_at=datetime.utcnow()
        )

        self.active_grids[grid_id] = grid

        if llm_id not in self.grids_by_llm:
            self.grids_by_llm[llm_id] = []
        self.grids_by_llm[llm_id].append(grid_id)

        app_logger.info(
            f"[{llm_id}] Grid created: {grid_id} for {config.symbol} "
            f"(${config.lower_limit}-${config.upper_limit}, {config.grid_levels} levels)"
        )

        return grid

    def get_grid(self, grid_id: str) -> Optional[GridInstance]:
        """Get grid by ID."""
        return self.active_grids.get(grid_id)

    def get_llm_grids(self, llm_id: str) -> List[GridInstance]:
        """Get all grids for an LLM."""
        grid_ids = self.grids_by_llm.get(llm_id, [])
        return [self.active_grids[gid] for gid in grid_ids if gid in self.active_grids]

    def stop_grid(self, grid_id: str, reason: str = "MANUAL"):
        """Stop a grid."""
        grid = self.get_grid(grid_id)
        if grid:
            grid.status = "STOPPED"
            app_logger.info(f"[{grid.llm_id}] Grid {grid_id} stopped: {reason}")

    def pause_grid(self, grid_id: str):
        """Pause a grid."""
        grid = self.get_grid(grid_id)
        if grid:
            grid.status = "PAUSED"
            app_logger.info(f"[{grid.llm_id}] Grid {grid_id} paused")

    def resume_grid(self, grid_id: str):
        """Resume a paused grid."""
        grid = self.get_grid(grid_id)
        if grid and grid.status == "PAUSED":
            grid.status = "ACTIVE"
            app_logger.info(f"[{grid.llm_id}] Grid {grid_id} resumed")

    def get_all_active_grids(self) -> List[GridInstance]:
        """Get all active grids."""
        return [g for g in self.active_grids.values() if g.status == "ACTIVE"]

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all grids."""
        total_grids = len(self.active_grids)
        active_grids = len(self.get_all_active_grids())
        total_cycles = sum(g.cycles_completed for g in self.active_grids.values())
        total_profit = sum(g.total_profit_usdt for g in self.active_grids.values())

        # Per-LLM stats
        llm_stats = {}
        for llm_id in self.grids_by_llm.keys():
            grids = self.get_llm_grids(llm_id)
            llm_stats[llm_id] = {
                "total_grids": len(grids),
                "active_grids": len([g for g in grids if g.status == "ACTIVE"]),
                "total_cycles": sum(g.cycles_completed for g in grids),
                "total_profit": float(sum(g.total_profit_usdt for g in grids)),
                "avg_profit_per_grid": float(sum(g.total_profit_usdt for g in grids) / Decimal(str(len(grids)))) if grids else 0
            }

        return {
            "total_grids": total_grids,
            "active_grids": active_grids,
            "total_cycles_completed": total_cycles,
            "total_profit_usdt": float(total_profit),
            "llm_stats": llm_stats
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"<GridEngine grids={len(self.active_grids)} active={len(self.get_all_active_grids())}>"
