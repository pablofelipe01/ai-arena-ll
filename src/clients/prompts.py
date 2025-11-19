"""
Prompt templates para decisiones de trading de LLMs.

Este módulo contiene los prompts estructurados que se envían a los LLMs
para obtener decisiones de trading en formato JSON.
"""

from typing import Dict, List, Any
from decimal import Decimal


# Trading constants
ALLOWED_SYMBOLS = ["DOGEUSDT", "TRXUSDT", "HBARUSDT", "XLMUSDT", "ADAUSDT", "ALGOUSDT"]
MAX_LEVERAGE = 10
MAX_POSITIONS = 3
MIN_TRADE_SIZE = 10
MAX_TRADE_SIZE = 40


SYSTEM_PROMPT = """You are an expert cryptocurrency futures trader with deep knowledge of technical analysis, market psychology, and risk management.

Your task is to analyze market data and make trading decisions for a virtual trading account with $100 USDT on Binance Futures.

IMPORTANT RULES:
1. You can only trade these symbols: DOGEUSDT, TRXUSDT, HBARUSDT, XLMUSDT, ADAUSDT, ALGOUSDT
2. Maximum leverage: 10x
3. Maximum open positions: 3 simultaneous positions
4. Minimum trade size: $10 USD
5. Maximum trade size: $40 USD (40% of balance per trade)
6. You must respond ONLY with valid JSON in the exact format specified
7. Always include your reasoning and confidence level

RESPONSE FORMAT:
You MUST respond with a JSON object containing:
{{
    "action": "BUY" | "SELL" | "CLOSE" | "HOLD",
    "symbol": "DOGEUSDT" | "TRXUSDT" | "HBARUSDT" | "XLMUSDT" | "ADAUSDT" | "ALGOUSDT" | null,
    "quantity_usd": <number between 10 and 40> | null,
    "leverage": <integer between 1 and 10> | null,
    "stop_loss_pct": <number between 1 and 20> | null,
    "take_profit_pct": <number between 2 and 50> | null,
    "reasoning": "<your analysis and reasoning>",
    "confidence": <decimal between 0.0 and 1.0>,
    "strategy": "momentum" | "mean_reversion" | "breakout" | "trend_following" | "scalping" | "swing"
}}

ACTION DEFINITIONS:
- BUY: Open a LONG position (expecting price to go UP)
- SELL: Open a SHORT position (expecting price to go DOWN)
- CLOSE: Close an existing position for the specified symbol
- HOLD: Do nothing, wait for better opportunities

RULES:
- If action is "HOLD", symbol, quantity_usd, leverage, stop_loss_pct, and take_profit_pct should be null
- If action is "CLOSE", only symbol is required, other fields should be null
- If action is "BUY" or "SELL", all fields except stop_loss_pct and take_profit_pct are required
- stop_loss_pct and take_profit_pct are optional but recommended
- confidence should reflect your certainty about the decision (0.0 = very uncertain, 1.0 = very certain)
- reasoning should be concise but informative (2-4 sentences)

Your personality and approach:
{personality}
"""

PERSONALITIES = {
    "LLM-A": """You are CONSERVATIVE and risk-averse:
- Prefer lower leverage (1x-3x)
- Focus on established coins (ETH, BNB)
- Only trade when confidence > 0.7
- Prioritize capital preservation
- Use tight stop losses (3-5%)
- Take profits early (5-10%)""",

    "LLM-B": """You are BALANCED and analytical:
- Use moderate leverage (3x-7x)
- Trade all symbols when opportunities arise
- Trade when confidence > 0.6
- Balance risk and reward
- Use reasonable stop losses (5-10%)
- Target moderate profits (10-20%)""",

    "LLM-C": """You are AGGRESSIVE and opportunistic:
- Maximize leverage (7x-10x)
- Actively trade volatile coins (DOGE, XRP, ADA)
- Trade even with moderate confidence (> 0.5)
- Seek maximum returns
- Use wider stop losses (10-15%)
- Target large profits (20-50%)"""
}


