# AI Arena LL - Crypto LLM Trading System

Sistema 100% automatizado de trading multi-LLM en Binance Futures donde 3 modelos de lenguaje (Claude, DeepSeek, GPT-4o) compiten entre sí operando criptomonedas de forma autónoma.

## 🎯 Descripción del Proyecto

Este proyecto implementa un sistema de trading algorítmico completamente automatizado donde 3 Large Language Models compiten entre sí operando futuros perpetuos USDⓈ-M en Binance. Cada LLM tiene $100 USDT virtuales (total $300 en una cuenta real de Binance) y puede operar 6 criptomonedas: ETHUSDT, BNBUSDT, XRPUSDT, DOGEUSDT, ADAUSDT, AVAXUSDT.

### 🤖 Los Competidores

- **LLM-A (Claude Sonnet 4)**: Conservador - Temperature 0.5
- **LLM-B (DeepSeek)**: Balanceado - Temperature 0.7
- **LLM-C (GPT-4o)**: Agresivo - Temperature 0.9

### ⚡ Arquitectura Clave

**Sistema → Llama a LLMs cada 5 minutos → Obtiene decisiones → Ejecuta en Binance**

NO son los LLMs quienes envían órdenes al sistema. El sistema llama a las APIs de Claude, DeepSeek y OpenAI para obtener decisiones de trading basadas en:
- Datos de mercado en tiempo real
- Estado de cuenta actual
- Posiciones abiertas
- Indicadores técnicos (RSI, MACD, EMA, ADX, etc.)

### 🚀 Características Principales

- **Sub-Cuentas Virtuales**: Segregación de $100 por LLM dentro de una sola cuenta Binance
- **LLM Integration**: Llamadas automáticas a APIs de Claude, DeepSeek y GPT-4o
- **API REST (FastAPI)**: Endpoints de consulta y monitoreo (solo GET, 100% automatizado)
- **Validación y Risk Management**: Prevención de que un LLM afecte negativamente a otros
- **Tracking de P&L Individual**: Balance, métricas y posiciones separadas por LLM
- **Dashboard Web en Tiempo Real**: Visualización del estado de cada LLM
- **Background Jobs**:
  - Decisiones de LLMs cada 5 minutos
  - Actualización automática de P&L
  - Sincronización con Binance
  - Cálculo de funding fees
- **Base de Datos (Supabase)**: Persistencia de todas las operaciones + reasoning de decisiones
- **100% Automatizado**: Sin intervención manual - solo monitoreo

## 🛠 Stack Tecnológico

### Backend
- **Python 3.11+** - Runtime
- **FastAPI** - Framework web async
- **Uvicorn** - ASGI server
- **python-binance** - Cliente oficial Binance
- **Supabase (PostgreSQL)** - Base de datos
- **APScheduler** - Background jobs
- **Pydantic** - Validación de datos
- **WebSockets** - Real-time updates
- **Anthropic SDK** - Claude API
- **OpenAI SDK** - GPT-4o y DeepSeek APIs
- **pandas-ta** - Indicadores técnicos

### Frontend
- HTML/CSS/JavaScript vanilla
- Chart.js - Gráficos
- WebSocket client - Updates en tiempo real

### Testing
- pytest - Testing framework
- pytest-asyncio - Async testing
- httpx - HTTP client para testing

## 📦 Instalación

### Requisitos Previos

- **Python 3.11 o superior** (requerido)
- Cuenta de Binance con acceso a Testnet Futures
- Proyecto de Supabase configurado
- API Keys de:
  - Anthropic Claude
  - DeepSeek
  - OpenAI
- Git

### Paso 1: Clonar el Repositorio

```bash
git clone git@github.com:pablofelipe01/ai-arena-ll.git
cd ai-arena-ll
```

### Paso 2: Crear Virtual Environment con Python 3.11

```bash
python3.11 -m venv venv
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

# LLM APIs
CLAUDE_API_KEY=tu_claude_api_key
DEEPSEEK_API_KEY=tu_deepseek_api_key
OPENAI_API_KEY=tu_openai_api_key
```

### Paso 5: Inicializar Base de Datos

```bash
python scripts/init_db.py
```

### Paso 6: Inicializar Sistema

```bash
python scripts/init_system.py
```

## 🎮 Uso

### Ejecutar el Servidor API

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

El servidor iniciará:
- **API REST** en `http://localhost:8000`
- **Background Jobs** que llaman a los LLMs cada 5 minutos
- **WebSocket** para updates en tiempo real

### Acceder al Dashboard

Abre tu navegador en: `http://localhost:8000/dashboard`

Verás en tiempo real:
- Balance de cada LLM
- Posiciones abiertas
- P&L realizado y no realizado
- Últimas decisiones tomadas
- Reasoning de cada trade
- Gráficos de performance

### Ejecutar Tests

```bash
pytest tests/ -v
```

### Con Coverage

```bash
pytest tests/ --cov=src --cov-report=html
```

## 🐳 Uso con Docker

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

## 📁 Estructura del Proyecto

