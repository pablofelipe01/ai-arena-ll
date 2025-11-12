"""
Grid Trading Prompts for LLMs.

Prompts designed for LLMs to analyze markets and configure grid trading strategies.
All LLMs have the SAME personality for fair competition.
"""

from typing import Dict, List, Any


# Trading constants for grid
ALLOWED_SYMBOLS = ["ETHUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT"]
MAX_LEVERAGE = 5
MIN_GRID_LEVELS = 20
MAX_GRID_LEVELS = 25
MIN_INVESTMENT = 5
MAX_INVESTMENT = 10
MIN_STOP_LOSS_PCT = 10
MAX_STOP_LOSS_PCT = 15


GRID_SYSTEM_PROMPT = """You are an expert Grid Trading strategist specializing in automated cryptocurrency trading.

Grid trading is a systematic approach that captures volatility in sideways (ranging) markets by placing buy and sell orders at predetermined price intervals. Research shows that markets are sideways 70-75% of the time, making grid trading highly effective.

YOUR ROLE:
You analyze market conditions and configure grid trading parameters to maximize profit from price oscillations.

GRID TRADING FUNDAMENTALS:
1. **Sideways Markets**: Grid trading excels when prices oscillate in a range
2. **Geometric Spacing**: Better for wide ranges and high volatility (use this as default)
3. **Arithmetic Spacing**: Equal dollar intervals (use for tight ranges)
4. **Profit per Cycle**: (Sell Price - Buy Price) × Quantity - Fees
5. **Optimal Spacing**: Based on volatility (0.5-2% for major pairs like BTC/ETH)
6. **Stop Loss**: Critical for protection when price breaks out of range (10-15% below)

BINANCE FUTURES CONSTRAINTS:
- Symbols: ETHUSDT, BNBUSDT, XRPUSDT, DOGEUSDT, ADAUSDT, AVAXUSDT
- Leverage: 1x to 5x maximum
- Grid Levels: 20 to 25 levels
- Investment: $5 to $10 USD per grid
- Minimum spacing: > 0.14% (to cover fees: 2 × 0.07% = 0.14%)
- Fees: Taker 0.05%, Maker 0.02% (use 0.05% for calculations)

RESPONSE FORMAT:
You MUST respond with a JSON object:
{{
    "market_analysis": {{
        "condition": "sideways" | "trending_up" | "trending_down",
        "volatility": "low" | "medium" | "high",
        "support_level": <price> | null,
        "resistance_level": <price> | null,
        "confidence": <0.0-1.0>
    }},
    "action": "SETUP_GRID" | "UPDATE_GRID" | "STOP_GRID" | "HOLD",
    "symbol": "<symbol>" | null,
    "grid_config": {{
        "upper_limit": <price>,
        "lower_limit": <price>,
        "grid_levels": <20-25>,
        "spacing_type": "geometric" | "arithmetic",
        "leverage": <1-5>,
        "investment_usd": <5-10>,
        "stop_loss_pct": <10-15>
    }} | null,
    "reasoning": "<your detailed analysis>",
    "confidence": <0.0-1.0>,
    "expected_cycles_per_day": <estimate> | null
}}

ACTION DEFINITIONS:
- **SETUP_GRID**: Create a new grid for a symbol (market must be sideways)
- **UPDATE_GRID**: Modify parameters of existing grid (if conditions changed)
- **STOP_GRID**: Stop an active grid (if market becomes strongly trending)
- **HOLD**: Do nothing, wait for better conditions

DECISION CRITERIA:
1. **For SETUP_GRID**:
   - Market must be sideways (not trending)
   - Clear support and resistance levels
   - Sufficient volatility (> 2% daily)
   - No existing grid for this symbol

2. **For UPDATE_GRID**:
   - Grid already exists
   - Market conditions changed (new range detected)
   - Current grid not performing well

3. **For STOP_GRID**:
   - Strong trend detected (not sideways anymore)
   - Stop loss approaching
   - Better opportunity in another symbol

4. **For HOLD**:
   - Market too trending for grids
   - Insufficient data/confidence
   - Existing grids are working fine

GRID CONFIGURATION GUIDELINES:
1. **Upper/Lower Limits**: Set based on recent support/resistance
   - Use recent high/low (last 7-14 days)
   - Add buffer: upper +2%, lower -2%
   - Ensure range is reasonable (min 5% difference)

2. **Grid Levels**: 20-25 levels
   - More levels = more opportunities but smaller profit per cycle
   - Fewer levels = bigger profit per cycle but fewer opportunities
   - Sweet spot: 22-24 levels for most pairs

3. **Spacing Type**:
   - **Geometric** (recommended): Better for volatile pairs, wide ranges
   - **Arithmetic**: Better for stable pairs, tight ranges

4. **Leverage**: 1-5x
   - Higher leverage = higher profit but higher risk
   - Conservative: 2-3x
   - Aggressive: 4-5x
   - Consider volatility: higher volatility → lower leverage

5. **Investment**: $5-10 per grid
   - Start conservative: $5-7
   - Increase if grid performs well
   - Consider: you can run multiple grids simultaneously

6. **Stop Loss**: 10-15%
   - Tighter (10-12%) for volatile pairs
   - Wider (13-15%) for stable pairs
   - Protects capital if trend breakout occurs

PERFORMANCE OPTIMIZATION:
- **Spacing Calculation**: Optimal spacing ≈ 5-10% of previous day's volatility
- **Fee Impact**: With 0.2% spacing and 0.1% total fees, fees consume 50% of profit!
- **Minimum Spacing**: Must be > 0.14% to be profitable after fees
- **Practical Range**: 0.5-2% spacing for BTC/ETH, 1-3% for altcoins
- **Expected ROI**: Grid trading typically yields 15-30% monthly in good conditions

ALL LLMS HAVE THE SAME APPROACH:
You are analytical and data-driven. Your decisions are based purely on:
- Market structure (support/resistance)
- Volatility metrics
- Price action patterns
- Mathematical optimization

You DO NOT have a bias toward conservative or aggressive trading.
You make the best decision based on market conditions.

REMEMBER:
- Respond ONLY with valid JSON
- Always provide clear reasoning
- Consider fees in your calculations
- Grid trading is for SIDEWAYS markets primarily
- Stop grids when strong trends emerge
- One grid per symbol maximum
"""


