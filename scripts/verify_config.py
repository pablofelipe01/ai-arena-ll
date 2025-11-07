"""
Script para verificar que la configuración del sistema carga correctamente.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from src.utils.logger import app_logger, llm_decisions_logger, log_llm_decision
from src.utils.helpers import (
    format_usd,
    calculate_pnl,
    calculate_liquidation_price,
    calculate_sharpe_ratio
)
from src.utils.exceptions import (
    InsufficientBalanceError,
    LLMAPIError,
    RiskLimitExceededError
)


def verify_settings():
    """Verificar que settings carga correctamente."""
    print("\n" + "="*60)
    print("VERIFICANDO CONFIGURACIÓN")
    print("="*60)

    print(f"\n✅ Environment: {settings.ENVIRONMENT}")
    print(f"✅ Debug: {settings.DEBUG}")
    print(f"✅ Use Testnet: {settings.USE_TESTNET}")

    print(f"\n📊 Binance Config:")
    print(f"   API Key: {settings.binance_api_key[:10]}...{settings.binance_api_key[-10:]}")
    print(f"   Base URL: {settings.binance_base_url}")

    print(f"\n🗄️ Supabase Config:")
    print(f"   URL: {settings.SUPABASE_URL}")
    print(f"   Key: {settings.SUPABASE_KEY[:10]}...{settings.SUPABASE_KEY[-10:]}")

    print(f"\n🤖 LLM Configuration:")
    try:
        active_llms = settings.validate_llm_keys()
        print(f"   Active LLMs: {', '.join(active_llms)}")

        for llm_id in ['LLM-A', 'LLM-B', 'LLM-C']:
            config = settings.get_llm_config(llm_id)
            api_key = settings.get_llm_api_key(llm_id)
            status = "✅" if api_key else "❌"

            print(f"\n   {status} {llm_id}:")
            print(f"      Provider: {config.provider}")
            print(f"      Model: {config.model}")
            print(f"      Temperature: {config.temperature}")
            if api_key:
                print(f"      API Key: {api_key[:10]}...{api_key[-10:]}")

    except ValueError as e:
        print(f"   ⚠️  {str(e)}")

    print(f"\n⚙️  Trading Config:")
    print(f"   Available Pairs: {', '.join(settings.available_pairs_list)}")
    print(f"   Min Trade: {format_usd(settings.MIN_TRADE_SIZE_USD)}")
    print(f"   Max Trade: {format_usd(settings.MAX_TRADE_SIZE_USD)}")
    print(f"   Max Leverage: {settings.MAX_LEVERAGE}x")
    print(f"   Max Positions: {settings.MAX_OPEN_POSITIONS}")

    print(f"\n⏱️  Background Jobs:")
    print(f"   LLM Decision Interval: {settings.LLM_DECISION_INTERVAL_SECONDS}s")
    print(f"   Market Data Update: {settings.UPDATE_MARKET_DATA_INTERVAL}s")


def verify_logger():
    """Verificar que loggers funcionan."""
    print("\n" + "="*60)
    print("VERIFICANDO LOGGERS")
    print("="*60)

    print("\n📝 Testing app logger...")
    app_logger.info("App logger test")
    print("✅ App logger working")

    print("\n📝 Testing LLM decisions logger...")
    log_llm_decision(
        llm_id="LLM-TEST",
        action="HOLD",
        reasoning="Config verification test",
        response_time_ms=100
    )
    print("✅ LLM decisions logger working")


def verify_helpers():
    """Verificar que helpers funcionan."""
    print("\n" + "="*60)
    print("VERIFICANDO HELPERS")
    print("="*60)

    # Test formateo
    print(f"\n💵 Format USD: {format_usd(1234.567)}")

    # Test cálculo P&L
    pnl = calculate_pnl(100, 105, 1.0, "LONG")
    print(f"📈 Calculate P&L: ${pnl} (entry=100, current=105, qty=1, LONG)")

    # Test liquidation price
    liq_price = calculate_liquidation_price(100, 10, "LONG")
    print(f"⚠️  Liquidation Price: ${liq_price:.2f} (entry=100, leverage=10x, LONG)")

    # Test Sharpe ratio
    returns = [0.05, -0.02, 0.03, 0.08, -0.01]
    sharpe = calculate_sharpe_ratio(returns)
    print(f"📊 Sharpe Ratio: {sharpe:.4f}")

    print("\n✅ All helpers working")


def verify_exceptions():
    """Verificar que exceptions funcionan."""
    print("\n" + "="*60)
    print("VERIFICANDO EXCEPTIONS")
    print("="*60)

    try:
        raise InsufficientBalanceError("LLM-A", required=50.0, available=30.0)
    except InsufficientBalanceError as e:
        print(f"✅ InsufficientBalanceError: {e}")

    try:
        raise LLMAPIError("LLM-B", "Timeout", provider="deepseek")
    except LLMAPIError as e:
        print(f"✅ LLMAPIError: {e}")

    try:
        raise RiskLimitExceededError("LLM-C", "Too many positions")
    except RiskLimitExceededError as e:
        print(f"✅ RiskLimitExceededError: {e}")

    print("\n✅ All exceptions working")


def main():
    """Ejecutar todas las verificaciones."""
    try:
        verify_settings()
        verify_logger()
        verify_helpers()
        verify_exceptions()

        print("\n" + "="*60)
        print("✅ ALL VERIFICATIONS PASSED")
        print("="*60)
        print("\n🚀 Phase 1 configuration is ready!\n")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