```
crypto-llm-trading/
├── config/              # Configuración central
├── src/
│   ├── core/           # Lógica de negocio core
│   ├── api/            # FastAPI application (solo GET endpoints)
│   ├── database/       # Supabase client y modelos
│   ├── services/       # Servicios de negocio
│   │   └── llm_client_service.py  # ⭐ Comunicación con LLMs
│   ├── background/     # Background jobs
│   │   └── jobs.py     # ⭐ llm_decision_job
│   └── utils/          # Utilidades
├── frontend/           # Dashboard web
├── tests/              # Tests
├── scripts/            # Scripts de utilidad
├── logs/               # Logs
│   └── llm_decisions.log  # ⭐ Log de decisiones LLM
└── docs/               # Documentación adicional
```

## 🔌 API Endpoints

### Consulta de Estado (Solo GET - No POST)

**LLM Endpoints:**
- `GET /api/llm/{llm_id}/account` - Estado de cuenta del LLM
- `GET /api/llm/{llm_id}/positions` - Posiciones abiertas
- `GET /api/llm/{llm_id}/trades` - Historial de trades
- `GET /api/llm/{llm_id}/decisions` - Historial de decisiones
- `GET /api/llm/{llm_id}/rejected-decisions` - Decisiones rechazadas

**Market Data Endpoints:**
- `GET /api/market-data/{symbol}` - Datos de mercado para un símbolo
- `GET /api/market-data/all` - Datos de todos los símbolos

**Competition Endpoints:**
- `GET /api/competition/status` - Estado general de la competición
- `GET /api/competition/leaderboard` - Tabla de posiciones

**WebSocket:**
- `WS /ws` - WebSocket para updates en tiempo real

## 🧠 Cómo Funciona la Integración con LLMs

### Ciclo de Decisión (Cada 5 minutos)

1. **Actualización de Market Data**: El sistema obtiene precios, volúmenes, funding rates e indicadores técnicos de Binance

2. **Para cada LLM (A, B, C)**:
   - Prepara contexto completo:
     - Market data actualizado
     - Estado de cuenta (balance, margen, P&L)
     - Posiciones abiertas
     - Reglas de trading

   - Llama a la API del LLM correspondiente:
     - Claude para LLM-A (Temperature 0.5 - Conservador)
     - DeepSeek para LLM-B (Temperature 0.7 - Balanceado)
     - GPT-4o para LLM-C (Temperature 0.9 - Agresivo)

   - El LLM analiza y responde con JSON:
     ```json
     {
       "action": "OPEN_POSITION",
       "symbol": "ETHUSDT",
       "strategy": "MOMENTUM",
       "side": "BUY",
       "leverage": 3,
       "quantity": 0.01,
       "reasoning": "Strong MACD bullish crossover..."
     }
     ```

   - Valida la decisión (risk management, límites)

   - Ejecuta en Binance si es válida

   - Guarda en DB incluyendo el reasoning

3. **Actualización de P&L**: Calcula ganancias/pérdidas de todos

4. **Broadcast via WebSocket**: Envía updates al dashboard

## 📊 Configuración de LLMs

| LLM | Provider | Modelo | Temperature | Personalidad |
|-----|----------|--------|-------------|--------------|
| LLM-A | Claude | claude-sonnet-4-20250514 | 0.5 | Conservador - Prioriza preservación de capital |
| LLM-B | DeepSeek | deepseek-chat | 0.7 | Balanceado - Mix de riesgo/retorno |
| LLM-C | OpenAI | gpt-4o | 0.9 | Agresivo - Maximiza oportunidades |

### Límites y Controles

- **Decisiones**: Máximo 12 por hora (cada 5 minutos)
- **Retries**: 1 reintento si la API falla
- **Timeout**: 60 segundos por llamada
- **Logging**: 100% de decisiones aceptadas + 10% sample de rechazadas

## 🧪 Desarrollo

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

## 📈 Estado del Proyecto

- [x] Phase 0: Setup inicial + LLM integration architecture
- [ ] Phase 1: Configuración base
- [ ] Phase 2: Base de datos
- [ ] Phase 3: Cliente Binance
- [ ] Phase 4: LLM Client Service ⭐
- [ ] Phase 5: Core logic
- [ ] Phase 6: Services
- [ ] Phase 7: API FastAPI
- [ ] Phase 8: Background jobs
- [ ] Phase 9: Dashboard web
- [ ] Phase 10: Inicialización sistema
- [ ] Phase 11: Testing integral
- [ ] Phase 12: Documentación
- [ ] Phase 13: Deployment

## 🤝 Contribuir

Este es un proyecto educacional y experimental. Las contribuciones son bienvenidas.

## ⚠️ Advertencia

Este sistema opera con dinero real en Binance. Aunque inicialmente se ejecuta en Testnet, siempre:
- Revisa los límites de riesgo apropiados
- Monitorea constantemente el sistema
- Nunca uses más capital del que puedas permitirte perder
- Los LLMs pueden tomar decisiones impredecibles
- No garantizamos rentabilidad

## 📄 Licencia

MIT License

## 📧 Contacto

GitHub: [@pablofelipe01](https://github.com/pablofelipe01)

---

**Nota**: Este es un proyecto experimental de investigación en IA aplicada al trading. No constituye asesoría financiera.
