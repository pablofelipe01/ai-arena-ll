"""
Custom exceptions para el sistema de trading multi-LLM.

Jerarquía de excepciones:
- TradingSystemError (base)
  - ConfigurationError
  - BinanceAPIError
    - BinanceConnectionError
  - LLMAPIError
    - LLMTimeoutError
    - LLMResponseParseError
  - TradingError
    - InsufficientBalanceError
    - InvalidOrderError
    - PositionNotFoundError
  - RiskLimitExceededError
    - MaxPositionsReachedError
    - MaxLeverageExceededError
    - MaxMarginUsageExceededError
  - DatabaseError
    - DatabaseConnectionError
  - ValidationError
    - InvalidSymbolError
    - InvalidQuantityError
"""


class TradingSystemError(Exception):
    """Excepción base para todos los errores del sistema de trading."""
    pass


# ============================================
# CONFIGURATION ERRORS
# ============================================

class ConfigurationError(TradingSystemError):
    """Error de configuración del sistema."""
    pass


# ============================================
# BINANCE API ERRORS
# ============================================

class BinanceAPIError(TradingSystemError):
    """Error en la API de Binance."""

    def __init__(self, message: str, code: int = None, response: dict = None):
        self.code = code
        self.response = response
        super().__init__(f"Binance API Error (code={code}): {message}")


class BinanceConnectionError(BinanceAPIError):
    """Error de conexión con Binance."""

    def __init__(self, message: str = "Could not connect to Binance API"):
        super().__init__(message)


# ============================================
# LLM API ERRORS
# ============================================

class LLMAPIError(TradingSystemError):
    """Error en API de LLM."""

    def __init__(self, llm_id: str, message: str, provider: str = None):
        self.llm_id = llm_id
        self.provider = provider
        super().__init__(f"LLM {llm_id} ({provider}): {message}")


