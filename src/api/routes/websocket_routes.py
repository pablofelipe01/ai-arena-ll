"""
WebSocket Routes - Real-time dashboard connections.

Provides WebSocket endpoint for real-time updates:
- Trading cycle events
- Market data updates
- LLM decisions
- Position changes
- Account updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from datetime import datetime

from src.api.websocket_manager import get_ws_manager
from src.api.dependencies import get_trading_service_dependency
from src.services.trading_service import TradingService
from src.utils.logger import app_logger


router = APIRouter(tags=["WebSocket"])


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    trading_service: TradingService = Depends(get_trading_service_dependency)
):
    """
    WebSocket endpoint for real-time dashboard updates.

    Protocol:
    - Client connects to /ws
    - Server sends connection confirmation
    - Server broadcasts updates:
      * Trading cycle events
      * Market data updates
      * LLM decisions
      * Position changes
      * Account updates
      * Scheduler status

    Message Format:
    {
        "type": "event_type",
        "data": {...},
        "timestamp": "ISO8601"
    }

    Event Types:
    - connection: Connection established
    - cycle_start: Trading cycle starting
    - cycle_complete: Trading cycle completed
    - market_update: Market prices updated
    - llm_decision: LLM made a decision
    - position_update: Position opened/closed
    - account_update: Account balances updated
    - scheduler_status: Scheduler status changed
    - error: Error occurred
    """
    ws_manager = get_ws_manager()

    # Accept connection
    await ws_manager.connect(websocket)

    try:
        # Send initial data
        await send_initial_data(websocket, trading_service, ws_manager)

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()

                # Handle client messages (ping, requests, etc.)
                await handle_client_message(
                    websocket,
                    data,
                    trading_service,
                    ws_manager
                )

            except WebSocketDisconnect:
                break
            except Exception as e:
                app_logger.error(f"Error in WebSocket loop: {e}", exc_info=True)
                break

    except Exception as e:
        app_logger.error(f"WebSocket error: {e}", exc_info=True)

    finally:
        # Disconnect
        ws_manager.disconnect(websocket)


async def send_initial_data(
    websocket: WebSocket,
    trading_service: TradingService,
    ws_manager
) -> None:
    """
    Send initial data to newly connected client.

    Args:
        websocket: WebSocket connection
        trading_service: TradingService instance
        ws_manager: WebSocketManager instance
    """
    try:
        # Get current trading status
        status = trading_service.get_trading_status()

        # Send trading status
        await ws_manager.send_personal_message(
            {
                "type": "initial_data",
                "trading_status": status,
                "timestamp": datetime.utcnow().isoformat()
            },
            websocket
        )

        # Get current market snapshot
        market_snapshot = trading_service.market_data.get_market_snapshot()

        # Send market data (convert all Decimals to floats)
        await ws_manager.send_personal_message(
            {
                "type": "market_snapshot",
                "data": {
                    "symbols": {
                        symbol: {
                            "price": float(data["price"]),
                            "price_change_pct_24h": float(data["price_change_pct_24h"]),
                            "volume_24h": float(data["volume_24h"])
                        }
                        for symbol, data in market_snapshot["symbols"].items()
                    },
                    "summary": {
                        "total_symbols": market_snapshot["summary"]["total_symbols"],
                        "gainers": market_snapshot["summary"]["gainers"],
                        "losers": market_snapshot["summary"]["losers"],
                        "total_volume_usdt": float(market_snapshot["summary"]["total_volume_usdt"])
                    }
                },
                "timestamp": datetime.utcnow().isoformat()
            },
            websocket
        )

        # Get scheduler status
        from src.background.scheduler import get_scheduler
        scheduler = get_scheduler()

        if scheduler:
            scheduler_status = scheduler.get_status()
            await ws_manager.send_personal_message(
                {
                    "type": "scheduler_status",
                    "status": scheduler_status,
                    "timestamp": datetime.utcnow().isoformat()
                },
                websocket
            )

    except Exception as e:
        app_logger.error(f"Error sending initial data: {e}", exc_info=True)


async def handle_client_message(
    websocket: WebSocket,
    message: str,
    trading_service: TradingService,
    ws_manager
) -> None:
    """
    Handle incoming messages from client.

    Args:
        websocket: WebSocket connection
        message: Message from client
        trading_service: TradingService instance
        ws_manager: WebSocketManager instance
    """
    try:
        import json

        # Parse message
        data = json.loads(message)
        msg_type = data.get("type")

        # Handle different message types
        if msg_type == "ping":
            # Respond to ping
            await ws_manager.send_personal_message(
                {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                },
                websocket
            )

        elif msg_type == "get_status":
            # Send current status
            status = trading_service.get_trading_status()
            await ws_manager.send_personal_message(
                {
                    "type": "trading_status",
                    "data": status,
                    "timestamp": datetime.utcnow().isoformat()
                },
                websocket
            )

        elif msg_type == "get_market":
            # Send current market data
            market_snapshot = trading_service.market_data.get_market_snapshot()
            # Convert Decimals to floats (done automatically by send_personal_message now)
            await ws_manager.send_personal_message(
                {
                    "type": "market_snapshot",
                    "data": market_snapshot,
                    "timestamp": datetime.utcnow().isoformat()
                },
                websocket
            )

        else:
            # Unknown message type
            await ws_manager.send_personal_message(
                {
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                    "timestamp": datetime.utcnow().isoformat()
                },
                websocket
            )

    except json.JSONDecodeError:
        app_logger.warning(f"Invalid JSON received: {message}")
    except Exception as e:
        app_logger.error(f"Error handling client message: {e}", exc_info=True)


# ============================================================================
# WebSocket Stats Endpoint
# ============================================================================

@router.get("/ws/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.

    Returns:
    - Number of active connections
    - Total connections made
    """
    ws_manager = get_ws_manager()
    return ws_manager.get_stats()
