"""
InfluxDB connection and time series data management
"""
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
from typing import List, Dict, Any, Optional
import structlog

from config import settings

logger = structlog.get_logger(__name__)


class InfluxDBManager:
    """
    InfluxDB connection and data management
    """
    
    def __init__(self):
        self.client: Optional[InfluxDBClient] = None
        self.write_api = None
        self.query_api = None
        self._connect()
    
    def _connect(self):
        """
        Initialize InfluxDB connection
        """
        try:
            self.client = InfluxDBClient(
                url=settings.database.influxdb_url,
                token=settings.database.influxdb_token,
                org=settings.database.influxdb_org
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            logger.info("InfluxDB connection established")
        except Exception as e:
            logger.error("Failed to connect to InfluxDB", error=str(e))
            raise
    
    def test_connection(self) -> bool:
        """
        Test InfluxDB connection
        """
        try:
            if self.client:
                # Try to ping the database
                health = self.client.health()
                if health.status == "pass":
                    logger.info("InfluxDB connection successful")
                    return True
            return False
        except Exception as e:
            logger.error("InfluxDB connection test failed", error=str(e))
            return False
    
    def write_market_data(self, symbol: str, price: float, volume: float, 
                         timestamp: datetime, source: str):
        """
        Write market data point to InfluxDB
        """
        try:
            point = Point("market_data") \
                .tag("symbol", symbol) \
                .tag("source", source) \
                .field("price", price) \
                .field("volume", volume) \
                .time(timestamp, WritePrecision.S)
            
            self.write_api.write(
                bucket=settings.database.influxdb_bucket,
                org=settings.database.influxdb_org,
                record=point
            )
            logger.debug("Market data written to InfluxDB", symbol=symbol, price=price)
            
        except Exception as e:
            logger.error("Failed to write market data", error=str(e), symbol=symbol)
            raise
    
    def write_technical_indicators(self, symbol: str, indicators: Dict[str, float], 
                                 timestamp: datetime):
        """
        Write technical indicators to InfluxDB
        """
        try:
            point = Point("technical_indicators") \
                .tag("symbol", symbol) \
                .time(timestamp, WritePrecision.S)
            
            for indicator_name, value in indicators.items():
                if value is not None:  # Only write non-null values
                    point = point.field(indicator_name, value)
            
            self.write_api.write(
                bucket=settings.database.influxdb_bucket,
                org=settings.database.influxdb_org,
                record=point
            )
            logger.debug("Technical indicators written to InfluxDB", symbol=symbol)
            
        except Exception as e:
            logger.error("Failed to write technical indicators", error=str(e), symbol=symbol)
            raise
    
    def write_sentiment_data(self, sentiment_score: float, impact_short: float,
                           impact_long: float, source: str, timestamp: datetime):
        """
        Write sentiment analysis data to InfluxDB
        """
        try:
            point = Point("sentiment_data") \
                .tag("source", source) \
                .tag("category", "bitcoin") \
                .field("sentiment_score", sentiment_score) \
                .field("impact_short", impact_short) \
                .field("impact_long", impact_long) \
                .time(timestamp, WritePrecision.S)
            
            self.write_api.write(
                bucket=settings.database.influxdb_bucket,
                org=settings.database.influxdb_org,
                record=point
            )
            logger.debug("Sentiment data written to InfluxDB", source=source)
            
        except Exception as e:
            logger.error("Failed to write sentiment data", error=str(e), source=source)
            raise
    
    def query_market_data(self, symbol: str, start_time: datetime, 
                         end_time: datetime) -> List[Dict[str, Any]]:
        """
        Query market data from InfluxDB
        """
        try:
            query = f'''
            from(bucket: "{settings.database.influxdb_bucket}")
                |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
                |> filter(fn: (r) => r["_measurement"] == "market_data")
                |> filter(fn: (r) => r["symbol"] == "{symbol}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            result = self.query_api.query(org=settings.database.influxdb_org, query=query)
            
            data = []
            for table in result:
                for record in table.records:
                    data.append({
                        'time': record.get_time(),
                        'symbol': record.values.get('symbol'),
                        'price': record.values.get('price'),
                        'volume': record.values.get('volume'),
                        'source': record.values.get('source')
                    })
            
    def query_technical_indicators(self, symbol: str, start_time: datetime, 
                                 end_time: datetime) -> List[Dict[str, Any]]:
        """
        Query technical indicators from InfluxDB
        """
        try:
            query = f'''
            from(bucket: "{settings.database.influxdb_bucket}")
                |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
                |> filter(fn: (r) => r["_measurement"] == "technical_indicators")
                |> filter(fn: (r) => r["symbol"] == "{symbol}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            result = self.query_api.query(org=settings.database.influxdb_org, query=query)
            
            data = []
            for table in result:
                for record in table.records:
                    indicator_data = {
                        'time': record.get_time(),
                        'symbol': record.values.get('symbol')
                    }
                    # Add all indicator fields
                    for key, value in record.values.items():
                        if key not in ['_time', '_measurement', 'symbol', 'result', 'table']:
                            indicator_data[key] = value
                    data.append(indicator_data)
            
            return data
            
        except Exception as e:
            logger.error("Failed to query technical indicators", error=str(e), symbol=symbol)
            raise
    
    def query_sentiment_data(self, source: str, start_time: datetime, 
                           end_time: datetime) -> List[Dict[str, Any]]:
        """
        Query sentiment data from InfluxDB
        """
        try:
            query = f'''
            from(bucket: "{settings.database.influxdb_bucket}")
                |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
                |> filter(fn: (r) => r["_measurement"] == "sentiment_data")
                |> filter(fn: (r) => r["source"] == "{source}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            result = self.query_api.query(org=settings.database.influxdb_org, query=query)
            
            data = []
            for table in result:
                for record in table.records:
                    data.append({
                        'time': record.get_time(),
                        'source': record.values.get('source'),
                        'category': record.values.get('category'),
                        'sentiment_score': record.values.get('sentiment_score'),
                        'impact_short': record.values.get('impact_short'),
                        'impact_long': record.values.get('impact_long')
                    })
            
            return data
            
        except Exception as e:
            logger.error("Failed to query sentiment data", error=str(e), source=source)
            raise
    
    def get_latest_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest market data point for a symbol
        """
        try:
            query = f'''
            from(bucket: "{settings.database.influxdb_bucket}")
                |> range(start: -1h)
                |> filter(fn: (r) => r["_measurement"] == "market_data")
                |> filter(fn: (r) => r["symbol"] == "{symbol}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> last()
            '''
            
            result = self.query_api.query(org=settings.database.influxdb_org, query=query)
            
            for table in result:
                for record in table.records:
                    return {
                        'time': record.get_time(),
                        'symbol': record.values.get('symbol'),
                        'price': record.values.get('price'),
                        'volume': record.values.get('volume'),
                        'source': record.values.get('source')
                    }
            
            return None
            
        except Exception as e:
            logger.error("Failed to get latest market data", error=str(e), symbol=symbol)
            raise
    
    def write_trading_signal(self, symbol: str, signal_type: str, strength: float,
                           confidence: float, timestamp: datetime):
        """
        Write trading signal to InfluxDB
        """
        try:
            point = Point("trading_signals") \
                .tag("symbol", symbol) \
                .tag("signal_type", signal_type) \
                .field("strength", strength) \
                .field("confidence", confidence) \
                .time(timestamp, WritePrecision.S)
            
            self.write_api.write(
                bucket=settings.database.influxdb_bucket,
                org=settings.database.influxdb_org,
                record=point
            )
            logger.debug("Trading signal written to InfluxDB", symbol=symbol, signal_type=signal_type)
            
        except Exception as e:
            logger.error("Failed to write trading signal", error=str(e), symbol=symbol)
            raise
    
    def write_portfolio_snapshot(self, btc_balance: float, usdt_balance: float,
                               total_value: float, unrealized_pnl: float, timestamp: datetime):
        """
        Write portfolio snapshot to InfluxDB
        """
        try:
            point = Point("portfolio_snapshots") \
                .field("btc_balance", btc_balance) \
                .field("usdt_balance", usdt_balance) \
                .field("total_value_usdt", total_value) \
                .field("unrealized_pnl", unrealized_pnl) \
                .time(timestamp, WritePrecision.S)
            
            self.write_api.write(
                bucket=settings.database.influxdb_bucket,
                org=settings.database.influxdb_org,
                record=point
            )
            logger.debug("Portfolio snapshot written to InfluxDB")
            
        except Exception as e:
            logger.error("Failed to write portfolio snapshot", error=str(e))
            raise
    
    def get_price_statistics(self, symbol: str, hours: int = 24) -> Dict[str, float]:
        """
        Get price statistics for a symbol over the specified time period
        """
        try:
            query = f'''
            from(bucket: "{settings.database.influxdb_bucket}")
                |> range(start: -{hours}h)
                |> filter(fn: (r) => r["_measurement"] == "market_data")
                |> filter(fn: (r) => r["symbol"] == "{symbol}")
                |> filter(fn: (r) => r["_field"] == "price")
            '''
            
            result = self.query_api.query(org=settings.database.influxdb_org, query=query)
            
            prices = []
            for table in result:
                for record in table.records:
                    prices.append(record.get_value())
            
            if not prices:
                return {}
            
            return {
                'min_price': min(prices),
                'max_price': max(prices),
                'avg_price': sum(prices) / len(prices),
                'price_change': prices[-1] - prices[0] if len(prices) > 1 else 0,
                'price_change_percent': ((prices[-1] - prices[0]) / prices[0] * 100) if len(prices) > 1 and prices[0] != 0 else 0,
                'data_points': len(prices)
            }
            
        except Exception as e:
            logger.error("Failed to get price statistics", error=str(e), symbol=symbol)
            raise
    
    def close(self):
        """
        Close InfluxDB connection
        """
        if self.client:
            self.client.close()
            logger.info("InfluxDB connection closed")


# Global InfluxDB manager instance
influxdb_manager = InfluxDBManager()