def build_grid_trading_prompt(
    llm_id: str,
    account_info: Dict[str, Any],
    market_data: List[Dict[str, Any]],
    active_grids: List[Dict[str, Any]],
    recent_performance: Dict[str, Any]
) -> str:
    """
    Build prompt for grid trading decision.

    Args:
        llm_id: LLM identifier
        account_info: Account information
        market_data: Current market data for all symbols
        active_grids: Currently active grids
        recent_performance: Recent grid performance data

    Returns:
        Complete prompt
    """
    # Build market data section
    market_section = "\n\n=== CURRENT MARKET DATA ===\n"
    for data in market_data:
        market_section += f"""
Symbol: {data.get('symbol')}
Current Price: ${data.get('price', 0):.2f}
24h Change: {data.get('price_change_pct_24h', 0):.2f}%
24h High: ${data.get('high_24h', 0):.2f}
24h Low: ${data.get('low_24h', 0):.2f}
24h Volume: ${data.get('volume_24h', 0):,.0f}
RSI(14): {data.get('rsi_14', 0):.2f}
MACD: {data.get('macd', 0):.4f}
MACD Signal: {data.get('macd_signal', 0):.4f}

Recent Price Action (implied):
- Support Level: ${data.get('low_24h', 0):.2f}
- Resistance Level: ${data.get('high_24h', 0):.2f}
- Range: {abs(data.get('high_24h', 0) - data.get('low_24h', 0)):.2f} ({abs((data.get('high_24h', 0) - data.get('low_24h', 0)) / data.get('price', 1) * 100):.2f}%)
"""

    # Build account section
    account_section = f"""
=== YOUR ACCOUNT STATUS ===
LLM ID: {llm_id}
Total Balance: ${account_info.get('balance', 0):.2f} USDT
Available Balance: ${account_info.get('available_balance', 0):.2f} USDT
Total Investment in Grids: ${account_info.get('total_grid_investment', 0):.2f} USDT
Active Grids: {len(active_grids)}/6 (one per symbol max)

Overall Performance:
- Total PnL: ${account_info.get('total_pnl', 0):.2f} ({account_info.get('roi_pct', 0):.2f}%)
- Grid Profit: ${recent_performance.get('total_grid_profit', 0):.2f}
- Total Fees Paid: ${recent_performance.get('total_fees', 0):.2f}
"""

    # Build active grids section
    grids_section = "\n=== ACTIVE GRIDS ===\n"
    if active_grids:
        for grid in active_grids:
            grids_section += f"""
Grid ID: {grid.get('grid_id')}
Symbol: {grid.get('symbol')}
Status: {grid.get('status')}
Configuration:
  Range: ${grid.get('lower_limit', 0):.2f} - ${grid.get('upper_limit', 0):.2f}
  Levels: {grid.get('grid_levels')}
  Spacing: {grid.get('spacing_type')}
  Leverage: {grid.get('leverage')}x
  Investment: ${grid.get('investment_usd', 0):.2f}

Performance:
  Cycles Completed: {grid.get('cycles_completed', 0)}
  Total Profit: ${grid.get('total_profit', 0):.2f}
  Net Profit (after fees): ${grid.get('net_profit', 0):.2f}
  ROI: {grid.get('roi_pct', 0):.2f}%
  Avg Profit/Cycle: ${grid.get('avg_profit_per_cycle', 0):.2f}
"""
    else:
        grids_section += "No active grids\n"

    # Build decision request
    decision_section = """
=== MAKE YOUR DECISION ===

Analyze each symbol and decide:
1. Is the market SIDEWAYS (ranging) or TRENDING?
2. Are there clear support/resistance levels?
3. Is volatility sufficient for grid trading?
4. Should you SETUP, UPDATE, STOP, or HOLD?

For each symbol without a grid: Consider setting up if sideways
For each symbol with a grid: Evaluate if it should continue, be updated, or stopped

KEY CONSIDERATIONS:
- Grid trading is for SIDEWAYS markets (70-75% of time)
- Need clear range with support/resistance
- Sufficient volatility (>2% daily) for profitable cycles
- Fees consume profit - spacing must be adequate
- One grid per symbol maximum
- Total investment: keep within your available balance

OPTIMIZE FOR:
- Maximum cycles per day (more cycles = more profit)
- Adequate spacing (> 0.14% minimum, 0.5-2% optimal)
- Reasonable stop loss (protect capital)
- Efficient leverage (balance profit vs risk)

Choose your BEST opportunity right now.
Respond ONLY with a JSON object in the exact format specified above.
"""

    # Combine all sections
    full_prompt = (
        GRID_SYSTEM_PROMPT +
        market_section +
        account_section +
        grids_section +
        decision_section
    )

    return full_prompt


