#!/usr/bin/env python3
"""
Emergency script to close all positions and cancel all orders.

⚠️ WARNING: This will immediately close ALL positions at market price
and cancel ALL pending orders. Use with caution.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.clients.binance_client import BinanceClient
from config.settings import settings
from src.utils.logger import app_logger


def close_all_positions(client: BinanceClient):
    """Close all open positions at market price."""
    print("\n" + "="*70)
    print("CLOSING ALL POSITIONS")
    print("="*70)

    try:
        # Get account info
        account_info = client.get_account_info()
        positions = account_info.get('positions', [])

        closed_count = 0
        for position in positions:
            # Skip if no position
            position_amt = float(position.get('positionAmt', 0))
            if position_amt == 0:
                continue

            symbol = position['symbol']

            print(f"\n📊 Position: {symbol}")
            print(f"   Amount: {position_amt}")
            print(f"   Side: {'LONG' if position_amt > 0 else 'SHORT'}")

            try:
                # Close position with market order
                side = 'SELL' if position_amt > 0 else 'BUY'
                quantity = abs(position_amt)

                order = client.create_order(
                    symbol=symbol,
                    side=side,
                    order_type='MARKET',
                    quantity=quantity,
                    reduce_only=True
                )

                print(f"   ✅ CLOSED - Order ID: {order['orderId']}")
                closed_count += 1

            except Exception as e:
                print(f"   ❌ Error closing {symbol}: {e}")

        print(f"\n✅ Total positions closed: {closed_count}")

    except Exception as e:
        print(f"❌ Error getting positions: {e}")


def cancel_all_orders(client: BinanceClient):
    """Cancel all pending orders."""
    print("\n" + "="*70)
    print("CANCELLING ALL ORDERS")
    print("="*70)

    # Get all symbols with open orders
    symbols = ['ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'DOGEUSDT', 'ADAUSDT', 'AVAXUSDT']

    total_cancelled = 0

    for symbol in symbols:
        try:
            # Get open orders for symbol
            open_orders = client.get_open_orders(symbol)

            if not open_orders:
                continue

            print(f"\n📋 {symbol}: {len(open_orders)} orders")

            # Cancel all orders for this symbol
            result = client.cancel_all_orders(symbol)

            cancelled = len(open_orders)
            total_cancelled += cancelled
            print(f"   ✅ Cancelled {cancelled} orders")

        except Exception as e:
            print(f"   ❌ Error cancelling orders for {symbol}: {e}")

    print(f"\n✅ Total orders cancelled: {total_cancelled}")


def show_final_status(client: BinanceClient):
    """Show final account status."""
    print("\n" + "="*70)
    print("FINAL STATUS")
    print("="*70)

    try:
        account_info = client.get_account_info()

        total_balance = float(account_info.get('totalWalletBalance', 0))
        available_balance = float(account_info.get('availableBalance', 0))
        unrealized_pnl = float(account_info.get('totalUnrealizedProfit', 0))

        print(f"\n💰 Account Summary:")
        print(f"   Total Balance:     ${total_balance:,.2f} USDT")
        print(f"   Available Balance: ${available_balance:,.2f} USDT")
        print(f"   Unrealized PnL:    ${unrealized_pnl:,.2f} USDT")

        # Check remaining positions
        positions = account_info.get('positions', [])
        open_positions = [p for p in positions if float(p.get('positionAmt', 0)) != 0]

        if open_positions:
            print(f"\n⚠️  WARNING: {len(open_positions)} positions still open!")
            for pos in open_positions:
                print(f"   - {pos['symbol']}: {pos['positionAmt']}")
        else:
            print(f"\n✅ No open positions")

        # Check remaining orders
        all_orders_count = 0
        for symbol in ['ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'DOGEUSDT', 'ADAUSDT', 'AVAXUSDT']:
            try:
                orders = client.get_open_orders(symbol)
                all_orders_count += len(orders)
            except:
                pass

        if all_orders_count > 0:
            print(f"\n⚠️  WARNING: {all_orders_count} orders still pending!")
        else:
            print(f"\n✅ No pending orders")

    except Exception as e:
        print(f"❌ Error getting final status: {e}")


def main():
    """Main function."""

    print("\n" + "="*70)
    print("⚠️  EMERGENCY CLOSE ALL - BINANCE FUTURES")
    print("="*70)
    print("\nThis script will:")
    print("  1. Close ALL open positions at MARKET price")
    print("  2. Cancel ALL pending orders")
    print("  3. Show final account status")
    print("\n⚠️  WARNING: This action is IMMEDIATE and IRREVERSIBLE")
    print("="*70)

    # Confirm
    response = input("\nType 'YES' to proceed: ")
    if response.strip().upper() != 'YES':
        print("\n❌ Cancelled by user")
        return

    # Determine if testnet or mainnet
    use_testnet = settings.USE_TESTNET
    env_name = "TESTNET" if use_testnet else "MAINNET (REAL MONEY)"

    print(f"\n🌐 Environment: {env_name}")

    if not use_testnet:
        print("\n⚠️⚠️⚠️  THIS IS MAINNET - REAL MONEY ⚠️⚠️⚠️")
        response = input("Type 'CONFIRM' to proceed with REAL money: ")
        if response.strip().upper() != 'CONFIRM':
            print("\n❌ Cancelled by user")
            return

    # Initialize client
    try:
        client = BinanceClient(testnet=use_testnet)
        print("✅ Connected to Binance")
    except Exception as e:
        print(f"❌ Error connecting to Binance: {e}")
        return

    # Execute emergency close
    try:
        # Step 1: Cancel all orders first
        cancel_all_orders(client)

        # Step 2: Close all positions
        close_all_positions(client)

        # Step 3: Show final status
        show_final_status(client)

        print("\n" + "="*70)
        print("✅ EMERGENCY CLOSE COMPLETED")
        print("="*70)
        print("\nNext steps:")
        print("  1. Verify in Binance UI that everything is closed")
        print("  2. Check your balance")
        print("  3. Review logs if needed")
        print()

    except Exception as e:
        print(f"\n❌ Error during emergency close: {e}")
        print("\n⚠️  Please check Binance UI manually")


if __name__ == "__main__":
    main()
