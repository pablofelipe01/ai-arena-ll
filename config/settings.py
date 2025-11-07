"""
Configuración central del sistema de trading multi-LLM.
Carga variables de entorno y proporciona acceso type-safe a la configuración.
"""

from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from typing import List, Optional
from dotenv import load_dotenv
import logging

# Cargar variables de entorno
load_dotenv()

# Logger para este módulo
logger = logging.getLogger(__name__)


class LLMConfig(BaseModel):
    """Configuración de un LLM específico."""

    provider: str  # 'claude', 'deepseek', 'openai'
    model: str
    max_tokens: int = 4000
    temperature: float
    base_url: Optional[str] = None  # Solo para DeepSeek

    class Config:
        frozen = True  # Inmutable


class Settings(BaseSettings):
    """Configuración principal del sistema."""

    # ============================================
    # ENVIRONMENT
    # ============================================
    ENVIRONMENT: str = "testnet"
    DEBUG: bool = True

    # ============================================
    # BINANCE API
    # ============================================
    BINANCE_TESTNET_API_KEY: str
    BINANCE_TESTNET_SECRET_KEY: str
    BINANCE_TESTNET_BASE_URL: str = "https://testnet.binancefuture.com"

    BINANCE_API_KEY: str = ""
    BINANCE_SECRET_KEY: str = ""
    BINANCE_BASE_URL: str = "https://fapi.binance.com"

    USE_TESTNET: bool = True

    # ============================================
    # SUPABASE
    # ============================================
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str = ""

    # ============================================
    # LLM API KEYS (Optional para flexibilidad)
    # ============================================
    CLAUDE_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # ============================================
    # LLM CONFIGURATION
    # ============================================

    # LLM-A: Claude (Conservador)
    LLM_A_PROVIDER: str = "claude"
    LLM_A_MODEL: str = "claude-sonnet-4-20250514"
    LLM_A_MAX_TOKENS: int = 4000
    LLM_A_TEMPERATURE: float = 0.5

    # LLM-B: DeepSeek (Balanceado)
    LLM_B_PROVIDER: str = "deepseek"
    LLM_B_MODEL: str = "deepseek-chat"
    LLM_B_MAX_TOKENS: int = 4000
    LLM_B_TEMPERATURE: float = 0.7
    LLM_B_BASE_URL: str = "https://api.deepseek.com"

    # LLM-C: GPT-4o (Agresivo)
    LLM_C_PROVIDER: str = "openai"
    LLM_C_MODEL: str = "gpt-4o"
    LLM_C_MAX_TOKENS: int = 4000
    LLM_C_TEMPERATURE: float = 0.9

    # ============================================
    # LLM DECISION MAKING
    # ============================================
    LLM_DECISION_INTERVAL_SECONDS: int = 300
    LLM_MAX_DECISIONS_PER_HOUR: int = 12
    LLM_MAX_RETRIES: int = 1
    LLM_RETRY_DELAY_SECONDS: int = 10
    LLM_TIMEOUT_SECONDS: int = 60

    # Logging
    SAVE_REASONING: bool = True
    SAVE_REJECTED_DECISIONS: bool = True
    REJECTED_DECISIONS_SAMPLE_RATE: float = 0.10

    # Validation
    STRICT_API_KEY_VALIDATION: bool = False  # True en producción

    # ============================================
    # APP CONFIGURATION
    # ============================================
    INITIAL_BALANCE_PER_LLM: float = 100.0
    TOTAL_LLMS: int = 3

    # ============================================
    # TRADING CONFIGURATION
    # ============================================
    AVAILABLE_PAIRS: str = "ETHUSDT,BNBUSDT,XRPUSDT,DOGEUSDT,ADAUSDT,AVAXUSDT"
    MIN_TRADE_SIZE_USD: float = 5.0
    MAX_TRADE_SIZE_USD: float = 40.0
    MAX_POSITION_PCT: float = 0.40
    MAX_OPEN_POSITIONS: int = 5
    MAX_POSITIONS_PER_ASSET: int = 2
    MAX_LEVERAGE: int = 10
    RECOMMENDED_LEVERAGE: int = 3
    MAX_MARGIN_USAGE: float = 0.80

    # ============================================
    # BACKGROUND JOBS INTERVALS (seconds)
    # ============================================
    UPDATE_MARKET_DATA_INTERVAL: int = 60
    SYNC_POSITIONS_INTERVAL: int = 300
    UPDATE_PNL_INTERVAL: int = 300
    CHECK_LIQUIDATION_INTERVAL: int = 300

    # ============================================
    # API SERVER
    # ============================================
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    # ============================================
    # LOGGING
    # ============================================
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "logs/app.log"
    LLM_DECISIONS_LOG_PATH: str = "logs/llm_decisions.log"

    # ============================================
    # PROPERTIES
    # ============================================

    @property
    def binance_api_key(self) -> str:
        """Obtener API key de Binance según entorno."""
        return self.BINANCE_TESTNET_API_KEY if self.USE_TESTNET else self.BINANCE_API_KEY

    @property
    def binance_secret_key(self) -> str:
        """Obtener secret key de Binance según entorno."""
        return self.BINANCE_TESTNET_SECRET_KEY if self.USE_TESTNET else self.BINANCE_SECRET_KEY

    @property
    def binance_base_url(self) -> str:
        """Obtener base URL de Binance según entorno."""
        return self.BINANCE_TESTNET_BASE_URL if self.USE_TESTNET else self.BINANCE_BASE_URL

    @property
    def available_pairs_list(self) -> List[str]:
        """Lista de pares disponibles para trading."""
        return [pair.strip().upper() for pair in self.AVAILABLE_PAIRS.split(',')]

    @property
    def llm_apis_configured(self) -> dict:
        """Verificar qué LLM APIs están configuradas."""
        return {
            'LLM-A': bool(self.CLAUDE_API_KEY and self.CLAUDE_API_KEY.startswith('sk-')),
            'LLM-B': bool(self.DEEPSEEK_API_KEY and self.DEEPSEEK_API_KEY.startswith('sk-')),
            'LLM-C': bool(self.OPENAI_API_KEY and self.OPENAI_API_KEY.startswith('sk-'))
        }

    @property
    def active_llms(self) -> List[str]:
        """Lista de LLMs con API keys configuradas."""
        return [llm_id for llm_id, configured in self.llm_apis_configured.items() if configured]

    # ============================================
    # MÉTODOS
    # ============================================

    def get_llm_config(self, llm_id: str) -> LLMConfig:
        """
        Obtener configuración de un LLM específico.

        Args:
            llm_id: ID del LLM ('LLM-A', 'LLM-B', 'LLM-C')

        Returns:
            LLMConfig: Configuración del LLM

        Raises:
            ValueError: Si el LLM ID es inválido
        """
        if llm_id not in ['LLM-A', 'LLM-B', 'LLM-C']:
            raise ValueError(f"Invalid LLM ID: {llm_id}. Must be 'LLM-A', 'LLM-B', or 'LLM-C'")

        letter = llm_id.split('-')[1]  # 'A', 'B', 'C'

        return LLMConfig(
            provider=getattr(self, f"LLM_{letter}_PROVIDER"),
            model=getattr(self, f"LLM_{letter}_MODEL"),
            max_tokens=getattr(self, f"LLM_{letter}_MAX_TOKENS"),
            temperature=getattr(self, f"LLM_{letter}_TEMPERATURE"),
            base_url=getattr(self, f"LLM_{letter}_BASE_URL", None)
        )

    def get_llm_api_key(self, llm_id: str) -> Optional[str]:
        """
        Obtener API key de un LLM específico.

        Args:
            llm_id: ID del LLM ('LLM-A', 'LLM-B', 'LLM-C')

        Returns:
            API key del LLM o None si no está configurada
        """
        llm_to_key = {
            'LLM-A': self.CLAUDE_API_KEY,
            'LLM-B': self.DEEPSEEK_API_KEY,
            'LLM-C': self.OPENAI_API_KEY
        }
        return llm_to_key.get(llm_id)

    def validate_llm_keys(self) -> List[str]:
        """
        Validar que haya al menos un LLM configurado.

        Returns:
            Lista de LLMs activos

        Raises:
            ValueError: Si no hay LLMs configurados o falta alguno en modo strict
        """
        configured = self.llm_apis_configured
        missing = [llm for llm, ok in configured.items() if not ok]

        if missing:
            message = f"Missing LLM API keys for: {', '.join(missing)}"

            # Strict en producción o si se solicita explícitamente
            if self.STRICT_API_KEY_VALIDATION or self.ENVIRONMENT == 'production':
                raise ValueError(f"❌ CRITICAL: {message}")
            else:
                logger.warning(f"⚠️  {message} - These LLMs will be skipped in background jobs")

        active = self.active_llms
        if not active:
            raise ValueError("❌ CRITICAL: No LLM API keys configured. System cannot operate.")

        logger.info(f"✅ Active LLMs: {', '.join(active)}")
        return active

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignorar variables de entorno extra


# ============================================
# SINGLETON INSTANCE
# ============================================

settings = Settings()
