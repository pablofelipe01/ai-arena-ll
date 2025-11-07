# AI Arena LL - Crypto LLM Trading System

Sistema automatizado de trading multi-LLM en Binance Futures donde 3 modelos de lenguaje compiten entre sí operando criptomonedas de forma autónoma.

## Descripción del Proyecto

Este proyecto implementa un sistema de trading algorítmico donde 3 LLMs (Large Language Models) compiten entre sí operando futuros perpetuos USDⓈ-M en Binance. Cada LLM tiene $100 USDT virtuales (total $300 en una cuenta real de Binance) y puede operar 6 criptomonedas: ETHUSDT, BNBUSDT, XRPUSDT, DOGEUSDT, ADAUSDT, AVAXUSDT.

### Características Principales

- **Sub-Cuentas Virtuales**: Segregación de $100 por LLM dentro de una sola cuenta Binance
- **API REST (FastAPI)**: Endpoints para que los LLMs envíen sus decisiones de trading
- **Validación y Risk Management**: Prevención de que un LLM afecte negativamente a otros
- **Tracking de P&L Individual**: Balance, métricas y posiciones separadas por LLM
- **Dashboard Web en Tiempo Real**: Visualización del estado de cada LLM
- **Background Jobs**: Actualización automática de P&L, sincronización con Binance, funding fees
- **Base de Datos (Supabase)**: Persistencia de todas las operaciones
- **100% Automatizado**: Los LLMs toman decisiones, el sistema ejecuta sin intervención manual

## Stack Tecnológico

### Backend
- Python 3.9+
- FastAPI - Framework web async
- Uvicorn - ASGI server
- python-binance - Cliente oficial Binance
- Supabase (PostgreSQL) - Base de datos
- APScheduler - Background jobs
- Pydantic - Validación de datos
- WebSockets - Real-time updates

### Frontend
- HTML/CSS/JavaScript vanilla
- Chart.js - Gráficos
- WebSocket client - Updates en tiempo real

### Testing
- pytest - Testing framework
- pytest-asyncio - Async testing
- httpx - HTTP client para testing

## Instalación

### Requisitos Previos

- Python 3.9 o superior
- Cuenta de Binance con acceso a Testnet Futures
- Proyecto de Supabase configurado
- Git

### Paso 1: Clonar el Repositorio

```bash
git clone git@github.com:pablofelipe01/ai-arena-ll.git
cd ai-arena-ll
```

### Paso 2: Crear Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### Paso 3: Instalar Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 4: Configurar Variables de Entorno

1. Copiar el archivo de ejemplo:
```bash
cp .env.example .env
```

2. Editar `.env` con tus credenciales:
```bash
# Binance Testnet
BINANCE_TESTNET_API_KEY=tu_api_key
BINANCE_TESTNET_SECRET_KEY=tu_secret_key

# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_supabase_anon_key
SUPABASE_SERVICE_KEY=tu_supabase_service_key
```

### Paso 5: Inicializar Base de Datos

```bash
python scripts/init_db.py
```

### Paso 6: Inicializar Sistema

```bash
python scripts/init_system.py
```

## Uso

### Ejecutar el Servidor API

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Acceder al Dashboard

Abre tu navegador en: `http://localhost:8000/dashboard`

### Ejecutar Tests

```bash
pytest tests/ -v
```

### Con Coverage

```bash
pytest tests/ --cov=src --cov-report=html
```

## Uso con Docker

### Build y Run

```bash
docker-compose up --build
```

### Solo Run

```bash
docker-compose up
```

### Stop

```bash
docker-compose down
```

## Estructura del Proyecto

```
crypto-llm-trading/
├── config/              # Configuración central
├── src/
│   ├── core/           # Lógica de negocio core
│   ├── api/            # FastAPI application
│   ├── database/       # Supabase client y modelos
│   ├── services/       # Servicios de negocio
│   ├── background/     # Background jobs
│   └── utils/          # Utilidades
├── frontend/           # Dashboard web
├── tests/              # Tests
├── scripts/            # Scripts de utilidad
├── logs/               # Logs
└── docs/               # Documentación adicional
```

## API Endpoints

### LLM Endpoints

- `POST /api/llm/{llm_id}/order` - Crear nueva orden de trading
- `GET /api/llm/{llm_id}/account` - Estado de cuenta del LLM
- `GET /api/llm/{llm_id}/positions` - Posiciones abiertas
- `GET /api/llm/{llm_id}/trades` - Historial de trades
- `POST /api/llm/{llm_id}/close-position` - Cerrar posición específica

### Market Data Endpoints

- `GET /api/market-data/{symbol}` - Datos de mercado para un símbolo
- `GET /api/market-data/all` - Datos de todos los símbolos

### Competition Endpoints

- `GET /api/competition/status` - Estado general de la competición

### WebSocket

- `WS /ws` - WebSocket para updates en tiempo real

## Documentación Adicional

- [Documentación API](docs/API.md)
- [Arquitectura del Sistema](docs/ARCHITECTURE.md)
- [Guía de Deployment](docs/DEPLOYMENT.md)

## Desarrollo

### Code Style

Este proyecto usa `black` para formateo y `ruff` para linting:

```bash
# Formatear código
black src/ tests/

# Linting
ruff check src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Estado del Proyecto

- [x] Phase 0: Setup inicial
- [ ] Phase 1: Configuración base
- [ ] Phase 2: Base de datos
- [ ] Phase 3: Cliente Binance
- [ ] Phase 4: Core logic
- [ ] Phase 5: Services
- [ ] Phase 6: API FastAPI
- [ ] Phase 7: Background jobs
- [ ] Phase 8: Dashboard web
- [ ] Phase 9: Inicialización sistema
- [ ] Phase 10: Testing integral
- [ ] Phase 11: Documentación
- [ ] Phase 12: Deployment

## Contribuir

Este es un proyecto educacional y experimental. Las contribuciones son bienvenidas.

## Advertencia

Este sistema opera con dinero real en Binance. Aunque inicialmente se ejecuta en Testnet, siempre:
- Revisa las órdenes antes de ejecutarlas
- Configura límites de riesgo apropiados
- Nunca uses más capital del que puedas permitirte perder
- Monitorea constantemente el sistema

## Licencia

MIT License

## Contacto

GitHub: [@pablofelipe01](https://github.com/pablofelipe01)
