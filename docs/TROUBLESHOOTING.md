# Troubleshooting Guide - Grid Trading System

Esta guía contiene soluciones a problemas comunes que pueden surgir durante la configuración y operación del sistema.

---

## Problemas de Base de Datos (Supabase)

### ❌ Error: "Could not find the 'balance' column"

**Error completo:**
```
Database error: Failed to upsert account: Could not find the 'balance' column of 'llm_accounts' in the schema cache
```

**Causa:**
El código busca la columna `balance` pero la tabla tiene `current_balance`.

**Solución:**
1. Ve a Supabase SQL Editor
2. Ejecuta el script de corrección:
   - Abre: `scripts/fix_schema.sql`
   - Copia TODO el contenido
   - Pega en SQL Editor
   - Haz clic en "Run"
3. Reinicia el servidor

---

### ❌ Error: "Could not find the 'cost_usd' column in llm_decisions"

**Error completo:**
```
Error inserting LLM decision: Could not find the 'cost_usd' column of 'llm_decisions' in the schema cache
```

**Causa:**
La tabla `llm_decisions` tiene un schema viejo que no incluye las columnas necesarias para el grid trading.

**Solución:**
Mismo que el error anterior - ejecuta `scripts/fix_schema.sql` en Supabase SQL Editor. Este script recreará la tabla con las columnas correctas:
- `cost_usd`
- `tokens_used`
- `response_time_ms`
- `execution_status`
- `execution_message`

---

### ❌ Error: "'SupabaseClient' object has no attribute 'insert_market_data'"

**Error completo:**
```
'SupabaseClient' object has no attribute 'insert_market_data'
```

**Causa:**
Falta el método `insert_market_data` en el cliente de Supabase.

**Solución:**
Este error ya está corregido en la versión actual del código. Si lo ves:
1. Haz `git pull` para obtener la última versión
2. O verifica que `src/database/supabase_client.py` tenga el método:
   ```python
   def insert_market_data(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
       return self.upsert_market_data(market_data)
   ```

---

## Problemas de Binance API

### ❌ Error -4061: "Order's position side does not match user's setting"

**Error completo:**
```
APIError(code=-4061): Order's position side does not match user's setting
```

**Causa:**
La cuenta de Binance Futures está en "Hedge Mode" pero el sistema requiere "One-way Mode".

**Solución:**
1. Ir a Binance Futures UI: https://www.binance.com/en/futures/BTCUSDT
2. En la esquina superior derecha, busca "Position Mode"
3. Cambia de "Hedge Mode" a "One-way Mode"
4. Reinicia el servidor

**Diferencia:**
- **One-way Mode**: Solo puedes tener UNA posición por símbolo (LONG o SHORT)
- **Hedge Mode**: Puedes tener LONG y SHORT simultáneamente

---

### ❌ Error -2015: "Invalid API-key, IP, or permissions"

**Error completo:**
```
APIError(code=-2015): Invalid API-key, IP, or permissions for action
```

**Causas posibles:**

1. **API Key sin permiso "Enable Futures":**
   - Ve a Binance → API Management
   - Edita tu API Key
   - Verifica que tenga: ✅ "Enable Futures" (o "Enable Portfolio Margin Trading" en mainnet)

2. **IP no autorizada (si usas IP Whitelist):**
   ```bash
   # Ver tu IP actual:
   curl ifconfig.me
   ```
   - Ir a Binance → API Management → Edit restrictions
   - Agregar tu IP a la lista blanca
   - Nota: Si tienes IP dinámica, considera:
     - No usar IP Whitelist (menos seguro)
     - Usar un servicio con IP fija
     - Actualizar manualmente cuando cambie

3. **API Key incorrecta en `.env`:**
   - Verifica que copiaste correctamente:
     - `BINANCE_API_KEY`
     - `BINANCE_SECRET_KEY`
   - Sin espacios al inicio/final

---

## Problemas del Sistema

### ⚠️ Error 500 en `/trading/binance-status`

**Error en logs:**
```
KeyError: 'Unknown'
2025-11-13 12:01:06 | ERROR | app | Error getting Binance status: 'Unknown'
File "src/api/routes/trading_routes.py", line 658, in get_binance_status
    positions_by_llm[llm_id].append({
KeyError: 'Unknown'
```

**Causa:**
Hay posiciones en Binance que no tienen órdenes asociadas (posiciones "huérfanas" del testnet o sesiones anteriores). El código intenta asignarlas a un LLM pero no puede determinar cuál.

**Solución:**
1. Cerrar todas las posiciones huérfanas:
   ```bash
   python3 scripts/emergency_close_all.py
   ```
2. Cuando pregunte, escribe `YES` y luego `CONFIRM` (si es mainnet)
3. Reinicia el servidor

---

### ❓ Grids creados pero no aparecen en Supabase

**Pregunta:**
"Veo posiciones en Binance pero no hay grids en la tabla `grids` de Supabase"

