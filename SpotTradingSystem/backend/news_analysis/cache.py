"""
Analysis cache implementation using Redis for caching sentiment analysis results
"""
import json
import logging
from typing import Optional, Dict, Any
import redis.asyncio as redis
from backend.config import settings

logger = logging.getLogger(__name__)


class AnalysisCache:
    """
    Redis-based cache for news analysis results
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize the analysis cache
        
        Args:
            redis_url: Redis connection URL, defaults to settings.redis.redis_url
        """
        self.redis_url = redis_url or settings.redis.redis_url
        self._redis_client = None
        self.key_prefix = "news_analysis:"
    
    async def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client"""
        if self._redis_client is None:
            self._redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._redis_client
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached analysis result
        
        Args:
            key: Cache key
            
        Returns:
            Cached data as dictionary or None if not found
        """
        try:
            client = await self._get_redis_client()
            cached_data = await client.get(f"{self.key_prefix}{key}")
            
            if cached_data:
                return json.loads(cached_data)
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
            return None
    
    async def set(self, key: str, data: Dict[str, Any], ttl: int = 3600) -> bool:
        """
        Set cached analysis result
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_redis_client()
            serialized_data = json.dumps(data)
            
            await client.setex(
                f"{self.key_prefix}{key}",
                ttl,
                serialized_data
            )
            
            logger.debug(f"Cached analysis result with key: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete cached analysis result
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_redis_client()
            result = await client.delete(f"{self.key_prefix}{key}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            return False
    
    async def clear_all(self) -> bool:
        """
        Clear all cached analysis results
        
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_redis_client()
            keys = await client.keys(f"{self.key_prefix}*")
            
            if keys:
                await client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cached analysis results")
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            client = await self._get_redis_client()
            keys = await client.keys(f"{self.key_prefix}*")
            
            # Get memory usage info
            info = await client.info('memory')
            
            return {
                "total_keys": len(keys),
                "memory_used": info.get('used_memory_human', 'unknown'),
                "key_prefix": self.key_prefix
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {
                "total_keys": 0,
                "memory_used": "unknown",
                "key_prefix": self.key_prefix,
                "error": str(e)
            }
    
    async def close(self):
        """Close Redis connection"""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None