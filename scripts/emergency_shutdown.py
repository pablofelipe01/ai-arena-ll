#!/usr/bin/env python3
"""
Emergency Shutdown Script - NO CONFIRMATIONS

Cancels all orders and closes all positions immediately.
Use AFTER stopping the server with Ctrl+C.

Usage:
    python3 scripts/emergency_shutdown.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clients.binance_client import BinanceClient
from config.settings import settings


def cancel_all_orders(binance: BinanceClient) -> int:
    """Cancel all open orders."""
    print("\n" + "="*70)
    print("CANCELLING ALL ORDERS")
    print("="*70 + "\n")

    symbols = settings.available_pairs_list
    total_cancelled = 0

    for symbol in symbols:
        try:
            orders = binance.get_open_orders(symbol)
            if not orders:
                continue

            print(f"{symbol}: Cancelling {len(orders)} orders...")

            for order in orders:
                try:
                    binance.cancel_order(symbol, order['orderId'])
                    total_cancelled += 1
                except Exception as e:
                    print(f"  Failed to cancel order {order['orderId']}: {e}")

            print(f"  ✓ Cancelled")

        except Exception as e:
            print(f"{symbol}: Error - {e}")

    print("\n" + "="*70)
    print(f"RESULT: {total_cancelled} orders cancelled")
    print("="*70)

    return total_cancelled


def close_all_positions(binance: BinanceClient) -> int:
    """Close all open positions."""
    print("\n" + "="*70)
    print("CLOSING ALL POSITIONS")
    print("="*70 + "\n")

    try:
        positions = binance.get_position_risk()
        active_positions = [p for p in positions if float(p.get('positionAmt', 0)) != 0]

        if not active_positions:
            print("No open positions to close")
            return 0

        total_closed = 0

        for pos in active_positions:
            symbol = pos['symbol']
            position_amt = float(pos['positionAmt'])

            try:
                # Close position with market order
                side = "SELL" if position_amt > 0 else "BUY"
                qty = abs(position_amt)

                print(f"{symbol}: Closing {side} position ({qty:.3f})...")

                result = binance.create_market_order(
                    symbol=symbol,
                    side=side,
                    quantity=qty,
                    reduce_only=True
                )

                print(f"  ✓ Position closed - Order ID: {result.get('orderId')}")
                total_closed += 1

            except Exception as e:
                print(f"  Failed to close {symbol}: {e}")

        print("\n" + "="*70)
        print(f"RESULT: {total_closed} positions closed")
        print("="*70)

        return total_closed

    except Exception as e:
        print(f"Error closing positions: {e}")
        return 0


def main():
    print("\n" + "="*70)
    print("⚠️  EMERGENCY SHUTDOWN (NO CONFIRMATIONS)")
    print("="*70)

    # Initialize Binance client
    print("\nConnecting to Binance...")
    try:
        binance = BinanceClient(testnet=settings.USE_TESTNET)
        env = "Testnet" if settings.USE_TESTNET else "MAINNET"
        print(f"✓ Connected to Binance {env}")
    except Exception as e:
        print(f"❌ Failed to connect to Binance: {e}")
        sys.exit(1)

    # Execute
    print("\n⚠️  Proceeding to cancel all orders and close all positions...")

    cancelled = cancel_all_orders(binance)
    closed = close_all_positions(binance)

    print("\n" + "="*70)
    print("✅ EMERGENCY SHUTDOWN COMPLETE")
    print("="*70)
    print(f"\n  • {cancelled} orders cancelled")
    print(f"  • {closed} positions closed")
    print("\n✓ Safe to proceed with configuration changes\n")


if __name__ == "__main__":
    main()
