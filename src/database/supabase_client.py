"""
Supabase client para el sistema de trading multi-LLM.

Proporciona una interfaz simplificada para interactuar con la base de datos
Supabase (PostgreSQL), incluyendo operaciones CRUD y consultas específicas
para el sistema de trading.
"""

from typing import Optional, Dict, List, Any
from datetime import datetime
import asyncio
from decimal import Decimal

from supabase import create_client, Client
from postgrest.exceptions import APIError

from config.settings import settings
from src.utils.logger import app_logger
from src.utils.exceptions import DatabaseError, DatabaseConnectionError


class SupabaseClient:
    """
    Cliente Supabase para el sistema de trading.

    Proporciona métodos para:
    - Gestión de cuentas LLM
    - Operaciones de posiciones
    - Registro de trades y órdenes
    - Consulta de datos de mercado
    - Logging de decisiones rechazadas y llamadas API
    """

    def __init__(self):
        """Inicializar cliente Supabase."""
        self._client: Optional[Client] = None
        self._connected: bool = False

    def connect(self) -> None:
        """
        Establecer conexión con Supabase.

        Raises:
            DatabaseConnectionError: Si falla la conexión
        """
        try:
            app_logger.info(f"Connecting to Supabase: {settings.SUPABASE_URL}")

            self._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )

            # Test connection with a simple query
            self._client.table("llm_accounts").select("llm_id").limit(1).execute()

            self._connected = True
            app_logger.info("✅ Successfully connected to Supabase")

        except Exception as e:
            self._connected = False
            error_msg = f"Failed to connect to Supabase: {str(e)}"
            app_logger.error(error_msg)
            raise DatabaseConnectionError(error_msg)

    def disconnect(self) -> None:
        """Cerrar conexión con Supabase."""
        self._client = None
        self._connected = False
        app_logger.info("Disconnected from Supabase")

    @property
    def is_connected(self) -> bool:
        """Check si está conectado."""
        return self._connected and self._client is not None

    def _ensure_connected(self) -> None:
        """Asegurar que hay conexión antes de ejecutar queries."""
        if not self.is_connected:
            raise DatabaseConnectionError("Not connected to database. Call connect() first.")

    # ============================================
    # LLM ACCOUNTS
    # ============================================

    def get_llm_account(self, llm_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener cuenta de un LLM.

        Args:
            llm_id: ID del LLM (ej: 'LLM-A')

        Returns:
            Dict con datos de la cuenta o None si no existe
        """
        self._ensure_connected()

        try:
            response = self._client.table("llm_accounts").select("*").eq("llm_id", llm_id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except APIError as e:
            app_logger.error(f"Error fetching LLM account {llm_id}: {e}")
            raise DatabaseError(f"Failed to fetch LLM account: {str(e)}")

    def get_all_llm_accounts(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Obtener todas las cuentas LLM.

        Args:
            active_only: Si True, solo retornar cuentas activas

        Returns:
            Lista de cuentas LLM
        """
        self._ensure_connected()

        try:
            query = self._client.table("llm_accounts").select("*")

            if active_only:
                query = query.eq("is_active", True).eq("is_trading_enabled", True)

            response = query.execute()
            return response.data if response.data else []

        except APIError as e:
            app_logger.error(f"Error fetching LLM accounts: {e}")
            raise DatabaseError(f"Failed to fetch LLM accounts: {str(e)}")

    def update_llm_balance(
        self,
        llm_id: str,
        new_balance: Decimal,
        margin_used: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Actualizar balance de un LLM.

        Args:
            llm_id: ID del LLM
            new_balance: Nuevo balance
            margin_used: Margen utilizado (opcional)

        Returns:
            Cuenta actualizada
        """
        self._ensure_connected()

        try:
            update_data = {"balance": float(new_balance)}

            if margin_used is not None:
                update_data["margin_used"] = float(margin_used)

            response = self._client.table("llm_accounts").update(update_data).eq("llm_id", llm_id).execute()

            if response.data and len(response.data) > 0:
                app_logger.info(f"Updated balance for {llm_id}: ${new_balance}")
                return response.data[0]

            raise DatabaseError(f"No LLM account found with ID {llm_id}")

        except APIError as e:
            app_logger.error(f"Error updating LLM balance for {llm_id}: {e}")
            raise DatabaseError(f"Failed to update LLM balance: {str(e)}")

    def update_llm_stats(
        self,
        llm_id: str,
        total_pnl: Optional[Decimal] = None,
        realized_pnl: Optional[Decimal] = None,
        unrealized_pnl: Optional[Decimal] = None,
        total_trades: Optional[int] = None,
        winning_trades: Optional[int] = None,
        losing_trades: Optional[int] = None,
        sharpe_ratio: Optional[float] = None,
        max_drawdown: Optional[float] = None,
        open_positions: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Actualizar estadísticas de trading de un LLM.

        Args:
            llm_id: ID del LLM
            **kwargs: Estadísticas a actualizar

        Returns:
            Cuenta actualizada
        """
        self._ensure_connected()

        try:
            update_data = {}

            if total_pnl is not None:
                update_data["total_pnl"] = float(total_pnl)
            if realized_pnl is not None:
                update_data["realized_pnl"] = float(realized_pnl)
            if unrealized_pnl is not None:
                update_data["unrealized_pnl"] = float(unrealized_pnl)
            if total_trades is not None:
                update_data["total_trades"] = total_trades
            if winning_trades is not None:
                update_data["winning_trades"] = winning_trades
            if losing_trades is not None:
                update_data["losing_trades"] = losing_trades
            if sharpe_ratio is not None:
                update_data["sharpe_ratio"] = sharpe_ratio
            if max_drawdown is not None:
                update_data["max_drawdown"] = max_drawdown
            if open_positions is not None:
                update_data["open_positions"] = open_positions

            response = self._client.table("llm_accounts").update(update_data).eq("llm_id", llm_id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]

            raise DatabaseError(f"No LLM account found with ID {llm_id}")

        except APIError as e:
            app_logger.error(f"Error updating LLM stats for {llm_id}: {e}")
            raise DatabaseError(f"Failed to update LLM stats: {str(e)}")

    def upsert_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert or update an LLM account (upsert based on llm_id).

        Args:
            account_data: Account data to upsert

        Returns:
            Upserted account
        """
        self._ensure_connected()

        try:
            # Use upsert with llm_id as unique key
            response = self._client.table("llm_accounts").upsert(
                account_data,
                on_conflict="llm_id"
            ).execute()

            if response.data and len(response.data) > 0:
                app_logger.debug(f"Upserted account: {account_data['llm_id']}")
                return response.data[0]

            raise DatabaseError("Failed to upsert account")

        except APIError as e:
            app_logger.error(f"Error upserting account: {e}")
            raise DatabaseError(f"Failed to upsert account: {str(e)}")

    def increment_api_calls(self, llm_id: str, increment_hour: bool = True, increment_day: bool = True) -> None:
        """
        Incrementar contadores de llamadas API.

        Args:
            llm_id: ID del LLM
            increment_hour: Incrementar contador horario
            increment_day: Incrementar contador diario
        """
        self._ensure_connected()

        try:
            # Get current values
            account = self.get_llm_account(llm_id)
            if not account:
                raise DatabaseError(f"LLM account {llm_id} not found")

            update_data = {"last_decision_at": datetime.now().isoformat()}

            if increment_hour:
                update_data["api_calls_this_hour"] = account["api_calls_this_hour"] + 1

            if increment_day:
                update_data["api_calls_today"] = account["api_calls_today"] + 1

            self._client.table("llm_accounts").update(update_data).eq("llm_id", llm_id).execute()

        except APIError as e:
            app_logger.error(f"Error incrementing API calls for {llm_id}: {e}")
            raise DatabaseError(f"Failed to increment API calls: {str(e)}")

    # ============================================
    # POSITIONS
    # ============================================

    def create_position(self, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear una nueva posición.

        Args:
            position_data: Datos de la posición

        Returns:
            Posición creada
        """
        self._ensure_connected()

        try:
            response = self._client.table("positions").insert(position_data).execute()

            if response.data and len(response.data) > 0:
                app_logger.info(f"Created position: {response.data[0]['id']}")
                return response.data[0]

            raise DatabaseError("Failed to create position")

        except APIError as e:
            app_logger.error(f"Error creating position: {e}")
            raise DatabaseError(f"Failed to create position: {str(e)}")

    def get_open_positions(self, llm_id: Optional[str] = None, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtener posiciones abiertas.

        Args:
            llm_id: Filtrar por LLM (opcional)
            symbol: Filtrar por símbolo (opcional)

        Returns:
            Lista de posiciones abiertas
        """
        self._ensure_connected()

        try:
            query = self._client.table("positions").select("*").eq("status", "OPEN")

            if llm_id:
                query = query.eq("llm_id", llm_id)

            if symbol:
                query = query.eq("symbol", symbol)

            response = query.execute()
            return response.data if response.data else []

        except APIError as e:
            app_logger.error(f"Error fetching open positions: {e}")
            raise DatabaseError(f"Failed to fetch open positions: {str(e)}")

    def get_position_by_id(self, position_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener posición por ID.

        Args:
            position_id: UUID de la posición

        Returns:
            Posición o None si no existe
        """
        self._ensure_connected()

        try:
            response = self._client.table("positions").select("*").eq("id", position_id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except APIError as e:
            app_logger.error(f"Error fetching position {position_id}: {e}")
            raise DatabaseError(f"Failed to fetch position: {str(e)}")

    def update_position(self, position_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualizar posición.

        Args:
            position_id: UUID de la posición
            update_data: Datos a actualizar

        Returns:
            Posición actualizada
        """
        self._ensure_connected()

        try:
            response = self._client.table("positions").update(update_data).eq("id", position_id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]

            raise DatabaseError(f"Position {position_id} not found")

        except APIError as e:
            app_logger.error(f"Error updating position {position_id}: {e}")
            raise DatabaseError(f"Failed to update position: {str(e)}")

    def upsert_position(self, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert or update a position (upsert based on position_id).

        Args:
            position_data: Position data to upsert

        Returns:
            Upserted position
        """
        self._ensure_connected()

        try:
            # Use upsert with position_id as unique key
            response = self._client.table("positions").upsert(
                position_data,
                on_conflict="position_id"
            ).execute()

            if response.data and len(response.data) > 0:
                app_logger.debug(f"Upserted position: {position_data['position_id']}")
                return response.data[0]

            raise DatabaseError("Failed to upsert position")

        except APIError as e:
            app_logger.error(f"Error upserting position: {e}")
            raise DatabaseError(f"Failed to upsert position: {str(e)}")

    def update_position_status(self, position_id: str, status: str) -> Dict[str, Any]:
        """
        Update position status.

        Args:
            position_id: Position identifier
            status: New status (OPEN, CLOSED, LIQUIDATED)

        Returns:
            Updated position
        """
        self._ensure_connected()

        try:
            update_data = {"status": status}

            if status in ["CLOSED", "LIQUIDATED"]:
                update_data["closed_at"] = datetime.now().isoformat()

            response = self._client.table("positions").update(update_data).eq("position_id", position_id).execute()

            if response.data and len(response.data) > 0:
                app_logger.debug(f"Updated position {position_id} status to {status}")
                return response.data[0]

            raise DatabaseError(f"Position {position_id} not found")

        except APIError as e:
            app_logger.error(f"Error updating position status: {e}")
            raise DatabaseError(f"Failed to update position status: {str(e)}")

    def close_position(
        self,
        position_id: str,
        current_price: Decimal,
        pnl: Decimal,
        status: str = "CLOSED"
    ) -> Dict[str, Any]:
        """
        Cerrar posición.

        Args:
            position_id: UUID de la posición
            current_price: Precio actual
            pnl: P&L final
            status: Estado ('CLOSED' o 'LIQUIDATED')

        Returns:
            Posición cerrada
        """
        self._ensure_connected()

        try:
            update_data = {
                "status": status,
                "current_price": float(current_price),
                "unrealized_pnl": float(pnl),
                "closed_at": datetime.now().isoformat()
            }

            response = self._client.table("positions").update(update_data).eq("id", position_id).execute()

            if response.data and len(response.data) > 0:
                app_logger.info(f"Closed position {position_id} with P&L: ${pnl}")
                return response.data[0]

            raise DatabaseError(f"Position {position_id} not found")

        except APIError as e:
            app_logger.error(f"Error closing position {position_id}: {e}")
            raise DatabaseError(f"Failed to close position: {str(e)}")

    # ============================================
    # TRADES
    # ============================================

    def create_trade(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Registrar un trade.

        Args:
            trade_data: Datos del trade

        Returns:
            Trade creado
        """
        self._ensure_connected()

        try:
            response = self._client.table("trades").insert(trade_data).execute()

            if response.data and len(response.data) > 0:
                app_logger.info(f"Created trade: {response.data[0]['id']}")
                return response.data[0]

            raise DatabaseError("Failed to create trade")

        except APIError as e:
            app_logger.error(f"Error creating trade: {e}")
            raise DatabaseError(f"Failed to create trade: {str(e)}")

    def get_trades(
        self,
        llm_id: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtener historial de trades.

        Args:
            llm_id: Filtrar por LLM (opcional)
            symbol: Filtrar por símbolo (opcional)
            limit: Máximo de trades a retornar

        Returns:
            Lista de trades
        """
        self._ensure_connected()

        try:
            query = self._client.table("trades").select("*").order("executed_at", desc=True).limit(limit)

            if llm_id:
                query = query.eq("llm_id", llm_id)

            if symbol:
                query = query.eq("symbol", symbol)

            response = query.execute()
            return response.data if response.data else []

        except APIError as e:
            app_logger.error(f"Error fetching trades: {e}")
            raise DatabaseError(f"Failed to fetch trades: {str(e)}")

    # ============================================
    # ORDERS
    # ============================================

    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear una orden.

        Args:
            order_data: Datos de la orden

        Returns:
            Orden creada
        """
        self._ensure_connected()

        try:
            response = self._client.table("orders").insert(order_data).execute()

            if response.data and len(response.data) > 0:
                app_logger.info(f"Created order: {response.data[0]['id']}")
                return response.data[0]

            raise DatabaseError("Failed to create order")

        except APIError as e:
            app_logger.error(f"Error creating order: {e}")
            raise DatabaseError(f"Failed to create order: {str(e)}")

    def update_order(self, order_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualizar orden.

        Args:
            order_id: UUID de la orden
            update_data: Datos a actualizar

        Returns:
            Orden actualizada
        """
        self._ensure_connected()

        try:
            response = self._client.table("orders").update(update_data).eq("id", order_id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]

            raise DatabaseError(f"Order {order_id} not found")

        except APIError as e:
            app_logger.error(f"Error updating order {order_id}: {e}")
            raise DatabaseError(f"Failed to update order: {str(e)}")

    # ============================================
    # MARKET DATA
    # ============================================

    def upsert_market_data(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insertar o actualizar datos de mercado.

        Args:
            market_data: Datos de mercado

        Returns:
            Market data guardado
        """
        self._ensure_connected()

        try:
            response = self._client.table("market_data").upsert(market_data).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]

            raise DatabaseError("Failed to upsert market data")

        except APIError as e:
            app_logger.error(f"Error upserting market data: {e}")
            raise DatabaseError(f"Failed to upsert market data: {str(e)}")

    def insert_market_data(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Alias for upsert_market_data for backwards compatibility.

        Args:
            market_data: Datos de mercado

        Returns:
            Market data guardado
        """
        return self.upsert_market_data(market_data)

    def get_latest_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Obtener últimos datos de mercado para un símbolo.

        Args:
            symbol: Símbolo (ej: 'ETHUSDT')

        Returns:
            Datos de mercado o None
        """
        self._ensure_connected()

        try:
            response = (
                self._client.table("market_data")
                .select("*")
                .eq("symbol", symbol)
                .order("data_timestamp", desc=True)
                .limit(1)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except APIError as e:
            app_logger.error(f"Error fetching market data for {symbol}: {e}")
            raise DatabaseError(f"Failed to fetch market data: {str(e)}")

    # ============================================
    # REJECTED DECISIONS
    # ============================================

    def log_rejected_decision(self, decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Registrar decisión rechazada (para el 10% sample).

        Args:
            decision_data: Datos de la decisión rechazada

        Returns:
            Registro creado
        """
        self._ensure_connected()

        try:
            response = self._client.table("rejected_decisions").insert(decision_data).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]

            raise DatabaseError("Failed to log rejected decision")

        except APIError as e:
            app_logger.error(f"Error logging rejected decision: {e}")
            raise DatabaseError(f"Failed to log rejected decision: {str(e)}")

    # ============================================
    # LLM DECISIONS
    # ============================================

    def insert_llm_decision(self, decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert an LLM trading decision into the database.

        Args:
            decision_data: Decision data to insert

        Returns:
            Inserted decision record
        """
        self._ensure_connected()

        try:
            response = self._client.table("llm_decisions").insert(decision_data).execute()

            if response.data and len(response.data) > 0:
                app_logger.debug(f"Inserted LLM decision: {decision_data.get('llm_id', 'UNKNOWN')}")
                return response.data[0]

            raise DatabaseError("Failed to insert LLM decision")

        except APIError as e:
            app_logger.error(f"Error inserting LLM decision: {e}")
            raise DatabaseError(f"Failed to insert LLM decision: {str(e)}")

    # ============================================
    # LLM API CALLS
    # ============================================

    def log_llm_api_call(self, api_call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Registrar llamada a API de LLM.

        Args:
            api_call_data: Datos de la llamada API

        Returns:
            Registro creado
        """
        self._ensure_connected()

        try:
            response = self._client.table("llm_api_calls").insert(api_call_data).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]

            raise DatabaseError("Failed to log LLM API call")

        except APIError as e:
            app_logger.error(f"Error logging LLM API call: {e}")
            raise DatabaseError(f"Failed to log LLM API call: {str(e)}")

    # ============================================
    # VIEWS & ANALYTICS
    # ============================================

    def get_llm_leaderboard(self) -> List[Dict[str, Any]]:
        """
        Obtener leaderboard de LLMs.

        Returns:
            Lista de LLMs ordenados por balance
        """
        self._ensure_connected()

        try:
            response = self._client.table("llm_leaderboard").select("*").execute()
            return response.data if response.data else []

        except APIError as e:
            app_logger.error(f"Error fetching leaderboard: {e}")
            raise DatabaseError(f"Failed to fetch leaderboard: {str(e)}")

    def get_active_positions_summary(self) -> List[Dict[str, Any]]:
        """
        Obtener resumen de posiciones activas.

        Returns:
            Lista de posiciones activas con P&L
        """
        self._ensure_connected()

        try:
            response = self._client.table("active_positions_summary").select("*").execute()
            return response.data if response.data else []

        except APIError as e:
            app_logger.error(f"Error fetching active positions summary: {e}")
            raise DatabaseError(f"Failed to fetch active positions summary: {str(e)}")

    def get_llm_trading_stats(self) -> List[Dict[str, Any]]:
        """
        Obtener estadísticas de trading por LLM.

        Returns:
            Lista de estadísticas por LLM
        """
        self._ensure_connected()

        try:
            response = self._client.table("llm_trading_stats").select("*").execute()
            return response.data if response.data else []

        except APIError as e:
            app_logger.error(f"Error fetching trading stats: {e}")
            raise DatabaseError(f"Failed to fetch trading stats: {str(e)}")


# ============================================
# SINGLETON INSTANCE
# ============================================

_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """
    Obtener instancia singleton del cliente Supabase.

    Returns:
        SupabaseClient instance
    """
    global _supabase_client

    if _supabase_client is None:
        _supabase_client = SupabaseClient()
        _supabase_client.connect()

    return _supabase_client
