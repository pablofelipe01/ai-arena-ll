"""
Configuración de pytest y fixtures compartidas.
"""

import pytest
import sys
from pathlib import Path

# Agregar el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_llm_ids():
    """IDs de LLMs para testing."""
    return ["LLM-A", "LLM-B", "LLM-C"]


@pytest.fixture
def sample_symbols():
    """Símbolos para testing."""
    return ["ETHUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT"]


@pytest.fixture
def sample_balance():
    """Balance de muestra para testing."""
    return 100.0


@pytest.fixture
def sample_position():
    """Posición de muestra para testing."""
    return {
        "symbol": "ETHUSDT",
        "side": "LONG",
        "entry_price": 3250.00,
        "quantity": 0.01,
        "leverage": 3,
        "margin_used": 10.83
    }
