"""
市场数据缓存
使用内存缓存存储期权链数据，减少API调用
"""

import time
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class MarketDataCache:
    """市场数据缓存类"""
    
    def __init__(self, ttl_seconds: int = 300):
        """
        初始化缓存
        
        Args:
            ttl_seconds: 缓存过期时间（秒），默认5分钟
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        logger.info(f"Market data cache initialized with TTL={ttl_seconds}s")
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的数据，如果不存在或已过期则返回None
        """
        if key not in self._cache:
            logger.debug(f"Cache miss: {key}")
            return None
        
        cache_entry = self._cache[key]
        current_time = time.time()
        
        # 检查是否过期
        if current_time - cache_entry['timestamp'] > self.ttl_seconds:
            logger.debug(f"Cache expired: {key}")
            del self._cache[key]
            return None
        
        logger.debug(f"Cache hit: {key}")
        return cache_entry['data']
    
    def set(self, key: str, data: Any) -> None:
        """
        设置缓存数据
        
        Args:
            key: 缓存键
            data: 要缓存的数据
        """
        self._cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
        logger.debug(f"Cache set: {key}")
    
    def delete(self, key: str) -> None:
        """
        删除缓存数据
        
        Args:
            key: 缓存键
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted: {key}")
    
    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0
        
        for cache_entry in self._cache.values():
            if current_time - cache_entry['timestamp'] > self.ttl_seconds:
                expired_entries += 1
            else:
                valid_entries += 1
        
        return {
            'total_entries': len(self._cache),
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'ttl_seconds': self.ttl_seconds
        }
    
    def cleanup_expired(self) -> int:
        """
        清理过期的缓存条目
        
        Returns:
            清理的条目数量
        """
        current_time = time.time()
        expired_keys = []
        
        for key, cache_entry in self._cache.items():
            if current_time - cache_entry['timestamp'] > self.ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)


# 全局缓存实例
_global_cache: Optional[MarketDataCache] = None


def get_cache(ttl_seconds: int = 300) -> MarketDataCache:
    """
    获取全局缓存实例
    
    Args:
        ttl_seconds: 缓存过期时间（秒）
        
    Returns:
        MarketDataCache实例
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = MarketDataCache(ttl_seconds=ttl_seconds)
    return _global_cache
