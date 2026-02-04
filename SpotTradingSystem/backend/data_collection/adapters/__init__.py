"""
Data source adapters for various external APIs and services

Implements specific collectors for news, social media, market data, and economic indicators
as specified in requirements 1.3 and 1.4.
"""

from .news_collector import NewsDataCollector
from .twitter_collector import TwitterDataCollector
from .market_collector import MarketDataCollector
from .economic_collector import EconomicDataCollector

__all__ = [
    'NewsDataCollector',
    'TwitterDataCollector', 
    'MarketDataCollector',
    'EconomicDataCollector'
]