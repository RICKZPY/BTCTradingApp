"""
Data Queue Manager for handling collected data

Implements the data queue processing mechanism as specified in requirements 1.1 and 1.2.
Manages the flow of collected data to analysis modules.
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from dataclasses import asdict
import structlog

from database.redis_client import RedisClient
from core.data_models import NewsItem, MarketData


logger = structlog.get_logger(__name__)


class DataQueueManager:
    """
    Manages data queues for different types of collected data
    
    Routes collected data to appropriate processing queues and handles
    queue operations with Redis backend.
    """
    
    # Queue names for different data types
    NEWS_QUEUE = "news_data_queue"
    MARKET_QUEUE = "market_data_queue"
    SOCIAL_QUEUE = "social_data_queue"
    ECONOMIC_QUEUE = "economic_data_queue"
    
    def __init__(self, redis_client: Optional[RedisClient] = None):
        self.redis_client = redis_client or RedisClient()
        self.logger = structlog.get_logger("queue_manager")
        self.processors: Dict[str, Callable] = {}
        self.is_processing = False
        self._stop_event = asyncio.Event()
        
    async def enqueue_data(self, source: str, data: List[Any]):
        """
        Enqueue collected data to appropriate queue
        
        Args:
            source: Data source name (collector name)
            data: List of data items to enqueue
        """
        if not data:
            return
            
        try:
            # Determine queue based on data type
            queue_name = self._get_queue_for_source(source)
            
            # Serialize and enqueue each item
            for item in data:
                serialized_item = self._serialize_data_item(item, source)
                await self.redis_client.lpush(queue_name, serialized_item)
            
            self.logger.info(
                "Data enqueued successfully",
                source=source,
                queue=queue_name,
                items=len(data)
            )
            
        except Exception as e:
            self.logger.error(
                "Error enqueuing data",
                source=source,
                error=str(e),
                items=len(data)
            )
            raise
    
    async def dequeue_data(self, queue_name: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """
        Dequeue data from specified queue
        
        Args:
            queue_name: Name of the queue to dequeue from
            timeout: Timeout in seconds for blocking pop
            
        Returns:
            Deserialized data item or None if timeout
        """
        try:
            result = await self.redis_client.brpop(queue_name, timeout=timeout)
            
            if result:
                _, serialized_data = result
                return json.loads(serialized_data)
            
            return None
            
        except Exception as e:
            self.logger.error(
                "Error dequeuing data",
                queue=queue_name,
                error=str(e)
            )
            return None
    
    async def get_queue_length(self, queue_name: str) -> int:
        """Get the current length of a queue"""
        try:
            return await self.redis_client.llen(queue_name)
        except Exception as e:
            self.logger.error(
                "Error getting queue length",
                queue=queue_name,
                error=str(e)
            )
            return 0
    
    async def clear_queue(self, queue_name: str):
        """Clear all items from a queue"""
        try:
            await self.redis_client.delete(queue_name)
            self.logger.info("Queue cleared", queue=queue_name)
        except Exception as e:
            self.logger.error(
                "Error clearing queue",
                queue=queue_name,
                error=str(e)
            )
    
    def register_processor(self, queue_name: str, processor_func: Callable):
        """
        Register a processor function for a specific queue
        
        Args:
            queue_name: Name of the queue to process
            processor_func: Async function to process queue items
        """
        self.processors[queue_name] = processor_func
        self.logger.info(
            "Processor registered",
            queue=queue_name,
            processor=processor_func.__name__
        )
    
    async def start_processing(self):
        """Start processing all registered queues"""
        if self.is_processing:
            self.logger.warning("Queue processing is already running")
            return
            
        self.is_processing = True
        self._stop_event.clear()
        
        self.logger.info("Starting queue processing")
        
        # Start processing tasks for each registered processor
        tasks = []
        for queue_name, processor in self.processors.items():
            task = asyncio.create_task(
                self._process_queue(queue_name, processor)
            )
            tasks.append(task)
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error("Error in queue processing", error=str(e))
        finally:
            self.is_processing = False
            self.logger.info("Queue processing stopped")
    
    async def stop_processing(self):
        """Stop queue processing"""
        if not self.is_processing:
            return
            
        self.logger.info("Stopping queue processing")
        self._stop_event.set()
    
    async def _process_queue(self, queue_name: str, processor_func: Callable):
        """Process items from a specific queue"""
        self.logger.info("Starting queue processor", queue=queue_name)
        
        while not self._stop_event.is_set():
            try:
                # Dequeue item with timeout
                item = await self.dequeue_data(queue_name, timeout=5)
                
                if item:
                    # Process the item
                    await processor_func(item)
                    
                    self.logger.debug(
                        "Item processed",
                        queue=queue_name,
                        item_id=item.get('id', 'unknown')
                    )
                
            except Exception as e:
                self.logger.error(
                    "Error processing queue item",
                    queue=queue_name,
                    error=str(e)
                )
                # Continue processing other items
                await asyncio.sleep(1)
        
        self.logger.info("Queue processor stopped", queue=queue_name)
    
    def _get_queue_for_source(self, source: str) -> str:
        """Determine appropriate queue based on data source"""
        source_lower = source.lower()
        
        if any(keyword in source_lower for keyword in ['news', 'article', 'coindesk', 'cointelegraph']):
            return self.NEWS_QUEUE
        elif any(keyword in source_lower for keyword in ['twitter', 'social', 'tweet']):
            return self.SOCIAL_QUEUE
        elif any(keyword in source_lower for keyword in ['market', 'price', 'binance', 'trading']):
            return self.MARKET_QUEUE
        elif any(keyword in source_lower for keyword in ['economic', 'macro', 'fred', 'indicator']):
            return self.ECONOMIC_QUEUE
        else:
            # Default to news queue for unknown sources
            return self.NEWS_QUEUE
    
    def _serialize_data_item(self, item: Any, source: str) -> str:
        """Serialize data item for queue storage"""
        try:
            # Add metadata
            queue_item = {
                'source': source,
                'timestamp': datetime.now().isoformat(),
                'data_type': type(item).__name__,
                'data': item.to_dict() if hasattr(item, 'to_dict') else asdict(item)
            }
            
            return json.dumps(queue_item, default=str)
            
        except Exception as e:
            self.logger.error(
                "Error serializing data item",
                source=source,
                item_type=type(item).__name__,
                error=str(e)
            )
            raise
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get statistics for all queues"""
        stats = {}
        
        queues = [
            self.NEWS_QUEUE,
            self.MARKET_QUEUE,
            self.SOCIAL_QUEUE,
            self.ECONOMIC_QUEUE
        ]
        
        for queue_name in queues:
            stats[queue_name] = {
                'length': await self.get_queue_length(queue_name),
                'has_processor': queue_name in self.processors
            }
        
        stats['processing_status'] = {
            'is_processing': self.is_processing,
            'registered_processors': len(self.processors)
        }
        
        return stats
    
    async def peek_queue(self, queue_name: str, count: int = 5) -> List[Dict[str, Any]]:
        """
        Peek at items in queue without removing them
        
        Args:
            queue_name: Name of the queue to peek
            count: Number of items to peek at
            
        Returns:
            List of queue items (newest first)
        """
        try:
            items = await self.redis_client.lrange(queue_name, 0, count - 1)
            return [json.loads(item) for item in items]
        except Exception as e:
            self.logger.error(
                "Error peeking queue",
                queue=queue_name,
                error=str(e)
            )
            return []