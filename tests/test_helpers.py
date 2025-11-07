"""
Tests críticos para helpers.py.

Estos tests validan las funciones financieras más importantes
para prevenir errores que podrían causar pérdidas reales.
"""

import pytest
from src.utils.helpers import (
    calculate_pnl,
    calculate_pnl_percentage,
    calculate_liquidation_price,
    calculate_position_value,
    calculate_required_margin,
    calculate_fees,
    calculate_risk_reward_ratio,
    format_usd,
    round_down,
    round_up,
    safe_divide,
    calculate_percentage_change,
    validate_symbol,
)


class TestCriticalCalculations:
    """Tests críticos de cálculos financieros."""

    def test_calculate_pnl_long(self):
        """Test P&L de posición LONG."""
        # Ganancia
        pnl = calculate_pnl(entry_price=100, current_price=110, quantity=1.0, side="LONG")
        assert pnl == 10.0

        # Pérdida
        pnl = calculate_pnl(entry_price=100, current_price=90, quantity=1.0, side="LONG")
        assert pnl == -10.0

    def test_calculate_pnl_short(self):
        """Test P&L de posición SHORT."""
        # Ganancia (precio baja)
        pnl = calculate_pnl(entry_price=100, current_price=90, quantity=1.0, side="SHORT")
        assert pnl == 10.0

        # Pérdida (precio sube)
        pnl = calculate_pnl(entry_price=100, current_price=110, quantity=1.0, side="SHORT")
        assert pnl == -10.0

    def test_calculate_liquidation_price_long(self):
        """
        Test CRÍTICO: precio de liquidación para LONG.
        Error aquí = liquidación inesperada.
        """
        liq_price = calculate_liquidation_price(
            entry_price=100,
            leverage=10,
            side="LONG"
        )
        # Con 10x leverage, liquidación aproximadamente en 90.4
        assert 90 < liq_price < 91

    def test_calculate_liquidation_price_short(self):
        """
        Test CRÍTICO: precio de liquidación para SHORT.
        Error aquí = liquidación inesperada.
        """
        liq_price = calculate_liquidation_price(
            entry_price=100,
            leverage=10,
            side="SHORT"
        )
        # Con 10x leverage, liquidación aproximadamente en 110.4
        assert 109 < liq_price < 111

    def test_calculate_required_margin(self):
        """
        Test CRÍTICO: cálculo de margen requerido.
        Error aquí = overdraft o insuficiente margen.
        """
        # Posición de $1000 con 10x leverage requiere $100 margin
        margin = calculate_required_margin(notional_value=1000, leverage=10)
        assert margin == 100.0

        # Sin leverage
        margin = calculate_required_margin(notional_value=1000, leverage=1)
        assert margin == 1000.0

    def test_calculate_fees(self):
        """Test cálculo de fees."""
        # Fee 0.05% sobre $1000 = $0.50
        fees = calculate_fees(notional_value=1000, fee_rate=0.0005)
        assert fees == 0.5

    def test_calculate_risk_reward_ratio_long(self):
        """Test risk/reward ratio para LONG."""
        # Entry 100, SL 95, TP 110 = Risk $5, Reward $10 = Ratio 2:1
        ratio = calculate_risk_reward_ratio(
            entry_price=100,
            stop_loss=95,
            take_profit=110,
            side="LONG"
        )
        assert ratio == 2.0

    def test_calculate_risk_reward_ratio_short(self):
        """Test risk/reward ratio para SHORT."""
        # Entry 100, SL 105, TP 90 = Risk $5, Reward $10 = Ratio 2:1
        ratio = calculate_risk_reward_ratio(
            entry_price=100,
            stop_loss=105,
            take_profit=90,
            side="SHORT"
        )
        assert ratio == 2.0


class TestSafeOperations:
    """Tests de operaciones seguras."""

    def test_safe_divide_normal(self):
        """Test división normal."""
        result = safe_divide(10, 2)
        assert result == 5.0

    def test_safe_divide_by_zero(self):
        """Test CRÍTICO: división por cero debe retornar default."""
        result = safe_divide(10, 0, default=0.0)
        assert result == 0.0

    def test_round_down(self):
        """Test CRÍTICO: round down para evitar exceder cantidades."""
        assert round_down(0.123456789, 6) == 0.123456
        assert round_down(1.999999, 2) == 1.99

    def test_round_up(self):
        """Test CRÍTICO: round up para asegurar margen suficiente."""
        assert round_up(0.123456789, 6) == 0.123457
        assert round_up(1.000001, 2) == 1.01


class TestFormatting:
    """Tests de formateo (menos críticos pero útiles)."""

    def test_format_usd(self):
        """Test formateo de USD."""
        assert format_usd(1234.567) == "$1,234.57"
        assert format_usd(0.1) == "$0.10"

    def test_calculate_percentage_change(self):
        """Test cambio porcentual."""
        change = calculate_percentage_change(100, 110)
        assert change == 10.0

        change = calculate_percentage_change(100, 90)
        assert change == -10.0


class TestValidation:
    """Tests de validación."""

    def test_validate_symbol(self):
        """Test validación de símbolos."""
        allowed = ["ETHUSDT", "BTCUSDT"]

        assert validate_symbol("ETHUSDT", allowed) is True
        assert validate_symbol("ethusdt", allowed) is True  # Case insensitive
        assert validate_symbol("DOGEUSDT", allowed) is False
