"""
Binance Futures API Client.

Este cliente proporciona una interfaz simplificada para interactuar con
Binance Futures API (Testnet y Mainnet).

Features:
- Account information (balance, margin, positions)
- Market data (tickers, klines, orderbook)
- Order management (create, cancel, query)
- Position management (open, close, modify)
- Leverage configuration
- Automatic request signing
- Error handling with retry logic
- Rate limiting
"""

import time
import hmac
import hashlib
from typing import Dict, List, Optional, Any
from decimal import Decimal
from urllib.parse import urlencode

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import settings
from src.utils.logger import app_logger
from src.utils.exceptions import BinanceAPIError, BinanceConnectionError


class BinanceClient:
    """
    Cliente para Binance Futures API.

    Soporta tanto Testnet como Mainnet, con métodos para:
    - Account management
    - Market data
    - Order execution
    - Position management
    """

    # Endpoints
    TESTNET_BASE_URL = "https://testnet.binancefuture.com"
    MAINNET_BASE_URL = "https://fapi.binance.com"

    # API paths
    ACCOUNT_INFO = "/fapi/v2/account"
    TICKER_PRICE = "/fapi/v1/ticker/price"
    TICKER_24HR = "/fapi/v1/ticker/24hr"
    KLINES = "/fapi/v1/klines"
    ORDERBOOK = "/fapi/v1/depth"
    CREATE_ORDER = "/fapi/v1/order"
    CANCEL_ORDER = "/fapi/v1/order"
    QUERY_ORDER = "/fapi/v1/order"
    OPEN_ORDERS = "/fapi/v1/openOrders"
    ALL_ORDERS = "/fapi/v1/allOrders"
    POSITION_RISK = "/fapi/v2/positionRisk"
    LEVERAGE = "/fapi/v1/leverage"
    MARGIN_TYPE = "/fapi/v1/marginType"
    POSITION_MARGIN = "/fapi/v1/positionMargin"

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        testnet: bool = True
    ):
        """
        Inicializar cliente Binance.

        Args:
            api_key: Binance API key (si None, usa settings)
            api_secret: Binance API secret (si None, usa settings)
            testnet: Si True, usa Testnet; si False, usa Mainnet
        """
        self.api_key = api_key or settings.BINANCE_API_KEY
        self.api_secret = api_secret or settings.BINANCE_SECRET_KEY
        self.testnet = testnet
        self.base_url = self.TESTNET_BASE_URL if testnet else self.MAINNET_BASE_URL

        # Setup session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set headers
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/json"
        })

        app_logger.info(f"Initialized BinanceClient ({'Testnet' if testnet else 'Mainnet'})")

    def _get_timestamp(self) -> int:
        """
        Obtener timestamp actual en milisegundos.

        Returns:
            Timestamp en ms
        """
        return int(time.time() * 1000)

    def _sign_request(self, params: Dict[str, Any]) -> str:
        """
        Firmar request con HMAC SHA256.

        Args:
            params: Parámetros del request

        Returns:
            Signature hexadecimal
        """
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False
    ) -> Dict[str, Any]:
        """
        Hacer request a Binance API.

        Args:
            method: HTTP method (GET, POST, DELETE)
            path: API path
            params: Request parameters
            signed: Si True, firma el request

        Returns:
            Response JSON

        Raises:
            BinanceAPIError: Si hay error en la API
            BinanceConnectionError: Si hay error de conexión
        """
        if params is None:
            params = {}

        # Add timestamp and signature for signed requests
        if signed:
            params['timestamp'] = self._get_timestamp()
            params['signature'] = self._sign_request(params)

        url = self.base_url + path

        try:
            if method == "GET":
                response = self.session.get(url, params=params, timeout=10)
            elif method == "POST":
                response = self.session.post(url, params=params, timeout=10)
            elif method == "DELETE":
                response = self.session.delete(url, params=params, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Check for errors
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('msg', response.text)
                error_code = error_data.get('code', response.status_code)

                app_logger.error(f"Binance API error: {error_code} - {error_msg}")
                raise BinanceAPIError(
                    message=error_msg,
                    code=error_code,
                    response=error_data
                )

            return response.json()

        except requests.exceptions.ConnectionError as e:
            app_logger.error(f"Connection error to Binance: {e}")
            raise BinanceConnectionError(f"Could not connect to Binance API: {str(e)}")

        except requests.exceptions.Timeout as e:
            app_logger.error(f"Timeout error: {e}")
            raise BinanceConnectionError(f"Request timeout: {str(e)}")

        except requests.exceptions.RequestException as e:
            app_logger.error(f"Request error: {e}")
            raise BinanceConnectionError(f"Request failed: {str(e)}")

    # ============================================
    # ACCOUNT INFORMATION
    # ============================================

    def get_account_info(self) -> Dict[str, Any]:
        """
        Obtener información de la cuenta.

        Returns:
            Dict con balance, margin, positions, etc.

        Example response:
            {
                "totalWalletBalance": "100.00000000",
                "totalUnrealizedProfit": "0.00000000",
                "totalMarginBalance": "100.00000000",
                "availableBalance": "100.00000000",
                "assets": [...],
                "positions": [...]
            }
        """
        return self._request("GET", self.ACCOUNT_INFO, signed=True)

    def get_balance(self) -> Decimal:
        """
        Obtener balance total de la cuenta.

        Returns:
            Balance en USDT
        """
        account_info = self.get_account_info()
        balance_str = account_info.get("totalWalletBalance", "0")
        return Decimal(balance_str)

    def get_available_balance(self) -> Decimal:
        """
        Obtener balance disponible (no usado en margin).

        Returns:
            Balance disponible en USDT
        """
        account_info = self.get_account_info()
        balance_str = account_info.get("availableBalance", "0")
        return Decimal(balance_str)

    # ============================================
    # MARKET DATA
    # ============================================

    def get_ticker_price(self, symbol: str) -> Decimal:
        """
        Obtener precio actual de un símbolo.

        Args:
            symbol: Par de trading (ej: 'ETHUSDT')

        Returns:
            Precio actual
        """
        response = self._request("GET", self.TICKER_PRICE, params={"symbol": symbol})
        return Decimal(response["price"])

    def get_ticker_24hr(self, symbol: str) -> Dict[str, Any]:
        """
        Obtener estadísticas de 24h de un símbolo.

        Args:
            symbol: Par de trading

        Returns:
            Dict con price, volume, priceChange, etc.
        """
        return self._request("GET", self.TICKER_24HR, params={"symbol": symbol})

    def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[List]:
        """
        Obtener datos históricos de klines/candlesticks.

        Args:
            symbol: Par de trading
            interval: Intervalo (1m, 5m, 15m, 1h, 4h, 1d, etc.)
            limit: Número de klines (max 1500)
            start_time: Timestamp de inicio en ms
            end_time: Timestamp de fin en ms

        Returns:
            Lista de klines [
                [openTime, open, high, low, close, volume, closeTime, ...]
            ]
        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }

        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        return self._request("GET", self.KLINES, params=params)

    def get_orderbook(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        Obtener orderbook (depth).

        Args:
            symbol: Par de trading
            limit: Número de niveles (5, 10, 20, 50, 100, 500, 1000)

        Returns:
            Dict con bids y asks
        """
        params = {"symbol": symbol, "limit": limit}
        return self._request("GET", self.ORDERBOOK, params=params)

    # ============================================
    # ORDER MANAGEMENT
    # ============================================

    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        time_in_force: str = "GTC",
        reduce_only: bool = False,
        close_position: bool = False,
        stop_price: Optional[Decimal] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Crear una orden.

        Args:
            symbol: Par de trading
            side: 'BUY' o 'SELL'
            order_type: 'LIMIT', 'MARKET', 'STOP', 'STOP_MARKET', etc.
            quantity: Cantidad a tradear
            price: Precio (requerido para LIMIT)
            time_in_force: 'GTC', 'IOC', 'FOK'
            reduce_only: Si True, solo reduce posición existente
            close_position: Si True, cierra toda la posición
            stop_price: Precio de activación para STOP orders
            **kwargs: Parámetros adicionales

        Returns:
            Dict con información de la orden

        Example:
            >>> client.create_order(
            ...     symbol="ETHUSDT",
            ...     side="BUY",
            ...     order_type="LIMIT",
            ...     quantity=Decimal("0.1"),
            ...     price=Decimal("3000"),
            ...     time_in_force="GTC"
            ... )
        """
        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": order_type.upper(),
            "quantity": str(quantity)
        }

        if price:
            params["price"] = str(price)

        if order_type.upper() == "LIMIT":
            params["timeInForce"] = time_in_force

        if reduce_only:
            params["reduceOnly"] = "true"

        if close_position:
            params["closePosition"] = "true"

        if stop_price:
            params["stopPrice"] = str(stop_price)

        # Add any additional parameters
        params.update(kwargs)

        return self._request("POST", self.CREATE_ORDER, params=params, signed=True)

    def create_market_order(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        reduce_only: bool = False
    ) -> Dict[str, Any]:
        """
        Crear orden MARKET (ejecución inmediata).

        Args:
            symbol: Par de trading
            side: 'BUY' o 'SELL'
            quantity: Cantidad
            reduce_only: Si True, solo reduce posición

        Returns:
            Dict con información de la orden
        """
        return self.create_order(
            symbol=symbol,
            side=side,
            order_type="MARKET",
            quantity=quantity,
            reduce_only=reduce_only
        )

    def create_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        time_in_force: str = "GTC"
    ) -> Dict[str, Any]:
        """
        Crear orden LIMIT.

        Args:
            symbol: Par de trading
            side: 'BUY' o 'SELL'
            quantity: Cantidad
            price: Precio límite
            time_in_force: 'GTC', 'IOC', 'FOK'

        Returns:
            Dict con información de la orden
        """
        return self.create_order(
            symbol=symbol,
            side=side,
            order_type="LIMIT",
            quantity=quantity,
            price=price,
            time_in_force=time_in_force
        )

    def cancel_order(self, symbol: str, order_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Cancelar una orden.

        Args:
            symbol: Par de trading
            order_id: ID de la orden a cancelar

        Returns:
            Dict con información de la cancelación
        """
        params = {"symbol": symbol}
        if order_id:
            params["orderId"] = order_id

        return self._request("DELETE", self.CANCEL_ORDER, params=params, signed=True)

    def cancel_all_orders(self, symbol: str) -> Dict[str, Any]:
        """
        Cancelar todas las órdenes abiertas de un símbolo.

        Args:
            symbol: Par de trading

        Returns:
            Dict con confirmación
        """
        return self._request(
            "DELETE",
            self.OPEN_ORDERS,
            params={"symbol": symbol},
            signed=True
        )

    def get_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Consultar información de una orden.

        Args:
            symbol: Par de trading
            order_id: ID de la orden

        Returns:
            Dict con información de la orden
        """
        params = {"symbol": symbol, "orderId": order_id}
        return self._request("GET", self.QUERY_ORDER, params=params, signed=True)

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtener todas las órdenes abiertas.

        Args:
            symbol: Par de trading (si None, retorna todas)

        Returns:
            Lista de órdenes abiertas
        """
        params = {}
        if symbol:
            params["symbol"] = symbol

        return self._request("GET", self.OPEN_ORDERS, params=params, signed=True)

    def get_all_orders(
        self,
        symbol: str,
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtener historial de órdenes.

        Args:
            symbol: Par de trading
            limit: Número de órdenes (max 1000)
            start_time: Timestamp de inicio
            end_time: Timestamp de fin

        Returns:
            Lista de órdenes
        """
        params = {"symbol": symbol, "limit": limit}

        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        return self._request("GET", self.ALL_ORDERS, params=params, signed=True)

    # ============================================
    # POSITION MANAGEMENT
    # ============================================

    def get_position_risk(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtener información de posiciones.

        Args:
            symbol: Par de trading (si None, retorna todas)

        Returns:
            Lista de posiciones con información de riesgo
        """
        params = {}
        if symbol:
            params["symbol"] = symbol

        return self._request("GET", self.POSITION_RISK, params=params, signed=True)

    def get_open_positions(self) -> List[Dict[str, Any]]:
        """
        Obtener solo posiciones abiertas (con cantidad > 0).

        Returns:
            Lista de posiciones abiertas
        """
        all_positions = self.get_position_risk()
        return [
            pos for pos in all_positions
            if Decimal(pos.get("positionAmt", "0")) != 0
        ]

    def close_position(
        self,
        symbol: str,
        position_side: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cerrar una posición usando closePosition.

        Args:
            symbol: Par de trading
            position_side: 'LONG' o 'SHORT' (para hedge mode)

        Returns:
            Dict con información de la orden de cierre
        """
        # Get current position to determine side
        positions = self.get_position_risk(symbol=symbol)

        if not positions:
            raise BinanceAPIError("No position found", code=0, response={})

        position = positions[0]
        position_amt = Decimal(position.get("positionAmt", "0"))

        if position_amt == 0:
            raise BinanceAPIError("Position already closed", code=0, response={})

        # Determine side for closing
        side = "SELL" if position_amt > 0 else "BUY"

        # Create market order to close
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "closePosition": "true"
        }

        if position_side:
            params["positionSide"] = position_side

        return self._request("POST", self.CREATE_ORDER, params=params, signed=True)

    def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """
        Configurar leverage para un símbolo.

        Args:
            symbol: Par de trading
            leverage: Leverage (1-125)

        Returns:
            Dict con confirmación
        """
        params = {"symbol": symbol, "leverage": leverage}
        return self._request("POST", self.LEVERAGE, params=params, signed=True)

    def set_margin_type(self, symbol: str, margin_type: str) -> Dict[str, Any]:
        """
        Configurar tipo de margin (ISOLATED o CROSSED).

        Args:
            symbol: Par de trading
            margin_type: 'ISOLATED' o 'CROSSED'

        Returns:
            Dict con confirmación
        """
        params = {"symbol": symbol, "marginType": margin_type.upper()}
        return self._request("POST", self.MARGIN_TYPE, params=params, signed=True)

    def modify_position_margin(
        self,
        symbol: str,
        amount: Decimal,
        position_side: str = "BOTH",
        action_type: int = 1
    ) -> Dict[str, Any]:
        """
        Modificar margin de una posición.

        Args:
            symbol: Par de trading
            amount: Cantidad de margin a añadir/remover
            position_side: 'BOTH', 'LONG', 'SHORT'
            action_type: 1 = añadir, 2 = remover

        Returns:
            Dict con confirmación
        """
        params = {
            "symbol": symbol,
            "amount": str(amount),
            "type": action_type,
            "positionSide": position_side
        }
        return self._request("POST", self.POSITION_MARGIN, params=params, signed=True)

    # ============================================
    # UTILITY METHODS
    # ============================================

    def ping(self) -> bool:
        """
        Verificar conectividad con Binance.

        Returns:
            True si la conexión es exitosa
        """
        try:
            self._request("GET", "/fapi/v1/ping")
            return True
        except Exception as e:
            app_logger.error(f"Ping failed: {e}")
            return False

    def get_server_time(self) -> int:
        """
        Obtener tiempo del servidor Binance.

        Returns:
            Timestamp del servidor en ms
        """
        response = self._request("GET", "/fapi/v1/time")
        return response["serverTime"]

    def get_exchange_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtener información del exchange (símbolos, limits, filters).

        Args:
            symbol: Par específico (si None, retorna todos)

        Returns:
            Dict con información del exchange
        """
        params = {}
        if symbol:
            params["symbol"] = symbol

        return self._request("GET", "/fapi/v1/exchangeInfo", params=params)
