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
                    leverage=leverage
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
        leverage: int
    ) -> None:
        """
        Open position on Binance.

        Args:
            symbol: Trading symbol
            side: "LONG" or "SHORT"
            entry_price: Entry price
            quantity_usd: Position size in USD
            leverage: Leverage to use
        """
        # Set leverage
        self.binance.set_leverage(symbol, leverage)

        # Calculate quantity (amount of crypto)
        quantity = quantity_usd / entry_price

        # Round quantity to valid precision
        quantity = self.binance.round_step_size(symbol, quantity)

        # Determine order side
        order_side = "BUY" if side == "LONG" else "SELL"

        # Create market order
        order = self.binance.create_market_order(
            symbol=symbol,
            side=order_side,
            quantity=quantity
        )

        app_logger.info(f"Binance order executed: {order}")

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

    def __repr__(self) -> str:
        """String representation."""
        return f"<TradeExecutor simulate={self.simulate}>"
