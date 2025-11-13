# Guía de Configuración - AI Arena Trading System

## 📋 Índice

- [Introducción](#introducción)
- [Requisitos Previos](#requisitos-previos)
- [Paso 1: Clonar el Repositorio](#paso-1-clonar-el-repositorio)
- [Paso 2: Instalar Dependencias](#paso-2-instalar-dependencias)
- [Paso 3: Configurar Binance API](#paso-3-configurar-binance-api)
- [Paso 4: Configurar LLM API Keys](#paso-4-configurar-llm-api-keys)
- [Paso 5: Configurar Supabase](#paso-5-configurar-supabase)
- [Paso 6: Configurar Telegram (Opcional)](#paso-6-configurar-telegram-opcional)
- [Paso 7: Configurar Variables de Entorno](#paso-7-configurar-variables-de-entorno)
- [Paso 8: Iniciar el Sistema](#paso-8-iniciar-el-sistema)
- [Paso 9: Monitorear el Sistema](#paso-9-monitorear-el-sistema)
- [Troubleshooting](#troubleshooting)
- [Seguridad y Mejores Prácticas](#seguridad-y-mejores-prácticas)
- [FAQ](#faq)

---

## Introducción

Esta guía te llevará paso a paso para configurar y ejecutar tu propio experimento de **Grid Trading con LLMs Autónomos**.

**⚠️ ADVERTENCIA IMPORTANTE:**
- Este sistema opera con dinero real en Binance Futures
- **Usa solo capital que puedas permitirte perder**
- Se recomienda comenzar en **Testnet** (simulación) antes de usar dinero real
- Este es un experimento académico, no asesoría financiera

**¿Qué vas a construir?**
- Sistema donde 3 LLMs (Claude, DeepSeek, GPT-4o) operan autónomamente
- Grid trading en Binance Futures (USDT-M)
- Monitoreo en tiempo real
- Notificaciones por Telegram

**Tiempo estimado:** 2-3 horas (primera vez)

---

## Requisitos Previos

### 🖥️ Software

1. **Python 3.9 o superior**
   ```bash
   python --version  # Debe mostrar 3.9.x o superior
   ```

2. **Git**
   ```bash
   git --version
   ```

3. **Cuenta de Binance**
   - Crear cuenta en [Binance](https://www.binance.com/)
   - Verificar identidad (KYC) si vas a usar dinero real
   - Activar Binance Futures

4. **API Keys de LLMs**
   - **Claude**: [Anthropic Console](https://console.anthropic.com/)
   - **OpenAI (GPT-4o)**: [OpenAI Platform](https://platform.openai.com/)
   - **DeepSeek**: [DeepSeek Platform](https://platform.deepseek.com/)

5. **Cuenta de Supabase** (Base de datos)
   - Crear cuenta en [Supabase](https://supabase.com/)
   - Plan gratuito es suficiente para empezar

6. **Cuenta de Telegram** (Opcional, para notificaciones)
   - Aplicación de Telegram instalada

### 💰 Presupuesto Estimado

**Testnet (Gratis):**
- Binance Testnet: Gratis
- Supabase: Plan gratuito
- LLM APIs: ~$5-10/día en llamadas

**Mainnet (Dinero Real):**
- Capital de trading: $600 recomendado (mínimo $300)
- LLM APIs: ~$5-10/día
- Fees de trading: ~0.04% por operación

---

## Paso 1: Clonar el Repositorio

### 1.1 Clonar desde GitHub

```bash
# Navegar a tu directorio de proyectos
cd ~/Projects  # O donde prefieras

# Clonar el repositorio
git clone https://github.com/pablofelipe01/ai-arena-ll.git

# Entrar al directorio
cd ai-arena-ll

# Verificar que todo está correcto
ls -la
```

**Deberías ver:**
```
config/
docs/
scripts/
src/
.env.example
.gitignore
README.md
requirements.txt
```

### 1.2 Crear rama de trabajo (Opcional)

```bash
# Crear tu propia rama para experimentar
git checkout -b mi-experimento

# Verificar rama actual
git branch
```

---

## Paso 2: Instalar Dependencias

### 2.1 Crear Entorno Virtual

**Recomendado:** Usar entorno virtual para aislar dependencias.

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En macOS/Linux:
source venv/bin/activate

# En Windows:
venv\Scripts\activate

# Deberías ver (venv) al inicio de tu prompt
```

### 2.2 Instalar Paquetes

```bash
# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación
pip list | grep fastapi  # Debe aparecer fastapi
pip list | grep anthropic  # Debe aparecer anthropic
```

**Principales paquetes instalados:**
- `fastapi` - API REST
- `uvicorn` - Servidor ASGI
- `anthropic` - Cliente de Claude
- `openai` - Cliente de GPT
- `httpx` - Cliente HTTP para DeepSeek
- `supabase` - Cliente de base de datos
- `python-telegram-bot` - Notificaciones
- `requests` - Cliente HTTP
- `python-dotenv` - Variables de entorno

---

## Paso 3: Configurar Binance API

### 3.1 Opción A: Testnet (Recomendado para empezar)

**Testnet es un entorno de simulación con dinero ficticio.**

1. **Ir a Binance Testnet:**
   - Visitar: [https://testnet.binancefuture.com/](https://testnet.binancefuture.com/)
   - Iniciar sesión con tu cuenta de Binance

2. **Crear API Keys:**
   ```
   1. Click en tu perfil (arriba derecha)
   2. "API Management"
   3. "Create API"
   4. Nombrar: "AI Arena Trading Bot"
   5. Guardar API Key y Secret Key ⚠️ (no los perderás, se muestran una vez)
   ```

3. **Configurar Permisos:**
   - ✅ Enable Futures
   - ✅ Enable Reading
   - ❌ NO Enable Withdrawals (por seguridad)

4. **Guardar Keys:**
   ```
   API Key: xxxxx...
   Secret Key: yyyyy...
   ```
   ⚠️ Guardar en lugar seguro (password manager)

### 3.2 Opción B: Mainnet (Dinero Real)

**⚠️ Solo después de probar en Testnet exitosamente.**

1. **Ir a Binance Mainnet:**
   - Visitar: [https://www.binance.com/](https://www.binance.com/)
   - Iniciar sesión

2. **Habilitar Futures Trading:**
   ```
   1. Ir a "Derivatives" > "USDⓈ-M Futures"
   2. Completar quiz de riesgo
   3. Aceptar términos
   ```

3. **Transferir Fondos a Futures:**
   ```
   1. Menú "Wallet" > "Futures"
   2. "Transfer" > From Spot to USDⓈ-M Futures
   3. Transferir USDT (ej: $600)
   ```

4. **Crear API Keys:**
   ```
   1. Perfil > "API Management"
   2. "Create API"
   3. Nombrar: "AI Arena Trading Bot"
   4. Verificación 2FA
   5. Guardar API Key y Secret Key
   ```

5. **Configurar Permisos:**
   - ✅ Enable Futures
   - ✅ Enable Reading
   - ❌ Enable Spot & Margin Trading (no necesario)
   - ❌ Enable Withdrawals (NUNCA habilitar)

6. **Configurar IP Whitelist (Muy Recomendado):**
   ```
   1. En API settings > "Edit restrictions"
   2. "Restrict access to trusted IPs only"
   3. Agregar tu IP pública
   4. Comando para obtener tu IP:
   ```
   ```bash
   curl ifconfig.me
   ```

7. **Configurar Margin Mode:**
   ```
   1. En Futures UI > Settings
   2. Margin Mode: "Cross" (default)
   3. Position Mode: "One-way Mode"
   ```

---

## Paso 4: Configurar LLM API Keys

### 4.1 Anthropic (Claude)

1. **Crear cuenta:**
   - Ir a: [https://console.anthropic.com/](https://console.anthropic.com/)
   - Sign up / Log in

2. **Obtener API Key:**
   ```
   1. Dashboard > "API Keys"
   2. "Create Key"
   3. Nombrar: "AI Arena"
   4. Copiar key (empieza con sk-ant-...)
   ```

3. **Añadir créditos:**
   - Mínimo $5-10 para empezar
   - Settings > Billing > Add credit

4. **Verificar cuota:**
   ```bash
   curl https://api.anthropic.com/v1/messages \
     -H "x-api-key: TU_API_KEY" \
     -H "anthropic-version: 2023-06-01" \
     -H "content-type: application/json" \
     -d '{"model":"claude-sonnet-4-20250514","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
   ```

### 4.2 OpenAI (GPT-4o)

1. **Crear cuenta:**
   - Ir a: [https://platform.openai.com/](https://platform.openai.com/)
   - Sign up / Log in

2. **Obtener API Key:**
   ```
   1. Dashboard > "API keys"
   2. "Create new secret key"
   3. Nombrar: "AI Arena"
   4. Copiar key (empieza con sk-...)
   ```

3. **Añadir créditos:**
   - Settings > Billing > Add payment method
   - Añadir $5-10 iniciales

4. **Verificar:**
   ```bash
   curl https://api.openai.com/v1/chat/completions \
     -H "Authorization: Bearer TU_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"gpt-4o","messages":[{"role":"user","content":"Hi"}],"max_tokens":10}'
   ```

### 4.3 DeepSeek

1. **Crear cuenta:**
   - Ir a: [https://platform.deepseek.com/](https://platform.deepseek.com/)
   - Sign up / Log in

2. **Obtener API Key:**
   ```
   1. Dashboard > "API Keys"
   2. "Create API Key"
   3. Nombrar: "AI Arena"
   4. Copiar key
   ```

3. **Añadir créditos:**
   - Añadir $5-10 iniciales

4. **Verificar:**
   ```bash
   curl https://api.deepseek.com/v1/chat/completions \
     -H "Authorization: Bearer TU_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"Hi"}],"max_tokens":10}'
   ```

---

## Paso 5: Configurar Supabase

### 5.1 Crear Proyecto

1. **Ir a Supabase:**
   - [https://supabase.com/](https://supabase.com/)
   - Sign up / Log in

2. **Crear nuevo proyecto:**
   ```
   1. "New Project"
   2. Nombre: "ai-arena-trading"
   3. Database Password: [crear contraseña fuerte]
   4. Region: Seleccionar más cercano
   5. Pricing Plan: Free (suficiente para empezar)
   6. "Create new project" (tarda ~2 min)
   ```

3. **Obtener credenciales:**
   ```
   1. Settings > API
   2. Copiar:
      - Project URL (https://xxx.supabase.co)
      - anon public key
      - service_role key (⚠️ mantener secreto)
   ```

### 5.2 Crear Tablas

**Opción A: SQL Editor (Recomendado)**

1. Ir a "SQL Editor" en Supabase
2. Crear nuevo query
3. Copiar y ejecutar este SQL:

```sql
-- Tabla de cuentas LLM
CREATE TABLE llm_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    llm_id TEXT UNIQUE NOT NULL,
    initial_balance NUMERIC(20,8) NOT NULL,
    current_balance NUMERIC(20,8) NOT NULL,
    total_pnl NUMERIC(20,8) DEFAULT 0,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de posiciones
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    llm_id TEXT NOT NULL,
    position_id TEXT UNIQUE NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    entry_price NUMERIC(20,8) NOT NULL,
    quantity NUMERIC(20,8) NOT NULL,
    leverage INTEGER NOT NULL,
    stop_loss_price NUMERIC(20,8),
    take_profit_price NUMERIC(20,8),
    status TEXT DEFAULT 'OPEN',
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    pnl NUMERIC(20,8),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de trades cerrados
CREATE TABLE closed_trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    llm_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    entry_price NUMERIC(20,8) NOT NULL,
    exit_price NUMERIC(20,8) NOT NULL,
    quantity NUMERIC(20,8) NOT NULL,
    leverage INTEGER NOT NULL,
    pnl NUMERIC(20,8) NOT NULL,
    pnl_pct NUMERIC(10,4) NOT NULL,
    opened_at TIMESTAMPTZ NOT NULL,
    closed_at TIMESTAMPTZ NOT NULL,
    duration_seconds INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de decisiones LLM
CREATE TABLE llm_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    llm_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    action TEXT NOT NULL,
    symbol TEXT,
    reasoning TEXT,
    confidence NUMERIC(3,2),
    grid_config JSONB,
    status TEXT DEFAULT 'PENDING',
    execution_result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de grids
CREATE TABLE grids (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grid_id TEXT UNIQUE NOT NULL,
    llm_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    status TEXT DEFAULT 'ACTIVE',
    config JSONB NOT NULL,
    cycles_completed INTEGER DEFAULT 0,
    total_profit NUMERIC(20,8) DEFAULT 0,
    total_fees NUMERIC(20,8) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para mejor performance
CREATE INDEX idx_positions_llm_id ON positions(llm_id);
CREATE INDEX idx_positions_status ON positions(status);
CREATE INDEX idx_trades_llm_id ON closed_trades(llm_id);
CREATE INDEX idx_decisions_llm_id ON llm_decisions(llm_id);
CREATE INDEX idx_grids_llm_id ON grids(llm_id);
CREATE INDEX idx_grids_status ON grids(status);

-- Insertar cuentas iniciales para las 3 LLMs
INSERT INTO llm_accounts (llm_id, initial_balance, current_balance)
VALUES
    ('LLM-A', 200.0, 200.0),
    ('LLM-B', 200.0, 200.0),
    ('LLM-C', 200.0, 200.0);
```

4. Click "Run" (abajo derecha)
5. Verificar: Debería mostrar "Success"

**Opción B: Usando script**

```bash
# Desde el directorio del proyecto
python scripts/setup_database.py
```

### 5.3 Verificar Tablas

1. Ir a "Table Editor" en Supabase
2. Deberías ver:
   - llm_accounts
   - positions
   - closed_trades
   - llm_decisions
   - grids

---

## Paso 6: Configurar Telegram (Opcional)

### 6.1 Crear Bot de Telegram

1. **Abrir Telegram**

2. **Buscar BotFather:**
   - Buscar: `@BotFather`
   - Iniciar chat

3. **Crear bot:**
   ```
   /newbot
   ```
   - Nombre: "AI Arena Trading Bot"
   - Username: "mi_arena_bot" (debe ser único y terminar en "bot")

4. **Guardar token:**
   ```
   BotFather responderá con:
   "Use this token to access the HTTP API:
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
   ```
   ⚠️ Guardar este token

### 6.2 Obtener Chat ID

1. **Iniciar chat con tu bot:**
   - Buscar tu bot por username
   - Click "Start"
   - Enviar cualquier mensaje: "Hola"

2. **Obtener Chat ID:**
   ```bash
   # Reemplazar TOKEN con tu bot token
   curl https://api.telegram.org/botTOKEN/getUpdates
   ```

3. **Buscar tu chat_id:**
   ```json
   {
     "result": [
       {
         "message": {
           "chat": {
             "id": 987654321  ← Este es tu chat_id
           }
         }
       }
     ]
   }
   ```

### 6.3 Probar Bot

```bash
# Enviar mensaje de prueba
curl -X POST \
  "https://api.telegram.org/botTOKEN/sendMessage" \
  -d "chat_id=CHAT_ID&text=Prueba desde AI Arena"
```

Deberías recibir el mensaje en Telegram.

### 6.4 Alternativamente: Usar @userinfobot

1. Buscar `@userinfobot` en Telegram
2. Iniciar chat
3. Te mostrará tu `Id:` inmediatamente

---

## Paso 7: Configurar Variables de Entorno

### 7.1 Crear archivo .env

```bash
# Copiar template
cp .env.example .env

# Editar con tu editor favorito
nano .env
# O
vim .env
# O
code .env  # Si usas VS Code
```

### 7.2 Configurar para Testnet

Editar `.env` con estos valores:

```bash
# ============================================
# ENVIRONMENT
# ============================================
ENVIRONMENT=testnet
DEBUG=true

# ============================================
# BINANCE TESTNET API
# ============================================
BINANCE_TESTNET_API_KEY=tu_testnet_api_key_aqui
BINANCE_TESTNET_SECRET_KEY=tu_testnet_secret_key_aqui
BINANCE_TESTNET_BASE_URL=https://testnet.binancefuture.com

# Binance Production (dejar vacío por ahora)
BINANCE_API_KEY=
BINANCE_SECRET_KEY=
BINANCE_BASE_URL=https://fapi.binance.com

# ============================================
# SUPABASE
# ============================================
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_supabase_anon_key_aqui
SUPABASE_SERVICE_KEY=tu_supabase_service_role_key_aqui

# ============================================
# TELEGRAM NOTIFICATIONS
# ============================================
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321
TELEGRAM_NOTIFICATIONS_ENABLED=true  # Cambiar a true si configuraste Telegram

# ============================================
# LLM API KEYS
# ============================================
CLAUDE_API_KEY=sk-ant-tu_api_key_aqui
OPENAI_API_KEY=sk-tu_api_key_aqui
DEEPSEEK_API_KEY=tu_api_key_aqui

# ============================================
# LLM CONFIGURATION
# ============================================
# LLM-A: Claude
LLM_A_PROVIDER=claude
LLM_A_MODEL=claude-sonnet-4-20250514
LLM_A_MAX_TOKENS=4000
LLM_A_TEMPERATURE=0.5

# LLM-B: DeepSeek
LLM_B_PROVIDER=deepseek
LLM_B_MODEL=deepseek-chat
LLM_B_MAX_TOKENS=4000
LLM_B_TEMPERATURE=0.7
LLM_B_BASE_URL=https://api.deepseek.com

# LLM-C: GPT-4o
LLM_C_PROVIDER=openai
LLM_C_MODEL=gpt-4o
LLM_C_MAX_TOKENS=4000
LLM_C_TEMPERATURE=0.9

# ============================================
# LLM DECISION MAKING
# ============================================
LLM_DECISION_INTERVAL_SECONDS=300  # 5 minutos
LLM_MAX_DECISIONS_PER_HOUR=12
LLM_MAX_RETRIES=1
LLM_RETRY_DELAY_SECONDS=10
LLM_TIMEOUT_SECONDS=60

# Logging
SAVE_REASONING=true
SAVE_REJECTED_DECISIONS=true
REJECTED_DECISIONS_SAMPLE_RATE=0.10

# ============================================
# APP CONFIGURATION
# ============================================
USE_TESTNET=true  # MUY IMPORTANTE: true para testnet
INITIAL_BALANCE_PER_LLM=100.0
TOTAL_LLMS=3

# ============================================
# TRADING CONFIGURATION
# ============================================
AVAILABLE_PAIRS=ETHUSDT,BNBUSDT,XRPUSDT,DOGEUSDT,ADAUSDT,AVAXUSDT
MIN_TRADE_SIZE_USD=5.0
MAX_TRADE_SIZE_USD=40.0
MAX_POSITION_PCT=0.40
MAX_OPEN_POSITIONS=5
MAX_POSITIONS_PER_ASSET=2
MAX_LEVERAGE=10
RECOMMENDED_LEVERAGE=3
MAX_MARGIN_USAGE=0.80

# ============================================
# API SERVER
# ============================================
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# ============================================
# LOGGING
# ============================================
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/app.log
LLM_DECISIONS_LOG_PATH=logs/llm_decisions.log
```

### 7.3 Verificar Configuración

```bash
# Crear directorio de logs
mkdir -p logs

# Probar que las variables se cargan
python -c "from config.settings import settings; print(f'Environment: {settings.ENVIRONMENT}'); print(f'Testnet: {settings.USE_TESTNET}')"
```

Debería mostrar:
```
Environment: testnet
Testnet: True
```

---

## Paso 8: Iniciar el Sistema

### 8.1 Verificar Conexiones

Antes de iniciar todo, probar conexiones:

```bash
# Probar conexión a Binance
python -c "from src.clients.binance_client import BinanceClient; client = BinanceClient(testnet=True); print(f'Balance: {client.get_balance()}')"

# Probar conexión a Supabase
python -c "from src.db.supabase_client import get_supabase_client; client = get_supabase_client(); print('Supabase OK')"

# Probar Telegram (si configurado)
python scripts/test_telegram.py
```

### 8.2 Iniciar API Server

```bash
# Activar entorno virtual si no está activo
source venv/bin/activate  # macOS/Linux
# O
venv\Scripts\activate  # Windows

# Iniciar servidor
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --log-level info --reload
```

**Deberías ver:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 8.3 Verificar API

**En otra terminal:**

```bash
# Probar endpoint de status
curl http://localhost:8000/trading/status | python -m json.tool

# Ver documentación interactiva
open http://localhost:8000/docs  # macOS
# O
xdg-open http://localhost:8000/docs  # Linux
# O visitar en navegador
```

### 8.4 Verificar Balance de Testnet

```bash
curl http://localhost:8000/trading/binance-status | python -m json.tool
```

Deberías ver tu balance de testnet (típicamente $10,000 USDT ficticios).

---

## Paso 9: Monitorear el Sistema

### 9.1 Monitor Simple (Recomendado para empezar)

```bash
# En nueva terminal
cd ai-arena-ll
source venv/bin/activate

# Iniciar monitor
python scripts/monitor_simple.py
```

**Verás un dashboard con:**
- Leaderboard de LLMs
- Posiciones abiertas
- Balance en tiempo real
- Resumen de mercado

### 9.2 Ver Logs

```bash
# Logs generales
tail -f logs/app.log

# Logs de decisiones LLM
tail -f logs/llm_decisions.log

# Buscar errores
grep ERROR logs/app.log
```

### 9.3 Comandos Útiles

```bash
# Ver todas las posiciones abiertas
curl http://localhost:8000/trading/positions | python -m json.tool

# Ver leaderboard
curl http://localhost:8000/trading/leaderboard | python -m json.tool

# Ver grids activos
curl http://localhost:8000/grid/grids/LLM-A | python -m json.tool

# Ver últimas decisiones
curl http://localhost:8000/llm/decisions/LLM-A?limit=5 | python -m json.tool
```

### 9.4 Notificaciones Telegram

Si configuraste Telegram, recibirás notificaciones sobre:
- ✅ Grids creados exitosamente
- ❌ Grids rechazados (balance insuficiente)
- ⚠️ Niveles de riesgo ALTO/CRÍTICO
- 🔴 Errores del sistema

---

## Troubleshooting

### Problema: "Module not found"

**Síntoma:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solución:**
```bash
# Verificar que entorno virtual está activo
which python  # Debe mostrar path dentro de venv/

# Reinstalar dependencias
pip install -r requirements.txt
```

### Problema: "Binance API Error 401"

**Síntoma:**
```
BinanceAPIError: API key invalid
```

**Solución:**
1. Verificar que API key es correcta en `.env`
2. Verificar que `USE_TESTNET=true` si usas testnet keys
3. Verificar que key tiene permisos de Futures
4. Regenerar API key si es necesario

### Problema: "Insufficient balance"

**Síntoma:**
```
Insufficient margin: $45.00 available, $50.00 required
```

**Solución (Testnet):**
1. Ir a [https://testnet.binancefuture.com/](https://testnet.binancefuture.com/)
2. Menú superior > "Faucet"
3. Recargar USDT de prueba

**Solución (Mainnet):**
1. Transferir más USDT a Futures
2. O reducir `investment_usd` en parámetros de grid

### Problema: "Supabase connection failed"

**Síntoma:**
```
Error connecting to Supabase
```

**Solución:**
1. Verificar URL y keys en `.env`
2. Verificar que proyecto Supabase está activo
3. Verificar que tablas fueron creadas:
   ```bash
   python -c "from src.db.supabase_client import get_supabase_client; client = get_supabase_client(); print(client.table('llm_accounts').select('*').execute())"
   ```

### Problema: "LLM API rate limit"

**Síntoma:**
```
Rate limit exceeded for Claude API
```

**Solución:**
1. Esperar 1 minuto
2. Verificar créditos en cuenta de LLM
3. Reducir `LLM_MAX_DECISIONS_PER_HOUR` en `.env`
4. Aumentar `LLM_DECISION_INTERVAL_SECONDS`

### Problema: "Port 8000 already in use"

**Síntoma:**
```
ERROR: [Errno 48] Address already in use
```

**Solución:**
```bash
# Encontrar proceso usando puerto 8000
lsof -i :8000

# Matar proceso
kill -9 PID_DEL_PROCESO

# O usar otro puerto
python -m uvicorn src.api.main:app --port 8001
```

### Problema: Telegram no recibe mensajes

**Solución:**
1. Verificar bot token y chat ID en `.env`
2. Verificar `TELEGRAM_NOTIFICATIONS_ENABLED=true`
3. Probar manualmente:
   ```bash
   python scripts/test_telegram.py
   ```
4. Verificar que iniciaste chat con el bot (enviar /start)

---

## Seguridad y Mejores Prácticas

### 🔒 Seguridad de API Keys

1. **NUNCA** compartir tus API keys
2. **NUNCA** commitear `.env` a git (ya está en `.gitignore`)
3. Usar API keys con permisos mínimos necesarios
4. Habilitar IP Whitelist en Binance
5. Usar 2FA en todas las cuentas

### 💰 Gestión de Riesgo

1. **Empezar en Testnet** - Probar 1-2 semanas
2. **Capital pequeño** - $300-600 inicialmente
3. **Monitorear diariamente** - Al menos primeras 2 semanas
4. **Stop loss mental** - Decide pérdida máxima aceptable
5. **No más del 5%** de tu capital total en este experimento

### 📊 Monitoreo

1. **Revisar logs** diariamente
2. **Revisar decisiones LLM** - ¿Son coherentes?
3. **Revisar balance** - Trends de ganancia/pérdida
4. **Telegram alerts** - Responder a riesgos críticos
5. **Supabase dashboard** - Visualizar datos históricos

### 🚫 Lo que NO hacer

❌ Habilitar withdrawals en API keys
❌ Usar más capital del que puedes perder
❌ Ignorar alertas de riesgo CRÍTICO
❌ Modificar código sin entenderlo
❌ Desactivar validaciones de seguridad
❌ Correr 24/7 sin monitorear primeros días

### ✅ Lo que SÍ hacer

✅ Leer toda la documentación
✅ Empezar en testnet
✅ Monitorear regularmente
✅ Mantener backups de configuración
✅ Documentar cambios y resultados
✅ Aprender de errores

---

## FAQ

### ¿Cuánto capital necesito?

**Testnet:** $0 (dinero ficticio)

**Mainnet:**
- Mínimo: $300 ($100/LLM)
- Recomendado: $600 ($200/LLM)
- Por grid: $100-300

### ¿Cuánto cuesta en APIs?

**Estimado diario:**
- Claude: $2-4/día
- GPT-4o: $2-4/día
- DeepSeek: $1-2/día
- **Total: ~$5-10/día**

Depende de:
- Frecuencia de decisiones
- Longitud de prompts
- Cantidad de grids activos

### ¿Puede perder todo mi dinero?

**Sí, potencialmente.** Este es un experimento con LLMs autónomos que:
- Toman decisiones sin supervisión
- No tienen stop loss automático
- Operan con apalancamiento (leverage)

**Por eso:**
- Usa solo capital que puedes perder
- Empieza en testnet
- Monitorea regularmente
- Puedes detener manualmente cuando quieras

### ¿Cuánto tiempo debo correrlo?

**Testnet:** 1-2 semanas para validar

**Mainnet:**
- Mínimo: 2-4 semanas para datos significativos
- Ideal: 1-3 meses para ver patrones
- Puedes parar cuando quieras

### ¿Las LLMs realmente operan solas?

**Sí, 100% autónomos.** Cada 5 minutos:
1. Reciben datos de mercado
2. Analizan grids activos
3. Deciden: crear, modificar, cerrar, o esperar
4. Sistema ejecuta sus decisiones

NO hay intervención humana durante operación.

### ¿Puedo modificar los parámetros?

**Sí**, en `.env`:
- `LLM_DECISION_INTERVAL_SECONDS` - Frecuencia de decisiones
- `INITIAL_BALANCE_PER_LLM` - Capital por LLM
- `MAX_LEVERAGE` - Apalancamiento máximo
- Y más...

**Cuidado:** Cambios pueden afectar performance y riesgo.

### ¿Puedo usar solo 1 o 2 LLMs?

**Sí**, puedes:
1. Comentar LLMs que no quieres en `config/settings.py`
2. O solo configurar API keys de las que quieres usar
3. Ajustar `TOTAL_LLMS` en `.env`

### ¿Funciona 24/7?

**Puede funcionar 24/7** si:
- Tu computadora está encendida
- Servidor API corriendo
- Internet estable

**Recomendación inicial:**
- Correr durante horas de trabajo
- Monitorear regularmente
- Después de 1-2 semanas: considerar 24/7

### ¿Puedo pausar el experimento?

**Sí**, en cualquier momento:

```bash
# Detener API server
CTRL+C en la terminal del servidor

# Las posiciones abiertas permanecen en Binance
# Puedes cerrarlas manualmente desde Binance UI
```

Para **resumir** después:
```bash
# Reiniciar servidor
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### ¿Dónde está la documentación completa?

```
docs/
├── GRID_TRADING_SYSTEM.md  - Explicación completa del sistema
├── SETUP_GUIDE.md           - Esta guía
├── MARGIN_VALIDATION.md     - Validación de margen
└── TELEGRAM_SETUP.md        - Setup detallado de Telegram
```

### ¿Cómo contribuir mejoras?

1. Fork el repositorio
2. Crear rama: `git checkout -b mi-mejora`
3. Hacer cambios
4. Commit: `git commit -m "Descripción"`
5. Push: `git push origin mi-mejora`
6. Crear Pull Request en GitHub

---

## 📞 Soporte

### Encontraste un bug?

1. Revisar [Issues en GitHub](https://github.com/pablofelipe01/ai-arena-ll/issues)
2. Si no existe, crear nuevo issue con:
   - Descripción del problema
   - Pasos para reproducir
   - Logs relevantes
   - Configuración (sin API keys!)

### ¿Preguntas sobre el experimento?

- Revisar `docs/GRID_TRADING_SYSTEM.md`
- Revisar FAQ arriba
- Crear Discussion en GitHub

### ¿Mejoras o ideas?

- Crear issue con tag "enhancement"
- O contribuir directamente con PR

---

## 🎓 Recursos Adicionales

### Binance Futures

- [Binance Futures Guide](https://www.binance.com/en/support/faq/futures)
- [API Documentation](https://binance-docs.github.io/apidocs/futures/en/)
- [Testnet Faucet](https://testnet.binancefuture.com/)

### Grid Trading

- [Grid Trading Explained](https://www.investopedia.com/terms/g/grid-trading.asp)
- [Binance Grid Trading](https://www.binance.com/en/support/faq/grid-trading)

### LLM APIs

- [Anthropic Docs](https://docs.anthropic.com/)
- [OpenAI Docs](https://platform.openai.com/docs)
- [DeepSeek Docs](https://platform.deepseek.com/docs)

---

## ✅ Checklist Final

Antes de comenzar en **Mainnet**, asegúrate de:

- [ ] Probado en Testnet por al menos 1 semana
- [ ] LLMs tomando decisiones coherentes
- [ ] Sistema estable sin crashes
- [ ] Telegram notificaciones funcionando
- [ ] Logs sin errores críticos
- [ ] Entiendes cómo funciona grid trading
- [ ] Entiendes el riesgo y autonomía de LLMs
- [ ] Capital es realmente dinero que puedes perder
- [ ] API keys de Mainnet con IP whitelist
- [ ] 2FA activado en Binance
- [ ] Decisión consciente de proceder

---

## 🚀 ¡Listo para Comenzar!

```bash
# 1. Clonar repo
git clone https://github.com/pablofelipe01/ai-arena-ll.git
cd ai-arena-ll

# 2. Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configurar
cp .env.example .env
nano .env  # Agregar tus API keys

# 4. Iniciar
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Monitorear
python scripts/monitor_simple.py
```

**¡Buena suerte con tu experimento! 🎯**

---

**Última actualización:** 2025-11-13
**Versión:** 1.0
**Autor:** Pablo Felipe
**Repositorio:** [https://github.com/pablofelipe01/ai-arena-ll](https://github.com/pablofelipe01/ai-arena-ll)
