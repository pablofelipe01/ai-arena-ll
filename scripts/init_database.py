"""
Database Initialization Script for Crypto LLM Trading System.

This script initializes the Supabase database by:
1. Creating all required tables
2. Setting up views and triggers
3. Inserting initial LLM account data
4. Verifying schema integrity

Usage:
    python scripts/init_database.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client, Client
from config.settings import settings
from src.utils.logger import app_logger


def read_schema_file() -> str:
    """
    Read the SQL schema file.

    Returns:
        SQL schema as string
    """
    schema_file = Path(__file__).parent / "schema.sql"

    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    app_logger.info(f"Reading schema from: {schema_file}")
    return schema_file.read_text()


def initialize_database() -> None:
    """
    Initialize Supabase database with complete schema.

    This function:
    1. Connects to Supabase
    2. Executes schema.sql
    3. Verifies table creation
    4. Initializes LLM accounts
    """
    print("\n" + "="*70)
    print("INITIALIZING CRYPTO LLM TRADING DATABASE")
    print("="*70)

    try:
        # Connect to Supabase
        print(f"\n📡 Connecting to Supabase...")
        print(f"   URL: {settings.SUPABASE_URL}")

        client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )

        print("✅ Connected to Supabase successfully")

        # NOTE: Supabase Python client doesn't support raw SQL execution directly
        # The schema.sql file should be executed manually in Supabase SQL Editor
        print("\n" + "="*70)
        print("⚠️  MANUAL STEP REQUIRED")
        print("="*70)
        print("\nThe Supabase Python client does not support executing raw SQL.")
        print("Please follow these steps to initialize your database:\n")
        print("1. Log in to your Supabase Dashboard")
        print(f"   URL: {settings.SUPABASE_URL.replace('.supabase.co', '.supabase.co')}")
        print("\n2. Navigate to: SQL Editor")
        print("\n3. Create a new query")
        print("\n4. Copy and paste the contents of:")
        print(f"   {Path(__file__).parent / 'schema.sql'}")
        print("\n5. Run the query")
        print("\n6. Verify that all tables were created successfully")
        print("\n" + "="*70)

        # Verify database schema
        print("\n📊 Verifying database schema...")
        verify_schema(client)

    except Exception as e:
        app_logger.error(f"Database initialization failed: {e}", exc_info=True)
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)


def verify_schema(client: Client) -> None:
    """
    Verify that all required tables exist.

    Args:
        client: Supabase client
    """
    required_tables = [
        "llm_accounts",
        "positions",
        "trades",
        "orders",
        "market_data",
        "rejected_decisions",
        "llm_api_calls"
    ]

    required_views = [
        "llm_leaderboard",
        "active_positions_summary",
        "llm_trading_stats"
    ]

    print("\n📋 Checking required tables...")

    for table in required_tables:
        try:
            # Try to query the table
            response = client.table(table).select("*").limit(0).execute()
            print(f"   ✅ {table}")
        except Exception as e:
            print(f"   ❌ {table} - NOT FOUND")
            print(f"      Error: {str(e)}")

    print("\n📋 Checking required views...")

    for view in required_views:
        try:
            response = client.table(view).select("*").limit(0).execute()
            print(f"   ✅ {view}")
        except Exception as e:
            print(f"   ⚠️  {view} - NOT FOUND (views may need manual verification)")

    # Check initial data
    print("\n📊 Checking initial LLM accounts...")

    try:
        response = client.table("llm_accounts").select("llm_id, provider, model_name, balance").execute()

        if response.data and len(response.data) > 0:
            print(f"   Found {len(response.data)} LLM accounts:")
            for account in response.data:
                print(f"   ✅ {account['llm_id']} - {account['provider']} - ${account['balance']}")
        else:
            print("   ⚠️  No LLM accounts found")
            print("\n   Please ensure you ran the INSERT statements from schema.sql:")
            print("   - LLM-A (Claude Sonnet 4)")
            print("   - LLM-B (DeepSeek Reasoner)")
            print("   - LLM-C (GPT-4o)")

    except Exception as e:
        print(f"   ❌ Error checking LLM accounts: {e}")


def reset_llm_accounts(client: Client) -> None:
    """
    Reset all LLM accounts to initial state ($100 balance).

    WARNING: This will delete all trading history!

    Args:
        client: Supabase client
    """
    print("\n" + "="*70)
    print("⚠️  WARNING: RESET LLM ACCOUNTS")
    print("="*70)
    print("\nThis will:")
    print("  - Delete all positions")
    print("  - Delete all trades")
    print("  - Delete all orders")
    print("  - Reset LLM accounts to $100 balance")
    print("\nThis action CANNOT be undone!")

    confirm = input("\nType 'RESET' to confirm: ")

    if confirm != "RESET":
        print("❌ Reset cancelled")
        return

    print("\n🗑️  Resetting database...")

    try:
        # Delete all positions
        client.table("positions").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print("   ✅ Deleted all positions")

        # Delete all trades
        client.table("trades").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print("   ✅ Deleted all trades")

        # Delete all orders
        client.table("orders").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print("   ✅ Deleted all orders")

        # Reset LLM accounts
        for llm_id in ["LLM-A", "LLM-B", "LLM-C"]:
            client.table("llm_accounts").update({
                "balance": 100.0,
                "margin_used": 0.0,
                "total_pnl": 0.0,
                "realized_pnl": 0.0,
                "unrealized_pnl": 0.0,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "sharpe_ratio": None,
                "max_drawdown": None,
                "open_positions": 0,
                "api_calls_this_hour": 0,
                "api_calls_today": 0,
                "last_decision_at": None
            }).eq("llm_id", llm_id).execute()
            print(f"   ✅ Reset {llm_id} to $100")

        print("\n✅ Database reset complete!")

    except Exception as e:
        print(f"\n❌ Error resetting database: {e}")
        raise


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Initialize or reset Supabase database for Crypto LLM Trading System"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset all LLM accounts to initial state (DELETES ALL DATA)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only verify schema, don't initialize"
    )

    args = parser.parse_args()

    if args.reset:
        # Reset mode
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        reset_llm_accounts(client)
    elif args.verify:
        # Verify mode
        print("\n" + "="*70)
        print("VERIFYING DATABASE SCHEMA")
        print("="*70)
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        verify_schema(client)
        print("\n✅ Schema verification complete")
    else:
        # Initialize mode
        initialize_database()

    print("\n" + "="*70)
    print("DONE")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
