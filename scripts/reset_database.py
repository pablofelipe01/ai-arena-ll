#!/usr/bin/env python3
"""
Reset database to clean state.

⚠️ WARNING: This will DELETE ALL data from the database.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.supabase_client import get_supabase_client
from config.settings import settings


def reset_database():
    """Reset all tables to clean state."""

    print("\n" + "="*70)
    print("⚠️  DATABASE RESET")
    print("="*70)
    print("\nThis will DELETE ALL data from:")
    print("  • positions")
    print("  • closed_trades")
    print("  • llm_decisions")
    print("  • grids")
    print("\nAnd RESET llm_accounts to initial balance")
    print("="*70)

    response = input("\nType 'DELETE ALL' to proceed: ")
    if response.strip() != 'DELETE ALL':
        print("\n❌ Cancelled by user")
        return

    try:
        supabase_wrapper = get_supabase_client()
        # Access the internal Supabase client
        client = supabase_wrapper._client
        print("\n✅ Connected to Supabase")

        # Delete from tables
        tables_to_clear = ['positions', 'closed_trades', 'llm_decisions', 'grids']

        for table in tables_to_clear:
            print(f"\n🗑️  Clearing {table}...")
            try:
                # Delete all rows
                result = client.table(table).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
                print(f"   ✅ Cleared")
            except Exception as e:
                print(f"   ⚠️  Error: {e}")

        # Reset LLM accounts
        print(f"\n🔄 Resetting LLM accounts to initial balance...")
        initial_balance = settings.INITIAL_BALANCE_PER_LLM

        for llm_id in ['LLM-A', 'LLM-B', 'LLM-C']:
            try:
                client.table('llm_accounts').update({
                    'current_balance': initial_balance,
                    'total_pnl': 0,
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0
                }).eq('llm_id', llm_id).execute()
                print(f"   ✅ {llm_id}: Reset to ${initial_balance:.2f}")
            except Exception as e:
                print(f"   ⚠️  {llm_id}: Error - {e}")

        print("\n" + "="*70)
        print("✅ DATABASE RESET COMPLETED")
        print("="*70)
        print("\nDatabase is now clean and ready for fresh start.")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    reset_database()
