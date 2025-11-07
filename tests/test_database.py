"""
Tests críticos para database operations.

Estos tests validan las operaciones esenciales de base de datos
para prevenir errores de datos que podrían causar pérdidas.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.database.supabase_client import SupabaseClient
from src.utils.exceptions import DatabaseError, DatabaseConnectionError


class TestSupabaseClient:
    """Tests para SupabaseClient."""

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock del cliente Supabase."""
        with patch('src.database.supabase_client.create_client') as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client

            # Mock successful connection test
            mock_table = Mock()
            mock_table.select.return_value.limit.return_value.execute.return_value = Mock(data=[])
            mock_client.table.return_value = mock_table

            yield mock_client

    def test_connect_success(self, mock_supabase_client):
        """Test conexión exitosa."""
        client = SupabaseClient()
        client.connect()

        assert client.is_connected is True

    def test_connect_failure(self):
        """Test fallo de conexión."""
        with patch('src.database.supabase_client.create_client') as mock_create:
            mock_create.side_effect = Exception("Connection failed")

            client = SupabaseClient()

            with pytest.raises(DatabaseConnectionError):
                client.connect()

            assert client.is_connected is False

    def test_disconnect(self, mock_supabase_client):
        """Test desconexión."""
        client = SupabaseClient()
        client.connect()
        client.disconnect()

        assert client.is_connected is False

    def test_ensure_connected_raises(self):
        """Test que _ensure_connected lanza error si no está conectado."""
        client = SupabaseClient()

        with pytest.raises(DatabaseConnectionError):
            client._ensure_connected()


class TestLLMAccountOperations:
    """Tests para operaciones de LLM accounts."""

    @pytest.fixture
    def connected_client(self):
        """Cliente conectado con mock."""
        with patch('src.database.supabase_client.create_client') as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client

            # Mock connection test
            mock_table = Mock()
            mock_table.select.return_value.limit.return_value.execute.return_value = Mock(data=[])
            mock_client.table.return_value = mock_table

            client = SupabaseClient()
            client.connect()

            # Setup mock client for subsequent calls
            client._client = mock_client

            yield client

    def test_get_llm_account_success(self, connected_client):
        """Test obtener cuenta LLM exitosamente."""
        mock_response = Mock()
        mock_response.data = [{
            'llm_id': 'LLM-A',
            'provider': 'claude',
            'balance': 100.00
        }]

        connected_client._client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        result = connected_client.get_llm_account('LLM-A')

        assert result is not None
        assert result['llm_id'] == 'LLM-A'
        assert result['balance'] == 100.00

    def test_get_llm_account_not_found(self, connected_client):
        """Test cuenta LLM no encontrada."""
        mock_response = Mock()
        mock_response.data = []

        connected_client._client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        result = connected_client.get_llm_account('LLM-X')

        assert result is None

    def test_update_llm_balance(self, connected_client):
        """Test actualizar balance de LLM."""
        mock_response = Mock()
        mock_response.data = [{
            'llm_id': 'LLM-A',
            'balance': 105.50,
            'margin_used': 10.00
        }]

        connected_client._client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

        result = connected_client.update_llm_balance(
            'LLM-A',
            Decimal('105.50'),
            Decimal('10.00')
        )

        assert result['llm_id'] == 'LLM-A'
        assert result['balance'] == 105.50


class TestPositionOperations:
    """Tests para operaciones de posiciones."""

    @pytest.fixture
    def connected_client(self):
        """Cliente conectado con mock."""
        with patch('src.database.supabase_client.create_client') as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client

            mock_table = Mock()
            mock_table.select.return_value.limit.return_value.execute.return_value = Mock(data=[])
            mock_client.table.return_value = mock_table

            client = SupabaseClient()
            client.connect()
            client._client = mock_client

            yield client

    def test_create_position(self, connected_client):
        """Test crear posición."""
        position_data = {
            'llm_id': 'LLM-A',
            'symbol': 'ETHUSDT',
            'side': 'LONG',
            'entry_price': 3250.00,
            'quantity': 0.01,
            'leverage': 3,
            'margin_used': 10.83,
            'liquidation_price': 2166.67
        }

        mock_response = Mock()
        mock_response.data = [{**position_data, 'id': 'position-uuid'}]

        connected_client._client.table.return_value.insert.return_value.execute.return_value = mock_response

        result = connected_client.create_position(position_data)

        assert result['llm_id'] == 'LLM-A'
        assert result['symbol'] == 'ETHUSDT'
        assert 'id' in result

    def test_get_open_positions(self, connected_client):
        """Test obtener posiciones abiertas."""
        mock_response = Mock()
        mock_response.data = [
            {'id': 'pos1', 'llm_id': 'LLM-A', 'symbol': 'ETHUSDT', 'status': 'OPEN'},
            {'id': 'pos2', 'llm_id': 'LLM-A', 'symbol': 'BNBUSDT', 'status': 'OPEN'}
        ]

        # Mock the chain: .table().select().eq("status", "OPEN").eq("llm_id", llm_id).execute()
        mock_query = Mock()
        mock_query.eq.return_value.execute.return_value = mock_response  # For second .eq() call
        mock_query.execute.return_value = mock_response  # Also support direct execute
        connected_client._client.table.return_value.select.return_value.eq.return_value = mock_query

        result = connected_client.get_open_positions(llm_id='LLM-A')

        assert len(result) == 2
        assert all(pos['status'] == 'OPEN' for pos in result)

    def test_close_position(self, connected_client):
        """Test cerrar posición."""
        mock_response = Mock()
        mock_response.data = [{
            'id': 'position-uuid',
            'status': 'CLOSED',
            'current_price': 3300.00,
            'unrealized_pnl': 5.00
        }]

        connected_client._client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

        result = connected_client.close_position(
            'position-uuid',
            Decimal('3300.00'),
            Decimal('5.00')
        )

        assert result['status'] == 'CLOSED'
        assert result['unrealized_pnl'] == 5.00


