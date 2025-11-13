# Validación de Margen antes de Crear Grids

## Descripción

El sistema ahora valida que haya suficiente **margen disponible** antes de crear un nuevo grid trading. Esto previene errores de "insufficient balance" cuando se usa capital real limitado.

## Cómo Funciona

### Cálculo del Margen Requerido

Cuando un LLM decide crear un nuevo grid, el sistema calcula el margen necesario para el **peor caso** (todas las órdenes del grid ejecutadas):

```
Margen Requerido = Investment USD ÷ Leverage
```

### Ejemplo Real

```python
# Grid propuesto por LLM
Investment: $150
Leverage: 3x
Grid Levels: 5

# Cálculo
Margen Requerido = $150 ÷ 3 = $50

# Validación
Balance Disponible: $45 ❌ RECHAZADO
Balance Disponible: $60 ✅ APROBADO
```

## Implementación

**Ubicación**: `src/services/trading_service.py:482-510`

### Proceso de Validación

1. **Extrae configuración del grid**
   ```python
   investment_usd = Decimal(str(grid_config_data["investment_usd"]))
   leverage = grid_config_data["leverage"]
   ```

2. **Calcula margen requerido**
   ```python
   margin_required = investment_usd / Decimal(str(leverage))
   ```

3. **Obtiene balance disponible de Binance**
   ```python
   available_balance = self.executor.binance.get_available_balance()
   ```

4. **Valida y rechaza si no hay fondos**
   ```python
   if available_balance < margin_required:
       # Rechaza grid creation
       # Envía notificación de Telegram
       return {"status": "REJECTED", "message": "Insufficient margin"}
   ```

## Notificaciones

Cuando se rechaza un grid por fondos insuficientes, se envía una notificación de Telegram:

```
⚠️ ERROR: Insufficient Margin

Type: Insufficient Margin
LLM: LLM-A - ETHUSDT
Details: Required: $50.00, Available: $45.00
Time: 2025-11-12 16:45:23
```

## Escenario con $600 en Cuenta Real

### División de Capital
- **Total**: $600
- **Por LLM**: $200 cada uno (LLM-A, LLM-B, LLM-C)

### Ejemplo de Creación de Grids

```
LLM-A: $200 disponible
  Grid 1: Investment $150, Leverage 3x → Margen $50 ✅
  Queda: $150 disponible

  Grid 2: Investment $180, Leverage 3x → Margen $60 ✅
  Queda: $90 disponible

  Grid 3: Investment $150, Leverage 3x → Margen $50 ✅
  Queda: $40 disponible

  Grid 4: Investment $150, Leverage 3x → Margen $50 ❌
  RECHAZADO: Solo $40 disponible, se requieren $50
```

## Consideraciones Importantes

### 1. Órdenes LIMIT no consumen margen hasta ejecutarse
```
Grid con 5 niveles, $150 investment:
- 5 órdenes LIMIT colocadas → Margen usado: $0
- 2 órdenes ejecutadas → Margen usado: ~$20
- Todas ejecutadas (peor caso) → Margen usado: ~$50
```

### 2. La validación usa el PEOR CASO
El sistema valida para el escenario donde **todas las órdenes del grid se ejecutan simultáneamente**, garantizando que siempre haya margen suficiente.

### 3. Balance vs Margen
- **Balance Total**: Todo el capital en la cuenta
- **Balance Disponible**: Capital no usado en margen de posiciones abiertas
- **Margen Usado**: Capital bloqueado para posiciones abiertas

## Configuración Recomendada para $600

Para optimizar el uso de capital con $600:

```bash
# .env
INITIAL_BALANCE_PER_LLM=200.0    # $200 cada LLM
MIN_TRADE_SIZE_USD=100.0         # Mínimo $100 por grid
MAX_TRADE_SIZE_USD=200.0         # Máximo $200 por grid
MAX_OPEN_POSITIONS=3             # Máximo 3 grids por LLM
RECOMMENDED_LEVERAGE=3           # Leverage 3x
```

Esto permite:
- **3 grids por LLM** con investment $100-$200
- **Margen por grid**: $33-$67 (con leverage 3x)
- **Total grids sistema**: 9 grids máximo (3 LLMs × 3 grids)
- **Margen total usado**: ~$300-$600 (50-100% del capital)

## Logs y Debugging

### Log cuando se rechaza por margen insuficiente:
```
WARNING | [LLM-A] Grid creation rejected: Insufficient margin: $45.00 available, $50.00 required ($150 / 3x)
```

### Log cuando se aprueba:
```
INFO | [LLM-A] Grid created and orders placed for ETHUSDT: $3300.00-$3660.00, 5 levels, arithmetic spacing, 5 orders placed
```

## Ventajas de esta Validación

✅ **Previene errores en Binance**: No se intenta crear grids sin fondos
✅ **Notificaciones inmediatas**: Telegram alerta cuando falta capital
✅ **Protege el capital**: Evita sobreapalancamiento accidental
✅ **Logs claros**: Fácil debugging de problemas de fondos
✅ **Calcula peor caso**: Garantiza margen para todas las órdenes
