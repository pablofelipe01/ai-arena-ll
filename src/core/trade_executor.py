"""
Trade Executor - Executes validated trading decisions.

Converts LLM decisions into actual Binance trades and updates account state.
"""

from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

from src.core.llm_account import LLMAccount, Position, Trade
from src.core.risk_manager import RiskManager
from src.clients.binance_client import BinanceClient
from src.utils.logger import app_logger
from src.utils.exceptions import TradingError


class TradeExecutor:
    """
    Executes trading decisions after risk validation.

    Workflow:
    1. Validate decision with RiskManager
    2. Execute on Binance (or simulate)
    3. Update LLMAccount state
    4. Return execution result
    """

    def __init__(
        self,
        binance_client: BinanceClient,
        risk_manager: RiskManager,
        simulate: bool = False
    ):
        """
        Initialize trade executor.

        Args:
            binance_client: Binance API client
            risk_manager: Risk manager for validation
            simulate: If True, simulate trades without real execution
        """
        self.binance = binance_client
        self.risk_manager = risk_manager
        self.simulate = simulate

        app_logger.info(f"TradeExecutor initialized (simulate={simulate})")

    def execute_decision(
        self,
        decision: Dict[str, Any],
        account: LLMAccount,
        current_prices: Optional[Dict[str, Decimal]] = None
    ) -> Dict[str, Any]:
        """
        Execute a trading decision.

        Args:
            decision: LLM trading decision
            account: LLM account
            current_prices: Current market prices (optional, will fetch if not provided)

        Returns:
            Execution result dict with status, message, and details

        Raises:
            TradingError: If execution fails
        """
        action = decision["action"]

        # Get current prices if not provided
        if current_prices is None:
            current_prices = self._fetch_current_prices()

        # Validate decision
        is_valid, error_msg = self.risk_manager.validate_decision(
            decision, account, current_prices
        )

        if not is_valid:
            app_logger.warning(
                f"{account.llm_id}: Decision rejected - {error_msg}"
            )
            return {
                "status": "REJECTED",
                "action": action,
                "reason": error_msg,
                "decision": decision
            }

        # Execute based on action
        if action == "HOLD":
            return self._execute_hold(decision, account)

        elif action == "CLOSE":
            return self._execute_close(decision, account, current_prices)

        elif action in ["BUY", "SELL"]:
            return self._execute_open(decision, account, current_prices)

        else:
            raise TradingError(f"Unknown action: {action}")

    def _execute_hold(
        self,
        decision: Dict[str, Any],
        account: LLMAccount
    ) -> Dict[str, Any]:
        """Execute HOLD decision."""
        app_logger.info(f"{account.llm_id}: HOLD - {decision.get('reasoning', 'N/A')}")

        return {
            "status": "SUCCESS",
            "action": "HOLD",
            "message": "No action taken",
            "reasoning": decision.get("reasoning"),
            "confidence": decision.get("confidence")
        }

    def _execute_close(
        self,
        decision: Dict[str, Any],
        account: LLMAccount,
        current_prices: Dict[str, Decimal]
    ) -> Dict[str, Any]:
        """Execute CLOSE decision."""
        symbol = decision["symbol"]
        position = account.get_position_by_symbol(symbol)

        if not position:
            raise TradingError(f"No position found for {symbol}")

        # Get current price
        exit_price = current_prices[symbol]

        # Execute on Binance (or simulate)
        if not self.simulate:
            try:
                # Close position on Binance
                self._close_binance_position(position, exit_price)
            except Exception as e:
                app_logger.error(f"{account.llm_id}: Failed to close position on Binance: {e}")
                raise TradingError(f"Binance execution failed: {e}")

        # Update account
        trade = account.close_position(
            position_id=position.position_id,
            exit_price=exit_price,
            exit_reason="MANUAL"
        )

        return {
            "status": "SUCCESS",
            "action": "CLOSE",
            "message": f"Closed {position.side} position for {symbol}",
            "symbol": symbol,
            "entry_price": float(position.entry_price),
            "exit_price": float(exit_price),
            "pnl_usd": float(trade.pnl_usd),
            "pnl_pct": float(trade.pnl_pct),
            "trade": trade.to_dict()
        }

    def _execute_open(
        self,
        decision: Dict[str, Any],
        account: LLMAccount,
        current_prices: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute BUY/SELL decision."""
        action = decision["action"]
        symbol = decision["symbol"]
        quantity_usd = Decimal(str(decision["quantity_usd"]))
        leverage = decision["leverage"]
        stop_loss_pct = decision.get("stop_loss_pct")
        take_profit_pct = decision.get("take_profit_pct")

        # Determine side
        side = "LONG" if action == "BUY" else "SHORT"

        # Get entry price
        entry_price = current_prices[symbol]

        # Execute on Binance (or simulate)
        if not self.simulate:
            try:
                self._open_binance_position(
                    symbol=symbol,
                    side=side,
                    entry_price=entry_price,
                    quantity_usd=quantity_usd,
                    leverage=leverage,
                    llm_id=account.llm_id
                )
            except Exception as e:
                app_logger.error(f"{account.llm_id}: Failed to open position on Binance: {e}")
                raise TradingError(f"Binance execution failed: {e}")

        # Update account
        position = account.open_position(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity_usd=quantity_usd,
            leverage=leverage,
            stop_loss_pct=Decimal(str(stop_loss_pct)) if stop_loss_pct else None,
            take_profit_pct=Decimal(str(take_profit_pct)) if take_profit_pct else None
        )

        return {
            "status": "SUCCESS",
            "action": action,
            "message": f"Opened {side} position for {symbol}",
            "symbol": symbol,
            "side": side,
            "entry_price": float(entry_price),
            "quantity_usd": float(quantity_usd),
            "leverage": leverage,
            "margin_used": float(position.margin_used),
            "stop_loss_price": float(position.stop_loss_price) if position.stop_loss_price else None,
            "take_profit_price": float(position.take_profit_price) if position.take_profit_price else None,
            "position": position.to_dict(),
            "reasoning": decision.get("reasoning"),
            "confidence": decision.get("confidence")
        }

    def auto_close_triggers(
        self,
        account: LLMAccount,
        current_prices: Optional[Dict[str, Decimal]] = None
    ) -> list[Dict[str, Any]]:
        """
        Automatically close positions that hit stop loss or take profit.

        Args:
            account: LLM account
            current_prices: Current market prices (optional)

        Returns:
            List of execution results for auto-closed positions
        """
        # Get current prices if not provided
        if current_prices is None:
            current_prices = self._fetch_current_prices()

        results = []

        # Check stop losses
        sl_triggered = self.risk_manager.check_stop_loss_triggers(account, current_prices)
        for position_id in sl_triggered:
            position = account.open_positions[position_id]
            exit_price = current_prices[position.symbol]

            # Close position
            try:
                if not self.simulate:
                    self._close_binance_position(position, exit_price)

                trade = account.close_position(position_id, exit_price, "STOP_LOSS")

                results.append({
                    "status": "SUCCESS",
                    "action": "AUTO_CLOSE",
                    "trigger": "STOP_LOSS",
                    "symbol": position.symbol,
                    "pnl_usd": float(trade.pnl_usd),
                    "trade": trade.to_dict()
                })
            except Exception as e:
                app_logger.error(f"Failed to auto-close stop loss: {e}")
                results.append({
                    "status": "ERROR",
                    "trigger": "STOP_LOSS",
                    "error": str(e)
                })

        # Check take profits
        tp_triggered = self.risk_manager.check_take_profit_triggers(account, current_prices)
        for position_id in tp_triggered:
            position = account.open_positions[position_id]
            exit_price = current_prices[position.symbol]

            # Close position
            try:
                if not self.simulate:
                    self._close_binance_position(position, exit_price)

                trade = account.close_position(position_id, exit_price, "TAKE_PROFIT")

                results.append({
                    "status": "SUCCESS",
                    "action": "AUTO_CLOSE",
                    "trigger": "TAKE_PROFIT",
                    "symbol": position.symbol,
                    "pnl_usd": float(trade.pnl_usd),
                    "trade": trade.to_dict()
                })
            except Exception as e:
                app_logger.error(f"Failed to auto-close take profit: {e}")
                results.append({
                    "status": "ERROR",
                    "trigger": "TAKE_PROFIT",
                    "error": str(e)
                })

        return results

    def _fetch_current_prices(self) -> Dict[str, Decimal]:
        """
        Fetch current market prices for all symbols.

        Returns:
            Dict of symbol -> price
        """
        prices = {}

        for symbol in self.risk_manager.allowed_symbols:
            try:
                ticker = self.binance.get_ticker_price(symbol)
                prices[symbol] = Decimal(str(ticker["price"]))
            except Exception as e:
                app_logger.error(f"Failed to fetch price for {symbol}: {e}")

        return prices

    def _open_binance_position(
        self,
        symbol: str,
        side: str,
        entry_price: Decimal,
        quantity_usd: Decimal,
        leverage: int,
        llm_id: str
    ) -> None:
        """
        Open position on Binance.

        Args:
            symbol: Trading symbol
            side: "LONG" or "SHORT"
            entry_price: Entry price
            quantity_usd: Position size in USD
            leverage: Leverage to use
            llm_id: LLM identifier for tracking
        """
        # Set leverage
        self.binance.set_leverage(symbol, leverage)

        # Calculate quantity (amount of crypto)
        quantity = quantity_usd / entry_price

        # Round quantity to valid precision
        quantity = self.binance.round_step_size(symbol, quantity)

        # Determine order side
        order_side = "BUY" if side == "LONG" else "SELL"

        # Generate clientOrderId with LLM identifier
        # Format: LLM-A_BTCUSDT_1234567890
        import time
        client_order_id = f"{llm_id}_{symbol}_{int(time.time() * 1000)}"

        # Create market order with clientOrderId
        order = self.binance.create_market_order(
            symbol=symbol,
            side=order_side,
            quantity=quantity,
            newClientOrderId=client_order_id
        )

        app_logger.info(f"Binance order executed for {llm_id}: {order}")

    def _close_binance_position(
        self,
        position: Position,
        exit_price: Decimal
    ) -> None:
        """
        Close position on Binance.

        Args:
            position: Position to close
            exit_price: Exit price
        """
        # Determine closing side (opposite of position side)
        close_side = "SELL" if position.side == "LONG" else "BUY"

        # Round quantity
        quantity = self.binance.round_step_size(position.symbol, position.quantity)

        # Create market order to close
        order = self.binance.create_market_order(
            symbol=position.symbol,
            side=close_side,
            quantity=quantity,
            reduce_only=True
        )

        app_logger.info(f"Binance position closed: {order}")

    # ==================== GRID TRADING METHODS ====================

    def place_grid_orders(
        self,
        grid_instance: Any,
        llm_id: str
    ) -> Dict[str, Any]:
        """
        Place all grid orders (buy and sell limit orders) for a grid.

        Args:
            grid_instance: GridInstance from grid_engine
            llm_id: LLM identifier

        Returns:
            Dict with placement results
        """
        symbol = grid_instance.config.symbol
        leverage = grid_instance.config.leverage

        app_logger.info(
            f"[{llm_id}] Placing grid orders for {symbol}: "
            f"{len(grid_instance.buy_levels)} buy, {len(grid_instance.sell_levels)} sell"
        )

        placed_orders = []
        failed_orders = []

        # Set leverage
        try:
            if not self.simulate:
                self.binance.set_leverage(symbol, leverage)
        except Exception as e:
            app_logger.error(f"[{llm_id}] Failed to set leverage for {symbol}: {e}")
            return {
                "status": "ERROR",
                "message": f"Failed to set leverage: {e}",
                "placed": [],
                "failed": []
            }

        # Place buy orders
        for level in grid_instance.buy_levels:
            try:
                if not self.simulate:
                    # Round quantity and price
                    quantity = self.binance.round_step_size(symbol, level.quantity)
                    price = self.binance.round_tick_size(symbol, level.price)

                    # Place limit order
                    order = self.binance.create_limit_order(
                        symbol=symbol,
                        side="BUY",
                        quantity=quantity,
                        price=price,
                        newClientOrderId=level.level_id
                    )

                    level.order_id = order.get("orderId")
                    placed_orders.append({
                        "level_id": level.level_id,
                        "order_id": level.order_id,
                        "side": "BUY",
                        "price": float(price),
                        "quantity": float(quantity)
                    })

                    app_logger.debug(
                        f"[{llm_id}] Placed BUY order: {level.level_id} @ ${price}"
                    )
                else:
                    # Simulate
                    level.order_id = f"SIM_{level.level_id}"
                    placed_orders.append({
                        "level_id": level.level_id,
                        "order_id": level.order_id,
                        "side": "BUY",
                        "price": float(level.price),
                        "quantity": float(level.quantity)
                    })

            except Exception as e:
                app_logger.error(f"[{llm_id}] Failed to place BUY order {level.level_id}: {e}")
                failed_orders.append({
                    "level_id": level.level_id,
                    "side": "BUY",
                    "error": str(e)
                })

        # Place sell orders
        for level in grid_instance.sell_levels:
            try:
                if not self.simulate:
                    # Round quantity and price
                    quantity = self.binance.round_step_size(symbol, level.quantity)
                    price = self.binance.round_tick_size(symbol, level.price)

                    # Place limit order
                    order = self.binance.create_limit_order(
                        symbol=symbol,
                        side="SELL",
                        quantity=quantity,
                        price=price,
                        newClientOrderId=level.level_id
                    )

                    level.order_id = order.get("orderId")
                    placed_orders.append({
                        "level_id": level.level_id,
                        "order_id": level.order_id,
                        "side": "SELL",
                        "price": float(price),
                        "quantity": float(quantity)
                    })

                    app_logger.debug(
                        f"[{llm_id}] Placed SELL order: {level.level_id} @ ${price}"
                    )
                else:
                    # Simulate
                    level.order_id = f"SIM_{level.level_id}"
                    placed_orders.append({
                        "level_id": level.level_id,
                        "order_id": level.order_id,
                        "side": "SELL",
                        "price": float(level.price),
                        "quantity": float(level.quantity)
                    })

            except Exception as e:
                app_logger.error(f"[{llm_id}] Failed to place SELL order {level.level_id}: {e}")
                failed_orders.append({
                    "level_id": level.level_id,
                    "side": "SELL",
                    "error": str(e)
                })

        app_logger.info(
            f"[{llm_id}] Grid orders placed: {len(placed_orders)} success, {len(failed_orders)} failed"
        )

        return {
            "status": "SUCCESS" if len(placed_orders) > 0 else "ERROR",
            "message": f"Placed {len(placed_orders)} orders, {len(failed_orders)} failed",
            "placed": placed_orders,
            "failed": failed_orders
        }

    def monitor_grid_orders(
        self,
        grid_instance: Any,
        llm_id: str
    ) -> Dict[str, Any]:
        """
        Monitor grid orders and update filled levels.

        Args:
            grid_instance: GridInstance from grid_engine
            llm_id: LLM identifier

        Returns:
            Dict with monitoring results (filled orders, cycles detected)
        """
        symbol = grid_instance.config.symbol
        filled_orders = []
        cycles_detected = []

        # Get pending orders
        pending_levels = grid_instance.get_pending_orders()

        if not pending_levels:
            return {
                "filled_orders": [],
                "cycles_detected": [],
                "message": "No pending orders to monitor"
            }

        # Check order status on Binance
        for level in pending_levels:
            try:
                if not self.simulate and level.order_id:
                    # Query order status
                    order = self.binance.get_order(symbol, level.order_id)

                    if order["status"] == "FILLED":
                        # Mark level as filled
                        filled_price = Decimal(str(order["avgPrice"]))
                        filled_at = datetime.utcnow()

                        grid_instance.mark_level_filled(
                            level_id=level.level_id,
                            order_id=level.order_id,
                            filled_price=filled_price,
                            filled_at=filled_at
                        )

                        filled_orders.append({
                            "level_id": level.level_id,
                            "side": level.side,
                            "price": float(filled_price),
                            "quantity": float(level.quantity),
                            "filled_at": filled_at.isoformat()
                        })

                        app_logger.info(
                            f"[{llm_id}] Grid order filled: {level.side} @ ${filled_price}"
                        )

            except Exception as e:
                app_logger.error(
                    f"[{llm_id}] Failed to check order status for {level.level_id}: {e}"
                )

        # Detect completed cycles (buy + sell fills at adjacent levels)
        cycles_detected = self._detect_grid_cycles(grid_instance, llm_id)

        return {
            "filled_orders": filled_orders,
            "cycles_detected": cycles_detected,
            "message": f"{len(filled_orders)} fills, {len(cycles_detected)} cycles"
        }

    def _detect_grid_cycles(
        self,
        grid_instance: Any,
        llm_id: str
    ) -> list[Dict[str, Any]]:
        """
        Detect completed grid cycles (buy filled -> sell filled).

        A cycle is complete when:
        1. A buy order is filled
        2. The corresponding sell order above it is filled

        Args:
            grid_instance: GridInstance
            llm_id: LLM identifier

        Returns:
            List of detected cycles
        """
        cycles = []
        filled_buys = [level for level in grid_instance.buy_levels if level.status == "FILLED"]
        filled_sells = [level for level in grid_instance.sell_levels if level.status == "FILLED"]

        # Match buy-sell pairs
        for buy_level in filled_buys:
            # Find corresponding sell level (next price above buy)
            matching_sells = [
                sell for sell in filled_sells
                if sell.price > buy_level.price and sell.status == "FILLED"
            ]

            if matching_sells:
                # Take the closest sell above the buy
                sell_level = min(matching_sells, key=lambda s: s.price)

                # Calculate profit
                buy_price = buy_level.filled_price or buy_level.price
                sell_price = sell_level.filled_price or sell_level.price
                quantity = buy_level.quantity  # Assuming same quantity

                gross, fees, net = grid_instance.calculate_cycle_profit(
                    buy_price=buy_price,
                    sell_price=sell_price,
                    quantity=quantity
                )

                # Record cycle
                grid_instance.record_completed_cycle(
                    buy_price=buy_price,
                    sell_price=sell_price,
                    quantity=quantity
                )

                cycles.append({
                    "buy_level_id": buy_level.level_id,
                    "sell_level_id": sell_level.level_id,
                    "buy_price": float(buy_price),
                    "sell_price": float(sell_price),
                    "quantity": float(quantity),
                    "gross_profit": float(gross),
                    "fees": float(fees),
                    "net_profit": float(net)
                })

                app_logger.info(
                    f"[{llm_id}] Grid cycle #{grid_instance.cycles_completed}: "
                    f"Buy @ ${buy_price}, Sell @ ${sell_price}, "
                    f"Net profit: ${net:.4f}"
                )

                # Reset levels to PENDING for next cycle
                buy_level.status = "PENDING"
                sell_level.status = "PENDING"

        return cycles

    def cancel_grid_orders(
        self,
        grid_instance: Any,
        llm_id: str
    ) -> Dict[str, Any]:
        """
        Cancel all pending grid orders.

        Args:
            grid_instance: GridInstance
            llm_id: LLM identifier

        Returns:
            Cancellation results
        """
        symbol = grid_instance.config.symbol
        pending_orders = grid_instance.get_pending_orders()

        cancelled = []
        failed = []

        app_logger.info(
            f"[{llm_id}] Cancelling {len(pending_orders)} pending grid orders for {symbol}"
        )

        for level in pending_orders:
            try:
                if not self.simulate and level.order_id:
                    self.binance.cancel_order(symbol, level.order_id)

                level.status = "CANCELLED"
                cancelled.append(level.level_id)

                app_logger.debug(f"[{llm_id}] Cancelled order: {level.level_id}")

            except Exception as e:
                app_logger.error(f"[{llm_id}] Failed to cancel order {level.level_id}: {e}")
                failed.append({
                    "level_id": level.level_id,
                    "error": str(e)
                })

        return {
            "status": "SUCCESS" if len(cancelled) > 0 else "ERROR",
            "cancelled": cancelled,
            "failed": failed,
            "message": f"Cancelled {len(cancelled)} orders, {len(failed)} failed"
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"<TradeExecutor simulate={self.simulate}>"
