#!/usr/bin/env python3
"""Quick script to check current Binance status."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.clients.binance_client import BinanceClient

binance = BinanceClient(testnet=False)

print('📊 ESTADO ACTUAL EN BINANCE MAINNET')
print('=' * 70)

# Posiciones
positions = binance.get_position_risk()
active_positions = [p for p in positions if float(p.get('positionAmt', 0)) != 0]

print(f'POSICIONES ABIERTAS: {len(active_positions)}')
print()

total_pnl = 0
for pos in active_positions:
    symbol = pos['symbol']
    position_amt = float(pos['positionAmt'])
    entry_price = float(pos['entryPrice'])
    current_price = float(pos['markPrice'])
    unrealized_pnl = float(pos['unRealizedProfit'])
    leverage = int(pos['leverage'])

    side = 'LONG' if position_amt > 0 else 'SHORT'
    total_pnl += unrealized_pnl

    print(f'{symbol:10} {side:5} | Qty: {abs(position_amt):8.4f} | Entry: ${entry_price:8.2f} | Current: ${current_price:8.2f} | Lev: {leverage}x | PnL: ${unrealized_pnl:7.2f}')

print()
print(f'TOTAL PnL: ${total_pnl:.2f}')
print()

# Órdenes
print('ÓRDENES ABIERTAS POR SÍMBOLO:')
print('-' * 70)
from config.settings import settings
symbols = settings.available_pairs_list
total_orders = 0
for symbol in symbols:
    try:
        orders = binance.get_open_orders(symbol)
        if orders:
            print(f'{symbol:10}: {len(orders):3} órdenes')
            total_orders += len(orders)
    except:
        pass

print('-' * 70)
print(f'TOTAL: {total_orders} órdenes activas')
