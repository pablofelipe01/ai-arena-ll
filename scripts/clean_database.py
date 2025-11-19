#!/usr/bin/env python3
"""
Clean Database Script - NO CONFIRMATIONS

Deletes all data and resets LLM accounts to initial balance.
"""

import sys
from pathlib import Path
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.supabase_client import get_supabase_client
from src.clients.binance_client import BinanceClient
from config.settings import settings


def clean_database():
    """Clean all tables and reset LLM accounts."""

    print("\n" + "="*70)
    print("🔄 CLEANING DATABASE (NO CONFIRMATIONS)")
    print("="*70)

    try:
        supabase_wrapper = get_supabase_client()
        # Access the internal Supabase client
        client = supabase_wrapper._client
        print("\n✅ Connected to Supabase")

        # Delete from tables
        tables_to_clear = ['positions', 'closed_trades', 'llm_decisions', 'grids', 'decisions']

        for table in tables_to_clear:
            print(f"\n🗑️  Clearing {table}...")
            try:
                # Delete all rows
                result = client.table(table).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
                print(f"   ✅ Cleared")
            except Exception as e:
                print(f"   ⚠️  Error (table may not exist): {e}")

        # Get actual balance from Binance
        print(f"\n💰 Getting balance from Binance...")
        try:
            binance = BinanceClient(testnet=settings.USE_TESTNET)
            total_balance = binance.get_balance()
            initial_balance = float(total_balance / Decimal("3"))
            print(f"   Total balance: ${float(total_balance):.2f}")
            print(f"   Per LLM: ${initial_balance:.2f}")
        except Exception as e:
            print(f"   ⚠️  Could not get Binance balance: {e}")
            print(f"   Using default: ${settings.INITIAL_BALANCE_PER_LLM}")
            initial_balance = settings.INITIAL_BALANCE_PER_LLM

        # Reset LLM accounts
        print(f"\n🔄 Resetting LLM accounts to initial balance...")

        for llm_id in ['LLM-A', 'LLM-B', 'LLM-C']:
            try:
                # Try to update first
                result = client.table('llm_accounts').select('*').eq('llm_id', llm_id).execute()

                if result.data:
                    # Account exists, update it
                    client.table('llm_accounts').update({
                        'current_balance': initial_balance,
                        'total_pnl': 0,
                        'total_trades': 0,
                        'winning_trades': 0,
                        'losing_trades': 0
                    }).eq('llm_id', llm_id).execute()
                    print(f"   ✅ {llm_id}: Reset to ${initial_balance:.2f}")
                else:
                    # Account doesn't exist, create it
                    client.table('llm_accounts').insert({
                        'llm_id': llm_id,
                        'current_balance': initial_balance,
                        'total_pnl': 0,
                        'total_trades': 0,
                        'winning_trades': 0,
                        'losing_trades': 0
                    }).execute()
                    print(f"   ✅ {llm_id}: Created with ${initial_balance:.2f}")
            except Exception as e:
                print(f"   ⚠️  {llm_id}: Error - {e}")

        print("\n" + "="*70)
        print("✅ DATABASE CLEANED")
        print("="*70)
        print(f"\n  • All tables cleared")
        print(f"  • LLM accounts reset to ${initial_balance:.2f} each")
        print(f"  • Total capital: ${initial_balance * 3:.2f}")
        print("\n✓ Ready to start trading!\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    clean_database()