def build_trading_prompt(
    llm_id: str,
    account_info: Dict[str, Any],
    market_data: List[Dict[str, Any]],
    open_positions: List[Dict[str, Any]],
    recent_trades: List[Dict[str, Any]]
) -> str:
    """
    Construir prompt completo para decisión de trading.

    Args:
        llm_id: ID del LLM ('LLM-A', 'LLM-B', 'LLM-C')
        account_info: Información de la cuenta del LLM
        market_data: Datos de mercado actuales para todos los símbolos
        open_positions: Posiciones abiertas actuales
        recent_trades: Últimos trades del LLM

    Returns:
        Prompt completo con todos los datos
    """
    personality = PERSONALITIES.get(llm_id, PERSONALITIES["LLM-B"])

    system_prompt = SYSTEM_PROMPT.format(personality=personality)

    # Build market data section
    market_section = "\n\n=== CURRENT MARKET DATA ===\n"
    for data in market_data:
        market_section += f"""
Symbol: {data.get('symbol')}
Price: ${data.get('price', 0):.2f}
24h Change: {data.get('price_change_pct_24h', 0):.2f}%
24h Volume: ${data.get('volume_24h', 0):,.0f}
RSI(14): {data.get('rsi_14', 0):.2f}
MACD: {data.get('macd', 0):.4f}
"""

    # Build account section
    account_section = f"""
=== YOUR ACCOUNT STATUS ===
LLM ID: {llm_id}
Total Balance: ${account_info.get('balance', 0):.2f} USDT
Available Balance: ${account_info.get('available_balance', 0):.2f} USDT
Margin Used: ${account_info.get('margin_used', 0):.2f} USDT
Open Positions: {account_info.get('open_positions', 0)}/{account_info.get('max_positions', 3)}

Performance:
- Total PnL: ${account_info.get('total_pnl', 0):.2f} ({account_info.get('roi_pct', 0):.2f}%)
- Win Rate: {account_info.get('win_rate', 0):.2f}%
- Total Trades: {account_info.get('total_trades', 0)}
"""

    # Build positions section
    positions_section = "\n=== OPEN POSITIONS ===\n"
    if open_positions:
        for pos in open_positions:
            positions_section += f"""
Symbol: {pos.get('symbol')}
Side: {pos.get('side')}
Entry Price: ${pos.get('entry_price', 0):.2f}
Current Price: ${pos.get('current_price', 0):.2f}
Quantity: {pos.get('quantity', 0):.4f}
Leverage: {pos.get('leverage', 1)}x
Unrealized PnL: ${pos.get('unrealized_pnl', 0):.2f} ({pos.get('pnl_percentage', 0):.2f}%)
Liquidation Price: ${pos.get('liquidation_price', 0):.2f}
"""
    else:
        positions_section += "No open positions\n"

    # Build recent trades section
    trades_section = "\n=== RECENT TRADES (Last 5) ===\n"
    if recent_trades:
        for trade in recent_trades[:5]:
            trades_section += f"""
{trade.get('executed_at', 'N/A')}: {trade.get('trade_type')} {trade.get('symbol')}
  Side: {trade.get('side')}, Price: ${trade.get('price', 0):.2f}
  PnL: ${trade.get('pnl', 0):.2f} ({trade.get('pnl_percentage', 0):.2f}%)
  Reasoning: {trade.get('reasoning', 'N/A')[:100]}
"""
    else:
        trades_section += "No recent trades\n"

    # Build decision request
    decision_section = """
=== MAKE YOUR DECISION ===

Based on the market data, your account status, and your trading personality,
make a trading decision RIGHT NOW.

Consider:
1. Current market trends and momentum
2. Your account balance and risk limits
3. Your existing positions and overall exposure
4. Technical indicators (RSI, MACD)
5. Your trading personality and risk tolerance

Remember:
- You can HOLD if no good opportunities
- You can CLOSE existing positions if needed
- You can BUY (LONG) or SELL (SHORT) new positions
- Always stay within risk limits
- Provide clear reasoning for your decision

Respond ONLY with a JSON object in the exact format specified above.
"""

    # Combine all sections
    full_prompt = (
        system_prompt +
        market_section +
        account_section +
        positions_section +
        trades_section +
        decision_section
    )

    return full_prompt