**Respuesta:**
Esto es **NORMAL**. Los grids se almacenan solo en **RAM (memoria)** del servidor, no en Supabase. Esto es por diseño para mejorar el performance del grid engine.

**Para verificar grids activos:**
```bash
# Opción 1: API
curl http://localhost:8000/trading/grids

# Opción 2: Python
python3 -c "
from src.core.grid_engine import get_grid_engine
engine = get_grid_engine()
print(f'Active grids: {len(engine.active_grids)}')
for grid_id, grid in engine.active_grids.items():
    print(f'  {grid_id}: {grid.config.symbol}')
"
```

**Lo que SÍ se guarda en Supabase:**
- ✅ `llm_decisions`: Decisiones de crear/parar grids
- ✅ `positions`: Posiciones abiertas (sincronizadas desde Binance)
- ✅ `closed_trades`: Historial de trades cerrados
- ✅ `llm_accounts`: Balances y estadísticas

**¿Qué pasa si el servidor se reinicia?**
Los grids en RAM se pierden, pero las posiciones y órdenes siguen en Binance. El sistema tiene mecanismos de sincronización para recuperar el estado desde Binance al reiniciar.

---

## Problemas de Configuración

### ❌ "ModuleNotFoundError: No module named 'src.db'"

**Error completo:**
```
from src.db.supabase_client import get_supabase_client
ModuleNotFoundError: No module named 'src.db'
```

**Causa:**
El código intenta importar desde `src.db` pero el módulo correcto es `src.database`.

**Solución:**
Este script está desactualizado. Cambia:
```python
from src.db.supabase_client import get_supabase_client
```
Por:
```python
from src.database.supabase_client import get_supabase_client
```

---

## Verificación del Sistema

### ✅ Test de conexión a Binance Mainnet

Antes de iniciar trading, verifica que todo funcione:

```bash
python3 scripts/test_mainnet_connection.py
```

**Output esperado:**
```
======================================================================
🔗 TESTING MAINNET CONNECTION
======================================================================

✅ Configuration looks good
   Environment: production
   Use Testnet: False

📡 Connecting to Binance Mainnet...
✅ Connected successfully!

======================================================================
💰 ACCOUNT SUMMARY
======================================================================
Total Wallet Balance:    $628.26 USDT
Available Balance:       $628.26 USDT
Margin Balance:          $628.26 USDT
Unrealized PNL:          $0.00 USDT

Required for experiment: $600.00 USDT
   (3 LLMs × $200.00 each)

✅ Sufficient balance: $628.26 ≥ $600.00

✅ No existing positions - Account is clean

======================================================================
⚙️  RECOMMENDED SETTINGS CHECK
======================================================================

Before starting, verify in Binance UI:
  1. Margin Mode: Should be 'Cross' (not Isolated)
  2. Position Mode: Should be 'One-way Mode'
  3. No existing positions (unless intentional)
```

---

### ✅ Test de conexión a Supabase

```bash
python3 -c "
from src.database.supabase_client import get_supabase_client

print('Testing Supabase connection...')
client = get_supabase_client()
print('✅ Connected!')

# Check llm_accounts
accounts = client._client.table('llm_accounts').select('llm_id, current_balance').execute()
print(f'Found {len(accounts.data)} LLM accounts:')
for acc in accounts.data:
    print(f\"  {acc['llm_id']}: \${acc['current_balance']}\")
"
```

**Output esperado:**
```
Testing Supabase connection...
✅ Connected!
Found 3 LLM accounts:
  LLM-A: $200.0
  LLM-B: $200.0
  LLM-C: $200.0
```

---

## Scripts de Utilidad

### 🔧 Cerrar todas las posiciones (Emergencia)

```bash
python3 scripts/emergency_close_all.py
```

Usa este script si necesitas cerrar TODAS las posiciones y cancelar TODAS las órdenes inmediatamente.

⚠️ **Cuidado**: Cierra posiciones a precio de mercado (puede tener slippage).

---

### 🔧 Reset de base de datos

```bash
python3 scripts/reset_database.py
```

Limpia todas las tablas y resetea los balances de LLM a inicial.

⚠️ **Cuidado**: Esto borra TODO el historial (decisiones, trades, etc).

---

### 🔧 Monitor simple

```bash
python3 scripts/monitor_simple.py
```

Muestra en tiempo real:
- Balances de LLMs
- Posiciones abiertas
- PnL total
- Estado de grids

---

## Contacto y Soporte

Si encuentras un problema no documentado aquí:

1. **Revisa los logs:**
   ```bash
   tail -100 logs/app.log
   ```

2. **Busca el error específico:**
   ```bash
   grep -i "error\|exception" logs/app.log | tail -20
   ```

3. **Reporta el issue:**
   - GitHub: https://github.com/pablofelipe01/ai-arena-ll/issues
   - Incluye:
     - Mensaje de error completo
     - Líneas relevantes de logs
     - Pasos para reproducir

---

**Última actualización:** 2025-11-13
**Versión:** 1.0
