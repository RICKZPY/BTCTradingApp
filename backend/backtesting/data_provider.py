"""
Historical Data Provider
Handles querying and processing of historical market data for backtesting
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_models import MarketData, NewsItem, SentimentScore
from database.postgres import get_db_session
from database.models import MarketData as MarketDataModel, NewsItem as NewsItemModel, SentimentAnalysis

logger = logging.getLogger(__name__)


class HistoricalDataProvider:
    """
    Provides historical data for backtesting
    """
    
    def __init__(self):
        """Initialize historical data provider"""
        self.db_session: Optional[Session] = None
        logger.info("Historical data provider initialized")
    
    def get_market_data(self, 
                       symbol: str = "BTCUSDT",
                       start_date: datetime = None,
                       end_date: datetime = None,
                       limit: int = 10000) -> List[MarketData]:
        """
        Get historical market data
        
        Args:
            symbol: Trading symbol
            start_date: Start date for data
            end_date: End date for data
            limit: Maximum number of records
            
        Returns:
            List of MarketData objects
        """
        try:
            with get_db_session() as session:
                query = session.query(MarketDataModel).filter(
                    MarketDataModel.symbol == symbol
                )
                
                if start_date:
                    query = query.filter(MarketDataModel.timestamp >= start_date)
                
                if end_date:
                    query = query.filter(MarketDataModel.timestamp <= end_date)
                
                query = query.order_by(MarketDataModel.timestamp).limit(limit)
                
                db_records = query.all()
                
                # Convert to domain objects
                market_data = []
                for record in db_records:
                    market_data.append(MarketData(
                        symbol=record.symbol,
                        price=record.price,
                        volume=record.volume,
                        timestamp=record.timestamp,
                        source=record.source
                    ))
                
                logger.info(f"Retrieved {len(market_data)} market data records for {symbol}")
                return market_data
                
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            return []
    
    def get_sentiment_data(self,
                          start_date: datetime = None,
                          end_date: datetime = None,
                          limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get historical sentiment analysis data
        
        Args:
            start_date: Start date for data
            end_date: End date for data
            limit: Maximum number of records
            
        Returns:
            List of sentiment data dictionaries
        """
        try:
            with get_db_session() as session:
                query = session.query(SentimentAnalysis).join(NewsItemModel)
                
                if start_date:
                    query = query.filter(NewsItemModel.published_at >= start_date)
                
                if end_date:
                    query = query.filter(NewsItemModel.published_at <= end_date)
                
                query = query.order_by(NewsItemModel.published_at).limit(limit)
                
                db_records = query.all()
                
                # Convert to dictionaries
                sentiment_data = []
                for record in db_records:
                    sentiment_data.append({
                        'timestamp': record.news_item.published_at.isoformat(),
                        'sentiment_value': record.sentiment_score,
                        'confidence': record.confidence,
                        'key_factors': record.key_factors or [],
                        'short_term_impact': record.short_term_impact,
                        'long_term_impact': record.long_term_impact,
                        'impact_confidence': record.impact_confidence,
                        'reasoning': record.reasoning
                    })
                
                logger.info(f"Retrieved {len(sentiment_data)} sentiment records")
                return sentiment_data
                
        except Exception as e:
            logger.error(f"Failed to get sentiment data: {e}")
            return []
    
    def get_news_data(self,
                     start_date: datetime = None,
                     end_date: datetime = None,
                     limit: int = 1000) -> List[NewsItem]:
        """
        Get historical news data
        
        Args:
            start_date: Start date for data
            end_date: End date for data
            limit: Maximum number of records
            
        Returns:
            List of NewsItem objects
        """
        try:
            with get_db_session() as session:
                query = session.query(NewsItemModel)
                
                if start_date:
                    query = query.filter(NewsItemModel.published_at >= start_date)
                
                if end_date:
                    query = query.filter(NewsItemModel.published_at <= end_date)
                
                query = query.order_by(NewsItemModel.published_at).limit(limit)
                
                db_records = query.all()
                
                # Convert to domain objects
                news_items = []
                for record in db_records:
                    news_items.append(NewsItem(
                        id=str(record.id),
                        title=record.title,
                        content=record.content,
                        source=record.source,
                        published_at=record.published_at,
                        url=record.url or "",
                        sentiment_score=record.sentiment_score
                    ))
                
                logger.info(f"Retrieved {len(news_items)} news records")
                return news_items
                
        except Exception as e:
            logger.error(f"Failed to get news data: {e}")
            return []
    
    def generate_sample_data(self, 
                           start_date: datetime,
                           end_date: datetime,
                           interval_minutes: int = 60) -> List[MarketData]:
        """
        Generate sample market data for testing
        
        Args:
            start_date: Start date
            end_date: End date
            interval_minutes: Data interval in minutes
            
        Returns:
            List of sample MarketData objects
        """
        import random
        import math
        
        sample_data = []
        current_time = start_date
        base_price = 45000.0  # Starting BTC price
        
        while current_time <= end_date:
            # Generate realistic price movement
            price_change = random.gauss(0, 0.02)  # 2% volatility
            base_price *= (1 + price_change)
            base_price = max(base_price, 1000.0)  # Minimum price
            
            # Generate volume
            base_volume = 100.0
            volume_multiplier = random.uniform(0.5, 2.0)
            volume = base_volume * volume_multiplier
            
            market_data = MarketData(
                symbol="BTCUSDT",
                price=round(base_price, 2),
                volume=round(volume, 4),
                timestamp=current_time,
                source="sample_generator"
            )
            
            sample_data.append(market_data)
            current_time += timedelta(minutes=interval_minutes)
        
        logger.info(f"Generated {len(sample_data)} sample data points")
        return sample_data
    
    def get_data_summary(self, 
                        symbol: str = "BTCUSDT",
                        days: int = 30) -> Dict[str, Any]:
        """
        Get summary of available historical data
        
        Args:
            symbol: Trading symbol
            days: Number of days to look back
            
        Returns:
            Data summary dictionary
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        try:
            with get_db_session() as session:
                # Market data summary
                market_count = session.query(MarketDataModel).filter(
                    and_(
                        MarketDataModel.symbol == symbol,
                        MarketDataModel.timestamp >= start_date,
                        MarketDataModel.timestamp <= end_date
                    )
                ).count()
                
                # Get date range
                first_record = session.query(MarketDataModel).filter(
                    MarketDataModel.symbol == symbol
                ).order_by(MarketDataModel.timestamp).first()
                
                last_record = session.query(MarketDataModel).filter(
                    MarketDataModel.symbol == symbol
                ).order_by(desc(MarketDataModel.timestamp)).first()
                
                # News data summary
                news_count = session.query(NewsItemModel).filter(
                    and_(
                        NewsItemModel.published_at >= start_date,
                        NewsItemModel.published_at <= end_date
                    )
                ).count()
                
                # Sentiment data summary
                sentiment_count = session.query(SentimentAnalysis).join(NewsItemModel).filter(
                    and_(
                        NewsItemModel.published_at >= start_date,
                        NewsItemModel.published_at <= end_date
                    )
                ).count()
                
                return {
                    'symbol': symbol,
                    'period_days': days,
                    'market_data_points': market_count,
                    'news_items': news_count,
                    'sentiment_analyses': sentiment_count,
                    'first_record': first_record.timestamp.isoformat() if first_record else None,
                    'last_record': last_record.timestamp.isoformat() if last_record else None,
                    'data_available': market_count > 0,
                    'summary_generated': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get data summary: {e}")
            return {
                'symbol': symbol,
                'period_days': days,
                'error': str(e),
                'data_available': False
            }
    
    def validate_data_quality(self, 
                            market_data: List[MarketData],
                            min_points: int = 100) -> Dict[str, Any]:
        """
        Validate data quality for backtesting
        
        Args:
            market_data: Market data to validate
            min_points: Minimum required data points
            
        Returns:
            Validation results dictionary
        """
        if not market_data:
            return {
                'valid': False,
                'issues': ['No data provided'],
                'data_points': 0
            }
        
        issues = []
        
        # Check minimum data points
        if len(market_data) < min_points:
            issues.append(f"Insufficient data points: {len(market_data)} < {min_points}")
        
        # Check for gaps in data
        sorted_data = sorted(market_data, key=lambda x: x.timestamp)
        gaps = []
        
        for i in range(1, len(sorted_data)):
            time_diff = sorted_data[i].timestamp - sorted_data[i-1].timestamp
            if time_diff > timedelta(hours=2):  # Gap larger than 2 hours
                gaps.append({
                    'start': sorted_data[i-1].timestamp.isoformat(),
                    'end': sorted_data[i].timestamp.isoformat(),
                    'duration_hours': time_diff.total_seconds() / 3600
                })
        
        if gaps:
            issues.append(f"Found {len(gaps)} data gaps")
        
        # Check for invalid prices
        invalid_prices = [d for d in market_data if d.price <= 0]
        if invalid_prices:
            issues.append(f"Found {len(invalid_prices)} invalid prices")
        
        # Check for invalid volumes
        invalid_volumes = [d for d in market_data if d.volume < 0]
        if invalid_volumes:
            issues.append(f"Found {len(invalid_volumes)} invalid volumes")
        
        # Calculate data statistics
        prices = [d.price for d in market_data if d.price > 0]
        volumes = [d.volume for d in market_data if d.volume >= 0]
        
        price_stats = {
            'min': min(prices) if prices else 0,
            'max': max(prices) if prices else 0,
            'mean': sum(prices) / len(prices) if prices else 0,
            'std': pd.Series(prices).std() if len(prices) > 1 else 0
        }
        
        volume_stats = {
            'min': min(volumes) if volumes else 0,
            'max': max(volumes) if volumes else 0,
            'mean': sum(volumes) / len(volumes) if volumes else 0,
            'std': pd.Series(volumes).std() if len(volumes) > 1 else 0
        }
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'data_points': len(market_data),
            'date_range': {
                'start': sorted_data[0].timestamp.isoformat() if sorted_data else None,
                'end': sorted_data[-1].timestamp.isoformat() if sorted_data else None
            },
            'gaps': gaps,
            'price_stats': price_stats,
            'volume_stats': volume_stats,
            'validation_timestamp': datetime.utcnow().isoformat()
        }
    
    def prepare_backtest_data(self,
                            symbol: str = "BTCUSDT",
                            start_date: datetime = None,
                            end_date: datetime = None,
                            include_sentiment: bool = True) -> Dict[str, Any]:
        """
        Prepare complete dataset for backtesting
        
        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            include_sentiment: Whether to include sentiment data
            
        Returns:
            Complete dataset dictionary
        """
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.utcnow()
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        logger.info(f"Preparing backtest data for {symbol} from {start_date} to {end_date}")
        
        # Get market data
        market_data = self.get_market_data(symbol, start_date, end_date)
        
        # Validate data quality
        validation = self.validate_data_quality(market_data)
        
        # Get sentiment data if requested
        sentiment_data = []
        if include_sentiment:
            sentiment_data = self.get_sentiment_data(start_date, end_date)
        
        # Get news data
        news_data = self.get_news_data(start_date, end_date)
        
        return {
            'symbol': symbol,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'market_data': market_data,
            'sentiment_data': sentiment_data,
            'news_data': news_data,
            'data_validation': validation,
            'prepared_at': datetime.utcnow().isoformat()
        }