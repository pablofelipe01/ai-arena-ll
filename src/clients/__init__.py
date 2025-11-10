"""
Clients package for external API integrations.

Exports:
- BinanceClient: Client for Binance Futures API
"""

from .binance_client import BinanceClient

__all__ = [
    "BinanceClient",
]
