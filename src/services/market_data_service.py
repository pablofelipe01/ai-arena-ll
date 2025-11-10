"""
Market Data Service - Fetches and caches market data from Binance.

Provides:
- Current prices for all trading symbols
- 24h price changes and volumes
- OHLCV (candlestick) data for technical analysis
- Data caching to reduce API calls
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import time

from src.clients.binance_client import BinanceClient
from src.clients.prompts import ALLOWED_SYMBOLS
from src.utils.logger import app_logger


class MarketDataCache:
    """Simple cache for market data to reduce API calls."""

    def __init__(self, ttl_seconds: int = 60):
        """
        Initialize cache.

        Args:
            ttl_seconds: Time-to-live for cached data
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached data if still valid."""
        if key not in self._cache:
            return None

        # Check if expired
        if time.time() - self._timestamps[key] > self.ttl_seconds:
            del self._cache[key]
            del self._timestamps[key]
            return None

        return self._cache[key]

    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Set cached data."""
        self._cache[key] = value
        self._timestamps[key] = time.time()

    def clear(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        self._timestamps.clear()


class MarketDataService:
    """
    Service for fetching and managing market data.

    Provides current prices, 24h statistics, and OHLCV data
    for all trading symbols with caching to reduce API load.
    """

    def __init__(
        self,
        binance_client: BinanceClient,
        symbols: Optional[List[str]] = None,
        cache_ttl: int = 60
    ):
        """
        Initialize market data service.

        Args:
            binance_client: Binance API client
            symbols: List of symbols to track (default: ALLOWED_SYMBOLS)
            cache_ttl: Cache time-to-live in seconds
        """
        self.binance = binance_client
        self.symbols = symbols or ALLOWED_SYMBOLS
        self.cache = MarketDataCache(ttl_seconds=cache_ttl)

        app_logger.info(f"MarketDataService initialized for {len(self.symbols)} symbols")

    def get_current_prices(self, use_cache: bool = True) -> Dict[str, Decimal]:
        """
        Get current prices for all symbols.

        Args:
            use_cache: Whether to use cached data

        Returns:
            Dict of symbol -> current_price
        """
        cache_key = "current_prices"

        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                app_logger.debug("Using cached current prices")
                return cached

        prices = {}

        for symbol in self.symbols:
            try:
                ticker = self.binance.get_ticker_price(symbol)
                prices[symbol] = Decimal(str(ticker["price"]))
            except Exception as e:
                app_logger.error(f"Failed to fetch price for {symbol}: {e}")
                # Use last known price if available
                if symbol in prices:
                    continue
                # Otherwise set to 0 as fallback
                prices[symbol] = Decimal("0")

        self.cache.set(cache_key, prices)
        return prices

    def get_ticker_24h(self, symbol: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get 24h ticker statistics for a symbol.

        Args:
            symbol: Trading symbol
            use_cache: Whether to use cached data

        Returns:
            Dict with 24h price change, volume, high, low, etc.
        """
        cache_key = f"ticker_24h_{symbol}"

        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        try:
            ticker = self.binance.get_ticker_24h(symbol)

            result = {
                "symbol": symbol,
                "price": Decimal(str(ticker["lastPrice"])),
                "price_change": Decimal(str(ticker["priceChange"])),
                "price_change_pct": Decimal(str(ticker["priceChangePercent"])),
                "volume": Decimal(str(ticker["volume"])),
                "quote_volume": Decimal(str(ticker["quoteVolume"])),
                "high_24h": Decimal(str(ticker["highPrice"])),
                "low_24h": Decimal(str(ticker["lowPrice"])),
                "open_24h": Decimal(str(ticker["openPrice"])),
                "close_time": datetime.fromtimestamp(ticker["closeTime"] / 1000)
            }

            self.cache.set(cache_key, result)
            return result

        except Exception as e:
            app_logger.error(f"Failed to fetch 24h ticker for {symbol}: {e}")
            raise

    def get_all_tickers_24h(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get 24h ticker statistics for all symbols.

        Args:
            use_cache: Whether to use cached data

        Returns:
            List of ticker data for all symbols
        """
        cache_key = "all_tickers_24h"

        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                app_logger.debug("Using cached 24h tickers")
                return cached

        tickers = []

        for symbol in self.symbols:
            try:
                ticker = self.get_ticker_24h(symbol, use_cache=False)
                tickers.append(ticker)
            except Exception as e:
                app_logger.error(f"Failed to fetch ticker for {symbol}: {e}")

        self.cache.set(cache_key, tickers)
        return tickers

    def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 100,
        use_cache: bool = False  # Don't cache klines by default
    ) -> List[Dict[str, Any]]:
        """
        Get candlestick (OHLCV) data for a symbol.

        Args:
            symbol: Trading symbol
            interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles to fetch
            use_cache: Whether to use cached data

        Returns:
            List of candlestick data
        """
        cache_key = f"klines_{symbol}_{interval}_{limit}"

        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        try:
            klines = self.binance.get_klines(symbol, interval, limit)

            result = []
            for kline in klines:
                result.append({
                    "open_time": datetime.fromtimestamp(kline[0] / 1000),
                    "open": Decimal(str(kline[1])),
                    "high": Decimal(str(kline[2])),
                    "low": Decimal(str(kline[3])),
                    "close": Decimal(str(kline[4])),
                    "volume": Decimal(str(kline[5])),
                    "close_time": datetime.fromtimestamp(kline[6] / 1000),
                    "quote_volume": Decimal(str(kline[7])),
                    "trades": int(kline[8])
                })

            if use_cache:
                self.cache.set(cache_key, result)

            return result

        except Exception as e:
            app_logger.error(f"Failed to fetch klines for {symbol}: {e}")
            raise

    def get_market_snapshot(self) -> Dict[str, Any]:
        """
        Get complete market snapshot for all symbols.

        Returns:
            Dict with current prices and 24h statistics for all symbols
        """
        try:
            prices = self.get_current_prices()
            tickers = self.get_all_tickers_24h()

            # Build snapshot
            snapshot = {
                "timestamp": datetime.utcnow(),
                "symbols": {},
                "summary": {
                    "total_symbols": len(self.symbols),
                    "gainers": 0,
                    "losers": 0,
                    "total_volume_usdt": Decimal("0")
                }
            }

            for ticker in tickers:
                symbol = ticker["symbol"]
                snapshot["symbols"][symbol] = {
                    "price": ticker["price"],
                    "price_change_pct_24h": ticker["price_change_pct"],
                    "volume_24h": ticker["quote_volume"],
                    "high_24h": ticker["high_24h"],
                    "low_24h": ticker["low_24h"]
                }

                # Update summary
                if ticker["price_change_pct"] > 0:
                    snapshot["summary"]["gainers"] += 1
                else:
                    snapshot["summary"]["losers"] += 1

                snapshot["summary"]["total_volume_usdt"] += ticker["quote_volume"]

            return snapshot

        except Exception as e:
            app_logger.error(f"Failed to get market snapshot: {e}")
            raise

    def format_market_data_for_llm(
        self,
        include_indicators: bool = False,
        indicator_data: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Format market data for LLM consumption.

        Args:
            include_indicators: Whether to include technical indicators
            indicator_data: Pre-calculated indicator data

        Returns:
            List of formatted market data for each symbol
        """
        tickers = self.get_all_tickers_24h()

        formatted = []

        for ticker in tickers:
            symbol = ticker["symbol"]

            data = {
                "symbol": symbol,
                "price": float(ticker["price"]),
                "price_change_pct_24h": float(ticker["price_change_pct"]),
                "volume_24h": float(ticker["quote_volume"]),
                "high_24h": float(ticker["high_24h"]),
                "low_24h": float(ticker["low_24h"])
            }

            # Add indicators if provided
            if include_indicators and indicator_data and symbol in indicator_data:
                indicators = indicator_data[symbol]
                data["rsi"] = indicators.get("rsi", 0.0)
                data["macd"] = indicators.get("macd", 0.0)
                data["macd_signal"] = indicators.get("macd_signal", 0.0)
            else:
                # Default values if no indicators
                data["rsi"] = 0.0
                data["macd"] = 0.0
                data["macd_signal"] = 0.0

            formatted.append(data)

        return formatted

    def clear_cache(self) -> None:
        """Clear all cached market data."""
        self.cache.clear()
        app_logger.info("Market data cache cleared")

    def __repr__(self) -> str:
        """String representation."""
        return f"<MarketDataService symbols={len(self.symbols)} cache_ttl={self.cache.ttl_seconds}s>"
