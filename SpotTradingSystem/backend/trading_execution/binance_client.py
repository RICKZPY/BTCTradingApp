"""
Binance API Client
Handles connection, authentication, and API calls to Binance exchange
"""
import logging
import hashlib
import hmac
import time
import requests
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_models import OrderResult, OrderStatus, ActionType, MarketData

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Binance order types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"


class OrderSide(Enum):
    """Binance order sides"""
    BUY = "BUY"
    SELL = "SELL"


class TimeInForce(Enum):
    """Binance time in force options"""
    GTC = "GTC"  # Good Till Canceled
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill


@dataclass
class BinanceOrderRequest:
    """Binance order request structure"""
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.GTC
    new_client_order_id: Optional[str] = None


@dataclass
class BinanceBalance:
    """Binance account balance"""
    asset: str
    free: float
    locked: float
    
    @property
    def total(self) -> float:
        return self.free + self.locked


@dataclass
class BinanceOrderInfo:
    """Binance order information"""
    order_id: int
    client_order_id: str
    symbol: str
    side: str
    type: str
    status: str
    quantity: float
    price: float
    executed_quantity: float
    executed_price: float
    time: datetime
    update_time: datetime


class BinanceAPIError(Exception):
    """Binance API specific error"""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Binance API Error {code}: {message}")


