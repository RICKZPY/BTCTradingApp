"""
Economic Data Collector

Implements macroeconomic data collection from FRED API and other sources.
Fulfills requirements 1.4 for economic indicator data collection.
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


class EconomicDataCollector(DataCollector):
    """
    Collects macroeconomic data from FRED (Federal Reserve Economic Data) and other sources
    
    Monitors key economic indicators that may impact Bitcoin price
    """
    
    # FRED API endpoint
    FRED_API_URL = "https://api.stlouisfed.org/fred"
    
    # Key economic indicators to monitor
    ECONOMIC_INDICATORS = {
        'DGS10': {
            'name': '10-Year Treasury Rate',
            'description': 'Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity',
            'impact': 'Inverse correlation with Bitcoin - higher rates may reduce crypto appeal'
        },
        'UNRATE': {
            'name': 'Unemployment Rate',
            'description': 'Civilian Unemployment Rate',
            'impact': 'Economic health indicator - affects risk appetite'
        },
        'CPIAUCSL': {
            'name': 'Consumer Price Index',
            'description': 'Consumer Price Index for All Urban Consumers: All Items',
            'impact': 'Inflation indicator - Bitcoin often seen as inflation hedge'
        },
        'DEXUSEU': {
            'name': 'USD/EUR Exchange Rate',
            'description': 'U.S. / Euro Foreign Exchange Rate',
            'impact': 'USD strength affects Bitcoin as it is primarily USD-denominated'
        },
        'DEXJPUS': {
            'name': 'JPY/USD Exchange Rate', 
            'description': 'Japan / U.S. Foreign Exchange Rate',
            'impact': 'Major currency pair affecting global risk sentiment'
        },
        'VIXCLS': {
            'name': 'VIX Volatility Index',
            'description': 'CBOE Volatility Index: VIX',
            'impact': 'Market fear gauge - high VIX may correlate with crypto volatility'
        }
    }
    
    def __init__(self, indicators: Optional[List[str]] = None, lookback_days: int = 7):
        super().__init__("economic_collector")
        self.indicators = indicators or list(self.ECONOMIC_INDICATORS.keys())
        self.lookback_days = lookback_days
        self.fred_api_key = getattr(settings.api, 'fred_api_key', '')
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_collection_time = datetime.now() - timedelta(days=lookback_days)
        
    async def validate_connection(self) -> bool:
        """Validate connection to FRED API"""
        if not self.fred_api_key:
            self.logger.warning("FRED API key not configured, using public access (limited)")
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={
                        'User-Agent': 'Bitcoin Trading System Economic Collector 1.0'
                    }
                )
            
            # Test API connection with a simple request
            params = {
                'series_id': 'DGS10',  # 10-year treasury rate
                'api_key': self.fred_api_key,
                'file_type': 'json',
                'limit': 1
            }
            
            url = f"{self.FRED_API_URL}/series/observations"
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return 'observations' in data
                elif response.status == 400:
                    # Check if it's an API key issue
                    error_data = await response.json()
                    if 'api_key' in str(error_data).lower():
                        self.logger.error("Invalid FRED API key")
                        return False
                else:
                    self.logger.error("FRED API connection failed", status=response.status)
                    return False
                    
        except Exception as e:
            self.logger.error("Economic data connection validation failed", error=str(e))
            return False
    
    async def collect_data(self) -> List[NewsItem]:
        """
        Collect economic indicator data from FRED API
        
        Returns:
            List of NewsItem objects representing economic data points
        """
        all_economic_data = []
        
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'User-Agent': 'Bitcoin Trading System Economic Collector 1.0'
                }
            )
        
        # Collect data for each indicator
        for indicator_id in self.indicators:
            try:
                indicator_config = self.ECONOMIC_INDICATORS.get(indicator_id, {})
                
                self.logger.info(
                    "Collecting economic indicator",
                    indicator=indicator_id,
                    name=indicator_config.get('name', indicator_id)
                )
                
                # Fetch recent data for this indicator
                data_points = await self._fetch_indicator_data(indicator_id)
                
                # Convert to NewsItem format for consistency
                news_items = self._convert_to_news_items(indicator_id, data_points, indicator_config)
                
                all_economic_data.extend(news_items)
                
                self.logger.info(
                    "Economic indicator collected",
                    indicator=indicator_id,
                    data_points=len(data_points),
                    news_items=len(news_items)
                )
                
                # Small delay between requests to be respectful
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.logger.error(
                    "Error collecting economic indicator",
                    indicator=indicator_id,
                    error=str(e)
                )
                continue
        
        # Update last collection time
        self.last_collection_time = datetime.now()
        
        self.logger.info(
            "Economic data collection completed",
            total_indicators=len(self.indicators),
            total_items=len(all_economic_data)
        )
        
        return all_economic_data
    
    async def _fetch_indicator_data(self, indicator_id: str) -> List[Dict[str, Any]]:
        """Fetch data for a specific economic indicator"""
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = self.last_collection_time
            
            params = {
                'series_id': indicator_id,
                'api_key': self.fred_api_key,
                'file_type': 'json',
                'observation_start': start_date.strftime('%Y-%m-%d'),
                'observation_end': end_date.strftime('%Y-%m-%d'),
                'sort_order': 'desc',
                'limit': 100
            }
            
            # Remove empty api_key if not provided
            if not self.fred_api_key:
                del params['api_key']
            
            url = f"{self.FRED_API_URL}/series/observations"
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    observations = data.get('observations', [])
                    
                    # Filter out missing values
                    valid_observations = [
                        obs for obs in observations 
                        if obs.get('value') != '.' and obs.get('value') is not None
                    ]
                    
                    return valid_observations
                    
                elif response.status == 429:
                    self.logger.warning("FRED API rate limit exceeded")
                    await asyncio.sleep(60)  # Wait 1 minute
                    return []
                else:
                    self.logger.error(
                        "FRED API request failed",
                        indicator=indicator_id,
                        status=response.status,
                        response=await response.text()
                    )
                    return []
                    
        except Exception as e:
            self.logger.error(
                "Error fetching indicator data",
                indicator=indicator_id,
                error=str(e)
            )
            return []
    
    def _convert_to_news_items(
        self, 
        indicator_id: str, 
        data_points: List[Dict[str, Any]], 
        indicator_config: Dict[str, Any]
    ) -> List[NewsItem]:
        """Convert economic data points to NewsItem format"""
        news_items = []
        
        for data_point in data_points:
            try:
                # Parse date and value
                date_str = data_point.get('date', '')
                value_str = data_point.get('value', '')
                
                if not date_str or not value_str:
                    continue
                
                # Parse date
                observation_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                # Skip if too old
                if observation_date < self.last_collection_time:
                    continue
                
                # Parse value
                try:
                    value = float(value_str)
                except ValueError:
                    continue
                
                # Create title and content
                indicator_name = indicator_config.get('name', indicator_id)
                title = f"Economic Indicator Update: {indicator_name}"
                
                content = f"""
