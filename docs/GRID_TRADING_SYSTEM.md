# Sistema de Grid Trading Autónomo con LLMs

## 📋 Tabla de Contenidos

- [¿Qué es Grid Trading?](#qué-es-grid-trading)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Rol de las LLMs](#rol-de-las-llms)
- [Información que Reciben las LLMs](#información-que-reciben-las-llms)
- [Autonomía y Toma de Decisiones](#autonomía-y-toma-de-decisiones)
- [Gestión de Margen en Cross Margin](#gestión-de-margen-en-cross-margin)
- [Flujo Operativo](#flujo-operativo)
- [Filosofía del Experimento](#filosofía-del-experimento)

---

## ¿Qué es Grid Trading?

Grid Trading es una estrategia sistemática de trading que captura volatilidad en mercados laterales (sideways markets) mediante la colocación automática de órdenes de compra y venta en intervalos de precio predeterminados.

### 🎯 Concepto Fundamental

El grid trading aprovecha que **los mercados están en rango (sideways) el 70-75% del tiempo**, generando ganancias mediante ciclos repetidos de compra-venta dentro de ese rango.

### 📊 Ejemplo Visual

```
Precio
  │
$3,400 ├─────────────────────  ← Límite Superior
  │    SELL │ SELL │ SELL │
$3,300 ├──────────────────────
  │    SELL │ SELL │ BUY  │
$3,200 ├──────────────────────
  │    SELL │ BUY  │ BUY  │
$3,100 ├──────────────────────  ← Límite Inferior
  │    BUY  │ BUY  │ BUY  │
$3,000 ├──────────────────────
  │
  └─────────────────────► Tiempo
```

### 💰 Cómo Genera Ganancia

**Ciclo Completo:**
1. **Compra** a $3,100 (orden limit ejecutada)
2. Precio sube
3. **Vende** a $3,200 (orden limit ejecutada)
4. **Ganancia**: ($3,200 - $3,100) × Cantidad - Fees

Este ciclo se repite automáticamente mientras el precio oscile dentro del rango.

### ⚙️ Parámetros Clave

1. **Rango (Upper/Lower Limits)**
   - Define los límites del grid
   - Basado en soporte y resistencia técnica
   - Ejemplo: $3,000 - $3,400

2. **Niveles del Grid (Grid Levels)**
   - Cantidad de órdenes: 5-8 niveles
   - Más niveles = más oportunidades, menor ganancia por ciclo
   - Menos niveles = mayor ganancia por ciclo, menos oportunidades

3. **Tipo de Espaciado**
   - **Geométrico**: Los espacios crecen proporcionalmente (mejor para alta volatilidad)
   - **Aritmético**: Espacios iguales en dólares (mejor para baja volatilidad)

4. **Apalancamiento (Leverage)**
   - Multiplica la exposición: 1x a 5x
   - Mayor leverage = mayor ganancia potencial pero mayor riesgo
   - Típico: 3x (balance entre riesgo/retorno)

5. **Inversión (Investment USD)**
   - Capital asignado al grid: $100-$300
   - Se divide entre los niveles del grid
   - Cada orden debe cumplir mínimo $20 notional value

6. **Stop Loss**
   - Protección contra ruptura del rango: 10-15% bajo límite inferior
   - Ejemplo: Si límite inferior = $3,000, stop loss = $2,640 (12%)
   - **Crítico**: En este sistema, las LLMs deben ejecutarlo manualmente

---

## Arquitectura del Sistema

### 🏗️ Componentes Principales

```
┌─────────────────────────────────────────────────────────────┐
│                      BINANCE FUTURES API                     │
│              (Cross Margin - Testnet/Mainnet)               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ├── Precios en tiempo real
                         ├── Ejecución de órdenes
                         ├── Estado de posiciones
                         └── Balance y margen
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    GRID ENGINE                               │
│  • Calcula niveles del grid                                 │
│  • Coloca órdenes limit en Binance                          │
│  • Monitorea fills (ejecuciones)                            │
│  • Detecta ciclos completos (buy + sell)                    │
│  • Calcula ganancias por ciclo                              │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌────────▼──────┐ ┌──────▼──────┐ ┌─────▼───────┐
│    LLM-A      │ │   LLM-B     │ │   LLM-C     │
│   (Claude)    │ │ (DeepSeek)  │ │  (GPT-4o)   │
│               │ │             │ │             │
│ Capital: $200 │ │ Capital: $200│ │ Capital: $200│
└───────────────┘ └─────────────┘ └─────────────┘
         │               │               │
         └───────────────┴───────────────┘
                         │
                  Decisiones cada 5 min:
                  • SETUP_GRID
                  • UPDATE_GRID
                  • STOP_GRID
                  • HOLD
```

### 🔄 Ciclo de Vida de un Grid

1. **Creación (por LLM)**
   - LLM analiza mercado
   - Decide crear grid en símbolo específico
   - Define parámetros (rango, niveles, leverage, etc.)

2. **Colocación de Órdenes**
   - Grid Engine calcula precios de cada nivel
   - Coloca órdenes LIMIT en Binance:
     - BUY orders abajo del precio actual
     - SELL orders arriba del precio actual

3. **Ejecución Automática**
   - Cuando precio alcanza un nivel, orden se ejecuta
   - No requiere intervención manual
   - Binance ejecuta las órdenes 24/7

4. **Ciclos Completos**
   - Sistema detecta: BUY ejecutado → SELL ejecutado
   - Registra ganancia del ciclo
   - Recoloca órdenes automáticamente

5. **Finalización (por LLM)**
   - LLM decide hacer STOP_GRID
   - Sistema cancela todas las órdenes pendientes
   - Posiciones abiertas permanecen (no se cierran automáticamente)

---

## Rol de las LLMs

### 🤖 Las LLMs son los "Traders"

En este sistema, **las LLMs son completamente autónomas** y actúan como traders independientes que compiten entre sí.

### 🎯 Responsabilidades de las LLMs

#### 1. Análisis de Mercado

Las LLMs analizan:
- **Condición del mercado**: Sideways, Trending Up, o Trending Down
- **Volatilidad**: Low, Medium, o High
- **Soporte y Resistencia**: Niveles técnicos clave
- **Indicadores técnicos**: RSI, MACD, volumen
- **Rango de precios**: High/Low 24h

#### 2. Toma de Decisiones

Cada 5 minutos, las LLMs deciden:

**SETUP_GRID** - Crear nuevo grid
```json
{
  "action": "SETUP_GRID",
  "symbol": "ETHUSDT",
  "grid_config": {
    "upper_limit": 3400,
    "lower_limit": 3000,
    "grid_levels": 5,
    "spacing_type": "geometric",
    "leverage": 3,
    "investment_usd": 150,
    "stop_loss_pct": 12
  },
  "reasoning": "Market sideways con soporte en $3000 y resistencia en $3400..."
}
```

**UPDATE_GRID** - Modificar grid existente
```json
{
  "action": "UPDATE_GRID",
  "symbol": "ETHUSDT",
  "grid_config": {
    "upper_limit": 3500,  // Nuevo rango
    "lower_limit": 3100,
    ...
  },
  "reasoning": "Rango ha cambiado, ajustando límites..."
}
```

**STOP_GRID** - Detener grid
```json
{
  "action": "STOP_GRID",
  "symbol": "ETHUSDT",
  "reasoning": "Mercado trending fuertemente, grid ya no es efectivo"
}
```

**HOLD** - No hacer nada
```json
{
  "action": "HOLD",
  "reasoning": "Grids actuales funcionando bien, esperando..."
}
```

#### 3. Gestión de Riesgo

Las LLMs son **100% responsables** de:
- Monitorear distancia al stop loss
- Decidir cuándo cerrar grids en riesgo
- Balancear cantidad de grids activos
- Gestionar capital entre múltiples grids
- Reaccionar a condiciones de mercado adversas

**NO HAY STOP LOSS AUTOMÁTICO** - Las LLMs deben decidir activamente.

---

## Información que Reciben las LLMs

### 📊 Prompt Completo (Cada 5 minutos)

#### 1. Datos de Mercado (Todos los símbolos)

```
Symbol: ETHUSDT
Current Price: $3,300.00
24h Change: +2.5%
24h High: $3,350.00
24h Low: $3,250.00
24h Volume: $1,500,000
RSI(14): 55.0
MACD: 0.0015
MACD Signal: 0.0012

Recent Price Action:
- Support Level: $3,250.00
- Resistance Level: $3,350.00
- Range: 100.00 (3.03%)
```

#### 2. Estado de Cuenta

```
LLM ID: LLM-A
Total Balance: $200.00 USDT
Available Balance: $150.00 USDT
Total Investment in Grids: $150.00 USDT
Active Grids: 1/6

Overall Performance:
- Total PnL: +$12.50 (+6.25%)
- Grid Profit: $24.00
- Total Fees Paid: $1.60
```

#### 3. Grids Activos (CON INFORMACIÓN COMPLETA DE RIESGO)

```
Grid ID: grid_eth_001
Symbol: ETHUSDT
Status: ACTIVE

Configuration:
  Range: $3,200.00 - $3,400.00
  Stop Loss: $2,816.00 (12% below lower limit)  ← NUEVO
  Levels: 5
  Spacing: geometric
  Leverage: 3x
  Investment: $150.00

Current Market Position:                         ← NUEVO
  Current Price: $3,300.00
  Position in Grid: 50.0% (0% = lower, 100% = upper)
  Distance to Upper Limit: -2.94% ($-100.00)
  Distance to Lower Limit: +3.12% ($+100.00)
  Distance to Stop Loss: +17.19% ($+484.00)     ← CRÍTICO

Risk Assessment:                                  ← NUEVO
  Risk Level: 🟢 LOW
  Alert: ✓ Grid operating normally within range

Performance:
  Cycles Completed: 8
  Total Profit: $24.00
  Net Profit (after fees): $22.40
  ROI: 14.93%
  Avg Profit/Cycle: $3.00
```

#### 4. Niveles de Riesgo

🟢 **LOW** - Grid operando normalmente
- Precio dentro del rango
- Distancia al stop loss > 15%
- Todo normal

🟡 **MEDIUM** - Atención requerida
- Precio cerca del límite inferior (< 2%)
- Precio fuera del rango pero stop loss lejano
- Monitorear

🟠 **HIGH** - Riesgo elevado
- Distancia al stop loss < 15%
- Considerar cerrar grid
- Decisión crítica

🔴 **CRITICAL** - Riesgo inminente
- Distancia al stop loss < 5%
- Stop loss a punto de ser alcanzado
- **ACTUAR INMEDIATAMENTE**

#### 5. Recordatorio de Autonomía

```
CRITICAL - YOU ARE 100% AUTONOMOUS:
- There are NO automatic stop losses or circuit breakers
- YOU must monitor risk and decide when to stop grids
- System will NOT intervene even at stop loss price
- Risk management is YOUR responsibility
- Use the Risk Assessment data to make informed decisions
```

---

## Autonomía y Toma de Decisiones

### 🧠 Filosofía: LLMs con Control Total

Este sistema es un **experimento académico** diseñado para evaluar la capacidad de LLMs de trading autónomo. Por lo tanto:

#### ✅ LLMs DECIDEN TODO

- Cuándo crear grids
- Qué parámetros usar
- Cuándo modificar grids
- Cuándo cerrar grids
- Cómo gestionar riesgo
- Cuánto capital asignar

#### ❌ El Sistema NO Interfiere

- **No hay stop loss automático**
- **No hay circuit breakers**
- **No hay limits adicionales**
- **No hay intervención humana durante operación**

#### 🎯 Objetivos del Diseño

1. **Validez Académica**
   - Decisiones 100% de AI
   - Datos limpios para análisis
   - Comparación justa entre LLMs

2. **Aprendizaje Real**
   - LLMs aprenden de errores (incluso costosos)
   - Evolución de estrategias
   - Adaptación a condiciones cambiantes

3. **Información vs Automatización**
   - LLMs reciben **información perfecta** (riesgo, precios, estado)
   - LLMs toman **decisiones autónomas**
   - Sin automatizaciones que sesguen el experimento

### 🔍 Ejemplo de Decisión Crítica

**Escenario: Grid en Riesgo**

```
Situación:
- ETHUSDT grid con límite inferior $3,200
- Stop loss en $2,816 (12% abajo)
- Precio actual: $2,900 ← Cayó fuera del rango

Información que recibe la LLM:
Risk Assessment:
  Risk Level: 🔴 CRITICAL
  Distance to Stop Loss: +2.98% ($+84.00)
  Alert: ⚠️ STOP LOSS IMMINENT - Price very close to stop!

Opciones de la LLM:
1. STOP_GRID inmediatamente (limitar pérdidas)
2. HOLD y esperar rebote (confianza en soporte)
3. UPDATE_GRID con nuevo rango (adaptarse)

La LLM debe decidir - NO HAY AYUDA AUTOMÁTICA
```

### 🤔 ¿Por qué No Stop Loss Automático?

**Argumento a favor**: Protege capital en situaciones extremas

**Argumento en contra** (adoptado):
1. Rompe la autonomía del experimento
2. Sesga las decisiones (¿qué tan buenas son realmente las LLMs?)
3. Quita oportunidad de aprendizaje
4. No es representativo de trading real autónomo

**Compromiso**: Información perfecta, pero decisión 100% autónoma

---

## Gestión de Margen en Cross Margin

### 📘 Conceptos de Margen en Binance Futures

#### Initial Margin vs Maintenance Margin

**Initial Margin** (Margen Inicial)
- Capital requerido para **ABRIR** una posición
- Fórmula: `Investment USD ÷ Leverage`
- Ejemplo: $150 / 3x = $50 necesarios para abrir

**Maintenance Margin** (Margen de Mantenimiento)
- Capital requerido para **MANTENER** una posición abierta
- Mucho menor que initial margin (~0.4% del valor nocional)
- Ejemplo: $150 × 3x × 0.4% = $1.80 bloqueado permanentemente

### 🔄 Cómo Funciona Cross Margin

En **Cross Margin Mode**, todo tu balance actúa como colateral compartido:

1. **Al abrir posición**:
   - Necesitas $50 disponibles (Initial Margin)
   - Sistema verifica que tienes suficiente balance

2. **Después de abrir**:
   - Solo $1.80 queda "bloqueado" (Maintenance Margin)
   - Los otros $48.20 se liberan y están disponibles de nuevo

3. **Capital compartido**:
   - Todos los grids comparten el mismo pool de capital
   - Balance disponible = Balance Total - Suma de Maintenance Margins
   - Altamente eficiente para múltiples posiciones

### 💡 Ejemplo Real: $600 de Capital

```
Capital Inicial: $600 ($200 por LLM)

Grid 1 - ETHUSDT:
  Investment: $150, Leverage: 3x
  Initial Margin: $50 ← Necesita esto para ABRIR
  Maintenance Margin: $1.80 ← Queda bloqueado
  Capital liberado: $48.20

Grid 2 - BNBUSDT:
  Investment: $180, Leverage: 3x
  Initial Margin: $60
  Maintenance Margin: $2.16
  Capital liberado: $57.84

Grid 3 - XRPUSDT:
  Investment: $150, Leverage: 3x
  Initial Margin: $50
  Maintenance Margin: $1.80
  Capital liberado: $48.20

Estado Final:
  Capital original: $200.00
  Total bloqueado (maintenance): $5.76 (2.88%)
  Capital disponible: $194.24 (97.12%)
```

### 🎯 Por Qué Es Importante

**Eficiencia de Capital**:
- Puedes operar $450 de inversión ($150 × 3 grids)
- Solo necesitas $200 de capital
- Solo $5.76 queda bloqueado permanentemente

**Validación Pre-Grid**:
```python
# En src/services/trading_service.py:482-510
investment_usd = 150
leverage = 3
margin_required = investment_usd / leverage  # $50

# Verificar ANTES de crear grid
if available_balance < margin_required:
    # RECHAZAR - No hay suficiente capital para abrir
    # LLM recibe notificación por Telegram
    return "REJECTED"
```

Esta validación **NO contradice la autonomía** porque:
- Previene errores técnicos (no decisiones de trading)
- Es como verificar que tienes fondos antes de hacer un pago
- Las LLMs siguen decidiendo QUÉ y CUÁNDO operar

### 📊 Ejemplo Real de la Cuenta Demo

**Estado actual (12 horas de operación)**:
```
Balance: $4,910.15 USDT
Maintenance Margin: $12.09 USDT (0.25%)
Unrealized PnL: +$19.31 USDT

Grids activos: ~15 grids
Capital en grids: ~$2,250 (15 × $150 promedio)
Capital bloqueado: Solo $12.09 (0.54%)
Capital disponible: $3,258.05 (66.3%)
```

**Eficiencia demostrada**: Con solo $4,910 se están operando ~$2,250 en inversión con margen mínimo bloqueado.

---

## Flujo Operativo

### 🔄 Ciclo Completo (Cada 5 minutos)

```
┌─────────────────────────────────────────┐
│  1. Recolección de Datos                │
│     • Precios actuales de mercado       │
│     • Estado de grids activos           │
│     • Balance disponible                │
│     • Posiciones abiertas               │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  2. Construcción de Prompts             │
│     • Market data para 6 símbolos       │
│     • Account status por LLM            │
│     • Active grids con risk assessment  │
│     • Performance metrics               │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴───────┐
       │               │
┌──────▼─────┐  ┌─────▼──────┐  ┌──────▼─────┐
│  LLM-A     │  │  LLM-B     │  │  LLM-C     │
│  Analiza   │  │  Analiza   │  │  Analiza   │
│  y Decide  │  │  y Decide  │  │  y Decide  │
└──────┬─────┘  └─────┬──────┘  └──────┬─────┘
       │               │                │
       └───────┬───────┴────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  3. Validación de Decisiones            │
│     • JSON válido                       │
│     • Parámetros en rangos correctos    │
│     • Balance suficiente (margin check) │
│     • Grid no duplicado                 │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  4. Ejecución (si aprobado)             │
│     • SETUP_GRID: Crear y colocar órdenes│
│     • UPDATE_GRID: Cancelar y recolocar │
│     • STOP_GRID: Cancelar órdenes       │
│     • HOLD: No hacer nada               │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  5. Monitoreo Continuo                  │
│     • Detectar órdenes ejecutadas       │
│     • Identificar ciclos completos      │
│     • Calcular P&L                      │
│     • Actualizar metrics                │
└─────────────────────────────────────────┘
               │
               └─── Repetir en 5 minutos
```

### ⚡ Eventos Especiales

**Orden Ejecutada (Fill)**:
```
1. Binance ejecuta orden limit
2. Sistema detecta fill en siguiente check
3. Marca nivel como FILLED
4. Verifica si completó un ciclo (buy + sell)
5. Si ciclo completo:
   - Calcula ganancia
   - Actualiza ROI del grid
   - Incrementa contador de ciclos
   - Recoloca órdenes en ese nivel
```

**Ciclo Completo Detectado**:
```
Ejemplo:
- BUY @ $3,100 ejecutado
- SELL @ $3,200 ejecutado
- Profit = ($3,200 - $3,100) × 0.018 ETH - fees
- Profit = $1.80 - $0.09 fees = $1.71
- ROI del grid aumenta
- Recolocar órdenes en esos niveles
```

**Notificación Telegram**:
```
Triggers:
• Grid creado exitosamente
• Grid rechazado (balance insuficiente)
• Risk level CRITICAL detectado
• Error en ejecución
• Ciclos completados (opcional)
```

---

## Filosofía del Experimento

### 🎓 Objetivos Académicos

Este sistema fue diseñado como un **experimento académico** para evaluar:

1. **Capacidad de LLMs en Trading Autónomo**
   - ¿Pueden LLMs operar rentablemente sin intervención?
   - ¿Aprenden de errores y adaptan estrategias?
   - ¿Qué diferencias hay entre diferentes modelos (Claude vs GPT vs DeepSeek)?

2. **Gestión de Riesgo por AI**
   - ¿Pueden LLMs detectar y reaccionar a riesgo alto?
   - ¿Toman decisiones conservadoras o agresivas?
   - ¿Mejoran su gestión de riesgo con experiencia?

3. **Grid Trading en Condiciones Reales**
   - Validar efectividad de grid trading con capital real
   - Métricas: ROI, win rate, profit factor, drawdown
   - Comparar vs estrategias tradicionales

### 🔬 Principios del Diseño

#### 1. Autonomía Total

**Sin intervención** significa realmente sin intervención:
- No stop loss automático
- No límites de pérdida forzados
- No sugerencias humanas durante operación
- No rescue del sistema

**Razón**: Solo así podemos medir capacidad real de AI autónoma.

#### 2. Información Perfecta

Las LLMs deben tener **toda la información necesaria**:
- Precios en tiempo real
- Estado de posiciones
- Métricas de riesgo calculadas
- Distancia a stop loss
- Performance histórica

**Razón**: No queremos que fallen por falta de información, queremos ver cómo deciden con información completa.

#### 3. Competición Justa

Las 3 LLMs compiten en igualdad de condiciones:
- Mismo capital inicial ($200 cada una)
- Mismas reglas y límites
- Misma información de mercado
- Mismo prompt base (no personalidades distintas)

**Diferencia**: Solo el modelo de AI y parámetros (temperature).

#### 4. Aprendizaje de Errores

**Los errores son parte del experimento**:
- Si una LLM pierde dinero, es dato válido
- Si una LLM no cierra grid en riesgo, aprende
- Las pérdidas son parte del aprendizaje

**Límite ético**: Usar capital que podemos permitirnos perder (experimento académico).

### 📊 Métricas de Éxito

**Performance (Objetivo primario)**:
- ROI total por LLM
- Win rate (% operaciones ganadoras)
- Profit factor (ganancia/pérdida)
- Sharpe ratio (retorno ajustado a riesgo)

**Gestión de Riesgo**:
- Max drawdown (máxima pérdida desde pico)
- Veces que alcanzó stop loss
- Tiempo promedio de reacción a riesgo
- % de grids cerrados proactivamente

**Adaptabilidad**:
- Cambio de estrategia según condiciones
- Aprendizaje de errores previos
- Diversificación de símbolos
- Ajuste de parámetros con tiempo

**Comparación entre LLMs**:
- LLM-A (Claude): ¿Conservador y consistente?
- LLM-B (DeepSeek): ¿Balanceado?
- LLM-C (GPT-4o): ¿Agresivo pero rentable?

### 🚀 Fase de Transición: Testnet → Mainnet

**Testnet (Completado)**:
- Validar que sistema funciona técnicamente
- Verificar que LLMs toman decisiones coherentes
- Probar prompts mejorados con información de riesgo
- Resultado: +$71.69 en 12 horas, sistema estable

**Mainnet (Siguiente fase)**:
- Capital real: $600 ($200 por LLM)
- Operación real en Binance Futures
- Stakes reales → decisiones con consecuencias
- Duración sugerida: 30-60 días para datos significativos

**Consideraciones Éticas**:
- Capital que podemos permitirnos perder
- Sistema supervisado (podemos detener manualmente)
- Limites por grid ($100-$300) y leverage (máx 5x)
- Experimento académico, no inversión seria

---

## 🎯 Resumen Ejecutivo

### Sistema de Grid Trading Autónomo:

**¿Qué hace?**
- 3 LLMs (Claude, DeepSeek, GPT-4o) operan grids en Binance Futures
- Cada una con $200 de capital
- Decisiones cada 5 minutos
- 100% autónomas

**¿Cómo funciona?**
- LLMs analizan 6 pares cripto (ETHUSDT, BNBUSDT, etc.)
- Deciden crear/modificar/cerrar grids
- Sistema ejecuta órdenes en Binance
- Grids capturan volatilidad automáticamente

**¿Qué aporta?**
- Información completa de riesgo a LLMs
- Sin intervención automática (experimento puro)
- Métricas de comparación entre modelos de AI
- Validación de grid trading con AI

**¿Por qué es único?**
- Autonomía real (no simulada)
- Capital real (no paper trading)
- Comparación directa entre LLMs
- Experimento académico riguroso

**Resultado esperado**:
- Datos sobre capacidad de LLMs en trading
- Métricas de performance y riesgo
- Comparación entre modelos
- Validación (o invalidación) de AI trading autónomo

---

## 📚 Referencias

- **Grid Trading Research**: Markets are sideways 70-75% of time ([Investopedia](https://www.investopedia.com/))
- **Binance Futures Docs**: [https://binance-docs.github.io/apidocs/futures/en/](https://binance-docs.github.io/apidocs/futures/en/)
- **Cross Margin vs Isolated**: [Binance Academy](https://academy.binance.com/)
- **Maintenance Margin Rates**: [Binance Futures Trading Rules](https://www.binance.com/en/futures/trading-rules)

---

## 📝 Notas Finales

Este documento refleja las conversaciones y decisiones de diseño del sistema. El código implementa estos principios en:

- `src/core/grid_engine.py` - Lógica de grid trading
- `src/clients/grid_prompts.py` - Prompts con información de riesgo
- `src/services/trading_service.py` - Orquestación de decisiones
- `src/core/trade_executor.py` - Ejecución en Binance

**Última actualización**: 2025-11-13
**Versión**: 1.0 - Preparación para mainnet con prompts mejorados