class BinanceClient:
    """
    Binance API client for trading operations
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """
        Initialize Binance client
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Use testnet (default True for safety)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # API endpoints
        if testnet:
            self.base_url = "https://testnet.binance.vision"
        else:
            self.base_url = "https://api.binance.com"
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        logger.info(f"Binance client initialized (testnet: {testnet})")
    
    def _generate_signature(self, query_string: str) -> str:
        """Generate HMAC SHA256 signature for authenticated requests"""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _get_timestamp(self) -> int:
        """Get current timestamp in milliseconds"""
        return int(time.time() * 1000)
    
    def _rate_limit(self):
        """Implement basic rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, 
                     signed: bool = False) -> Dict[str, Any]:
        """
        Make HTTP request to Binance API
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint
            params: Request parameters
            signed: Whether request needs signature
            
        Returns:
            API response as dictionary
        """
        self._rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        
        if signed:
            params['timestamp'] = self._get_timestamp()
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            params['signature'] = self._generate_signature(query_string)
        
        try:
            if method == 'GET':
                response = self.session.get(url, params=params)
            elif method == 'POST':
                response = self.session.post(url, params=params)
            elif method == 'DELETE':
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise
    
    def test_connectivity(self) -> bool:
        """
        Test API connectivity
        
        Returns:
            True if connection successful
        """
        try:
            response = self._make_request('GET', '/api/v3/ping')
            logger.info("Binance API connectivity test successful")
            return True
        except Exception as e:
            logger.error(f"Binance API connectivity test failed: {e}")
            return False
    
    def get_server_time(self) -> datetime:
        """
        Get Binance server time
        
        Returns:
            Server timestamp as datetime
        """
        try:
            response = self._make_request('GET', '/api/v3/time')
            timestamp = response['serverTime'] / 1000
            return datetime.fromtimestamp(timestamp)
        except Exception as e:
            logger.error(f"Failed to get server time: {e}")
            raise
    
    def get_exchange_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get exchange trading rules and symbol information
        
        Args:
            symbol: Specific symbol to get info for (optional)
            
        Returns:
            Exchange information
        """
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol
            
            response = self._make_request('GET', '/api/v3/exchangeInfo', params)
            return response
        except Exception as e:
            logger.error(f"Failed to get exchange info: {e}")
            raise
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information including balances
        
        Returns:
            Account information
        """
        try:
            response = self._make_request('GET', '/api/v3/account', signed=True)
            return response
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise
    
    def get_balances(self) -> List[BinanceBalance]:
        """
        Get account balances
        
        Returns:
            List of account balances
        """
        try:
            account_info = self.get_account_info()
            balances = []
            
            for balance_data in account_info['balances']:
                balance = BinanceBalance(
                    asset=balance_data['asset'],
                    free=float(balance_data['free']),
                    locked=float(balance_data['locked'])
                )
                # Only include balances with non-zero amounts
                if balance.total > 0:
                    balances.append(balance)
            
            return balances
        except Exception as e:
            logger.error(f"Failed to get balances: {e}")
            raise
    
    def get_balance(self, asset: str) -> Optional[BinanceBalance]:
        """
        Get balance for specific asset
        
        Args:
            asset: Asset symbol (e.g., 'BTC', 'USDT')
            
        Returns:
            Balance for the asset or None if not found
        """
        try:
            balances = self.get_balances()
            for balance in balances:
                if balance.asset == asset:
                    return balance
            return None
        except Exception as e:
            logger.error(f"Failed to get balance for {asset}: {e}")
            raise
    
    def get_ticker_price(self, symbol: str) -> float:
        """
        Get current price for a symbol
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            
        Returns:
            Current price
        """
        try:
            params = {'symbol': symbol}
            response = self._make_request('GET', '/api/v3/ticker/price', params)
            return float(response['price'])
        except Exception as e:
            logger.error(f"Failed to get ticker price for {symbol}: {e}")
            raise
    
    def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        Get order book for a symbol
        
        Args:
            symbol: Trading pair symbol
            limit: Number of entries to return (default 100)
            
        Returns:
            Order book data
        """
        try:
            params = {'symbol': symbol, 'limit': limit}
            response = self._make_request('GET', '/api/v3/depth', params)
            return response
        except Exception as e:
            logger.error(f"Failed to get order book for {symbol}: {e}")
            raise
    
    def place_order(self, order_request: BinanceOrderRequest) -> BinanceOrderInfo:
        """
        Place a new order
        
        Args:
            order_request: Order request details
            
        Returns:
            Order information
        """
        try:
            params = {
                'symbol': order_request.symbol,
                'side': order_request.side.value,
                'type': order_request.type.value,
                'quantity': order_request.quantity,
                'timeInForce': order_request.time_in_force.value
            }
            
            # Add price for limit orders
            if order_request.type in [OrderType.LIMIT, OrderType.STOP_LOSS_LIMIT, OrderType.TAKE_PROFIT_LIMIT]:
                if order_request.price is None:
                    raise ValueError(f"Price required for {order_request.type.value} orders")
                params['price'] = order_request.price
            
            # Add stop price for stop orders
            if order_request.type in [OrderType.STOP_LOSS, OrderType.STOP_LOSS_LIMIT, 
                                    OrderType.TAKE_PROFIT, OrderType.TAKE_PROFIT_LIMIT]:
                if order_request.stop_price is None:
                    raise ValueError(f"Stop price required for {order_request.type.value} orders")
                params['stopPrice'] = order_request.stop_price
            
            # Add client order ID if provided
            if order_request.new_client_order_id:
                params['newClientOrderId'] = order_request.new_client_order_id
            
            response = self._make_request('POST', '/api/v3/order', params, signed=True)
            
            # Convert response to BinanceOrderInfo
            order_info = BinanceOrderInfo(
                order_id=response['orderId'],
                client_order_id=response['clientOrderId'],
                symbol=response['symbol'],
                side=response['side'],
                type=response['type'],
                status=response['status'],
                quantity=float(response['origQty']),
                price=float(response['price']) if response['price'] != '0.00000000' else 0.0,
                executed_quantity=float(response['executedQty']),
                executed_price=float(response.get('fills', [{}])[0].get('price', 0)) if response.get('fills') else 0.0,
                time=datetime.fromtimestamp(response['transactTime'] / 1000),
                update_time=datetime.fromtimestamp(response['transactTime'] / 1000)
            )
            
            logger.info(f"Order placed successfully: {order_info.order_id}")
            return order_info
            
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise
    
    def place_market_order(self, symbol: str, side: OrderSide, quantity: float,
                          client_order_id: Optional[str] = None) -> BinanceOrderInfo:
        """
        Place a market order
        
        Args:
            symbol: Trading pair symbol
            side: Order side (BUY/SELL)
            quantity: Order quantity
            client_order_id: Custom client order ID
            
        Returns:
            Order information
        """
        order_request = BinanceOrderRequest(
            symbol=symbol,
            side=side,
            type=OrderType.MARKET,
            quantity=quantity,
            new_client_order_id=client_order_id
        )
        
        return self.place_order(order_request)
    
    def place_limit_order(self, symbol: str, side: OrderSide, quantity: float, price: float,
                         time_in_force: TimeInForce = TimeInForce.GTC,
                         client_order_id: Optional[str] = None) -> BinanceOrderInfo:
        """
        Place a limit order
        
        Args:
            symbol: Trading pair symbol
            side: Order side (BUY/SELL)
            quantity: Order quantity
            price: Order price
            time_in_force: Time in force option
            client_order_id: Custom client order ID
            
        Returns:
            Order information
        """
        order_request = BinanceOrderRequest(
            symbol=symbol,
            side=side,
            type=OrderType.LIMIT,
            quantity=quantity,
            price=price,
            time_in_force=time_in_force,
            new_client_order_id=client_order_id
        )
        
        return self.place_order(order_request)
    
    def get_order(self, symbol: str, order_id: Optional[int] = None,
                  client_order_id: Optional[str] = None) -> BinanceOrderInfo:
        """
        Get order information
        
        Args:
            symbol: Trading pair symbol
            order_id: Binance order ID
            client_order_id: Client order ID
            
        Returns:
            Order information
        """
        try:
            params = {'symbol': symbol}
            
            if order_id:
                params['orderId'] = order_id
            elif client_order_id:
                params['origClientOrderId'] = client_order_id
            else:
                raise ValueError("Either order_id or client_order_id must be provided")
            
            response = self._make_request('GET', '/api/v3/order', params, signed=True)
            
            order_info = BinanceOrderInfo(
                order_id=response['orderId'],
                client_order_id=response['clientOrderId'],
                symbol=response['symbol'],
                side=response['side'],
                type=response['type'],
                status=response['status'],
                quantity=float(response['origQty']),
                price=float(response['price']),
                executed_quantity=float(response['executedQty']),
                executed_price=float(response['price']) if float(response['executedQty']) > 0 else 0.0,
                time=datetime.fromtimestamp(response['time'] / 1000),
                update_time=datetime.fromtimestamp(response['updateTime'] / 1000)
            )
            
            return order_info
            
        except Exception as e:
            logger.error(f"Failed to get order: {e}")
            raise
    
    def cancel_order(self, symbol: str, order_id: Optional[int] = None,
                    client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel an order
        
        Args:
            symbol: Trading pair symbol
            order_id: Binance order ID
            client_order_id: Client order ID
            
        Returns:
            Cancellation result
        """
        try:
            params = {'symbol': symbol}
            
            if order_id:
                params['orderId'] = order_id
            elif client_order_id:
                params['origClientOrderId'] = client_order_id
            else:
                raise ValueError("Either order_id or client_order_id must be provided")
            
            response = self._make_request('DELETE', '/api/v3/order', params, signed=True)
            logger.info(f"Order cancelled successfully: {response.get('orderId', 'Unknown')}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            raise
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[BinanceOrderInfo]:
        """
        Get all open orders
        
        Args:
            symbol: Trading pair symbol (optional, gets all if not specified)
            
        Returns:
            List of open orders
        """
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol
            
            response = self._make_request('GET', '/api/v3/openOrders', params, signed=True)
            
            orders = []
            for order_data in response:
                order_info = BinanceOrderInfo(
                    order_id=order_data['orderId'],
                    client_order_id=order_data['clientOrderId'],
                    symbol=order_data['symbol'],
                    side=order_data['side'],
                    type=order_data['type'],
                    status=order_data['status'],
                    quantity=float(order_data['origQty']),
                    price=float(order_data['price']),
                    executed_quantity=float(order_data['executedQty']),
                    executed_price=0.0,  # Not provided in open orders
                    time=datetime.fromtimestamp(order_data['time'] / 1000),
                    update_time=datetime.fromtimestamp(order_data['updateTime'] / 1000)
                )
                orders.append(order_info)
            
            return orders
            
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            raise
    
    def get_order_history(self, symbol: str, limit: int = 500) -> List[BinanceOrderInfo]:
        """
        Get order history for a symbol
        
        Args:
            symbol: Trading pair symbol
            limit: Number of orders to return (max 1000)
            
        Returns:
            List of historical orders
        """
        try:
            params = {'symbol': symbol, 'limit': min(limit, 1000)}
            response = self._make_request('GET', '/api/v3/allOrders', params, signed=True)
            
            orders = []
            for order_data in response:
                order_info = BinanceOrderInfo(
                    order_id=order_data['orderId'],
                    client_order_id=order_data['clientOrderId'],
                    symbol=order_data['symbol'],
                    side=order_data['side'],
                    type=order_data['type'],
                    status=order_data['status'],
                    quantity=float(order_data['origQty']),
                    price=float(order_data['price']),
                    executed_quantity=float(order_data['executedQty']),
                    executed_price=float(order_data['price']) if float(order_data['executedQty']) > 0 else 0.0,
                    time=datetime.fromtimestamp(order_data['time'] / 1000),
                    update_time=datetime.fromtimestamp(order_data['updateTime'] / 1000)
                )
                orders.append(order_info)
            
            return orders
            
        except Exception as e:
            logger.error(f"Failed to get order history: {e}")
            raise
    
    def get_market_data(self, symbol: str) -> MarketData:
        """
        Get current market data for a symbol
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Market data
        """
        try:
            # Get 24hr ticker statistics
            params = {'symbol': symbol}
            ticker_response = self._make_request('GET', '/api/v3/ticker/24hr', params)
            
            market_data = MarketData(
                symbol=symbol,
                price=float(ticker_response['lastPrice']),
                volume=float(ticker_response['volume']),
                timestamp=datetime.utcnow(),
                source="binance"
            )
            
            return market_data
            
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            raise
    
    def convert_to_order_result(self, binance_order: BinanceOrderInfo) -> OrderResult:
        """
        Convert Binance order info to internal OrderResult format
        
        Args:
            binance_order: Binance order information
            
        Returns:
            OrderResult in internal format
        """
        # Map Binance status to internal status
        status_mapping = {
            'NEW': OrderStatus.PENDING,
            'PARTIALLY_FILLED': OrderStatus.PARTIALLY_FILLED,
            'FILLED': OrderStatus.FILLED,
            'CANCELED': OrderStatus.CANCELLED,
            'REJECTED': OrderStatus.REJECTED,
            'EXPIRED': OrderStatus.EXPIRED
        }
        
        return OrderResult(
            order_id=str(binance_order.order_id),
            status=status_mapping.get(binance_order.status, OrderStatus.UNKNOWN),
            executed_amount=binance_order.executed_quantity,
            executed_price=binance_order.executed_price,
            timestamp=binance_order.update_time
        )
    
    def close(self):
        """Close the HTTP session"""
        if self.session:
            self.session.close()
            logger.info("Binance client session closed")