#!/usr/bin/env python3
"""
Emergency Cancel All Orders Script

CRITICAL: Use this script BEFORE shutting down the server if you want to cancel
all active grid orders and optionally close all positions.

This prevents orphaned orders from staying active on Binance after shutdown.

Usage:
    python3 scripts/emergency_cancel.py                    # Preview mode (shows what would be cancelled)
    python3 scripts/emergency_cancel.py --confirm          # Cancel all orders
    python3 scripts/emergency_cancel.py --confirm --close  # Cancel orders AND close all positions
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from src.clients.binance_client import BinanceClient
from config.settings import settings


def preview_orders(binance: BinanceClient):
    """Show what orders would be cancelled."""
    print("\n" + "="*70)
    print("PREVIEW MODE - No changes will be made")
    print("="*70 + "\n")

    symbols = ["ETHUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT"]
    total_orders = 0
    order_details = []

    for symbol in symbols:
        try:
            orders = binance.get_open_orders(symbol)
            if orders:
                print(f"{symbol}: {len(orders)} open orders")
                total_orders += len(orders)

                for order in orders:
                    client_id = order.get('clientOrderId', 'N/A')
                    side = order.get('side', 'N/A')
                    price = float(order.get('price', 0))
                    qty = float(order.get('origQty', 0))

                    order_details.append({
                        'symbol': symbol,
                        'order_id': order['orderId'],
                        'client_id': client_id,
                        'side': side,
                        'price': price,
                        'qty': qty
                    })
        except Exception as e:
            print(f"{symbol}: Error fetching orders - {e}")

    print("\n" + "="*70)
    print(f"TOTAL: {total_orders} orders across all symbols")
    print("="*70)

    if order_details and len(order_details) <= 20:
        print("\nOrder Details:")
        for order in order_details:
            print(f"  {order['symbol']}: {order['side']} @ ${order['price']:.4f} x {order['qty']:.3f}")

    return total_orders


def preview_positions(binance: BinanceClient):
    """Show what positions would be closed."""
    print("\n" + "="*70)
    print("OPEN POSITIONS")
    print("="*70 + "\n")

    try:
        positions = binance.get_position_risk()
        active_positions = [p for p in positions if float(p.get('positionAmt', 0)) != 0]

        if not active_positions:
            print("No open positions")
            return 0

        for pos in active_positions:
            symbol = pos['symbol']
            position_amt = float(pos['positionAmt'])
            entry_price = float(pos['entryPrice'])
            unrealized_pnl = float(pos['unRealizedProfit'])
            leverage = int(pos['leverage'])

            side = "LONG" if position_amt > 0 else "SHORT"
            qty = abs(position_amt)

            print(f"{symbol}: {side} {qty:.3f} @ ${entry_price:.4f} ({leverage}x)")
            print(f"  Unrealized PnL: ${unrealized_pnl:.2f}")

        print(f"\nTotal: {len(active_positions)} open positions")
        return len(active_positions)

    except Exception as e:
        print(f"Error fetching positions: {e}")
        return 0


def cancel_all_orders(binance: BinanceClient) -> int:
    """Cancel all open orders."""
    print("\n" + "="*70)
    print("CANCELLING ALL ORDERS")
    print("="*70 + "\n")

    symbols = ["ETHUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT"]
    total_cancelled = 0
    total_failed = 0

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
                    total_failed += 1

            print(f"  ✓ {len(orders) - total_failed} cancelled")

        except Exception as e:
            print(f"{symbol}: Error - {e}")

    print("\n" + "="*70)
    print(f"RESULT: {total_cancelled} cancelled, {total_failed} failed")
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
    parser = argparse.ArgumentParser(
        description="Emergency Cancel All Orders Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/emergency_cancel.py                    # Preview
  python3 scripts/emergency_cancel.py --confirm          # Cancel orders
  python3 scripts/emergency_cancel.py --confirm --close  # Cancel + Close positions
        """
    )

    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually cancel orders (without this, just preview)"
    )
    parser.add_argument(
        "--close",
        action="store_true",
        help="Also close all open positions (requires --confirm)"
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("⚠️  EMERGENCY CANCEL SCRIPT")
    print("="*70)

    # Initialize Binance client
    print("\nConnecting to Binance...")
    try:
        binance = BinanceClient(
            api_key=settings.BINANCE_API_KEY,
            api_secret=settings.BINANCE_API_SECRET,
            testnet=settings.BINANCE_TESTNET
        )
        print("✓ Connected to Binance Testnet" if settings.BINANCE_TESTNET else "✓ Connected to Binance MAINNET")
    except Exception as e:
        print(f"❌ Failed to connect to Binance: {e}")
        sys.exit(1)

    # Preview
    total_orders = preview_orders(binance)
    total_positions = preview_positions(binance) if args.close else 0

    if not args.confirm:
        print("\n" + "="*70)
        print("PREVIEW MODE - No changes made")
        print("="*70)
        print("\nTo actually cancel orders, run:")
        print("  python3 scripts/emergency_cancel.py --confirm")
        if total_positions > 0:
            print("\nTo also close positions, run:")
            print("  python3 scripts/emergency_cancel.py --confirm --close")
        print()
        return

    # Confirm action
    print("\n" + "="*70)
    print("⚠️  WARNING: YOU ARE ABOUT TO:")
    print("="*70)
    print(f"  • Cancel {total_orders} open orders")
    if args.close:
        print(f"  • Close {total_positions} open positions")
    print("\nThis action CANNOT be undone!")
    print("="*70)

    response = input("\nType 'YES' to confirm: ")
    if response.strip().upper() != "YES":
        print("\n❌ Cancelled by user")
        return

    # Execute
    cancelled = cancel_all_orders(binance)

    if args.close and total_positions > 0:
        closed = close_all_positions(binance)
        print(f"\n✓ Complete: {cancelled} orders cancelled, {closed} positions closed")
    else:
        print(f"\n✓ Complete: {cancelled} orders cancelled")

    print("\n" + "="*70)
    print("SAFE TO SHUT DOWN SERVER NOW")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
