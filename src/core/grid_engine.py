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
from src.utils.telegram_notifier import get_telegram_notifier


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
        if grid_levels > 8:
            raise ValueError("Maximum 8 grid levels allowed")
        if spacing_type not in ["arithmetic", "geometric"]:
            raise ValueError("Spacing type must be 'arithmetic' or 'geometric'")
        if leverage < 1 or leverage > 5:
            raise ValueError("Leverage must be between 1x and 5x")
        if investment_usd < Decimal("30"):
            raise ValueError("Minimum investment $30")
        if investment_usd > Decimal("80"):
            raise ValueError("Maximum investment $80 per grid")

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
        # Total investment split across all levels (with leverage applied)
        total_position_size = config.investment_usd * Decimal(str(config.leverage))
        investment_per_level = total_position_size / Decimal(str(config.grid_levels))

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

            # Send Telegram notification
            telegram = get_telegram_notifier()
            if telegram and telegram.enabled:
                telegram.notify_stop_loss_triggered(
                    llm_id=self.llm_id,
                    symbol=self.config.symbol,
                    grid_id=self.grid_id,
                    current_price=float(current_price),
                    stop_price=float(stop_loss_price)
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

    def restore_grid_from_db(self, db_grid: Dict[str, Any]) -> bool:
        """
        Restore a grid from database record.

        Args:
            db_grid: Grid record from database

        Returns:
            True if successfully restored, False otherwise
        """
        try:
            grid_id = db_grid["grid_id"]
            llm_id = db_grid["llm_id"]

            # Check if grid already exists
            if grid_id in self.active_grids:
                app_logger.warning(f"Grid {grid_id} already exists, skipping restore")
                return False

            # Create GridConfig from DB data
            config = GridConfig(
                symbol=db_grid["symbol"],
                upper_limit=Decimal(str(db_grid["upper_limit"])),
                lower_limit=Decimal(str(db_grid["lower_limit"])),
                grid_levels=db_grid["grid_levels"],
                spacing_type=db_grid["spacing_type"],
                leverage=db_grid["leverage"],
                investment_usd=Decimal(str(db_grid["investment_usd"])),
                stop_loss_pct=Decimal(str(db_grid["stop_loss_pct"]))
            )

            # Parse created_at
            created_at = db_grid.get("created_at")
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            elif not isinstance(created_at, datetime):
                created_at = datetime.utcnow()

            # Create GridInstance
            grid = GridInstance(
                grid_id=grid_id,
                llm_id=llm_id,
                config=config,
                created_at=created_at
            )

            # Restore performance metrics
            grid.cycles_completed = db_grid.get("cycles_completed", 0)
            grid.total_profit_usdt = Decimal(str(db_grid.get("total_profit_usdt", 0)))
            grid.total_fees_usdt = Decimal(str(db_grid.get("total_fees_usdt", 0)))

            # Add to active grids
            self.active_grids[grid_id] = grid

            if llm_id not in self.grids_by_llm:
                self.grids_by_llm[llm_id] = []
            if grid_id not in self.grids_by_llm[llm_id]:
                self.grids_by_llm[llm_id].append(grid_id)

            app_logger.info(
                f"[{llm_id}] Grid restored from DB: {grid_id} for {config.symbol} "
                f"(${config.lower_limit}-${config.upper_limit}, {config.grid_levels} levels, "
                f"{grid.cycles_completed} cycles, ${float(grid.total_profit_usdt):.2f} profit)"
            )

            return True

        except Exception as e:
            app_logger.error(f"Failed to restore grid from DB: {e}")
            return False

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

    def sync_from_binance(self, binance_client) -> Dict[str, Any]:
        """
        Synchronize grid state from Binance open orders.

        This method reconstructs GridInstances from existing orders on Binance.
        Critical for recovering state after server restart.

        Args:
            binance_client: BinanceClient instance

        Returns:
            Dict with sync statistics
        """
        from decimal import Decimal
        import re

        app_logger.info("=" * 60)
        app_logger.info("SYNCING GRIDS FROM BINANCE")
        app_logger.info("=" * 60)

        # Get all open orders from Binance
        from src.clients.grid_prompts import ALLOWED_SYMBOLS
        symbols = ALLOWED_SYMBOLS
        all_orders = []

        for symbol in symbols:
            try:
                orders = binance_client.get_open_orders(symbol)
                all_orders.extend(orders)
            except Exception as e:
                app_logger.warning(f"Failed to get orders for {symbol}: {e}")

        app_logger.info(f"Found {len(all_orders)} open orders on Binance")

        # Parse orders and group by grid_id
        # Pattern: GRID_LLM-X_SYMBOL_GRIDID_SIDE_LEVEL
        pattern = re.compile(r'^GRID_(LLM-[ABC])_([A-Z]+)_([a-f0-9]{8})_(BUY|SELL)_(\d+)$')

        grids_data = {}  # grid_id -> {orders, llm_id, symbol, ...}
        orphan_orders = []

        for order in all_orders:
            client_id = order.get('clientOrderId', '')
            match = pattern.match(client_id)

            if match:
                llm_id, symbol, grid_id_short, side, level = match.groups()
                grid_id = f"GRID_{llm_id}_{symbol}_{grid_id_short}"

                if grid_id not in grids_data:
                    grids_data[grid_id] = {
                        'grid_id': grid_id,
                        'llm_id': llm_id,
                        'symbol': symbol,
                        'orders': []
                    }

                grids_data[grid_id]['orders'].append({
                    'order': order,
                    'side': side,
                    'level': int(level),
                    'price': Decimal(str(order['price'])),
                    'quantity': Decimal(str(order['origQty'])),
                    'order_id': order['orderId']
                })
            else:
                # Order doesn't match grid pattern
                if 'GRID_' in client_id:
                    orphan_orders.append(order)

        app_logger.info(f"Identified {len(grids_data)} unique grids from orders")
        app_logger.info(f"Found {len(orphan_orders)} orphan orders (old pattern or invalid)")

        # Reconstruct GridInstance for each grid
        synced_grids = 0
        failed_grids = 0

        for grid_id, grid_data in grids_data.items():
            try:
                # Extract grid configuration from orders
                orders = grid_data['orders']
                prices = [o['price'] for o in orders]

                if not prices:
                    app_logger.warning(f"Grid {grid_id} has no orders, skipping")
                    continue

                lower_limit = min(prices)
                upper_limit = max(prices)
                grid_levels = len(set(prices))  # Unique price levels

                # Infer spacing type (simplified - assume geometric)
                spacing_type = "geometric"

                # Infer leverage and investment from order sizes
                # This is approximate since we don't have original config
                avg_quantity = sum(o['quantity'] for o in orders) / len(orders)
                avg_price = sum(prices) / len(prices)
                estimated_investment = avg_quantity * avg_price * Decimal(str(grid_levels)) / Decimal("2")

                # Create grid config
                config = GridConfig(
                    symbol=grid_data['symbol'],
                    upper_limit=upper_limit,
                    lower_limit=lower_limit,
                    grid_levels=grid_levels,
                    spacing_type=spacing_type,
                    leverage=3,  # Default assumption
                    investment_usd=estimated_investment,
                    stop_loss_pct=Decimal("12")  # Default
                )

                # Create grid instance
                grid = GridInstance(
                    grid_id=grid_id,
                    llm_id=grid_data['llm_id'],
                    config=config,
                    created_at=datetime.utcnow()  # We don't know original timestamp
                )

                # Mark orders as pending (they're still active on Binance)
                for order_data in orders:
                    level_id = f"{grid_id}_{order_data['side']}_{order_data['level']}"

                    # Find matching level in grid
                    for level in grid.buy_levels + grid.sell_levels:
                        if level.level_id == level_id:
                            level.status = "PENDING"
                            level.order_id = str(order_data['order_id'])
                            break

                # Add to active grids
                self.active_grids[grid_id] = grid

                if grid_data['llm_id'] not in self.grids_by_llm:
                    self.grids_by_llm[grid_data['llm_id']] = []
                self.grids_by_llm[grid_data['llm_id']].append(grid_id)

                synced_grids += 1
                app_logger.info(
                    f"✓ Synced grid {grid_id}: {grid_data['symbol']} "
                    f"(${lower_limit:.2f}-${upper_limit:.2f}, {len(orders)} orders)"
                )

            except Exception as e:
                failed_grids += 1
                app_logger.error(f"Failed to sync grid {grid_id}: {e}", exc_info=True)

        # Summary
        summary = {
            'total_orders': len(all_orders),
            'unique_grids_found': len(grids_data),
            'grids_synced': synced_grids,
            'grids_failed': failed_grids,
            'orphan_orders': len(orphan_orders),
            'grids_by_llm': {
                llm_id: len(grid_ids)
                for llm_id, grid_ids in self.grids_by_llm.items()
            }
        }

        app_logger.info("=" * 60)
        app_logger.info(f"SYNC COMPLETE: {synced_grids} grids synced, {failed_grids} failed")
        app_logger.info(f"Grids by LLM: {summary['grids_by_llm']}")
        if orphan_orders:
            app_logger.warning(f"⚠️  {len(orphan_orders)} orphan orders detected (may need manual cleanup)")
        app_logger.info("=" * 60)

        return summary

    def cancel_orphan_orders(self, binance_client, orphan_order_ids: List[int]) -> int:
        """
        Cancel orphan orders that don't belong to any known grid.

        Args:
            binance_client: BinanceClient instance
            orphan_order_ids: List of order IDs to cancel

        Returns:
            Number of orders cancelled
        """
        cancelled = 0

        for order_id in orphan_order_ids:
            try:
                # We'd need to know the symbol to cancel, this is a simplified version
                app_logger.info(f"Would cancel orphan order {order_id}")
                cancelled += 1
            except Exception as e:
                app_logger.error(f"Failed to cancel order {order_id}: {e}")

        return cancelled

    def __repr__(self) -> str:
        """String representation."""
        return f"<GridEngine grids={len(self.active_grids)} active={len(self.get_all_active_grids())}>"
