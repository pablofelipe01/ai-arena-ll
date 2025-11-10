"""
Tests críticos para Binance Futures API Client.

Estos tests validan las operaciones esenciales del cliente de Binance
para prevenir errores que podrían causar pérdidas reales.

IMPORTANTE: Todos los tests usan mocks - NO se conectan a Binance real.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
import requests

from src.clients.binance_client import BinanceClient
from src.utils.exceptions import BinanceAPIError, BinanceConnectionError


class TestBinanceClientInitialization:
    """Tests para inicialización del cliente."""

    def test_init_with_testnet(self):
        """Test inicialización con Testnet."""
        client = BinanceClient(
            api_key="test_key",
            api_secret="test_secret",
            testnet=True
        )

        assert client.testnet is True
        assert client.base_url == BinanceClient.TESTNET_BASE_URL
        assert client.api_key == "test_key"

    def test_init_with_mainnet(self):
        """Test inicialización con Mainnet."""
        client = BinanceClient(
            api_key="test_key",
            api_secret="test_secret",
            testnet=False
        )

        assert client.testnet is False
        assert client.base_url == BinanceClient.MAINNET_BASE_URL

    def test_init_from_settings(self):
        """Test inicialización usando settings."""
        client = BinanceClient(testnet=True)

        # Should use settings
        assert client.api_key is not None
        assert client.api_secret is not None


class TestRequestSigning:
    """Tests para firma de requests."""

    def test_get_timestamp(self):
        """Test generación de timestamp."""
        client = BinanceClient(api_key="test", api_secret="test", testnet=True)
        timestamp = client._get_timestamp()

        assert isinstance(timestamp, int)
        assert timestamp > 0

    def test_sign_request(self):
        """Test firma de request."""
        client = BinanceClient(api_key="test", api_secret="test_secret", testnet=True)

        params = {"symbol": "ETHUSDT", "side": "BUY", "timestamp": 1234567890}
        signature = client._sign_request(params)

        assert isinstance(signature, str)
        assert len(signature) == 64  # HMAC SHA256 produces 64 hex chars


class TestMarketData:
    """Tests para obtención de datos de mercado."""

    @pytest.fixture
    def client(self):
        """Cliente con mock."""
        return BinanceClient(api_key="test", api_secret="test", testnet=True)

    def test_get_ticker_price(self, client):
        """Test obtener precio de ticker."""
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {"symbol": "ETHUSDT", "price": "3250.50"}

            price = client.get_ticker_price("ETHUSDT")

            assert price == Decimal("3250.50")
            mock_request.assert_called_once()

    def test_get_ticker_24hr(self, client):
        """Test obtener estadísticas 24h."""
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {
                "symbol": "ETHUSDT",
                "priceChange": "50.00",
                "priceChangePercent": "1.56",
                "lastPrice": "3250.50",
                "volume": "1000000.00"
            }

            ticker = client.get_ticker_24hr("ETHUSDT")

            assert ticker["symbol"] == "ETHUSDT"
            assert ticker["priceChange"] == "50.00"

    def test_get_klines(self, client):
        """Test obtener klines históricos."""
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = [
                [1640000000000, "3200", "3250", "3190", "3240", "1000", 1640003600000],
                [1640003600000, "3240", "3260", "3230", "3250", "1100", 1640007200000]
            ]

            klines = client.get_klines("ETHUSDT", interval="1h", limit=2)

            assert len(klines) == 2
            assert klines[0][1] == "3200"  # Open price

    def test_get_orderbook(self, client):
        """Test obtener orderbook."""
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {
                "lastUpdateId": 123456,
                "bids": [["3250.00", "10.5"], ["3249.00", "5.2"]],
                "asks": [["3251.00", "8.3"], ["3252.00", "12.1"]]
            }

            orderbook = client.get_orderbook("ETHUSDT", limit=10)

            assert len(orderbook["bids"]) == 2
            assert len(orderbook["asks"]) == 2


class TestAccountInformation:
    """Tests para información de cuenta."""

    @pytest.fixture
    def client(self):
        """Cliente con mock."""
        return BinanceClient(api_key="test", api_secret="test", testnet=True)

    def test_get_account_info(self, client):
        """Test obtener información de cuenta."""
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {
                "totalWalletBalance": "100.50000000",
                "totalUnrealizedProfit": "5.00000000",
                "totalMarginBalance": "105.50000000",
                "availableBalance": "90.00000000",
                "assets": [],
                "positions": []
            }

            account = client.get_account_info()

            assert account["totalWalletBalance"] == "100.50000000"
            assert account["availableBalance"] == "90.00000000"

    def test_get_balance(self, client):
        """Test obtener balance total."""
        with patch.object(client, 'get_account_info') as mock_get_account:
            mock_get_account.return_value = {"totalWalletBalance": "100.50000000"}

            balance = client.get_balance()

            assert balance == Decimal("100.50000000")

    def test_get_available_balance(self, client):
        """Test obtener balance disponible."""
        with patch.object(client, 'get_account_info') as mock_get_account:
            mock_get_account.return_value = {"availableBalance": "90.00000000"}

            available = client.get_available_balance()

            assert available == Decimal("90.00000000")


class TestOrderManagement:
    """Tests para gestión de órdenes."""

    @pytest.fixture
    def client(self):
        """Cliente con mock."""
        return BinanceClient(api_key="test", api_secret="test", testnet=True)

    def test_create_market_order(self, client):
        """Test crear orden MARKET."""
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {
                "orderId": 123456,
                "symbol": "ETHUSDT",
                "status": "FILLED",
                "type": "MARKET",
                "side": "BUY",
                "executedQty": "0.1",
                "avgPrice": "3250.00"
            }

            order = client.create_market_order(
                symbol="ETHUSDT",
                side="BUY",
                quantity=Decimal("0.1")
            )

            assert order["orderId"] == 123456
            assert order["status"] == "FILLED"
            assert order["type"] == "MARKET"

    def test_create_limit_order(self, client):
        """Test crear orden LIMIT."""
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {
                "orderId": 123457,
                "symbol": "ETHUSDT",
                "status": "NEW",
                "type": "LIMIT",
                "side": "BUY",
                "price": "3200.00",
                "origQty": "0.1"
            }

            order = client.create_limit_order(
                symbol="ETHUSDT",
                side="BUY",
                quantity=Decimal("0.1"),
                price=Decimal("3200.00")
            )

            assert order["orderId"] == 123457
            assert order["type"] == "LIMIT"
            assert order["price"] == "3200.00"

    def test_cancel_order(self, client):
        """Test cancelar orden."""
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {
                "orderId": 123456,
                "symbol": "ETHUSDT",
                "status": "CANCELED"
            }

            result = client.cancel_order(symbol="ETHUSDT", order_id=123456)

            assert result["status"] == "CANCELED"

    def test_get_open_orders(self, client):
        """Test obtener órdenes abiertas."""
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = [
                {"orderId": 123, "symbol": "ETHUSDT", "status": "NEW"},
                {"orderId": 124, "symbol": "ETHUSDT", "status": "PARTIALLY_FILLED"}
            ]

            orders = client.get_open_orders(symbol="ETHUSDT")

            assert len(orders) == 2
            assert orders[0]["orderId"] == 123


class TestPositionManagement:
    """Tests para gestión de posiciones."""

    @pytest.fixture
    def client(self):
        """Cliente con mock."""
        return BinanceClient(api_key="test", api_secret="test", testnet=True)

    def test_get_position_risk(self, client):
        """Test obtener información de posiciones."""
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = [
                {
                    "symbol": "ETHUSDT",
                    "positionAmt": "0.1",
                    "entryPrice": "3200.00",
                    "markPrice": "3250.00",
                    "unRealizedProfit": "5.00",
                    "liquidationPrice": "2800.00",
                    "leverage": "3"
                }
            ]

            positions = client.get_position_risk(symbol="ETHUSDT")

            assert len(positions) == 1
            assert positions[0]["symbol"] == "ETHUSDT"
            assert positions[0]["positionAmt"] == "0.1"

    def test_get_open_positions(self, client):
        """Test obtener solo posiciones abiertas."""
        with patch.object(client, 'get_position_risk') as mock_get_risk:
            mock_get_risk.return_value = [
                {"symbol": "ETHUSDT", "positionAmt": "0.1"},
                {"symbol": "BNBUSDT", "positionAmt": "0"},  # Closed
                {"symbol": "XRPUSDT", "positionAmt": "-0.5"}
            ]

            open_positions = client.get_open_positions()

            # Should only return positions with amt != 0
            assert len(open_positions) == 2
            assert open_positions[0]["symbol"] == "ETHUSDT"
            assert open_positions[1]["symbol"] == "XRPUSDT"

    def test_close_position_long(self, client):
        """Test cerrar posición LONG."""
        with patch.object(client, 'get_position_risk') as mock_get_risk:
            mock_get_risk.return_value = [
                {"symbol": "ETHUSDT", "positionAmt": "0.1"}  # LONG position
            ]

            with patch.object(client, '_request') as mock_request:
                mock_request.return_value = {
                    "orderId": 123,
                    "symbol": "ETHUSDT",
                    "side": "SELL",
                    "type": "MARKET",
                    "status": "FILLED"
                }

                result = client.close_position("ETHUSDT")

                assert result["side"] == "SELL"
                assert result["status"] == "FILLED"

    def test_close_position_short(self, client):
        """Test cerrar posición SHORT."""
        with patch.object(client, 'get_position_risk') as mock_get_risk:
            mock_get_risk.return_value = [
                {"symbol": "ETHUSDT", "positionAmt": "-0.1"}  # SHORT position
            ]

            with patch.object(client, '_request') as mock_request:
                mock_request.return_value = {
                    "orderId": 124,
                    "symbol": "ETHUSDT",
                    "side": "BUY",
                    "type": "MARKET",
                    "status": "FILLED"
                }

                result = client.close_position("ETHUSDT")

                assert result["side"] == "BUY"

    def test_set_leverage(self, client):
        """Test configurar leverage."""
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {
                "leverage": 10,
                "symbol": "ETHUSDT"
            }

            result = client.set_leverage("ETHUSDT", 10)

            assert result["leverage"] == 10
            assert result["symbol"] == "ETHUSDT"


class TestErrorHandling:
    """Tests para manejo de errores."""

    @pytest.fixture
    def client(self):
        """Cliente con mock."""
        return BinanceClient(api_key="test", api_secret="test", testnet=True)

    def test_api_error_handling(self, client):
        """Test manejo de errores de API."""
        with patch.object(client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "code": -1102,
                "msg": "Mandatory parameter 'symbol' was not sent"
            }
            mock_get.return_value = mock_response

            with pytest.raises(BinanceAPIError) as exc_info:
                client._request("GET", "/test", params={})

            assert exc_info.value.code == -1102

    def test_connection_error_handling(self, client):
        """Test manejo de errores de conexión."""
        with patch.object(client.session, 'get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

            with pytest.raises(BinanceConnectionError):
                client._request("GET", "/test", params={})

    def test_timeout_error_handling(self, client):
        """Test manejo de timeout."""
        with patch.object(client.session, 'get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Request timeout")

            with pytest.raises(BinanceConnectionError):
                client._request("GET", "/test", params={})


class TestUtilityMethods:
    """Tests para métodos de utilidad."""

    @pytest.fixture
    def client(self):
        """Cliente con mock."""
        return BinanceClient(api_key="test", api_secret="test", testnet=True)

    def test_ping_success(self, client):
        """Test ping exitoso."""
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {}

            result = client.ping()

            assert result is True

    def test_ping_failure(self, client):
        """Test ping fallido."""
        with patch.object(client, '_request') as mock_request:
            mock_request.side_effect = BinanceConnectionError("Connection failed")

            result = client.ping()

            assert result is False

    def test_get_server_time(self, client):
        """Test obtener tiempo del servidor."""
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {"serverTime": 1640000000000}

            server_time = client.get_server_time()

            assert server_time == 1640000000000

    def test_get_exchange_info(self, client):
        """Test obtener información del exchange."""
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {
                "timezone": "UTC",
                "serverTime": 1640000000000,
                "symbols": [
                    {"symbol": "ETHUSDT", "status": "TRADING"}
                ]
            }

            exchange_info = client.get_exchange_info(symbol="ETHUSDT")

            assert exchange_info["timezone"] == "UTC"
            assert len(exchange_info["symbols"]) == 1
