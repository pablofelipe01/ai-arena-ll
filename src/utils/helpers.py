"""
Funciones auxiliares y utilidades para el sistema de trading multi-LLM.

Incluye:
- Formateo de moneda y cripto
- Cálculos financieros (P&L, liquidation price, margin, fees)
- Precision y rounding
- Timestamps y fechas
- Validación de símbolos
- Comparaciones seguras
- Risk calculations (Sharpe ratio, risk/reward, etc.)
"""

from decimal import Decimal, ROUND_DOWN, ROUND_UP
from typing import Union, List, Tuple
from datetime import datetime
import pytz


# ============================================
# FORMATEO DE MONEDA
# ============================================

def format_usd(amount: Union[float, Decimal], decimals: int = 2) -> str:
    """
    Formatear cantidad como USD.

    Args:
        amount: Cantidad a formatear
        decimals: Número de decimales

    Returns:
        String formateado con símbolo $

    Example:
        >>> format_usd(1234.567)
        '$1,234.57'
    """
    return f"${amount:,.{decimals}f}"


def format_crypto(amount: Union[float, Decimal], symbol: str = "") -> str:
    """
    Formatear cantidad cripto con precisión apropiada.

    Args:
        amount: Cantidad a formatear
        symbol: Símbolo de la criptomoneda

    Returns:
        String formateado con símbolo

    Example:
        >>> format_crypto(0.001234, "BTC")
        '0.001234 BTC'
    """
    if amount >= 1:
        formatted = f"{amount:.6f}".rstrip('0').rstrip('.')
    else:
        formatted = f"{amount:.8f}".rstrip('0').rstrip('.')

    return f"{formatted} {symbol}".strip()


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Formatear como porcentaje.

    Args:
        value: Valor a formatear (ej: 5.5 para 5.5%)
        decimals: Número de decimales

    Returns:
        String formateado con símbolo %

    Example:
        >>> format_percentage(5.5)
        '5.50%'
    """
    return f"{value:.{decimals}f}%"


# ============================================
# CÁLCULOS FINANCIEROS
# ============================================

def calculate_pnl(
    entry_price: float,
    current_price: float,
    quantity: float,
    side: str
) -> float:
    """
    Calcular P&L de una posición.

    Args:
        entry_price: Precio de entrada
        current_price: Precio actual
        quantity: Cantidad
        side: Lado de la posición ('LONG', 'BUY', 'SHORT', 'SELL')

    Returns:
        P&L en USDT

    Example:
        >>> calculate_pnl(100, 105, 1.0, "LONG")
        5.0
    """
    if side.upper() in ["LONG", "BUY"]:
        return (current_price - entry_price) * quantity
    else:  # SHORT, SELL
        return (entry_price - current_price) * quantity


def calculate_pnl_percentage(entry_price: float, current_price: float, side: str) -> float:
    """
    Calcular P&L en porcentaje.

    Args:
        entry_price: Precio de entrada
        current_price: Precio actual
        side: Lado de la posición

    Returns:
        P&L en porcentaje

    Example:
        >>> calculate_pnl_percentage(100, 105, "LONG")
        5.0
    """
    if side.upper() in ["LONG", "BUY"]:
        return ((current_price - entry_price) / entry_price) * 100
    else:  # SHORT, SELL
        return ((entry_price - current_price) / entry_price) * 100


def calculate_liquidation_price(
    entry_price: float,
    leverage: int,
    side: str,
    maintenance_margin_rate: float = 0.004  # 0.4% para la mayoría en Binance
) -> float:
    """
    Calcular precio de liquidación aproximado.

    Args:
        entry_price: Precio de entrada
        leverage: Leverage utilizado
        side: Lado de la posición
        maintenance_margin_rate: Tasa de margen de mantenimiento

    Returns:
        Precio de liquidación estimado

    Example:
        >>> calculate_liquidation_price(100, 10, "LONG")
        90.4
    """
    if side.upper() in ["LONG", "BUY"]:
        # Long: liquidation cuando price cae
        return entry_price * (1 - (1/leverage) + maintenance_margin_rate)
    else:  # SHORT, SELL
        # Short: liquidation cuando price sube
        return entry_price * (1 + (1/leverage) - maintenance_margin_rate)


def calculate_position_value(quantity: float, price: float) -> float:
    """
    Calcular valor nocional de posición.

    Args:
        quantity: Cantidad
        price: Precio

    Returns:
        Valor nocional en USDT
    """
    return quantity * price


def calculate_required_margin(notional_value: float, leverage: int) -> float:
    """
    Calcular margen requerido.

    Args:
        notional_value: Valor nocional de la posición
        leverage: Leverage utilizado

    Returns:
        Margen requerido en USDT
    """
    return notional_value / leverage


def calculate_fees(notional_value: float, fee_rate: float = 0.0005) -> float:
    """
    Calcular fees de trading.

    Args:
        notional_value: Valor nocional de la operación
        fee_rate: Tasa de comisión (default: 0.05% taker fee en Binance)

    Returns:
        Fees en USDT
    """
    return notional_value * fee_rate


def calculate_position_size(
    balance: float,
    price: float,
    max_position_pct: float,
    leverage: int = 1
) -> float:
    """
    Calcular tamaño de posición basado en balance y % máximo.

    Args:
        balance: Balance disponible
        price: Precio del activo
        max_position_pct: % máximo del balance a usar (ej: 0.40 para 40%)
        leverage: Leverage a utilizar

    Returns:
        Cantidad a comprar/vender
    """
    max_size_usd = balance * max_position_pct
    quantity = (max_size_usd * leverage) / price
    return quantity


# ============================================
# PRECISION Y ROUNDING
# ============================================

def round_down(value: float, decimals: int = 8) -> float:
    """
    Round down para evitar exceder cantidades máximas.

    Args:
        value: Valor a redondear
        decimals: Número de decimales

    Returns:
        Valor redondeado hacia abajo
    """
    multiplier = Decimal(10 ** decimals)
    return float(Decimal(str(value)) * multiplier // 1 / multiplier)


def round_up(value: float, decimals: int = 8) -> float:
    """
    Round up para asegurar margen suficiente.

    Args:
        value: Valor a redondear
        decimals: Número de decimales

    Returns:
        Valor redondeado hacia arriba
    """
    multiplier = Decimal(10 ** decimals)
    return float((Decimal(str(value)) * multiplier).quantize(Decimal('1'), rounding=ROUND_UP) / multiplier)


def adjust_quantity_to_step_size(quantity: float, step_size: float) -> float:
    """
    Ajustar cantidad a step size de Binance.

    Args:
        quantity: Cantidad original
        step_size: Step size del símbolo

    Returns:
        Cantidad ajustada

    Example:
        >>> adjust_quantity_to_step_size(0.001234, 0.0001)
        0.0012
    """
    return round_down(quantity / step_size) * step_size


def round_to_precision(value: float, precision: int = 8) -> Decimal:
    """
    Redondear a precisión específica usando Decimal.

    Args:
        value: Valor a redondear
        precision: Número de decimales

    Returns:
        Decimal redondeado
    """
    return Decimal(str(value)).quantize(Decimal(10) ** -precision)


# ============================================
# TIMESTAMPS Y FECHAS
# ============================================

def utc_now() -> datetime:
    """
    Datetime actual en UTC.

    Returns:
        Datetime en UTC
    """
    return datetime.now(pytz.UTC)


def format_timestamp(dt: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Formatear timestamp.

    Args:
        dt: Datetime a formatear
        format: Formato del string

    Returns:
        String formateado
    """
    return dt.strftime(format)


