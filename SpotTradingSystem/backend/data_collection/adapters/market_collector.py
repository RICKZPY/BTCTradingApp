"""
Market Data Collector

Implements real-time market data collection from Binance and other exchanges.
Fulfills requirements 1.4 for market data collection.
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import ccxt.async_support as ccxt
import structlog

from data_collection.base import DataCollector
from core.data_models import MarketData, generate_id
from config import settings


logger = structlog.get_logger(__name__)


class MarketDataCollector(DataCollector):
    """
    Collects real-time market data from cryptocurrency exchanges
    
    Primary focus on Bitcoin price and volume data from Binance
    """
    
    # Trading pairs to monitor
    TRADING_PAIRS = [
        'BTC/USDT',
        'BTC/BUSD', 
        'BTC/USD',
        'ETH/USDT',  # For market correlation analysis
        'BNB/USDT'   # For exchange health monitoring
    ]
    
    def __init__(self, pairs: Optional[List[str]] = None, exchanges: Optional[List[str]] = None):
        super().__init__("market_collector")
        self.pairs = pairs or self.TRADING_PAIRS
        self.exchange_names = exchanges or ['binance']
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def validate_connection(self) -> bool:
        """Validate connection to exchanges"""
        try:
            # Initialize exchanges
            await self._initialize_exchanges()
            
            # Test connection to primary exchange (Binance)
            if 'binance' in self.exchanges:
                exchange = self.exchanges['binance']
                
                # Test by fetching ticker for BTC/USDT
                ticker = await exchange.fetch_ticker('BTC/USDT')
                
                if ticker and 'last' in ticker:
                    self.logger.info("Market data connection validated", price=ticker['last'])
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error("Market data connection validation failed", error=str(e))
            return False
    
    async def collect_data(self) -> List[MarketData]:
        """
        Collect market data from configured exchanges
        
        Returns:
            List of MarketData objects
        """
        all_market_data = []
        
        try:
            # Initialize exchanges if not already done
            if not self.exchanges:
                await self._initialize_exchanges()
            
            # Collect from each exchange
            for exchange_name, exchange in self.exchanges.items():
                try:
                    self.logger.info("Collecting market data", exchange=exchange_name)
                    
                    # Collect ticker data for all pairs
                    market_data = await self._collect_from_exchange(exchange, exchange_name)
                    all_market_data.extend(market_data)
                    
                    self.logger.info(
                        "Market data collected",
                        exchange=exchange_name,
                        pairs=len(market_data)
                    )
                    
                except Exception as e:
                    self.logger.error(
                        "Error collecting from exchange",
                        exchange=exchange_name,
                        error=str(e)
                    )
                    continue
            
            self.logger.info(
                "Market data collection completed",
                total_exchanges=len(self.exchanges),
                total_data_points=len(all_market_data)
            )
            
        except Exception as e:
            self.logger.error("Error in market data collection", error=str(e))
        
        return all_market_data
    
    async def _initialize_exchanges(self):
        """Initialize exchange connections"""
        for exchange_name in self.exchange_names:
            try:
                if exchange_name == 'binance':
                    exchange = ccxt.binance({
                        'apiKey': settings.api.binance_api_key,
                        'secret': settings.api.binance_secret_key,
                        'sandbox': settings.api.binance_testnet,
                        'enableRateLimit': True,
                        'options': {
                            'defaultType': 'spot'  # Use spot trading
                        }
                    })
                else:
                    # Add other exchanges as needed
                    exchange_class = getattr(ccxt, exchange_name, None)
                    if exchange_class:
                        exchange = exchange_class({
                            'enableRateLimit': True
                        })
                    else:
                        self.logger.warning("Unknown exchange", exchange=exchange_name)
                        continue
                
                self.exchanges[exchange_name] = exchange
                
                self.logger.info("Exchange initialized", exchange=exchange_name)
                
            except Exception as e:
                self.logger.error(
                    "Error initializing exchange",
                    exchange=exchange_name,
                    error=str(e)
                )
    
    async def _collect_from_exchange(self, exchange: ccxt.Exchange, exchange_name: str) -> List[MarketData]:
        """Collect market data from a specific exchange"""
        market_data = []
        current_time = datetime.now()
        
        for pair in self.pairs:
            try:
                # Fetch ticker data
                ticker = await exchange.fetch_ticker(pair)
                
                if not ticker:
                    continue
                
                # Extract relevant data
                price = ticker.get('last') or ticker.get('close')
                volume = ticker.get('baseVolume') or ticker.get('volume')
                
                if price is None or volume is None:
                    self.logger.warning(
                        "Incomplete ticker data",
                        exchange=exchange_name,
                        pair=pair,
                        ticker=ticker
                    )
                    continue
                
                # Create MarketData object
                market_item = MarketData(
                    symbol=pair,
                    price=float(price),
                    volume=float(volume),
                    timestamp=current_time,
                    source=exchange_name
                )
                
                market_data.append(market_item)
                
                # Add additional metrics if available
                if ticker.get('high') and ticker.get('low'):
                    # Create additional data points for high/low
                    high_item = MarketData(
                        symbol=f"{pair}_HIGH_24H",
                        price=float(ticker['high']),
                        volume=float(volume),
                        timestamp=current_time,
                        source=exchange_name
                    )
                    
                    low_item = MarketData(
                        symbol=f"{pair}_LOW_24H",
                        price=float(ticker['low']),
                        volume=float(volume),
                        timestamp=current_time,
                        source=exchange_name
                    )
                    
                    market_data.extend([high_item, low_item])
                
                # Small delay between requests to respect rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(
                    "Error fetching ticker",
                    exchange=exchange_name,
                    pair=pair,
                    error=str(e)
                )
                continue
        
        return market_data
    
    async def collect_orderbook_data(self, pair: str = 'BTC/USDT', limit: int = 10) -> Optional[Dict[str, Any]]:
        """
        Collect order book data for deeper market analysis
        
        Args:
            pair: Trading pair to collect orderbook for
            limit: Number of orders to collect from each side
            
        Returns:
            Order book data or None if failed
        """
        try:
            if 'binance' not in self.exchanges:
                await self._initialize_exchanges()
            
            exchange = self.exchanges.get('binance')
            if not exchange:
                return None
            
            orderbook = await exchange.fetch_order_book(pair, limit)
            
            if orderbook:
                # Add timestamp
                orderbook['timestamp'] = datetime.now().isoformat()
                orderbook['symbol'] = pair
                
                self.logger.debug(
                    "Order book collected",
                    pair=pair,
                    bids=len(orderbook.get('bids', [])),
                    asks=len(orderbook.get('asks', []))
                )
            
            return orderbook
            
        except Exception as e:
            self.logger.error(
                "Error collecting order book",
                pair=pair,
                error=str(e)
            )
            return None
    
    async def collect_kline_data(
        self, 
        pair: str = 'BTC/USDT', 
        timeframe: str = '1m', 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Collect candlestick/kline data for technical analysis
        
        Args:
            pair: Trading pair
            timeframe: Timeframe (1m, 5m, 1h, etc.)
            limit: Number of candles to collect
            
        Returns:
            List of OHLCV data
        """
        try:
            if 'binance' not in self.exchanges:
                await self._initialize_exchanges()
            
            exchange = self.exchanges.get('binance')
            if not exchange:
                return []
            
            ohlcv = await exchange.fetch_ohlcv(pair, timeframe, limit=limit)
            
            # Convert to more readable format
            klines = []
            for candle in ohlcv:
                kline = {
                    'timestamp': datetime.fromtimestamp(candle[0] / 1000),
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5],
                    'symbol': pair,
                    'timeframe': timeframe
                }
                klines.append(kline)
            
            self.logger.debug(
                "Kline data collected",
                pair=pair,
                timeframe=timeframe,
                candles=len(klines)
            )
            
            return klines
            
        except Exception as e:
            self.logger.error(
                "Error collecting kline data",
                pair=pair,
                timeframe=timeframe,
                error=str(e)
            )
            return []
    
    async def close(self):
        """Close exchange connections"""
        for exchange_name, exchange in self.exchanges.items():
            try:
                await exchange.close()
                self.logger.info("Exchange connection closed", exchange=exchange_name)
            except Exception as e:
                self.logger.error(
                    "Error closing exchange connection",
                    exchange=exchange_name,
                    error=str(e)
                )
        
        self.exchanges.clear()
        
        if self.session:
            await self.session.close()
            self.session = None
    
    def __del__(self):
        """Cleanup on deletion"""
        if self.exchanges:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.close())
            except:
                pass