"""
Redis client for caching and message queue
"""
import redis
import json
from typing import Any, Optional, Dict, List
from datetime import timedelta
import structlog

from config import settings

logger = structlog.get_logger(__name__)


class RedisClient:
    """
    Redis client wrapper for caching and message queue operations
    """
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self._connect()
    
    def _connect(self):
        """
        Initialize Redis connection
        """
        try:
            self.client = redis.Redis(
                host=settings.redis.redis_host,
                port=settings.redis.redis_port,
                db=settings.redis.redis_db,
                password=settings.redis.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    def test_connection(self) -> bool:
        """
        Test Redis connection
        """
        try:
            if self.client:
                self.client.ping()
                logger.info("Redis connection successful")
                return True
            return False
        except Exception as e:
            logger.error("Redis connection test failed", error=str(e))
            return False
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        Set a key-value pair in Redis
        """
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            result = self.client.set(key, value, ex=expire)
            logger.debug("Redis SET operation", key=key, expire=expire)
            return result
        except Exception as e:
            logger.error("Redis SET failed", error=str(e), key=key)
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value by key from Redis
        """
        try:
            value = self.client.get(key)
            if value is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error("Redis GET failed", error=str(e), key=key)
            return None
    
    def delete(self, key: str) -> bool:
        """
        Delete key from Redis
        """
        try:
            result = self.client.delete(key)
            logger.debug("Redis DELETE operation", key=key)
            return bool(result)
        except Exception as e:
            logger.error("Redis DELETE failed", error=str(e), key=key)
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis
        """
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error("Redis EXISTS failed", error=str(e), key=key)
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for a key
        """
        try:
            result = self.client.expire(key, seconds)
            logger.debug("Redis EXPIRE operation", key=key, seconds=seconds)
            return result
        except Exception as e:
            logger.error("Redis EXPIRE failed", error=str(e), key=key)
            return False
    
    def lpush(self, key: str, *values: Any) -> int:
        """
        Push values to the left of a list
        """
        try:
            # Convert complex objects to JSON
            json_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    json_values.append(json.dumps(value))
                else:
                    json_values.append(value)
            
            result = self.client.lpush(key, *json_values)
            logger.debug("Redis LPUSH operation", key=key, count=len(values))
            return result
        except Exception as e:
            logger.error("Redis LPUSH failed", error=str(e), key=key)
            return 0
    
    def rpop(self, key: str) -> Optional[Any]:
        """
        Pop value from the right of a list
        """
        try:
            value = self.client.rpop(key)
            if value is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error("Redis RPOP failed", error=str(e), key=key)
            return None
    
    def llen(self, key: str) -> int:
        """
        Get length of a list
        """
        try:
            return self.client.llen(key)
        except Exception as e:
            logger.error("Redis LLEN failed", error=str(e), key=key)
            return 0
    
    def publish(self, channel: str, message: Any) -> int:
        """
        Publish message to a channel
        """
        try:
            if isinstance(message, (dict, list)):
                message = json.dumps(message)
            
            result = self.client.publish(channel, message)
            logger.debug("Redis PUBLISH operation", channel=channel)
            return result
        except Exception as e:
            logger.error("Redis PUBLISH failed", error=str(e), channel=channel)
            return 0
    
    def subscribe(self, *channels: str):
        """
        Subscribe to channels
        """
        try:
            pubsub = self.client.pubsub()
            pubsub.subscribe(*channels)
            logger.info("Subscribed to Redis channels", channels=channels)
            return pubsub
        except Exception as e:
            logger.error("Redis SUBSCRIBE failed", error=str(e), channels=channels)
            return None
    
    def cache_market_data(self, symbol: str, data: Dict[str, Any], 
                         expire_seconds: int = 60):
        """
        Cache market data with expiration
        """
        key = f"market_data:{symbol}"
        return self.set(key, data, expire_seconds)
    
    def get_cached_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get cached market data
        """
        key = f"market_data:{symbol}"
        return self.get(key)
    
    def cache_sentiment_analysis(self, content_hash: str, analysis: Dict[str, Any],
                               expire_seconds: int = 3600):
        """
        Cache sentiment analysis results
        """
        key = f"sentiment:{content_hash}"
        return self.set(key, analysis, expire_seconds)
    
    def get_cached_sentiment(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get cached sentiment analysis
        """
        key = f"sentiment:{content_hash}"
        return self.get(key)
    
    def close(self):
        """
        Close Redis connection
        """
        if self.client:
            self.client.close()
            logger.info("Redis connection closed")


# Global Redis client instance
redis_client = RedisClient()