def milliseconds_since_epoch(dt: datetime = None) -> int:
    """
    Convertir datetime a milisegundos desde epoch (para Binance API).

    Args:
        dt: Datetime a convertir (si None, usa tiempo actual)

    Returns:
        Milisegundos desde epoch
    """
    if dt is None:
        dt = utc_now()
    return int(dt.timestamp() * 1000)


def timestamp_to_datetime(timestamp: int) -> datetime:
    """
    Convertir timestamp de Binance a datetime UTC.

    Args:
        timestamp: Timestamp en milisegundos

    Returns:
        Datetime en UTC
    """
    return datetime.fromtimestamp(timestamp / 1000, tz=pytz.UTC)


def datetime_to_timestamp(dt: datetime) -> int:
    """
    Convertir datetime a timestamp de Binance.

    Args:
        dt: Datetime a convertir

    Returns:
        Timestamp en milisegundos
    """
    return int(dt.timestamp() * 1000)


def get_current_timestamp() -> int:
    """
    Obtener timestamp actual en milisegundos.

    Returns:
        Timestamp actual
    """
    return milliseconds_since_epoch()


# ============================================
# VALIDACIÓN DE SÍMBOLOS
# ============================================

def validate_symbol(symbol: str, allowed_pairs: List[str]) -> bool:
    """
    Validar que símbolo está en lista permitida.

    Args:
        symbol: Símbolo a validar
        allowed_pairs: Lista de símbolos permitidos

    Returns:
        True si es válido, False si no
    """
    return symbol.upper() in [p.upper() for p in allowed_pairs]


