"""
Twitter/X Data Collector

Implements Twitter API integration for collecting Bitcoin-related tweets and discussions.
Fulfills requirements 1.3 for social media data collection.
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import structlog

from data_collection.base import DataCollector
from core.data_models import NewsItem, generate_id
from config import settings


logger = structlog.get_logger(__name__)


class TwitterDataCollector(DataCollector):
    """
    Collects Twitter/X data using Twitter API v2
    
    Monitors Bitcoin-related keywords and hashtags for sentiment analysis
    """
    
    # Twitter API endpoints
    SEARCH_TWEETS_URL = "https://api.twitter.com/2/tweets/search/recent"
    
    # Bitcoin-related keywords and hashtags
    BITCOIN_KEYWORDS = [
        "bitcoin", "BTC", "#bitcoin", "#BTC", 
        "cryptocurrency", "crypto", "#crypto",
        "blockchain", "#blockchain", "satoshi",
        "hodl", "#hodl", "btcprice", "bitcoinprice"
    ]
    
    def __init__(self, keywords: Optional[List[str]] = None, max_tweets: int = 100):
        super().__init__("twitter_collector")
        self.keywords = keywords or self.BITCOIN_KEYWORDS
        self.max_tweets = min(max_tweets, 100)  # Twitter API limit
        self.bearer_token = settings.api.twitter_bearer_token
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_collection_time = datetime.now() - timedelta(hours=1)  # Start with 1h lookback
        
    async def validate_connection(self) -> bool:
        """Validate Twitter API connection"""
        if not self.bearer_token:
            self.logger.error("Twitter bearer token not configured")
            return False
            
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={
                        'Authorization': f'Bearer {self.bearer_token}',
                        'User-Agent': 'Bitcoin Trading System Twitter Collector 1.0'
                    }
                )
            
            # Test API connection with a simple query
            test_params = {
                'query': 'bitcoin',
                'max_results': 10,
                'tweet.fields': 'created_at,public_metrics,context_annotations'
            }
            
            async with self.session.get(self.SEARCH_TWEETS_URL, params=test_params) as response:
                if response.status == 200:
                    return True
                elif response.status == 401:
                    self.logger.error("Twitter API authentication failed")
                    return False
                elif response.status == 429:
                    self.logger.warning("Twitter API rate limit exceeded")
                    return False
                else:
                    self.logger.error("Twitter API connection failed", status=response.status)
                    return False
                    
        except Exception as e:
            self.logger.error("Twitter connection validation failed", error=str(e))
            return False
    
    async def collect_data(self) -> List[NewsItem]:
        """
        Collect Twitter data for Bitcoin-related keywords
        
        Returns:
            List of NewsItem objects representing tweets
        """
        if not self.bearer_token:
            self.logger.error("Twitter bearer token not configured")
            return []
        
        all_tweets = []
        
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'Authorization': f'Bearer {self.bearer_token}',
                    'User-Agent': 'Bitcoin Trading System Twitter Collector 1.0'
                }
            )
        
        try:
            # Build search query
            query = self._build_search_query()
            
            self.logger.info("Collecting Twitter data", query=query, max_results=self.max_tweets)
            
            # Search for tweets
            tweets = await self._search_tweets(query)
            
            # Convert tweets to NewsItem format
            news_items = self._convert_tweets_to_news_items(tweets)
            
            # Filter for recent tweets
            recent_items = self._filter_recent_tweets(news_items)
            
            all_tweets.extend(recent_items)
            
            # Update last collection time
            self.last_collection_time = datetime.now()
            
            self.logger.info(
                "Twitter collection completed",
                total_tweets=len(tweets),
                converted_items=len(news_items),
                recent_items=len(recent_items)
            )
            
        except Exception as e:
            self.logger.error("Error collecting Twitter data", error=str(e))
        
        return all_tweets
    
    def _build_search_query(self) -> str:
        """Build Twitter search query from keywords"""
        # Combine keywords with OR operator
        # Exclude retweets and replies for cleaner data
        keyword_query = " OR ".join(self.keywords[:10])  # Limit to avoid query length issues
        
        # Add filters to exclude retweets and get only English tweets
        query = f"({keyword_query}) -is:retweet -is:reply lang:en"
        
        return query
    
    async def _search_tweets(self, query: str) -> List[Dict[str, Any]]:
        """Search for tweets using Twitter API v2"""
        params = {
            'query': query,
            'max_results': self.max_tweets,
            'tweet.fields': 'created_at,public_metrics,context_annotations,author_id,lang',
            'user.fields': 'username,verified,public_metrics',
            'expansions': 'author_id'
        }
        
        try:
            async with self.session.get(self.SEARCH_TWEETS_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', [])
                elif response.status == 429:
                    self.logger.warning("Twitter API rate limit exceeded")
                    # Wait for rate limit reset (15 minutes for search endpoint)
                    await asyncio.sleep(900)
                    return []
                else:
                    self.logger.error(
                        "Twitter API request failed",
                        status=response.status,
                        response=await response.text()
                    )
                    return []
                    
        except Exception as e:
            self.logger.error("Error searching tweets", error=str(e))
            return []
    
    def _convert_tweets_to_news_items(self, tweets: List[Dict[str, Any]]) -> List[NewsItem]:
        """Convert Twitter API response to NewsItem objects"""
        news_items = []
        
        for tweet in tweets:
            try:
                # Extract tweet data
                tweet_id = tweet.get('id', '')
                text = tweet.get('text', '').strip()
                created_at = self._parse_twitter_date(tweet.get('created_at', ''))
                author_id = tweet.get('author_id', '')
                
                # Skip empty tweets
                if not text:
                    continue
                
                # Create URL to tweet
                tweet_url = f"https://twitter.com/i/status/{tweet_id}"
                
                # Extract metrics for additional context
                metrics = tweet.get('public_metrics', {})
                engagement_score = (
                    metrics.get('like_count', 0) + 
                    metrics.get('retweet_count', 0) * 2 +  # Retweets weighted more
                    metrics.get('reply_count', 0)
                )
                
                # Add engagement info to content
                enhanced_content = f"{text}\n\n[Engagement: {engagement_score} interactions]"
                
                # Create NewsItem
                news_item = NewsItem(
                    id=generate_id(),
                    title=f"Tweet: {text[:100]}..." if len(text) > 100 else f"Tweet: {text}",
                    content=enhanced_content,
                    source="twitter",
                    published_at=created_at or datetime.now(),
                    url=tweet_url
                )
                
                news_items.append(news_item)
                
            except Exception as e:
                self.logger.error(
                    "Error converting tweet to news item",
                    tweet_id=tweet.get('id', 'unknown'),
                    error=str(e)
                )
                continue
        
        return news_items
    
    def _parse_twitter_date(self, date_string: str) -> Optional[datetime]:
        """Parse Twitter API date format"""
        if not date_string:
            return None
            
        try:
            # Twitter API v2 uses ISO 8601 format
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except Exception as e:
            self.logger.error("Error parsing Twitter date", date=date_string, error=str(e))
            return datetime.now()
    
    def _filter_recent_tweets(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """Filter tweets to only include recent ones"""
        recent_items = []
        
        for item in news_items:
            if item.published_at >= self.last_collection_time:
                recent_items.append(item)
        
        return recent_items
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def __del__(self):
        """Cleanup on deletion"""
        if self.session and not self.session.closed:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.close())
            except:
                pass