Economic Indicator: {indicator_name}
Value: {value}
Date: {date_str}
Series ID: {indicator_id}

Description: {indicator_config.get('description', 'No description available')}

Market Impact: {indicator_config.get('impact', 'Impact analysis not available')}

This economic data point may influence Bitcoin and cryptocurrency markets through its effect on:
- Overall economic sentiment
- Risk appetite among investors  
- Monetary policy expectations
- Currency strength and inflation expectations
                """.strip()
                
                # Create NewsItem
                news_item = NewsItem(
                    id=generate_id(),
                    title=title,
                    content=content,
                    source="fred_economic_data",
                    published_at=observation_date,
                    url=f"https://fred.stlouisfed.org/series/{indicator_id}"
                )
                
                news_items.append(news_item)
                
            except Exception as e:
                self.logger.error(
                    "Error converting data point to news item",
                    indicator=indicator_id,
                    data_point=data_point,
                    error=str(e)
                )
                continue
        
        return news_items
    
    async def get_latest_value(self, indicator_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest value for a specific economic indicator"""
        try:
            params = {
                'series_id': indicator_id,
                'api_key': self.fred_api_key,
                'file_type': 'json',
                'limit': 1,
                'sort_order': 'desc'
            }
            
            if not self.fred_api_key:
                del params['api_key']
            
            url = f"{self.FRED_API_URL}/series/observations"
            
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30)
                )
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    observations = data.get('observations', [])
                    
                    if observations and observations[0].get('value') != '.':
                        latest = observations[0]
                        return {
                            'indicator_id': indicator_id,
                            'value': float(latest['value']),
                            'date': latest['date'],
                            'name': self.ECONOMIC_INDICATORS.get(indicator_id, {}).get('name', indicator_id)
                        }
                    
        except Exception as e:
            self.logger.error(
                "Error getting latest value",
                indicator=indicator_id,
                error=str(e)
            )
        
        return None
    
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