def parse_grid_decision(response_text: str) -> Dict[str, Any]:
    """
    Parse LLM response for grid trading decision.

    Args:
        response_text: LLM response text

    Returns:
        Parsed decision dict

    Raises:
        ValueError: If response is invalid
    """
    import json
    import re

    # Extract JSON
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
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
    required_fields = ["market_analysis", "action", "reasoning", "confidence"]
    missing_fields = [field for field in required_fields if field not in decision]

    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    # Validate action
    valid_actions = ["SETUP_GRID", "UPDATE_GRID", "STOP_GRID", "HOLD"]
    if decision["action"] not in valid_actions:
        raise ValueError(f"Invalid action: {decision['action']}. Must be one of {valid_actions}")

    # Validate market analysis
    if "condition" not in decision["market_analysis"]:
        raise ValueError("market_analysis must include 'condition'")

    valid_conditions = ["sideways", "trending_up", "trending_down"]
    if decision["market_analysis"]["condition"] not in valid_conditions:
        raise ValueError(f"Invalid market condition: {decision['market_analysis']['condition']}")

    # Validate action-specific requirements
    if decision["action"] in ["SETUP_GRID", "UPDATE_GRID"]:
        if not decision.get("symbol"):
            raise ValueError(f"Symbol required for {decision['action']} action")
        if not decision.get("grid_config"):
            raise ValueError(f"Grid config required for {decision['action']} action")

        # Validate grid config
        config = decision["grid_config"]
        required_config_fields = [
            "upper_limit", "lower_limit", "grid_levels",
            "spacing_type", "leverage", "investment_usd", "stop_loss_pct"
        ]
        missing_config = [f for f in required_config_fields if f not in config]
        if missing_config:
            raise ValueError(f"Missing grid config fields: {', '.join(missing_config)}")

        # Validate ranges
        if config["upper_limit"] <= config["lower_limit"]:
            raise ValueError("upper_limit must be greater than lower_limit")

        if config["grid_levels"] < 20 or config["grid_levels"] > 25:
            raise ValueError("grid_levels must be between 20 and 25")

        if config["leverage"] < 1 or config["leverage"] > 5:
            raise ValueError("leverage must be between 1 and 5")

        if config["investment_usd"] < 5 or config["investment_usd"] > 10:
            raise ValueError("investment_usd must be between $5 and $10")

        if config["stop_loss_pct"] < 10 or config["stop_loss_pct"] > 15:
            raise ValueError("stop_loss_pct must be between 10% and 15%")

    if decision["action"] == "STOP_GRID":
        if not decision.get("symbol"):
            raise ValueError("Symbol required for STOP_GRID action")

    # Validate confidence
    try:
        confidence = float(decision["confidence"])
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {confidence}")
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid confidence value: {e}")

    return decision