def parse_symbol(symbol: str) -> Tuple[str, str]:
    """
    Parsear símbolo en base y quote.

    Args:
        symbol: Símbolo a parsear (ej: 'ETHUSDT')

    Returns:
        Tupla (base, quote)

    Example:
        >>> parse_symbol("ETHUSDT")
        ('ETH', 'USDT')
    """
    # Para USDT pairs
    if symbol.endswith("USDT"):
        return (symbol[:-4], "USDT")
    # Para BUSD pairs
    elif symbol.endswith("BUSD"):
        return (symbol[:-4], "BUSD")
    else:
        raise ValueError(f"Unknown quote currency in {symbol}")


# ============================================
# COMPARACIONES SEGURAS
# ============================================

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    División segura que retorna default si denominator es 0.

    Args:
        numerator: Numerador
        denominator: Denominador
        default: Valor por defecto si división falla

    Returns:
        Resultado de la división o default
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (ZeroDivisionError, TypeError):
        return default


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Calcular cambio porcentual.

    Args:
        old_value: Valor anterior
        new_value: Valor nuevo

    Returns:
        Cambio porcentual

    Example:
        >>> calculate_percentage_change(100, 105)
        5.0
    """
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100


# ============================================
# RISK CALCULATIONS
# ============================================

def calculate_risk_reward_ratio(
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    side: str
) -> float:
    """
    Calcular ratio risk:reward.

    Args:
        entry_price: Precio de entrada
        stop_loss: Precio de stop loss
        take_profit: Precio de take profit
        side: Lado de la posición

    Returns:
        Ratio risk:reward

    Example:
        >>> calculate_risk_reward_ratio(100, 95, 110, "LONG")
        2.0  # Risk $5 para ganar $10
    """
    if side.upper() in ["LONG", "BUY"]:
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
    else:  # SHORT, SELL
        risk = abs(stop_loss - entry_price)
        reward = abs(entry_price - take_profit)

    return safe_divide(reward, risk, default=0.0)


def calculate_sharpe_ratio(
    returns: List[float],
    risk_free_rate: float = 0.0
) -> float:
    """
    Calcular Sharpe ratio.

    Args:
        returns: Lista de retornos periódicos
        risk_free_rate: Tasa libre de riesgo

    Returns:
        Sharpe ratio

    Note:
        Requiere numpy. Retorna 0.0 si no hay suficientes datos.
    """
    if not returns or len(returns) < 2:
        return 0.0

    try:
        import numpy as np

        returns_array = np.array(returns)
        excess_returns = returns_array - risk_free_rate

        if np.std(excess_returns) == 0:
            return 0.0

        return float(np.mean(excess_returns) / np.std(excess_returns))
    except ImportError:
        # Si numpy no está disponible, calcular manualmente
        if len(returns) < 2:
            return 0.0

        mean_return = sum(returns) / len(returns) - risk_free_rate
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5

        return safe_divide(mean_return, std_dev, default=0.0)


def calculate_max_drawdown(equity_curve: List[float]) -> float:
    """
    Calcular maximum drawdown.

    Args:
        equity_curve: Lista de valores de equity a través del tiempo

    Returns:
        Maximum drawdown (valor negativo)

    Example:
        >>> calculate_max_drawdown([100, 110, 105, 95, 100])
        -13.64  # Desde 110 a 95
    """
    if not equity_curve or len(equity_curve) < 2:
        return 0.0

    max_drawdown = 0.0
    peak = equity_curve[0]

    for value in equity_curve:
        if value > peak:
            peak = value

        drawdown = ((value - peak) / peak) * 100
        if drawdown < max_drawdown:
            max_drawdown = drawdown

    return max_drawdown


def calculate_win_rate(winning_trades: int, total_trades: int) -> float:
    """
    Calcular win rate.

    Args:
        winning_trades: Número de trades ganadores
        total_trades: Número total de trades

    Returns:
        Win rate en porcentaje
    """
    return safe_divide(winning_trades, total_trades, default=0.0) * 100


# ============================================
# UTILIDADES ADICIONALES
# ============================================

def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    Limitar valor entre mínimo y máximo.

    Args:
        value: Valor a limitar
        min_value: Valor mínimo
        max_value: Valor máximo

    Returns:
        Valor limitado
    """
    return max(min_value, min(value, max_value))


def is_within_range(value: float, min_value: float, max_value: float) -> bool:
    """
    Verificar si valor está dentro de un rango.

    Args:
        value: Valor a verificar
        min_value: Valor mínimo
        max_value: Valor máximo

    Returns:
        True si está dentro del rango
    """
    return min_value <= value <= max_value
