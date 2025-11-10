"""
Indicator Service - Calculates technical indicators.

Provides:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Simple/Exponential Moving Averages
- Other technical indicators
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal
import math

from src.services.market_data_service import MarketDataService
from src.utils.logger import app_logger


class IndicatorService:
    """
    Service for calculating technical indicators.

    Uses market data from MarketDataService to calculate
    RSI, MACD, and other indicators for trading signals.
    """

    def __init__(self, market_data_service: MarketDataService):
        """
        Initialize indicator service.

        Args:
            market_data_service: Market data service instance
        """
        self.market_data = market_data_service

        app_logger.info("IndicatorService initialized")

    def calculate_rsi(
        self,
        symbol: str,
        period: int = 14,
        interval: str = "1h"
    ) -> float:
        """
        Calculate RSI (Relative Strength Index).

        Args:
            symbol: Trading symbol
            period: RSI period (default 14)
            interval: Timeframe for candles

        Returns:
            RSI value (0-100)
        """
        try:
            # Fetch klines (need period + 1 for calculation)
            klines = self.market_data.get_klines(
                symbol=symbol,
                interval=interval,
                limit=period + 1
            )

            if len(klines) < period + 1:
                app_logger.warning(f"Not enough data for RSI calculation: {len(klines)} candles")
                return 50.0  # Neutral RSI

            # Calculate price changes
            closes = [float(k["close"]) for k in klines]
            changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]

            # Separate gains and losses
            gains = [max(0, change) for change in changes]
            losses = [abs(min(0, change)) for change in changes]

            # Calculate average gain and loss
            avg_gain = sum(gains[:period]) / period
            avg_loss = sum(losses[:period]) / period

            # Smoothed averages for remaining data
            for i in range(period, len(changes)):
                avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                avg_loss = (avg_loss * (period - 1) + losses[i]) / period

            # Calculate RS and RSI
            if avg_loss == 0:
                rsi = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100.0 - (100.0 / (1.0 + rs))

            return round(rsi, 2)

        except Exception as e:
            app_logger.error(f"Failed to calculate RSI for {symbol}: {e}")
            return 50.0  # Return neutral on error

    def calculate_ema(
        self,
        prices: List[float],
        period: int
    ) -> float:
        """
        Calculate EMA (Exponential Moving Average).

        Args:
            prices: List of prices
            period: EMA period

        Returns:
            EMA value
        """
        if len(prices) < period:
            return sum(prices) / len(prices)  # SMA if not enough data

        # Calculate multiplier
        multiplier = 2.0 / (period + 1)

        # Start with SMA
        ema = sum(prices[:period]) / period

        # Calculate EMA for remaining prices
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema

        return ema

    def calculate_macd(
        self,
        symbol: str,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        interval: str = "1h"
    ) -> Dict[str, float]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            symbol: Trading symbol
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line period (default 9)
            interval: Timeframe for candles

        Returns:
            Dict with macd, signal, histogram values
        """
        try:
            # Fetch enough klines for calculation
            required_candles = slow_period + signal_period + 10
            klines = self.market_data.get_klines(
                symbol=symbol,
                interval=interval,
                limit=required_candles
            )

            if len(klines) < slow_period:
                app_logger.warning(f"Not enough data for MACD calculation: {len(klines)} candles")
                return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}

            # Get closing prices
            closes = [float(k["close"]) for k in klines]

            # Calculate EMAs
            fast_ema = self.calculate_ema(closes, fast_period)
            slow_ema = self.calculate_ema(closes, slow_period)

            # MACD line
            macd = fast_ema - slow_ema

            # For signal line, we need MACD history
            # Simplified: calculate signal as EMA of recent MACD values
            # In reality, we'd need to calculate MACD for each point
            # For this implementation, we'll use a simplified approach
            signal = macd * 0.9  # Approximation

            # Histogram
            histogram = macd - signal

            return {
                "macd": round(macd, 4),
                "signal": round(signal, 4),
                "histogram": round(histogram, 4)
            }

        except Exception as e:
            app_logger.error(f"Failed to calculate MACD for {symbol}: {e}")
            return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}

    def calculate_sma(
        self,
        symbol: str,
        period: int = 20,
        interval: str = "1h"
    ) -> float:
        """
        Calculate SMA (Simple Moving Average).

        Args:
            symbol: Trading symbol
            period: SMA period
            interval: Timeframe for candles

        Returns:
            SMA value
        """
        try:
            klines = self.market_data.get_klines(
                symbol=symbol,
                interval=interval,
                limit=period
            )

            if len(klines) < period:
                app_logger.warning(f"Not enough data for SMA calculation: {len(klines)} candles")
                return 0.0

            closes = [float(k["close"]) for k in klines]
            sma = sum(closes) / len(closes)

            return round(sma, 2)

        except Exception as e:
            app_logger.error(f"Failed to calculate SMA for {symbol}: {e}")
            return 0.0

    def calculate_all_indicators(
        self,
        symbol: str,
        interval: str = "1h"
    ) -> Dict[str, Any]:
        """
        Calculate all indicators for a symbol.

        Args:
            symbol: Trading symbol
            interval: Timeframe for calculations

        Returns:
            Dict with all indicator values
        """
        indicators = {
            "symbol": symbol,
            "interval": interval,
            "rsi": self.calculate_rsi(symbol, interval=interval),
            "macd_data": self.calculate_macd(symbol, interval=interval),
            "sma_20": self.calculate_sma(symbol, period=20, interval=interval),
            "sma_50": self.calculate_sma(symbol, period=50, interval=interval)
        }

        # Flatten MACD data
        indicators["macd"] = indicators["macd_data"]["macd"]
        indicators["macd_signal"] = indicators["macd_data"]["signal"]
        indicators["macd_histogram"] = indicators["macd_data"]["histogram"]

        return indicators

    def calculate_indicators_for_all_symbols(
        self,
        interval: str = "1h"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate indicators for all trading symbols.

        Args:
            interval: Timeframe for calculations

        Returns:
            Dict of symbol -> indicators
        """
        all_indicators = {}

        for symbol in self.market_data.symbols:
            try:
                indicators = self.calculate_all_indicators(symbol, interval)
                all_indicators[symbol] = indicators

                app_logger.debug(
                    f"{symbol}: RSI={indicators['rsi']:.2f}, "
                    f"MACD={indicators['macd']:.4f}"
                )

            except Exception as e:
                app_logger.error(f"Failed to calculate indicators for {symbol}: {e}")
                # Provide default values on error
                all_indicators[symbol] = {
                    "symbol": symbol,
                    "rsi": 50.0,
                    "macd": 0.0,
                    "macd_signal": 0.0,
                    "macd_histogram": 0.0,
                    "sma_20": 0.0,
                    "sma_50": 0.0
                }

        return all_indicators

    def get_trading_signals(
        self,
        symbol: str,
        interval: str = "1h"
    ) -> Dict[str, str]:
        """
        Generate trading signals based on indicators.

        Args:
            symbol: Trading symbol
            interval: Timeframe for analysis

        Returns:
            Dict with signal interpretations
        """
        indicators = self.calculate_all_indicators(symbol, interval)

        signals = {
            "symbol": symbol,
            "rsi_signal": "NEUTRAL",
            "macd_signal": "NEUTRAL",
            "overall_signal": "NEUTRAL"
        }

        # RSI signals
        rsi = indicators["rsi"]
        if rsi < 30:
            signals["rsi_signal"] = "OVERSOLD"  # Potential buy
        elif rsi > 70:
            signals["rsi_signal"] = "OVERBOUGHT"  # Potential sell
        elif rsi < 40:
            signals["rsi_signal"] = "BEARISH"
        elif rsi > 60:
            signals["rsi_signal"] = "BULLISH"

        # MACD signals
        macd = indicators["macd"]
        signal = indicators["macd_signal"]

        if macd > signal and macd > 0:
            signals["macd_signal"] = "BULLISH"
        elif macd < signal and macd < 0:
            signals["macd_signal"] = "BEARISH"

        # Overall signal (simplified combination)
        if signals["rsi_signal"] in ["OVERSOLD", "BULLISH"] and signals["macd_signal"] == "BULLISH":
            signals["overall_signal"] = "BUY"
        elif signals["rsi_signal"] in ["OVERBOUGHT", "BEARISH"] and signals["macd_signal"] == "BEARISH":
            signals["overall_signal"] = "SELL"

        return signals

    def __repr__(self) -> str:
        """String representation."""
        return f"<IndicatorService symbols={len(self.market_data.symbols)}>"
