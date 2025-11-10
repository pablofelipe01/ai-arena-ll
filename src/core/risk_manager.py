"""
Risk Manager - Validates and enforces risk limits for trading decisions.

Ensures all trading decisions comply with:
- Position limits
- Leverage limits
- Balance requirements
- Symbol restrictions
- Trade size limits
"""

from typing import Dict, Any, Tuple
from decimal import Decimal

from src.core.llm_account import LLMAccount
from src.clients.prompts import ALLOWED_SYMBOLS, MAX_LEVERAGE, MIN_TRADE_SIZE, MAX_TRADE_SIZE
from src.utils.logger import app_logger


class RiskManager:
    """
    Risk manager for validating trading decisions.

    Enforces all risk limits before allowing trade execution.
    """

    def __init__(self):
        """Initialize risk manager."""
        self.allowed_symbols = ALLOWED_SYMBOLS
        self.max_leverage = MAX_LEVERAGE
        self.min_trade_size = Decimal(str(MIN_TRADE_SIZE))
        self.max_trade_size = Decimal(str(MAX_TRADE_SIZE))

    def validate_decision(
        self,
        decision: Dict[str, Any],
        account: LLMAccount,
        current_prices: Dict[str, Decimal]
    ) -> Tuple[bool, str]:
        """
        Validate a trading decision against all risk limits.

        Args:
            decision: LLM trading decision
            account: LLM account state
            current_prices: Current market prices

        Returns:
            Tuple of (is_valid, error_message)
            If valid: (True, "")
            If invalid: (False, "error description")
        """
        action = decision["action"]

        # HOLD is always valid
        if action == "HOLD":
            return True, ""

        symbol = decision.get("symbol")

        # Validate symbol
        if not symbol:
            return False, "Missing symbol for trading action"

        if symbol not in self.allowed_symbols:
            return False, f"Symbol {symbol} not in allowed list: {self.allowed_symbols}"

        # Check if price data available
        if symbol not in current_prices:
            return False, f"No price data available for {symbol}"

        # CLOSE validation
        if action == "CLOSE":
            return self._validate_close(symbol, account)

        # BUY/SELL validation
        if action in ["BUY", "SELL"]:
            return self._validate_open(decision, account, current_prices[symbol])

        return False, f"Invalid action: {action}"

    def _validate_close(
        self,
        symbol: str,
        account: LLMAccount
    ) -> Tuple[bool, str]:
        """
        Validate CLOSE action.

        Args:
            symbol: Symbol to close
            account: LLM account

        Returns:
            (is_valid, error_message)
        """
        # Check if position exists
        if not account.has_position_for_symbol(symbol):
            return False, f"No open position for {symbol} to close"

        return True, ""

    def _validate_open(
        self,
        decision: Dict[str, Any],
        account: LLMAccount,
        current_price: Decimal
    ) -> Tuple[bool, str]:
        """
        Validate BUY/SELL action.

        Args:
            decision: Trading decision
            account: LLM account
            current_price: Current market price

        Returns:
            (is_valid, error_message)
        """
        symbol = decision["symbol"]
        quantity_usd = Decimal(str(decision.get("quantity_usd", 0)))
        leverage = decision.get("leverage", 1)

        # Check if can open new position
        if not account.can_open_position():
            return False, (
                f"Maximum positions reached ({len(account.open_positions)}/{account.max_positions})"
            )

        # Check if already has position for this symbol
        if account.has_position_for_symbol(symbol):
            return False, f"Already have open position for {symbol}"

        # Validate trade size
        if quantity_usd < self.min_trade_size:
            return False, (
                f"Trade size ${quantity_usd} below minimum ${self.min_trade_size}"
            )

        if quantity_usd > self.max_trade_size:
            return False, (
                f"Trade size ${quantity_usd} exceeds maximum ${self.max_trade_size}"
            )

        # Validate leverage
        if leverage < 1 or leverage > self.max_leverage:
            return False, (
                f"Leverage {leverage}x outside allowed range (1x-{self.max_leverage}x)"
            )

        # Check balance
        margin_required = quantity_usd / Decimal(leverage)

        if margin_required > account.available_balance:
            return False, (
                f"Insufficient balance: need ${margin_required:.2f}, "
                f"have ${account.available_balance:.2f}"
            )

        # Validate stop loss and take profit percentages
        stop_loss_pct = decision.get("stop_loss_pct")
        if stop_loss_pct is not None:
            stop_loss_pct = Decimal(str(stop_loss_pct))
            if stop_loss_pct < 1 or stop_loss_pct > 20:
                return False, f"Stop loss {stop_loss_pct}% outside range (1-20%)"

        take_profit_pct = decision.get("take_profit_pct")
        if take_profit_pct is not None:
            take_profit_pct = Decimal(str(take_profit_pct))
            if take_profit_pct < 2 or take_profit_pct > 50:
                return False, f"Take profit {take_profit_pct}% outside range (2-50%)"

        return True, ""

    def check_stop_loss_triggers(
        self,
        account: LLMAccount,
        current_prices: Dict[str, Decimal]
    ) -> list[str]:
        """
        Check if any positions should trigger stop loss.

        Args:
            account: LLM account
            current_prices: Current market prices

        Returns:
            List of position_ids that should close due to stop loss
        """
        triggered_positions = []

        for position_id, position in account.open_positions.items():
            if position.symbol in current_prices:
                current_price = current_prices[position.symbol]

                if position.should_stop_loss(current_price):
                    triggered_positions.append(position_id)
                    app_logger.warning(
                        f"{account.llm_id}: Stop loss triggered for {position.symbol} "
                        f"at ${current_price} (SL: ${position.stop_loss_price})"
                    )

        return triggered_positions

    def check_take_profit_triggers(
        self,
        account: LLMAccount,
        current_prices: Dict[str, Decimal]
    ) -> list[str]:
        """
        Check if any positions should trigger take profit.

        Args:
            account: LLM account
            current_prices: Current market prices

        Returns:
            List of position_ids that should close due to take profit
        """
        triggered_positions = []

        for position_id, position in account.open_positions.items():
            if position.symbol in current_prices:
                current_price = current_prices[position.symbol]

                if position.should_take_profit(current_price):
                    triggered_positions.append(position_id)
                    app_logger.info(
                        f"{account.llm_id}: Take profit triggered for {position.symbol} "
                        f"at ${current_price} (TP: ${position.take_profit_price})"
                    )

        return triggered_positions

    def check_liquidation_risks(
        self,
        account: LLMAccount,
        current_prices: Dict[str, Decimal],
        warning_threshold_pct: Decimal = Decimal("90")
    ) -> list[Dict[str, Any]]:
        """
        Check for positions at risk of liquidation.

        Args:
            account: LLM account
            current_prices: Current market prices
            warning_threshold_pct: Warn if within this % of liquidation price

        Returns:
            List of positions at risk with details
        """
        at_risk = []

        for position_id, position in account.open_positions.items():
            if position.symbol in current_prices:
                current_price = current_prices[position.symbol]
                liquidation_price = position.calculate_liquidation_price()

                # Calculate distance to liquidation
                if position.side == "LONG":
                    distance_pct = ((current_price - liquidation_price) / liquidation_price) * 100
                else:  # SHORT
                    distance_pct = ((liquidation_price - current_price) / current_price) * 100

                # Warn if close to liquidation
                if distance_pct < warning_threshold_pct:
                    at_risk.append({
                        "position_id": position_id,
                        "symbol": position.symbol,
                        "side": position.side,
                        "current_price": current_price,
                        "liquidation_price": liquidation_price,
                        "distance_pct": distance_pct
                    })

                    app_logger.warning(
                        f"{account.llm_id}: Position {position.symbol} at liquidation risk! "
                        f"Current: ${current_price}, Liquidation: ${liquidation_price}, "
                        f"Distance: {distance_pct:.2f}%"
                    )

        return at_risk

    def get_max_position_size(
        self,
        account: LLMAccount,
        leverage: int
    ) -> Decimal:
        """
        Calculate maximum position size given current balance and leverage.

        Args:
            account: LLM account
            leverage: Desired leverage

        Returns:
            Maximum position size in USD
        """
        # Maximum based on available balance
        max_from_balance = account.available_balance * Decimal(leverage)

        # Cap at MAX_TRADE_SIZE
        return min(max_from_balance, self.max_trade_size)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<RiskManager "
            f"symbols={len(self.allowed_symbols)} "
            f"max_leverage={self.max_leverage}x "
            f"trade_size=${self.min_trade_size}-${self.max_trade_size}>"
        )
