#!/usr/bin/env python3
"""
Test mainnet connection without making any trades.

This script will:
1. Connect to Binance Mainnet
2. Display your account balance
3. Show open positions (if any)
4. NOT create any trades
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.clients.binance_client import BinanceClient
from config.settings import settings


def test_mainnet_connection():
    """Test connection to Binance Mainnet."""

    print("\n" + "="*70)
    print("🔗 TESTING MAINNET CONNECTION")
    print("="*70)
    print()

    # Check configuration
    if settings.USE_TESTNET:
        print("❌ ERROR: USE_TESTNET is still set to True")
        print("   Please set USE_TESTNET=false in .env")
        return

    if settings.ENVIRONMENT != "production":
        print("⚠️  WARNING: ENVIRONMENT is not set to 'production'")
        print(f"   Current: {settings.ENVIRONMENT}")

    print("✅ Configuration looks good")
    print(f"   Environment: {settings.ENVIRONMENT}")
    print(f"   Use Testnet: {settings.USE_TESTNET}")
    print()

    # Initialize client
    try:
        print("📡 Connecting to Binance Mainnet...")
        client = BinanceClient(testnet=False)
        print("✅ Connected successfully!")
        print()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    # Get account info
    try:
        print("📊 Fetching account information...")
        account_info = client.get_account_info()

        total_balance = float(account_info.get('totalWalletBalance', 0))
        available_balance = float(account_info.get('availableBalance', 0))
        total_unrealized_pnl = float(account_info.get('totalUnrealizedProfit', 0))
        margin_balance = float(account_info.get('totalMarginBalance', 0))

        print()
        print("="*70)
        print("💰 ACCOUNT SUMMARY")
        print("="*70)
        print(f"Total Wallet Balance:    ${total_balance:,.2f} USDT")
        print(f"Available Balance:       ${available_balance:,.2f} USDT")
        print(f"Margin Balance:          ${margin_balance:,.2f} USDT")
        print(f"Unrealized PNL:          ${total_unrealized_pnl:,.2f} USDT")
        print()

        # Check if balance is sufficient
        required_balance = settings.INITIAL_BALANCE_PER_LLM * settings.TOTAL_LLMS
        print(f"Required for experiment: ${required_balance:,.2f} USDT")
        print(f"   ({settings.TOTAL_LLMS} LLMs × ${settings.INITIAL_BALANCE_PER_LLM:.2f} each)")
        print()

        if total_balance >= required_balance:
            print(f"✅ Sufficient balance: ${total_balance:,.2f} ≥ ${required_balance:,.2f}")
        else:
            shortage = required_balance - total_balance
            print(f"⚠️  WARNING: Insufficient balance!")
            print(f"   Have: ${total_balance:,.2f}")
            print(f"   Need: ${required_balance:,.2f}")
            print(f"   Short: ${shortage:,.2f}")
        print()

    except Exception as e:
        print(f"❌ Error fetching account info: {e}")
        return

    # Check for existing positions
    try:
        positions = account_info.get('positions', [])
        open_positions = [p for p in positions if float(p.get('positionAmt', 0)) != 0]

        if open_positions:
            print("="*70)
            print("⚠️  EXISTING OPEN POSITIONS")
            print("="*70)
            for pos in open_positions:
                symbol = pos['symbol']
                position_amt = float(pos['positionAmt'])
                entry_price = float(pos['entryPrice'])
                unrealized_pnl = float(pos['unRealizedProfit'])

                side = "LONG" if position_amt > 0 else "SHORT"

                print(f"\nSymbol: {symbol}")
                print(f"  Side: {side}")
                print(f"  Amount: {position_amt}")
                print(f"  Entry Price: ${entry_price:,.2f}")
                print(f"  Unrealized PNL: ${unrealized_pnl:,.2f}")
            print()
        else:
            print("✅ No existing positions - Account is clean")
            print()

    except Exception as e:
        print(f"⚠️  Could not check positions: {e}")

    # Check margin mode
    print("="*70)
    print("⚙️  RECOMMENDED SETTINGS CHECK")
    print("="*70)
    print()
    print("Before starting, verify in Binance UI:")
    print("  1. Margin Mode: Should be 'Cross' (not Isolated)")
    print("  2. Position Mode: Should be 'One-way Mode'")
    print("  3. No existing positions (unless intentional)")
    print()
    print("To verify, visit:")
    print("  https://www.binance.com/en/futures/BTCUSDT")
    print("  Check settings in top-right corner")
    print()

    print("="*70)
    print("✅ CONNECTION TEST COMPLETED")
    print("="*70)
    print()
    print("Next steps:")
    print("  1. Review the account summary above")
    print("  2. Verify settings in Binance UI")
    print("  3. If everything looks good, start the trading system:")
    print("     python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload")
    print()


if __name__ == "__main__":
    test_mainnet_connection()
