"""
Script para inicializar la base de datos Supabase.

Este script:
1. Lee el archivo schema.sql
2. Ejecuta el SQL en Supabase para crear todas las tablas
3. Verifica que las tablas se crearon correctamente
4. Inserta los datos iniciales de las 3 cuentas LLM
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from supabase import create_client, Client
from config.settings import settings
from src.utils.logger import app_logger


def read_schema_file() -> str:
    """
    Leer el archivo schema.sql.

    Returns:
        Contenido del archivo SQL
    """
    schema_path = Path(__file__).parent.parent.parent / "database" / "schema.sql"

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        return f.read()


def execute_sql(client: Client, sql: str) -> None:
    """
    Ejecutar SQL en Supabase.

    Args:
        client: Cliente Supabase
        sql: SQL a ejecutar

    Note:
        Supabase no permite ejecutar SQL directamente via API para seguridad.
        Este script requiere que el SQL se ejecute manualmente en la UI de Supabase
        o usando una herramienta como psql.
    """
    app_logger.info("=" * 70)
    app_logger.info("DATABASE INITIALIZATION")
    app_logger.info("=" * 70)

    print("\n" + "=" * 70)
    print("🗄️  SUPABASE DATABASE INITIALIZATION")
    print("=" * 70)
    print("\n⚠️  IMPORTANT: Supabase API does not allow direct SQL execution.")
    print("You need to execute the schema.sql file manually using one of these methods:\n")

    print("📝 METHOD 1: Supabase Dashboard (Recommended)")
    print("-" * 70)
    print(f"1. Go to: {settings.SUPABASE_URL}")
    print("2. Navigate to: SQL Editor (in the left sidebar)")
    print("3. Click: 'New Query'")
    print("4. Copy and paste the contents of: database/schema.sql")
    print("5. Click: 'Run' or press Ctrl+Enter")
    print("6. Verify all tables were created successfully\n")

    print("📝 METHOD 2: psql Command Line")
    print("-" * 70)
    print("1. Get your database connection string from Supabase Dashboard")
    print("2. Go to: Project Settings > Database > Connection String")
    print("3. Run:")
    print(f"   psql <connection_string> -f database/schema.sql\n")

    print("📝 METHOD 3: Supabase CLI")
    print("-" * 70)
    print("1. Install Supabase CLI: npm install -g supabase")
    print("2. Login: supabase login")
    print("3. Link project: supabase link --project-ref <project-ref>")
    print("4. Run migrations: supabase db push\n")

    print("=" * 70)
    print("📄 Schema file location: database/schema.sql")
    print("=" * 70)


def verify_tables(client: Client) -> bool:
    """
    Verificar que las tablas se crearon correctamente.

    Args:
        client: Cliente Supabase

    Returns:
        True si todas las tablas existen
    """
    print("\n🔍 Verifying database tables...")

    required_tables = [
        "llm_accounts",
        "positions",
        "trades",
        "orders",
        "market_data",
        "rejected_decisions",
        "llm_api_calls"
    ]

    all_exist = True

    for table_name in required_tables:
        try:
            # Try to query the table
            client.table(table_name).select("*").limit(1).execute()
            print(f"   ✅ {table_name}")
        except Exception as e:
            print(f"   ❌ {table_name} - {str(e)}")
            all_exist = False

    return all_exist


def verify_llm_accounts(client: Client) -> bool:
    """
    Verificar que las cuentas LLM se crearon correctamente.

    Args:
        client: Cliente Supabase

    Returns:
        True si las 3 cuentas existen
    """
    print("\n🤖 Verifying LLM accounts...")

    try:
        response = client.table("llm_accounts").select("llm_id, provider, model, balance").execute()

        if not response.data:
            print("   ❌ No LLM accounts found")
            return False

        if len(response.data) < 3:
            print(f"   ⚠️  Only {len(response.data)} accounts found (expected 3)")

        for account in response.data:
            print(f"   ✅ {account['llm_id']} ({account['provider']}) - ${account['balance']} USDT")

        return len(response.data) >= 3

    except Exception as e:
        print(f"   ❌ Error verifying LLM accounts: {e}")
        return False


def verify_views(client: Client) -> bool:
    """
    Verificar que las vistas se crearon correctamente.

    Args:
        client: Cliente Supabase

    Returns:
        True si todas las vistas existen
    """
    print("\n👁️  Verifying database views...")

    required_views = [
        "llm_leaderboard",
        "active_positions_summary",
        "llm_trading_stats"
    ]

    all_exist = True

    for view_name in required_views:
        try:
            client.table(view_name).select("*").limit(1).execute()
            print(f"   ✅ {view_name}")
        except Exception as e:
            print(f"   ❌ {view_name} - {str(e)}")
            all_exist = False

    return all_exist


def main():
    """Ejecutar inicialización de base de datos."""
    try:
        print("\n🚀 Starting database initialization...\n")

        # Leer schema
        print("📖 Reading schema.sql...")
        schema_sql = read_schema_file()
        print(f"   ✅ Loaded {len(schema_sql)} characters of SQL")

        # Conectar a Supabase
        print("\n🔌 Connecting to Supabase...")
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        print(f"   ✅ Connected to {settings.SUPABASE_URL}")

        # Mostrar instrucciones para ejecutar SQL
        execute_sql(client, schema_sql)

        # Preguntar si el usuario ya ejecutó el SQL
        print("\n" + "=" * 70)
        response = input("\n❓ Have you executed the schema.sql in Supabase? (yes/no): ").strip().lower()

        if response not in ['yes', 'y', 'si', 's']:
            print("\n⚠️  Please execute the schema.sql first, then run this script again.")
            print("   Run: python src/database/init_db.py\n")
            return

        # Verificar tablas
        print("\n" + "=" * 70)
        print("🔍 VERIFICATION")
        print("=" * 70)

        tables_ok = verify_tables(client)
        accounts_ok = verify_llm_accounts(client)
        views_ok = verify_views(client)

        # Resultado final
        print("\n" + "=" * 70)

        if tables_ok and accounts_ok and views_ok:
            print("✅ DATABASE INITIALIZATION SUCCESSFUL")
            print("=" * 70)
            print("\n🎉 All tables, views, and initial data are ready!")
            print("\n📊 You can now:")
            print("   - Run the trading system")
            print("   - Start the API server")
            print("   - View the dashboard")
            print("\n💡 Next step: python scripts/verify_config.py")
            print()
        else:
            print("❌ DATABASE INITIALIZATION INCOMPLETE")
            print("=" * 70)
            print("\n⚠️  Some issues were found:")
            if not tables_ok:
                print("   - Not all tables were created")
            if not accounts_ok:
                print("   - LLM accounts are missing")
            if not views_ok:
                print("   - Database views are missing")
            print("\n💡 Please check the SQL execution for errors and try again.")
            print()
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"\n❌ ERROR: {e}")
        print("   Make sure you're running this script from the project root.")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
