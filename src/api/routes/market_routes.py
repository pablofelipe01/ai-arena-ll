"""
Market Routes - Market data and technical indicators endpoints.

All endpoints are GET-only (read-only).
"""

from typing import Dict, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from decimal import Decimal

from src.services.market_data_service import MarketDataService
from src.services.indicator_service import IndicatorService
from src.api.dependencies import (
    get_market_data_service_dependency,
    get_indicator_service_dependency
)
from src.api.models.responses import (
    MarketTickerResponse,
    MarketIndicatorsResponse,
    MarketSnapshotResponse
)
from src.utils.logger import app_logger


router = APIRouter(prefix="/market", tags=["Market Data"])


# ============================================================================
# Market Snapshot Endpoint
# ============================================================================

@router.get(
    "/snapshot",
    response_model=MarketSnapshotResponse,
    summary="Get complete market snapshot",
    description="Returns current prices, technical indicators, and market summary for all tracked symbols."
)
async def get_market_snapshot(
    market_service: MarketDataService = Depends(get_market_data_service_dependency),
    indicator_service: IndicatorService = Depends(get_indicator_service_dependency)
) -> MarketSnapshotResponse:
    """
    Get complete market snapshot.

    Returns:
    - Current prices for all 6 symbols
    - 24h price changes and volumes
    - Technical indicators (RSI, MACD, SMA)
    - Market summary (gainers, losers)
    """
    try:
        # Get market snapshot
        snapshot = market_service.get_market_snapshot()

        # Get indicators for all symbols
        all_indicators = indicator_service.calculate_indicators_for_all_symbols()

        # Build ticker responses
        tickers = {}
        for symbol, data in snapshot["symbols"].items():
            tickers[symbol] = MarketTickerResponse(
                symbol=symbol,
                price=float(data["price"]),
                price_change_pct_24h=float(data["price_change_pct_24h"]),
                volume_24h=float(data["volume_24h"]),
                high_24h=float(data["high_24h"]),
                low_24h=float(data["low_24h"]),
                timestamp=snapshot["timestamp"]
            )

        # Build indicator responses
        indicators = {}
        for symbol, data in all_indicators.items():
            # Get trading signals
            signals = indicator_service.get_trading_signals(symbol)

            indicators[symbol] = MarketIndicatorsResponse(
                symbol=symbol,
                rsi=data.get("rsi", 0.0),
                macd=data.get("macd", 0.0),
                macd_signal=data.get("macd_signal", 0.0),
                macd_histogram=data.get("macd_histogram", 0.0),
                sma_20=data.get("sma_20", 0.0),
                sma_50=data.get("sma_50", 0.0),
                trading_signal=signals.get("overall_signal", "HOLD"),
                timestamp=datetime.utcnow()
            )

        return MarketSnapshotResponse(
            symbols=tickers,
            indicators=indicators,
            summary=snapshot["summary"],
            timestamp=snapshot["timestamp"]
        )

    except Exception as e:
        app_logger.error(f"Error getting market snapshot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Symbol-Specific Endpoints
# ============================================================================

@router.get(
    "/ticker/{symbol}",
    response_model=MarketTickerResponse,
    summary="Get ticker for specific symbol",
    description="Returns current price and 24h statistics for a specific symbol."
)
async def get_ticker(
    symbol: str = Path(..., description="Trading pair symbol (e.g., ETHUSDT)"),
    market_service: MarketDataService = Depends(get_market_data_service_dependency)
) -> MarketTickerResponse:
    """
    Get ticker for specific symbol.

    Parameters:
    - symbol: Trading pair (DOGEUSDT, TRXUSDT, HBARUSDT, XLMUSDT, ADAUSDT, ALGOUSDT)

    Returns:
    - Current price
    - 24h price change %
    - 24h volume
    - 24h high/low
    """
    try:
        ticker_data = market_service.get_ticker_24h(symbol, use_cache=True)

        return MarketTickerResponse(
            symbol=symbol,
            price=float(ticker_data["price"]),
            price_change_pct_24h=float(ticker_data["price_change_pct"]),
            volume_24h=float(ticker_data["volume_24h"]),
            high_24h=float(ticker_data["high_24h"]),
            low_24h=float(ticker_data["low_24h"]),
            timestamp=datetime.utcnow()
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Invalid symbol: {symbol}")
    except Exception as e:
        app_logger.error(f"Error getting ticker for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/indicators/{symbol}",
    response_model=MarketIndicatorsResponse,
    summary="Get technical indicators for specific symbol",
    description="Returns technical indicators (RSI, MACD, SMA) and trading signals for a specific symbol."
)
async def get_indicators(
    symbol: str = Path(..., description="Trading pair symbol (e.g., ETHUSDT)"),
    indicator_service: IndicatorService = Depends(get_indicator_service_dependency)
) -> MarketIndicatorsResponse:
    """
    Get technical indicators for specific symbol.

    Parameters:
    - symbol: Trading pair (DOGEUSDT, TRXUSDT, HBARUSDT, XLMUSDT, ADAUSDT, ALGOUSDT)

    Returns:
    - RSI (14 period)
    - MACD (12/26/9)
    - SMA 20 and 50
    - Trading signal (BUY/SELL/HOLD)
    """
    try:
        # Calculate indicators
        indicators = indicator_service.calculate_all_indicators(symbol)

        # Get trading signals
        signals = indicator_service.get_trading_signals(symbol)

        return MarketIndicatorsResponse(
            symbol=symbol,
            rsi=indicators.get("rsi", 0.0),
            macd=indicators.get("macd", 0.0),
            macd_signal=indicators.get("macd_signal", 0.0),
            macd_histogram=indicators.get("macd_histogram", 0.0),
            sma_20=indicators.get("sma_20", 0.0),
            sma_50=indicators.get("sma_50", 0.0),
            trading_signal=signals.get("overall_signal", "HOLD"),
            timestamp=datetime.utcnow()
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Invalid symbol: {symbol}")
    except Exception as e:
        app_logger.error(f"Error getting indicators for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Price Endpoint
# ============================================================================

@router.get(
    "/prices",
    response_model=Dict[str, float],
    summary="Get current prices for all symbols",
    description="Returns current prices for all 6 tracked symbols."
)
async def get_current_prices(
    use_cache: bool = Query(default=True, description="Use cached prices (60s TTL)"),
    market_service: MarketDataService = Depends(get_market_data_service_dependency)
) -> Dict[str, float]:
    """
    Get current prices for all symbols.

    Parameters:
    - use_cache: Use cached prices (default: true, 60s TTL)

    Returns:
    - Dict of symbol -> price
    """
    try:
        prices = market_service.get_current_prices(use_cache=use_cache)

        # Convert Decimal to float
        return {symbol: float(price) for symbol, price in prices.items()}

    except Exception as e:
        app_logger.error(f"Error getting current prices: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/price/{symbol}",
    response_model=float,
    summary="Get current price for specific symbol",
    description="Returns current price for a specific symbol."
)
async def get_price(
    symbol: str = Path(..., description="Trading pair symbol (e.g., ETHUSDT)"),
    use_cache: bool = Query(default=True, description="Use cached price (60s TTL)"),
    market_service: MarketDataService = Depends(get_market_data_service_dependency)
) -> float:
    """
    Get current price for specific symbol.

    Parameters:
    - symbol: Trading pair (DOGEUSDT, TRXUSDT, HBARUSDT, XLMUSDT, ADAUSDT, ALGOUSDT)
    - use_cache: Use cached price (default: true, 60s TTL)

    Returns:
    - Current price as float
    """
    try:
        prices = market_service.get_current_prices(use_cache=use_cache)

        if symbol not in prices:
            raise HTTPException(status_code=404, detail=f"Invalid symbol: {symbol}")

        return float(prices[symbol])

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error getting price for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
