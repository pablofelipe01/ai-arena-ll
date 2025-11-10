"""
API Dependencies - Service initialization and dependency injection.

Provides singleton instances of all services to FastAPI routes.
"""

from typing import Dict
from decimal import Decimal
from functools import lru_cache

from src.clients.binance_client import BinanceClient
from src.clients.claude_client import ClaudeClient
from src.clients.deepseek_client import DeepSeekClient
from src.clients.openai_client import OpenAIClient
from src.clients.llm_client import BaseLLMClient
from src.database.supabase_client import SupabaseClient
from src.services.market_data_service import MarketDataService
from src.services.indicator_service import IndicatorService
from src.services.account_service import AccountService
from src.services.trading_service import TradingService
from src.core.risk_manager import RiskManager
from src.core.trade_executor import TradeExecutor
from src.utils.logger import app_logger
from config.settings import settings


# ============================================================================
# Service Singletons
# ============================================================================

_binance_client: BinanceClient = None
_supabase_client: SupabaseClient = None
_llm_clients: Dict[str, BaseLLMClient] = None
_market_data_service: MarketDataService = None
_indicator_service: IndicatorService = None
_account_service: AccountService = None
_trading_service: TradingService = None


# ============================================================================
# Service Initializers
# ============================================================================

def get_binance_client() -> BinanceClient:
    """Get or create Binance client singleton."""
    global _binance_client
    if _binance_client is None:
        app_logger.info("Initializing Binance client...")
        _binance_client = BinanceClient(
            api_key=settings.BINANCE_API_KEY,
            api_secret=settings.BINANCE_API_SECRET,
            testnet=settings.BINANCE_TESTNET
        )
        app_logger.info("Binance client initialized")
    return _binance_client


def get_supabase_client() -> SupabaseClient:
    """Get or create Supabase client singleton."""
    global _supabase_client
    if _supabase_client is None:
        app_logger.info("Initializing Supabase client...")
        _supabase_client = SupabaseClient(
            url=settings.SUPABASE_URL,
            key=settings.SUPABASE_KEY
        )
        app_logger.info("Supabase client initialized")
    return _supabase_client


def get_llm_clients() -> Dict[str, BaseLLMClient]:
    """Get or create LLM clients singleton."""
    global _llm_clients
    if _llm_clients is None:
        app_logger.info("Initializing LLM clients...")
        _llm_clients = {
            "LLM-A": ClaudeClient(
                api_key=settings.ANTHROPIC_API_KEY,
                llm_id="LLM-A",
                personality="conservative"
            ),
            "LLM-B": DeepSeekClient(
                api_key=settings.DEEPSEEK_API_KEY,
                llm_id="LLM-B",
                personality="balanced"
            ),
            "LLM-C": OpenAIClient(
                api_key=settings.OPENAI_API_KEY,
                llm_id="LLM-C",
                personality="aggressive"
            )
        }
        app_logger.info(f"Initialized {len(_llm_clients)} LLM clients")
    return _llm_clients


def get_market_data_service() -> MarketDataService:
    """Get or create MarketDataService singleton."""
    global _market_data_service
    if _market_data_service is None:
        app_logger.info("Initializing MarketDataService...")
        binance = get_binance_client()
        _market_data_service = MarketDataService(
            binance_client=binance,
            cache_ttl=60  # 60 seconds cache
        )
        app_logger.info("MarketDataService initialized")
    return _market_data_service


def get_indicator_service() -> IndicatorService:
    """Get or create IndicatorService singleton."""
    global _indicator_service
    if _indicator_service is None:
        app_logger.info("Initializing IndicatorService...")
        market_data = get_market_data_service()
        _indicator_service = IndicatorService(market_data)
        app_logger.info("IndicatorService initialized")
    return _indicator_service


def get_account_service() -> AccountService:
    """Get or create AccountService singleton."""
    global _account_service
    if _account_service is None:
        app_logger.info("Initializing AccountService...")
        supabase = get_supabase_client()
        _account_service = AccountService(
            supabase_client=supabase,
            initial_balance=Decimal(str(settings.INITIAL_BALANCE_USDT))
        )
        app_logger.info("AccountService initialized")
    return _account_service


def get_trading_service() -> TradingService:
    """Get or create TradingService singleton."""
    global _trading_service
    if _trading_service is None:
        app_logger.info("Initializing TradingService...")

        # Get dependencies
        market_data = get_market_data_service()
        indicators = get_indicator_service()
        accounts = get_account_service()
        supabase = get_supabase_client()
        binance = get_binance_client()
        llm_clients = get_llm_clients()

        # Create core components
        risk_manager = RiskManager()
        trade_executor = TradeExecutor(binance_client=binance)

        # Create trading service
        _trading_service = TradingService(
            market_data_service=market_data,
            indicator_service=indicators,
            account_service=accounts,
            risk_manager=risk_manager,
            trade_executor=trade_executor,
            llm_clients=llm_clients,
            supabase_client=supabase
        )

        app_logger.info("TradingService initialized")
    return _trading_service


# ============================================================================
# FastAPI Dependencies
# ============================================================================

def get_trading_service_dependency() -> TradingService:
    """
    FastAPI dependency for TradingService.

    Use in route:
        @app.get("/status")
        async def status(service: TradingService = Depends(get_trading_service_dependency)):
            return service.get_trading_status()
    """
    return get_trading_service()


def get_market_data_service_dependency() -> MarketDataService:
    """FastAPI dependency for MarketDataService."""
    return get_market_data_service()


def get_indicator_service_dependency() -> IndicatorService:
    """FastAPI dependency for IndicatorService."""
    return get_indicator_service()


def get_account_service_dependency() -> AccountService:
    """FastAPI dependency for AccountService."""
    return get_account_service()


# ============================================================================
# Lifecycle Management
# ============================================================================

def initialize_all_services() -> None:
    """
    Initialize all services on startup.

    Call this in FastAPI startup event:
        @app.on_event("startup")
        async def startup_event():
            initialize_all_services()
    """
    app_logger.info("=" * 60)
    app_logger.info("Initializing all services...")
    app_logger.info("=" * 60)

    # Initialize in dependency order
    get_binance_client()
    get_supabase_client()
    get_llm_clients()
    get_market_data_service()
    get_indicator_service()
    get_account_service()
    get_trading_service()

    app_logger.info("=" * 60)
    app_logger.info("All services initialized successfully")
    app_logger.info("=" * 60)


def cleanup_all_services() -> None:
    """
    Cleanup all services on shutdown.

    Call this in FastAPI shutdown event:
        @app.on_event("shutdown")
        async def shutdown_event():
            cleanup_all_services()
    """
    app_logger.info("Cleaning up services...")

    global _binance_client, _supabase_client, _llm_clients
    global _market_data_service, _indicator_service, _account_service, _trading_service

    # Reset all singletons
    _binance_client = None
    _supabase_client = None
    _llm_clients = None
    _market_data_service = None
    _indicator_service = None
    _account_service = None
    _trading_service = None

    app_logger.info("Services cleaned up")
