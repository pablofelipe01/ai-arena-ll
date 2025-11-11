# 🏆 LLM Trading Competition Monitor

Dashboard de terminal en tiempo real para monitorear la competencia de trading de 24 horas.

## 🚀 Inicio Rápido

### 1. Asegúrate que el servidor esté corriendo:
```bash
python3 scripts/start.py
```

### 2. En otra terminal, inicia el monitor:
```bash
python3 scripts/monitor.py
```

## 📊 Características

El monitor muestra:

### Leaderboard 🥇🥈🥉
- Ranking de LLMs por equity
- PnL total y porcentaje
- Número de trades
- Win rate
- Posiciones abiertas

### Estadísticas Generales 💰
- Portfolio total combinado
- PnL agregado de todas las LLMs
- Total de trades ejecutados
- Win rate promedio

### Posiciones Abiertas 🎯
- Todas las posiciones activas
- PnL no realizado en tiempo real
- ROI porcentual
- Información de leverage

### Market Snapshot 📈
- Precios actuales de los 6 símbolos
- Actualización en tiempo real

## ⚙️ Configuración

Puedes modificar estas variables en `monitor.py`:

```python
API_BASE_URL = "http://localhost:8000"  # URL del servidor
REFRESH_INTERVAL = 30  # Segundos entre actualizaciones
```

## 🎨 Controles

- `Ctrl+C` - Detener el monitor
- Auto-refresh cada 30 segundos (configurable)

## 💡 Tips

1. **Ejecuta en una terminal grande** - El dashboard se ve mejor con al menos 120 columnas de ancho
2. **Usa tmux o screen** - Para mantenerlo corriendo en background
3. **Binance para posiciones reales** - Este monitor es complementario, usa Binance para ver posiciones reales

## 🔍 Troubleshooting

### "Failed to connect to API"
- Verifica que el servidor esté corriendo: `curl http://localhost:8000/health`
- Inicia el servidor: `python3 scripts/start.py`

### Monitor se ve cortado
- Aumenta el tamaño de tu terminal
- Usa terminal en pantalla completa

### Datos no se actualizan
- Verifica que el servidor esté respondiendo
- Revisa los logs del servidor para errores

## 📝 Alternativa: Logs en Archivo

Si prefieres ver logs en archivo en lugar del dashboard interactivo:

```bash
# Ver logs del servidor en tiempo real
tail -f /tmp/trading_system.log

# Ver solo decisiones de trading
tail -f /tmp/trading_system.log | grep "LLM-"

# Ver solo errores
tail -f /tmp/trading_system.log | grep ERROR
```

## 🎯 Para la Demo de 24 Horas

**Recomendación**: Ejecuta el monitor en una terminal separada mientras el servidor corre en otra.

```bash
# Terminal 1: Servidor
python3 scripts/start.py

# Terminal 2: Monitor
python3 scripts/monitor.py

# Terminal 3: Logs (opcional)
tail -f /tmp/trading_system.log
```