class TestTradeOperations:
    """Tests para operaciones de trades."""

    @pytest.fixture
    def connected_client(self):
        """Cliente conectado con mock."""
        with patch('src.database.supabase_client.create_client') as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client

            mock_table = Mock()
            mock_table.select.return_value.limit.return_value.execute.return_value = Mock(data=[])
            mock_client.table.return_value = mock_table

            client = SupabaseClient()
            client.connect()
            client._client = mock_client

            yield client

    def test_create_trade(self, connected_client):
        """Test crear trade."""
        trade_data = {
            'llm_id': 'LLM-A',
            'symbol': 'ETHUSDT',
            'side': 'BUY',
            'trade_type': 'OPEN',
            'price': 3250.00,
            'quantity': 0.01,
            'fees': 0.0163,
            'reasoning': 'Test trade',
            'status': 'EXECUTED'
        }

        mock_response = Mock()
        mock_response.data = [{**trade_data, 'id': 'trade-uuid'}]

        connected_client._client.table.return_value.insert.return_value.execute.return_value = mock_response

        result = connected_client.create_trade(trade_data)

        assert result['llm_id'] == 'LLM-A'
        assert result['symbol'] == 'ETHUSDT'
        assert 'id' in result

    def test_get_trades(self, connected_client):
        """Test obtener historial de trades."""
        mock_response = Mock()
        mock_response.data = [
            {'id': 'trade1', 'llm_id': 'LLM-A', 'symbol': 'ETHUSDT'},
            {'id': 'trade2', 'llm_id': 'LLM-A', 'symbol': 'BNBUSDT'}
        ]

        # Mock the full chain including .eq() which is called when llm_id is provided
        mock_query = Mock()
        mock_query.eq.return_value.execute.return_value = mock_response
        mock_query.execute.return_value = mock_response  # Also mock execute directly
        connected_client._client.table.return_value.select.return_value.order.return_value.limit.return_value = mock_query

        result = connected_client.get_trades(llm_id='LLM-A', limit=100)

        assert len(result) == 2


class TestMarketDataOperations:
    """Tests para operaciones de market data."""

    @pytest.fixture
    def connected_client(self):
        """Cliente conectado con mock."""
        with patch('src.database.supabase_client.create_client') as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client

            mock_table = Mock()
            mock_table.select.return_value.limit.return_value.execute.return_value = Mock(data=[])
            mock_client.table.return_value = mock_table

            client = SupabaseClient()
            client.connect()
            client._client = mock_client

            yield client

    def test_upsert_market_data(self, connected_client):
        """Test insertar/actualizar market data."""
        market_data = {
            'symbol': 'ETHUSDT',
            'price': 3250.00,
            'volume_24h': 1000000.00,
            'data_timestamp': datetime.utcnow().isoformat()
        }

        mock_response = Mock()
        mock_response.data = [market_data]

        connected_client._client.table.return_value.upsert.return_value.execute.return_value = mock_response

        result = connected_client.upsert_market_data(market_data)

        assert result['symbol'] == 'ETHUSDT'
        assert result['price'] == 3250.00

    def test_get_latest_market_data(self, connected_client):
        """Test obtener últimos datos de mercado."""
        mock_response = Mock()
        mock_response.data = [{
            'symbol': 'ETHUSDT',
            'price': 3250.00,
            'data_timestamp': datetime.utcnow().isoformat()
        }]

        # Mock the chain
        mock_query = Mock()
        mock_query.execute.return_value = mock_response
        connected_client._client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value = mock_query

        result = connected_client.get_latest_market_data('ETHUSDT')

        assert result is not None
        assert result['symbol'] == 'ETHUSDT'


class TestAnalyticsViews:
    """Tests para vistas de analytics."""

    @pytest.fixture
    def connected_client(self):
        """Cliente conectado con mock."""
        with patch('src.database.supabase_client.create_client') as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client

            mock_table = Mock()
            mock_table.select.return_value.limit.return_value.execute.return_value = Mock(data=[])
            mock_client.table.return_value = mock_table

            client = SupabaseClient()
            client.connect()
            client._client = mock_client

            yield client

    def test_get_llm_leaderboard(self, connected_client):
        """Test obtener leaderboard."""
        mock_response = Mock()
        mock_response.data = [
            {'llm_id': 'LLM-A', 'balance': 105.00, 'total_pnl': 5.00},
            {'llm_id': 'LLM-B', 'balance': 103.00, 'total_pnl': 3.00},
            {'llm_id': 'LLM-C', 'balance': 98.00, 'total_pnl': -2.00}
        ]

        connected_client._client.table.return_value.select.return_value.execute.return_value = mock_response

        result = connected_client.get_llm_leaderboard()

        assert len(result) == 3
        assert result[0]['llm_id'] == 'LLM-A'
