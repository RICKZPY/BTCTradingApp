"""
Data Collection Manager

Integrates all data collectors and provides a unified interface for data collection.
Implements the complete data collection system as specified in requirements 1.1-1.5.
"""

import asyncio
from typing import Dict, List, Any, Optional
import structlog

from data_collection.base import DataCollectionScheduler
from data_collection.queue_manager import DataQueueManager
from data_collection.adapters.news_collector import NewsDataCollector
from data_collection.adapters.twitter_collector import TwitterDataCollector
from data_collection.adapters.market_collector import MarketDataCollector
from data_collection.adapters.economic_collector import EconomicDataCollector
from database.redis_client import RedisClient
from config import settings


logger = structlog.get_logger(__name__)


class DataCollectionManager:
    """
    Main manager for all data collection activities
    
    Coordinates multiple data collectors and manages the overall data collection process
    """
    
    def __init__(self, redis_client: Optional[RedisClient] = None):
        self.redis_client = redis_client or RedisClient()
        self.queue_manager = DataQueueManager(self.redis_client)
        self.scheduler = DataCollectionScheduler(self.queue_manager)
        self.collectors: Dict[str, Any] = {}
        self.logger = structlog.get_logger("data_collection_manager")
        self.is_running = False
        
    async def initialize(self):
        """Initialize all data collectors and register them with the scheduler"""
        try:
            self.logger.info("Initializing data collection manager")
            
            # Initialize news collector
            news_collector = NewsDataCollector(
                max_articles_per_source=20
            )
            self.collectors['news'] = news_collector
            self.scheduler.register_collector(
                news_collector,
                interval_seconds=settings.app.news_collection_interval
            )
            
            # Initialize Twitter collector (if configured)
            if settings.api.twitter_bearer_token:
                twitter_collector = TwitterDataCollector(max_tweets=50)
                self.collectors['twitter'] = twitter_collector
                self.scheduler.register_collector(
                    twitter_collector,
                    interval_seconds=600  # 10 minutes
                )
            else:
                self.logger.warning("Twitter API not configured, skipping Twitter collector")
            
            # Initialize market data collector
            market_collector = MarketDataCollector()
            self.collectors['market'] = market_collector
            self.scheduler.register_collector(
                market_collector,
                interval_seconds=settings.app.market_data_interval
            )
            
            # Initialize economic data collector
            economic_collector = EconomicDataCollector(lookback_days=1)
            self.collectors['economic'] = economic_collector
            self.scheduler.register_collector(
                economic_collector,
                interval_seconds=3600  # 1 hour
            )
            
            self.logger.info(
                "Data collection manager initialized",
                collectors=len(self.collectors)
            )
            
        except Exception as e:
            self.logger.error("Error initializing data collection manager", error=str(e))
            raise
    
    async def start(self):
        """Start the data collection system"""
        if self.is_running:
            self.logger.warning("Data collection manager is already running")
            return
        
        try:
            self.logger.info("Starting data collection system")
            
            # Start queue processing
            queue_task = asyncio.create_task(self.queue_manager.start_processing())
            
            # Start scheduler
            scheduler_task = asyncio.create_task(self.scheduler.start())
            
            self.is_running = True
            
            # Wait for both tasks
            await asyncio.gather(queue_task, scheduler_task)
            
        except Exception as e:
            self.logger.error("Error starting data collection system", error=str(e))
            self.is_running = False
            raise
        finally:
            self.is_running = False
    
    async def stop(self):
        """Stop the data collection system"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping data collection system")
        
        try:
            # Stop scheduler
            await self.scheduler.stop()
            
            # Stop queue processing
            await self.queue_manager.stop_processing()
            
            # Close all collectors
            for name, collector in self.collectors.items():
                if hasattr(collector, 'close'):
                    await collector.close()
                    self.logger.info("Collector closed", collector=name)
            
            self.is_running = False
            self.logger.info("Data collection system stopped")
            
        except Exception as e:
            self.logger.error("Error stopping data collection system", error=str(e))
    
    async def force_collect_all(self) -> Dict[str, int]:
        """Force immediate collection from all collectors"""
        results = {}
        
        for name, collector in self.collectors.items():
            try:
                self.logger.info("Force collecting data", collector=name)
                data = await collector.safe_collect()
                
                if data and self.queue_manager:
                    await self.queue_manager.enqueue_data(name, data)
                
                results[name] = len(data)
                
                self.logger.info(
                    "Force collection completed",
                    collector=name,
                    items=len(data)
                )
                
            except Exception as e:
                self.logger.error(
                    "Error in force collection",
                    collector=name,
                    error=str(e)
                )
                results[name] = 0
        
        return results
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # Get scheduler status
            scheduler_status = self.scheduler.get_status()
            
            # Get queue statistics
            queue_stats = await self.queue_manager.get_queue_stats()
            
            # Get collector status
            collector_status = {}
            for name, collector in self.collectors.items():
                collector_status[name] = {
                    'is_active': collector.is_active,
                    'error_count': collector.error_count,
                    'max_errors': collector.max_errors
                }
            
            return {
                'system_running': self.is_running,
                'scheduler': scheduler_status,
                'queues': queue_stats,
                'collectors': collector_status,
                'timestamp': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            self.logger.error("Error getting system status", error=str(e))
            return {'error': str(e)}
    
    def register_queue_processor(self, queue_name: str, processor_func):
        """Register a processor function for a specific queue"""
        self.queue_manager.register_processor(queue_name, processor_func)
        self.logger.info(
            "Queue processor registered",
            queue=queue_name,
            processor=processor_func.__name__
        )
    
    async def get_recent_data(self, queue_name: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent data from a specific queue"""
        return await self.queue_manager.peek_queue(queue_name, count)
    
    async def clear_queue(self, queue_name: str):
        """Clear all data from a specific queue"""
        await self.queue_manager.clear_queue(queue_name)
        self.logger.info("Queue cleared", queue=queue_name)
    
    async def test_collectors(self) -> Dict[str, bool]:
        """Test connection for all collectors"""
        results = {}
        
        for name, collector in self.collectors.items():
            try:
                self.logger.info("Testing collector connection", collector=name)
                is_valid = await collector.validate_connection()
                results[name] = is_valid
                
                if is_valid:
                    self.logger.info("Collector connection test passed", collector=name)
                else:
                    self.logger.warning("Collector connection test failed", collector=name)
                    
            except Exception as e:
                self.logger.error(
                    "Error testing collector connection",
                    collector=name,
                    error=str(e)
                )
                results[name] = False
        
        return results