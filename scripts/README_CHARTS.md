# 📊 Monitor con Gráficos - Guía de Uso

## 🎯 Características

El **monitor con gráficos** (`monitor_charts.py`) proporciona visualización avanzada del performance de los LLMs en tiempo real:

### Gráficos Incluidos:

#### 1. **📈 Equity Over Time** (Línea)
- Muestra la evolución del equity de cada LLM
- Diferentes colores por LLM
- Últimos 20 puntos de datos
- Se actualiza cada 30 segundos

#### 2. **💰 Current PnL** (Barras)
- PnL actual de cada LLM
- Barras verdes (ganancia) / rojas (pérdida)
- Comparación visual inmediata

#### 3. **🎯 Win Rate Comparison** (Barras)
- Tasa de éxito de cada LLM
- Rango 0-100%
- Identifica qué LLM tiene mejor estrategia

#### 4. **📊 Leaderboard Table**
- Ranking actualizado
- Métricas detalladas por LLM
- Equity, PnL, trades, win rate

#### 5. **📌 Overall Statistics**
- Portfolio total
- PnL agregado
- Promedio de win rate

## 🚀 Uso

### Instalación de Dependencias

```bash
# Instalar plotext para gráficos
pip3 install plotext
```

### Ejecutar Monitor con Gráficos

```bash
# Opción 1: Ejecutable directo
./scripts/monitor_charts.py

# Opción 2: Con Python
python3 scripts/monitor_charts.py
```

### Recomendaciones

1. **Terminal en Fullscreen**: Los gráficos se ven mejor en pantalla completa
2. **Tema Oscuro**: Mejor contraste para los gráficos
3. **Esperar 1-2 ciclos**: Los gráficos se populan después de recolectar datos

## 📸 Ejemplo de Output

```
┌────────────────────────────────────────────────────────────────────────────┐
│          🏆 LLM TRADING COMPETITION - LIVE MONITOR 🏆                      │
│          Uptime: 0:15:30 | Last Update: 18:42:15                          │
└────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────── 📈 Equity Over Time ────────────────────────────────┐
│                                                                            │
│ 105.0 ┤                                            ╭──────────── LLM-A     │
│ 103.0 ┤                            ╭───────────────╯                       │
│ 101.0 ┤         ╭──────────────────╯                                       │
│ 100.0 ┼─────────╯                                                          │
│  99.0 ┤                  ╭─────────╮               ╭────────── LLM-B       │
│  98.0 ┤     ╭────────────╯         ╰───────────────╯                       │
│  97.0 ┤─────╯                                                              │
│       └─────┬────────┬────────┬────────┬────────┬────────┬────────┬───────│
│             0        5       10       15       20                          │
└────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────── 📊 LEADERBOARD ──────────────────────────────────┐
│ Rank │ LLM    │     Equity │        PnL │    PnL % │ Trades │ Win Rate    │
├──────┼────────┼────────────┼────────────┼──────────┼────────┼─────────────┤
│  🥇  │ LLM-A  │    $104.50 │     +$4.50 │   +4.50% │   5    │    60.0%    │
│  🥈  │ LLM-B  │    $98.20  │     -$1.80 │   -1.80% │   3    │    33.3%    │
│  🥉  │ LLM-C  │    $100.00 │     +$0.00 │    0.00% │   0    │     0.0%    │
└──────┴────────┴────────────┴────────────┴──────────┴────────┴─────────────┘

┌─────────── 💰 Current PnL ──────────┬────────── 🎯 Win Rates ─────────────┐
│                                     │                                      │
│ LLM-A ████████████ +$4.50           │ LLM-A ████████████████ 60%          │
│ LLM-B ███ -$1.80                    │ LLM-B ███████ 33%                   │
│ LLM-C  $0.00                        │ LLM-C  0%                           │
│                                     │                                      │
└─────────────────────────────────────┴──────────────────────────────────────┘
```

## 🎨 Personalización

### Cambiar Intervalo de Actualización

Edita `monitor_charts.py`:

```python
REFRESH_INTERVAL = 30  # Cambiar a 15, 60, etc.
```

### Cambiar Cantidad de Datos Históricos

```python
# Línea ~53
if len(timestamp_history) > 20:  # Cambiar a 50, 100, etc.
```

### Cambiar Tamaño de Gráficos

```python
# En create_equity_chart()
plt.plotsize(80, 15)  # Ancho, Alto
```

## 🆚 Monitor Básico vs Monitor con Gráficos

| Feature | monitor.py | monitor_charts.py |
|---------|-----------|-------------------|
| Tablas | ✅ | ✅ |
| Gráficos de línea | ❌ | ✅ |
| Gráficos de barras | ❌ | ✅ |
| Historial visual | ❌ | ✅ |
| Velocidad | Rápido | Normal |
| Tamaño terminal | Pequeña OK | Grande recomendado |
| Dependencias | Solo rich | rich + plotext |

## 🔧 Troubleshooting

### Los gráficos se ven mal
**Solución**: Aumenta el tamaño de la terminal o cambia `plt.plotsize()`

### "No module named plotext"
**Solución**:
```bash
pip3 install plotext
```

### Los gráficos están vacíos
**Solución**: Espera 1-2 ciclos de trading para que se recolecten datos

### Terminal muy pequeña
**Solución**: Usa `monitor.py` básico o aumenta tamaño de terminal

## 💡 Tips

1. **Maximiza la terminal** para mejor visualización
2. **Deja correr por 30-60 minutos** para ver tendencias claras
3. **Compara con Binance** para verificar accuracy
4. **Usa tema oscuro** para mejor contraste
5. **Toma screenshots** de momentos importantes

## 🚀 Próximas Mejoras

- [ ] Gráfico de drawdown
- [ ] Sharpe ratio visualization
- [ ] Trade frequency heatmap
- [ ] Per-symbol performance
- [ ] Exportar datos a CSV
- [ ] Alertas de performance

---

**¡Disfruta monitoreando la competencia entre LLMs en tiempo real! 📊🤖**