def parse_llm_response(response_text: str) -> Dict[str, Any]:
    """
    Parsear respuesta del LLM a formato estructurado.

    Args:
        response_text: Texto de respuesta del LLM

    Returns:
        Dict con la decisión parseada

    Raises:
        ValueError: Si el JSON es inválido o falta información requerida
    """
    import json
    import re

    # Try to extract JSON from the response
    # LLMs sometimes wrap JSON in markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find JSON object directly
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            raise ValueError("No JSON object found in LLM response")

    # Parse JSON
    try:
        decision = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in LLM response: {e}")

    # Validate required fields
    required_fields = ["action", "reasoning", "confidence", "strategy"]
    missing_fields = [field for field in required_fields if field not in decision]

    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    # Validate action
    valid_actions = ["BUY", "SELL", "CLOSE", "HOLD"]
    if decision["action"] not in valid_actions:
        raise ValueError(f"Invalid action: {decision['action']}. Must be one of {valid_actions}")

    # Validate action-specific requirements
    if decision["action"] in ["BUY", "SELL"]:
        if not decision.get("symbol"):
            raise ValueError(f"Symbol required for {decision['action']} action")
        if not decision.get("quantity_usd"):
            raise ValueError(f"Quantity (USD) required for {decision['action']} action")
        if not decision.get("leverage"):
            raise ValueError(f"Leverage required for {decision['action']} action")

    if decision["action"] == "CLOSE":
        if not decision.get("symbol"):
            raise ValueError("Symbol required for CLOSE action")

    # Validate confidence
    try:
        confidence = float(decision["confidence"])
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {confidence}")
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid confidence value: {e}")

    return decision


def validate_decision(
    decision: Dict[str, Any],
    available_balance: Decimal,
    max_positions: int,
    current_positions: int,
    allowed_symbols: List[str]
) -> tuple[bool, str]:
    """
    Validar que una decisión cumple con los límites de riesgo.

    Args:
        decision: Decisión parseada del LLM
        available_balance: Balance disponible en USDT
        max_positions: Máximo de posiciones permitidas
        current_positions: Número actual de posiciones abiertas
        allowed_symbols: Lista de símbolos permitidos

    Returns:
        Tuple (is_valid, error_message)
    """
    action = decision["action"]

    # HOLD always valid
    if action == "HOLD":
        return True, ""

    # Validate symbol
    symbol = decision.get("symbol")
    if symbol and symbol not in allowed_symbols:
        return False, f"Symbol {symbol} not allowed. Must be one of {allowed_symbols}"

    # CLOSE is valid if symbol is valid
    if action == "CLOSE":
        return True, ""

    # Validate BUY/SELL
    if action in ["BUY", "SELL"]:
        # Check position limit
        if current_positions >= max_positions:
            return False, f"Maximum positions reached ({current_positions}/{max_positions})"

        # Check quantity
        quantity_usd = Decimal(str(decision.get("quantity_usd", 0)))
        if quantity_usd < Decimal("10"):
            return False, f"Trade size too small (${quantity_usd} < $10 minimum)"

        if quantity_usd > Decimal("40"):
            return False, f"Trade size too large (${quantity_usd} > $40 maximum)"

        # Check available balance
        leverage = decision.get("leverage", 1)
        required_margin = quantity_usd / Decimal(str(leverage))

        if required_margin > available_balance:
            return False, f"Insufficient balance (need ${required_margin}, have ${available_balance})"

        # Check leverage
        if leverage < 1 or leverage > 10:
            return False, f"Leverage {leverage}x outside allowed range (1x-10x)"

    return True, ""
