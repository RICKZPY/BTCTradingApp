"""
Data Collection Module for Bitcoin Trading System

This module provides the infrastructure for collecting data from multiple sources
including news, social media, market data, and economic indicators.
"""

from .base import DataCollector, DataCollectionScheduler
from .queue_manager import DataQueueManager
from .adapters.news_collector import NewsDataCollector
from .adapters.twitter_collector import TwitterDataCollector
from .adapters.market_collector import MarketDataCollector
from .adapters.economic_collector import EconomicDataCollector

__all__ = [
    'DataCollector',
    'DataCollectionScheduler', 
    'DataQueueManager',
    'NewsDataCollector',
    'TwitterDataCollector',
    'MarketDataCollector',
    'EconomicDataCollector'
]