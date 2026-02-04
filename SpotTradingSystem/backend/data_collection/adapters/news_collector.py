"""
News Data Collector

Implements Web3 news data collection from sources like CoinDesk, CoinTelegraph, etc.
Fulfills requirements 1.3 for news data collection.
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import feedparser
import structlog

from data_collection.base import DataCollector
from core.data_models import NewsItem, generate_id
from config import settings


logger = structlog.get_logger(__name__)


class NewsDataCollector(DataCollector):
    """
    Collects news data from Web3 and cryptocurrency news sources
    
    Supports RSS feeds and web scraping from major crypto news sites
    """
    
    # News source configurations
    NEWS_SOURCES = {
        'coindesk': {
            'rss_url': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
            'base_url': 'https://www.coindesk.com',
            'keywords': ['bitcoin', 'btc', 'cryptocurrency', 'crypto']
        },
        'cointelegraph': {
            'rss_url': 'https://cointelegraph.com/rss',
            'base_url': 'https://cointelegraph.com',
            'keywords': ['bitcoin', 'btc', 'cryptocurrency', 'crypto']
        },
        'decrypt': {
            'rss_url': 'https://decrypt.co/feed',
            'base_url': 'https://decrypt.co',
            'keywords': ['bitcoin', 'btc', 'cryptocurrency', 'crypto']
        },
        'bitcoinmagazine': {
            'rss_url': 'https://bitcoinmagazine.com/.rss/full/',
            'base_url': 'https://bitcoinmagazine.com',
            'keywords': ['bitcoin', 'btc']
        }
    }
    
    def __init__(self, sources: Optional[List[str]] = None, max_articles_per_source: int = 10):
        super().__init__("news_collector")
        self.sources = sources or list(self.NEWS_SOURCES.keys())
        self.max_articles_per_source = max_articles_per_source
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_collection_time = datetime.now() - timedelta(hours=24)  # Start with 24h lookback
        
    async def validate_connection(self) -> bool:
        """Validate connection to news sources"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={
                        'User-Agent': 'Bitcoin Trading System News Collector 1.0'
                    }
                )
            
            # Test connection to first source
            first_source = self.sources[0] if self.sources else 'coindesk'
            test_url = self.NEWS_SOURCES[first_source]['rss_url']
            
            async with self.session.get(test_url) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error("Connection validation failed", error=str(e))
            return False
    
    async def collect_data(self) -> List[NewsItem]:
        """
        Collect news data from configured sources
        
        Returns:
            List of NewsItem objects
        """
        all_news_items = []
        
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'User-Agent': 'Bitcoin Trading System News Collector 1.0'
                }
            )
        
        # Collect from each source
        for source_name in self.sources:
            try:
                source_config = self.NEWS_SOURCES.get(source_name)
                if not source_config:
                    self.logger.warning("Unknown news source", source=source_name)
                    continue
                
                self.logger.info("Collecting from news source", source=source_name)
                
                # Collect RSS feed data
                news_items = await self._collect_from_rss(source_name, source_config)
                
                # Filter for Bitcoin-related content
                filtered_items = self._filter_bitcoin_content(news_items, source_config['keywords'])
                
                # Limit number of articles per source
                limited_items = filtered_items[:self.max_articles_per_source]
                
                all_news_items.extend(limited_items)
                
                self.logger.info(
                    "Collected news items",
                    source=source_name,
                    total_items=len(news_items),
                    filtered_items=len(filtered_items),
                    final_items=len(limited_items)
                )
                
                # Small delay between sources to be respectful
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(
                    "Error collecting from news source",
                    source=source_name,
                    error=str(e)
                )
                continue
        
        # Update last collection time
        self.last_collection_time = datetime.now()
        
        self.logger.info(
            "News collection completed",
            total_sources=len(self.sources),
            total_items=len(all_news_items)
        )
        
        return all_news_items
    
    async def _collect_from_rss(self, source_name: str, source_config: Dict[str, Any]) -> List[NewsItem]:
        """Collect news items from RSS feed"""
        news_items = []
        
        try:
            # Fetch RSS feed
            async with self.session.get(source_config['rss_url']) as response:
                if response.status != 200:
                    self.logger.error(
                        "Failed to fetch RSS feed",
                        source=source_name,
                        status=response.status
                    )
                    return []
                
                rss_content = await response.text()
            
            # Parse RSS feed
            feed = feedparser.parse(rss_content)
            
            if not feed.entries:
                self.logger.warning("No entries found in RSS feed", source=source_name)
                return []
            
            # Process each entry
            for entry in feed.entries:
                try:
                    # Parse publication date
                    published_at = self._parse_date(entry.get('published', ''))
                    
                    # Skip old articles (older than last collection)
                    if published_at and published_at < self.last_collection_time:
                        continue
                    
                    # Extract content
                    content = self._extract_content(entry)
                    
                    # Create NewsItem
                    news_item = NewsItem(
                        id=generate_id(),
                        title=entry.get('title', '').strip(),
                        content=content,
                        source=source_name,
                        published_at=published_at or datetime.now(),
                        url=entry.get('link', '')
                    )
                    
                    news_items.append(news_item)
                    
                except Exception as e:
                    self.logger.error(
                        "Error processing RSS entry",
                        source=source_name,
                        entry_title=entry.get('title', 'unknown'),
                        error=str(e)
                    )
                    continue
        
        except Exception as e:
            self.logger.error(
                "Error fetching RSS feed",
                source=source_name,
                url=source_config['rss_url'],
                error=str(e)
            )
        
        return news_items
    
    def _extract_content(self, entry: Dict[str, Any]) -> str:
        """Extract clean content from RSS entry"""
        # Try different content fields
        content_fields = ['content', 'summary', 'description']
        
        for field in content_fields:
            if field in entry:
                content_data = entry[field]
                
                # Handle different content formats
                if isinstance(content_data, list) and content_data:
                    content = content_data[0].get('value', '')
                elif isinstance(content_data, str):
                    content = content_data
                else:
                    continue
                
                # Clean HTML tags
                if content:
                    soup = BeautifulSoup(content, 'html.parser')
                    clean_content = soup.get_text().strip()
                    
                    if clean_content:
                        return clean_content
        
        # Fallback to title if no content found
        return entry.get('title', '')
    
    def _parse_date(self, date_string: str) -> Optional[datetime]:
        """Parse date string from RSS feed"""
        if not date_string:
            return None
            
        try:
            # Try parsing with feedparser's time parsing
            parsed_time = feedparser._parse_date(date_string)
            if parsed_time:
                return datetime(*parsed_time[:6])
        except:
            pass
        
        # Fallback to current time
        return datetime.now()
    
    def _filter_bitcoin_content(self, news_items: List[NewsItem], keywords: List[str]) -> List[NewsItem]:
        """Filter news items for Bitcoin-related content"""
        filtered_items = []
        
        for item in news_items:
            # Check if any keyword appears in title or content
            text_to_check = (item.title + ' ' + item.content).lower()
            
            if any(keyword.lower() in text_to_check for keyword in keywords):
                filtered_items.append(item)
        
        return filtered_items
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def __del__(self):
        """Cleanup on deletion"""
        if self.session and not self.session.closed:
            # Note: This is not ideal but necessary for cleanup
            # In production, always call close() explicitly
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.close())
            except:
                pass