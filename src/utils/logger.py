"""
Sistema de logging para el sistema de trading multi-LLM.

Estrategia:
- Logs de aplicación (app.log): Formato texto estructurado para debugging
- Logs de decisiones LLM (llm_decisions.log): Formato JSON para análisis
- Logs de trades (trades.log): Formato JSON para análisis
- Logs de errores (errors.log): Formato texto detallado
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from typing import Optional


def setup_logger(
    name: str,
    log_file: str,
    level: str = "INFO",
    json_format: bool = False,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Configurar un logger con archivo y consola.

    Args:
        name: Nombre del logger
        log_file: Ruta del archivo de log
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Si True, usa formato JSON. Si False, usa formato texto estructurado
        max_bytes: Tamaño máximo del archivo de log antes de rotation
        backup_count: Número de archivos de backup a mantener

    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Evitar duplicar handlers si el logger ya existe
    if logger.handlers:
        return logger

    # Crear directorio de logs si no existe
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # ============================================
    # FILE HANDLER con rotation
    # ============================================
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, level.upper()))

    # ============================================
    # CONSOLE HANDLER
    # ============================================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    # ============================================
    # FORMATTERS
    # ============================================
    if json_format:
        # Formato JSON para análisis programático
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s',
            rename_fields={
                'asctime': 'timestamp',
                'levelname': 'level',
                'name': 'logger'
            }
        )
    else:
        # Formato texto estructurado para legibilidad
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    file_handler.setFormatter(formatter)

    # Console siempre con formato texto (más legible)
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)

    # ============================================
    # ADD HANDLERS
    # ============================================
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    Obtener un logger existente o crear uno nuevo con configuración por defecto.

    Args:
        name: Nombre del logger (generalmente __name__ del módulo)
        log_level: Nivel de logging opcional (si None, usa INFO)

    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)

    # Si el logger no tiene handlers, configurarlo
    if not logger.handlers:
        logger.setLevel(log_level or "INFO")
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )
        logger.addHandler(handler)

    return logger


# ============================================
# LOGGERS DEL SISTEMA
# ============================================

# Logger principal de la aplicación (texto estructurado)
app_logger = setup_logger(
    name="app",
    log_file="logs/app.log",
    level="INFO",
    json_format=False
)

# Logger de decisiones LLM (JSON para análisis)
llm_decisions_logger = setup_logger(
    name="llm_decisions",
    log_file="logs/llm_decisions.log",
    level="INFO",
    json_format=True
)

# Logger de trades (JSON para análisis)
trades_logger = setup_logger(
    name="trades",
    log_file="logs/trades.log",
    level="INFO",
    json_format=True
)

# Logger de errores (texto detallado)
errors_logger = setup_logger(
    name="errors",
    log_file="logs/errors.log",
    level="ERROR",
    json_format=False
)


# ============================================
# HELPER FUNCTIONS
# ============================================

def log_llm_decision(
    llm_id: str,
    action: str,
    symbol: str = None,
    strategy: str = None,
    reasoning: str = None,
    response_time_ms: int = None,
    **kwargs
):
    """
    Loguear una decisión de LLM en formato estructurado.

    Args:
        llm_id: ID del LLM
        action: Acción tomada (OPEN_POSITION, CLOSE_POSITION, HOLD)
        symbol: Símbolo operado
        strategy: Estrategia utilizada
        reasoning: Razonamiento del LLM
        response_time_ms: Tiempo de respuesta en ms
        **kwargs: Datos adicionales
    """
    llm_decisions_logger.info(
        "LLM Decision",
        extra={
            'llm_id': llm_id,
            'action': action,
            'symbol': symbol,
            'strategy': strategy,
            'reasoning': reasoning,
            'response_time_ms': response_time_ms,
            **kwargs
        }
    )


def log_trade(
    llm_id: str,
    symbol: str,
    side: str,
    quantity: float,
    price: float = None,
    status: str = None,
    pnl: float = None,
    **kwargs
):
    """
    Loguear un trade ejecutado.

    Args:
        llm_id: ID del LLM
        symbol: Símbolo operado
        side: Lado del trade (BUY, SELL)
        quantity: Cantidad
        price: Precio de ejecución
        status: Estado del trade
        pnl: P&L realizado
        **kwargs: Datos adicionales
    """
    trades_logger.info(
        "Trade Executed",
        extra={
            'llm_id': llm_id,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'status': status,
            'pnl': pnl,
            **kwargs
        }
    )


def log_error(
    error_type: str,
    message: str,
    llm_id: str = None,
    **kwargs
):
    """
    Loguear un error del sistema.

    Args:
        error_type: Tipo de error
        message: Mensaje de error
        llm_id: ID del LLM (si aplica)
        **kwargs: Datos adicionales
    """
    errors_logger.error(
        f"{error_type}: {message}",
        extra={
            'error_type': error_type,
            'llm_id': llm_id,
            **kwargs
        }
    )


# ============================================
# EJEMPLO DE USO
# ============================================

if __name__ == "__main__":
    # Ejemplo de logging de aplicación
    app_logger.info("Sistema iniciado")
    app_logger.debug("Modo debug activado")
    app_logger.warning("Advertencia de prueba")

    # Ejemplo de logging de decisión LLM
    log_llm_decision(
        llm_id="LLM-A",
        action="OPEN_POSITION",
        symbol="ETHUSDT",
        strategy="MOMENTUM",
        reasoning="Strong MACD bullish crossover",
        response_time_ms=1234,
        confidence=7.5
    )

    # Ejemplo de logging de trade
    log_trade(
        llm_id="LLM-A",
        symbol="ETHUSDT",
        side="BUY",
        quantity=0.01,
        price=3250.50,
        status="FILLED",
        leverage=3
    )

    # Ejemplo de logging de error
    log_error(
        error_type="LLMAPIError",
        message="Timeout calling Claude API",
        llm_id="LLM-A",
        provider="claude"
    )
