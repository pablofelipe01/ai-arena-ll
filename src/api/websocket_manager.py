"""
WebSocket Connection Manager - Manages real-time client connections.

Handles:
- Client connection/disconnection
- Message broadcasting
- Event streaming to dashboard
"""

from typing import List, Dict, Any
from datetime import datetime
from decimal import Decimal
import json
import asyncio
from fastapi import WebSocket

from src.utils.logger import app_logger


def convert_decimals_to_float(obj: Any) -> Any:
    """
    Recursively convert Decimal objects to float for JSON serialization.

    Args:
        obj: Object to convert (dict, list, Decimal, or primitive)

    Returns:
        Object with all Decimals converted to floats
    """
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimals_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals_to_float(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_decimals_to_float(item) for item in obj)
    else:
        return obj


class WebSocketManager:
    """
    Manages WebSocket connections for real-time dashboard updates.

    Handles multiple concurrent client connections and broadcasts
    events (trading cycles, market updates, decisions) to all connected clients.
    """

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: List[WebSocket] = []
        self.connection_count = 0
        app_logger.info("WebSocketManager initialized")

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection to register
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_count += 1

        app_logger.info(
            f"WebSocket client connected. "
            f"Active connections: {len(self.active_connections)}"
        )

        # Send welcome message
        await self.send_personal_message(
            {
                "type": "connection",
                "status": "connected",
                "message": "Connected to trading system",
                "timestamp": datetime.utcnow().isoformat()
            },
            websocket
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Unregister a WebSocket connection.

        Args:
            websocket: WebSocket connection to unregister
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        app_logger.info(
            f"WebSocket client disconnected. "
            f"Active connections: {len(self.active_connections)}"
        )

    async def send_personal_message(
        self,
        message: Dict[str, Any],
        websocket: WebSocket
    ) -> None:
        """
        Send message to a specific WebSocket client.

        Args:
            message: Message dictionary to send
            websocket: Target WebSocket connection
        """
        try:
            # Convert Decimals to floats for JSON serialization
            converted_message = convert_decimals_to_float(message)
            await websocket.send_json(converted_message)
        except Exception as e:
            app_logger.error(f"Error sending personal message: {e}")

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast message to all connected clients.

        Args:
            message: Message dictionary to broadcast
        """
        if not self.active_connections:
            return

        app_logger.debug(
            f"Broadcasting message to {len(self.active_connections)} clients"
        )

        # Convert Decimals to floats for JSON serialization
        converted_message = convert_decimals_to_float(message)

        # Send to all connections
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(converted_message)
            except Exception as e:
                app_logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_trading_cycle_start(self) -> None:
        """Broadcast trading cycle start event."""
        await self.broadcast({
            "type": "cycle_start",
            "message": "Trading cycle starting",
            "timestamp": datetime.utcnow().isoformat()
        })

    async def broadcast_trading_cycle_complete(
        self,
        result: Dict[str, Any]
    ) -> None:
        """
        Broadcast trading cycle completion.

        Args:
            result: Trading cycle execution result
        """
        await self.broadcast({
            "type": "cycle_complete",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def broadcast_market_update(
        self,
        market_data: Dict[str, Any]
    ) -> None:
        """
        Broadcast market data update.

        Args:
            market_data: Current market prices and indicators
        """
        await self.broadcast({
            "type": "market_update",
            "data": market_data,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def broadcast_llm_decision(
        self,
        llm_id: str,
        decision: Dict[str, Any],
        execution_result: Dict[str, Any]
    ) -> None:
        """
        Broadcast LLM trading decision.

        Args:
            llm_id: LLM identifier
            decision: Trading decision
            execution_result: Execution result
        """
        await self.broadcast({
            "type": "llm_decision",
            "llm_id": llm_id,
            "decision": decision,
            "execution": execution_result,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def broadcast_position_update(
        self,
        llm_id: str,
        position: Dict[str, Any],
        action: str
    ) -> None:
        """
        Broadcast position update (open/close).

        Args:
            llm_id: LLM identifier
            position: Position data
            action: "opened" or "closed"
        """
        await self.broadcast({
            "type": "position_update",
            "llm_id": llm_id,
            "position": position,
            "action": action,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def broadcast_account_update(
        self,
        accounts: List[Dict[str, Any]]
    ) -> None:
        """
        Broadcast account balances and PnL update.

        Args:
            accounts: List of account data
        """
        await self.broadcast({
            "type": "account_update",
            "accounts": accounts,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def broadcast_error(
        self,
        error_type: str,
        error_message: str
    ) -> None:
        """
        Broadcast error notification.

        Args:
            error_type: Type of error
            error_message: Error description
        """
        await self.broadcast({
            "type": "error",
            "error_type": error_type,
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def broadcast_scheduler_status(
        self,
        status: Dict[str, Any]
    ) -> None:
        """
        Broadcast scheduler status update.

        Args:
            status: Scheduler status data
        """
        await self.broadcast({
            "type": "scheduler_status",
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_stats(self) -> Dict[str, Any]:
        """
        Get WebSocket manager statistics.

        Returns:
            Dict with connection statistics
        """
        return {
            "active_connections": len(self.active_connections),
            "total_connections": self.connection_count,
            "timestamp": datetime.utcnow().isoformat()
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<WebSocketManager "
            f"active={len(self.active_connections)} "
            f"total={self.connection_count}>"
        )


# Global WebSocket manager instance
_ws_manager: WebSocketManager = None


def get_ws_manager() -> WebSocketManager:
    """
    Get or create global WebSocket manager instance.

    Returns:
        WebSocketManager instance
    """
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WebSocketManager()
    return _ws_manager


def cleanup_ws_manager() -> None:
    """Cleanup global WebSocket manager."""
    global _ws_manager
    _ws_manager = None