class LLMTimeoutError(LLMAPIError):
    """Timeout en llamada a LLM."""

    def __init__(self, llm_id: str, provider: str, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        super().__init__(
            llm_id,
            f"API call timed out after {timeout_seconds} seconds",
            provider
        )


class LLMResponseParseError(LLMAPIError):
    """Error al parsear respuesta del LLM."""

    def __init__(self, llm_id: str, provider: str, raw_response: str, error: str):
        self.raw_response = raw_response
        self.parse_error = error
        super().__init__(
            llm_id,
            f"Failed to parse LLM response: {error}",
            provider
        )


# ============================================
# TRADING ERRORS
# ============================================

class TradingError(TradingSystemError):
    """Error base para operaciones de trading."""
    pass


class InsufficientBalanceError(TradingError):
    """Balance insuficiente para ejecutar operación."""

    def __init__(self, llm_id: str, required: float, available: float):
        self.llm_id = llm_id
        self.required = required
        self.available = available
        super().__init__(
            f"{llm_id}: Insufficient balance. Required: ${required:.2f}, Available: ${available:.2f}"
        )


class InvalidOrderError(TradingError):
    """Orden inválida."""

    def __init__(self, llm_id: str, reason: str, order_data: dict = None):
        self.llm_id = llm_id
        self.reason = reason
        self.order_data = order_data
        super().__init__(f"{llm_id}: Invalid order - {reason}")


class PositionNotFoundError(TradingError):
    """Posición no encontrada."""

    def __init__(self, llm_id: str, position_id: str = None, symbol: str = None):
        self.llm_id = llm_id
        self.position_id = position_id
        self.symbol = symbol

        if position_id:
            msg = f"{llm_id}: Position not found (ID: {position_id})"
        elif symbol:
            msg = f"{llm_id}: No open position found for {symbol}"
        else:
            msg = f"{llm_id}: Position not found"

        super().__init__(msg)


# ============================================
# RISK MANAGEMENT ERRORS
# ============================================

class RiskLimitExceededError(TradingError):
    """Límite de riesgo excedido."""

    def __init__(self, llm_id: str, reason: str, details: dict = None):
        self.llm_id = llm_id
        self.reason = reason
        self.details = details or {}
        super().__init__(f"{llm_id}: Risk limit exceeded - {reason}")


class MaxPositionsReachedError(RiskLimitExceededError):
    """Máximo de posiciones alcanzado."""

    def __init__(self, llm_id: str, current_positions: int, max_positions: int):
        self.current_positions = current_positions
        self.max_positions = max_positions
        super().__init__(
            llm_id,
            f"Maximum positions reached ({current_positions}/{max_positions})",
            {'current': current_positions, 'max': max_positions}
        )


class MaxLeverageExceededError(RiskLimitExceededError):
    """Leverage excede el máximo permitido."""

    def __init__(self, llm_id: str, requested_leverage: int, max_leverage: int):
        self.requested_leverage = requested_leverage
        self.max_leverage = max_leverage
        super().__init__(
            llm_id,
            f"Leverage too high ({requested_leverage}x > {max_leverage}x max)",
            {'requested': requested_leverage, 'max': max_leverage}
        )


class MaxMarginUsageExceededError(RiskLimitExceededError):
    """Uso de margen excede el máximo permitido."""

    def __init__(
        self,
        llm_id: str,
        current_margin: float,
        additional_margin: float,
        total_balance: float,
        max_usage_pct: float
    ):
        self.current_margin = current_margin
        self.additional_margin = additional_margin
        self.total_balance = total_balance
        self.max_usage_pct = max_usage_pct

        total_margin = current_margin + additional_margin
        usage_pct = (total_margin / total_balance) * 100 if total_balance > 0 else 0

        super().__init__(
            llm_id,
            f"Margin usage too high ({usage_pct:.1f}% > {max_usage_pct*100:.0f}% max)",
            {
                'current_margin': current_margin,
                'additional_margin': additional_margin,
                'total_margin': total_margin,
                'total_balance': total_balance,
                'usage_pct': usage_pct,
                'max_usage_pct': max_usage_pct * 100
            }
        )


class TradeSizeLimitExceededError(RiskLimitExceededError):
    """Tamaño del trade excede límites permitidos."""

    def __init__(
        self,
        llm_id: str,
        trade_size_usd: float,
        min_size: float = None,
        max_size: float = None
    ):
        self.trade_size_usd = trade_size_usd
        self.min_size = min_size
        self.max_size = max_size

        if trade_size_usd < min_size:
            reason = f"Trade size too small (${trade_size_usd:.2f} < ${min_size:.2f} minimum)"
        elif trade_size_usd > max_size:
            reason = f"Trade size too large (${trade_size_usd:.2f} > ${max_size:.2f} maximum)"
        else:
            reason = f"Trade size out of range: ${trade_size_usd:.2f}"

        super().__init__(
            llm_id,
            reason,
            {'trade_size': trade_size_usd, 'min': min_size, 'max': max_size}
        )


# ============================================
# DATABASE ERRORS
# ============================================

class DatabaseError(TradingSystemError):
    """Error de base de datos."""

    def __init__(self, message: str, query: str = None, original_error: Exception = None):
        self.query = query
        self.original_error = original_error
        super().__init__(f"Database error: {message}")


class DatabaseConnectionError(DatabaseError):
    """Error de conexión a la base de datos."""

    def __init__(self, message: str = "Could not connect to database"):
        super().__init__(message)


# ============================================
# VALIDATION ERRORS
# ============================================

class ValidationError(TradingSystemError):
    """Error de validación."""
    pass


class InvalidSymbolError(ValidationError):
    """Símbolo no válido o no soportado."""

    def __init__(self, symbol: str, allowed_symbols: list = None):
        self.symbol = symbol
        self.allowed_symbols = allowed_symbols

        msg = f"Invalid symbol: {symbol}"
        if allowed_symbols:
            msg += f". Allowed symbols: {', '.join(allowed_symbols)}"

        super().__init__(msg)


class InvalidQuantityError(ValidationError):
    """Cantidad inválida."""

    def __init__(self, quantity: float, reason: str = None):
        self.quantity = quantity
        self.reason = reason

        msg = f"Invalid quantity: {quantity}"
        if reason:
            msg += f" - {reason}"

        super().__init__(msg)


class InvalidPriceError(ValidationError):
    """Precio inválido."""

    def __init__(self, price: float, reason: str = None):
        self.price = price
        self.reason = reason

        msg = f"Invalid price: {price}"
        if reason:
            msg += f" - {reason}"

        super().__init__(msg)
