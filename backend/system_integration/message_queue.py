"""
Message Queue System
Handles asynchronous message processing and task distribution
"""
import logging
import asyncio
import json
import redis
from typing import Dict, List, Callable, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import pickle
from concurrent.futures import ThreadPoolExecutor
import threading

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class MessageStatus(Enum):
    """Message processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


@dataclass
class Message:
    """Queue message"""
    message_id: str
    queue_name: str
    payload: Dict[str, Any]
    priority: MessagePriority
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 300
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate message data"""
        if not self.message_id:
            self.message_id = str(uuid.uuid4())
        
        if not self.created_at:
            self.created_at = datetime.utcnow()
        
        if self.scheduled_at is None:
            self.scheduled_at = self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization"""
        return {
            'message_id': self.message_id,
            'queue_name': self.queue_name,
            'payload': self.payload,
            'priority': self.priority.value,
            'created_at': self.created_at.isoformat(),
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'timeout_seconds': self.timeout_seconds,
            'correlation_id': self.correlation_id,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        return cls(
            message_id=data['message_id'],
            queue_name=data['queue_name'],
            payload=data['payload'],
            priority=MessagePriority(data['priority']),
            created_at=datetime.fromisoformat(data['created_at']),
            scheduled_at=datetime.fromisoformat(data['scheduled_at']) if data.get('scheduled_at') else None,
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3),
            timeout_seconds=data.get('timeout_seconds', 300),
            correlation_id=data.get('correlation_id'),
            metadata=data.get('metadata', {})
        )
    
    def should_retry(self) -> bool:
        """Check if message should be retried"""
        return self.retry_count < self.max_retries
    
    def increment_retry(self):
        """Increment retry count"""
        self.retry_count += 1
    
    def is_expired(self) -> bool:
        """Check if message has expired"""
        if not self.scheduled_at:
            return False
        
        expiry_time = self.scheduled_at + timedelta(seconds=self.timeout_seconds)
        return datetime.utcnow() > expiry_time


@dataclass
class ProcessingResult:
    """Message processing result"""
    message_id: str
    status: MessageStatus
    result: Any = None
    error: Optional[str] = None
    processing_time: float = 0.0
    processed_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'message_id': self.message_id,
            'status': self.status.value,
            'result': self.result,
            'error': self.error,
            'processing_time': self.processing_time,
            'processed_at': self.processed_at.isoformat()
        }


class MessageProcessor:
    """Base message processor"""
    
    def __init__(self, processor_id: str):
        self.processor_id = processor_id
        self.processed_count = 0
        self.error_count = 0
        self.total_processing_time = 0.0
        self.last_processed = None
    
    async def process(self, message: Message) -> ProcessingResult:
        """
        Process a message (to be implemented by subclasses)
        
        Args:
            message: Message to process
            
        Returns:
            Processing result
        """
        raise NotImplementedError("Subclasses must implement process method")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics"""
        return {
            'processor_id': self.processor_id,
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'success_rate': (self.processed_count - self.error_count) / self.processed_count if self.processed_count > 0 else 0,
            'average_processing_time': self.total_processing_time / self.processed_count if self.processed_count > 0 else 0,
            'last_processed': self.last_processed.isoformat() if self.last_processed else None
        }


class MessageQueue:
    """
    Redis-based message queue system
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize message queue
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url or settings.redis.redis_url
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        
        # Queue configuration
        self.default_queue = "default"
        self.dead_letter_queue = "dead_letter"
        self.processing_queue = "processing"
        
        # Processors
        self.processors: Dict[str, MessageProcessor] = {}
        
        # Worker management
        self.workers: List[asyncio.Task] = []
        self.worker_count = 5
        self.running = False
        
        # Statistics
        self.total_messages = 0
        self.total_processed = 0
        self.total_failed = 0
        
        logger.info(f"Message queue initialized with Redis: {self.redis_url}")
    
    def register_processor(self, queue_name: str, processor: MessageProcessor):
        """
        Register message processor for a queue
        
        Args:
            queue_name: Queue name
            processor: Message processor
        """
        self.processors[queue_name] = processor
        logger.info(f"Registered processor {processor.processor_id} for queue {queue_name}")
    
    def unregister_processor(self, queue_name: str):
        """
        Unregister message processor
        
        Args:
            queue_name: Queue name
        """
        if queue_name in self.processors:
            del self.processors[queue_name]
            logger.info(f"Unregistered processor for queue {queue_name}")
    
    async def enqueue(self, message: Message) -> bool:
        """
        Add message to queue
        
        Args:
            message: Message to enqueue
            
        Returns:
            True if message was enqueued successfully
        """
        try:
            # Serialize message
            message_data = json.dumps(message.to_dict())
            
            # Add to priority queue (using sorted set with priority as score)
            queue_key = f"queue:{message.queue_name}"
            priority_score = message.priority.value * 1000000 + int(message.scheduled_at.timestamp())
            
            # Add message
            self.redis_client.zadd(queue_key, {message_data: priority_score})
            
            # Update statistics
            self.total_messages += 1
            
            logger.debug(f"Enqueued message {message.message_id} to {message.queue_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue message {message.message_id}: {e}")
            return False
    
    async def enqueue_simple(self, queue_name: str, payload: Dict[str, Any],
                           priority: MessagePriority = MessagePriority.NORMAL,
                           delay_seconds: int = 0,
                           correlation_id: Optional[str] = None) -> str:
        """
        Enqueue a simple message
        
        Args:
            queue_name: Queue name
            payload: Message payload
            priority: Message priority
            delay_seconds: Delay before processing
            correlation_id: Optional correlation ID
            
        Returns:
            Message ID
        """
        scheduled_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
        
        message = Message(
            message_id=str(uuid.uuid4()),
            queue_name=queue_name,
            payload=payload,
            priority=priority,
            created_at=datetime.utcnow(),
            scheduled_at=scheduled_at,
            correlation_id=correlation_id
        )
        
        await self.enqueue(message)
        return message.message_id
    
    async def dequeue(self, queue_name: str, timeout: int = 10) -> Optional[Message]:
        """
        Get next message from queue
        
        Args:
            queue_name: Queue name
            timeout: Timeout in seconds
            
        Returns:
            Next message or None if timeout
        """
        try:
            queue_key = f"queue:{queue_name}"
            
            # Get highest priority message that's ready to process
            current_time = datetime.utcnow().timestamp()
            max_score = MessagePriority.CRITICAL.value * 1000000 + current_time
            
            # Get messages with ZRANGEBYSCORE
            messages = self.redis_client.zrangebyscore(
                queue_key, 0, max_score, start=0, num=1, withscores=True
            )
            
            if not messages:
                return None
            
            message_data, score = messages[0]
            
            # Remove from queue
            self.redis_client.zrem(queue_key, message_data)
            
            # Parse message
            message_dict = json.loads(message_data)
            message = Message.from_dict(message_dict)
            
            # Move to processing queue
            processing_key = f"processing:{queue_name}"
            self.redis_client.hset(processing_key, message.message_id, message_data)
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to dequeue from {queue_name}: {e}")
            return None
    
    async def complete_message(self, message: Message, result: ProcessingResult):
        """
        Mark message as completed
        
        Args:
            message: Processed message
            result: Processing result
        """
        try:
            # Remove from processing queue
            processing_key = f"processing:{message.queue_name}"
            self.redis_client.hdel(processing_key, message.message_id)
            
            # Store result
            result_key = f"results:{message.message_id}"
            result_data = json.dumps(result.to_dict())
            self.redis_client.setex(result_key, 3600, result_data)  # Keep for 1 hour
            
            # Update statistics
            if result.status == MessageStatus.COMPLETED:
                self.total_processed += 1
            else:
                self.total_failed += 1
            
            logger.debug(f"Completed message {message.message_id} with status {result.status.value}")
            
        except Exception as e:
            logger.error(f"Failed to complete message {message.message_id}: {e}")
    
    async def retry_message(self, message: Message, error: str):
        """
        Retry a failed message
        
        Args:
            message: Failed message
            error: Error description
        """
        try:
            message.increment_retry()
            
            if message.should_retry():
                # Calculate exponential backoff delay
                delay_seconds = min(300, 2 ** message.retry_count)  # Max 5 minutes
                message.scheduled_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
                
                # Re-enqueue
                await self.enqueue(message)
                
                logger.info(f"Retrying message {message.message_id} (attempt {message.retry_count})")
            else:
                # Move to dead letter queue
                await self._move_to_dead_letter(message, error)
                
                logger.warning(f"Message {message.message_id} moved to dead letter queue after {message.retry_count} retries")
            
            # Remove from processing queue
            processing_key = f"processing:{message.queue_name}"
            self.redis_client.hdel(processing_key, message.message_id)
            
        except Exception as e:
            logger.error(f"Failed to retry message {message.message_id}: {e}")
    
    async def _move_to_dead_letter(self, message: Message, error: str):
        """Move message to dead letter queue"""
        try:
            dead_letter_data = {
                'message': message.to_dict(),
                'error': error,
                'moved_at': datetime.utcnow().isoformat()
            }
            
            dead_letter_key = f"dead_letter:{message.queue_name}"
            self.redis_client.lpush(dead_letter_key, json.dumps(dead_letter_data))
            
        except Exception as e:
            logger.error(f"Failed to move message to dead letter queue: {e}")
    
    async def process_message(self, message: Message) -> ProcessingResult:
        """
        Process a message using registered processor
        
        Args:
            message: Message to process
            
        Returns:
            Processing result
        """
        start_time = datetime.utcnow()
        
        try:
            # Check if message is expired
            if message.is_expired():
                return ProcessingResult(
                    message_id=message.message_id,
                    status=MessageStatus.FAILED,
                    error="Message expired",
                    processing_time=0.0
                )
            
            # Get processor
            processor = self.processors.get(message.queue_name)
            if not processor:
                return ProcessingResult(
                    message_id=message.message_id,
                    status=MessageStatus.FAILED,
                    error=f"No processor registered for queue {message.queue_name}",
                    processing_time=0.0
                )
            
            # Process message
            result = await processor.process(message)
            
            # Update processor stats
            processor.processed_count += 1
            processor.last_processed = datetime.utcnow()
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            processor.total_processing_time += processing_time
            result.processing_time = processing_time
            
            return result
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update processor error stats
            if message.queue_name in self.processors:
                self.processors[message.queue_name].error_count += 1
            
            logger.error(f"Failed to process message {message.message_id}: {e}")
            
            return ProcessingResult(
                message_id=message.message_id,
                status=MessageStatus.FAILED,
                error=str(e),
                processing_time=processing_time
            )
    
    async def worker(self, worker_id: int):
        """
        Message processing worker
        
        Args:
            worker_id: Worker identifier
        """
        logger.info(f"Worker {worker_id} started")
        
        while self.running:
            try:
                # Check all queues for messages
                processed_any = False
                
                for queue_name in self.processors.keys():
                    message = await self.dequeue(queue_name, timeout=1)
                    
                    if message:
                        processed_any = True
                        
                        # Process message
                        result = await self.process_message(message)
                        
                        # Handle result
                        if result.status == MessageStatus.COMPLETED:
                            await self.complete_message(message, result)
                        elif result.status == MessageStatus.FAILED:
                            await self.retry_message(message, result.error or "Unknown error")
                
                # If no messages processed, wait a bit
                if not processed_any:
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def start_workers(self, worker_count: Optional[int] = None):
        """
        Start message processing workers
        
        Args:
            worker_count: Number of workers to start
        """
        if self.running:
            logger.warning("Workers already running")
            return
        
        self.worker_count = worker_count or self.worker_count
        self.running = True
        
        # Start workers
        for i in range(self.worker_count):
            worker_task = asyncio.create_task(self.worker(i))
            self.workers.append(worker_task)
        
        logger.info(f"Started {self.worker_count} message queue workers")
    
    async def stop_workers(self):
        """Stop message processing workers"""
        if not self.running:
            return
        
        self.running = False
        
        # Wait for workers to finish
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
            self.workers.clear()
        
        logger.info("Stopped message queue workers")
    
    def get_queue_stats(self, queue_name: str) -> Dict[str, Any]:
        """
        Get queue statistics
        
        Args:
            queue_name: Queue name
            
        Returns:
            Queue statistics
        """
        try:
            queue_key = f"queue:{queue_name}"
            processing_key = f"processing:{queue_name}"
            dead_letter_key = f"dead_letter:{queue_name}"
            
            pending_count = self.redis_client.zcard(queue_key)
            processing_count = self.redis_client.hlen(processing_key)
            dead_letter_count = self.redis_client.llen(dead_letter_key)
            
            return {
                'queue_name': queue_name,
                'pending_messages': pending_count,
                'processing_messages': processing_count,
                'dead_letter_messages': dead_letter_count,
                'has_processor': queue_name in self.processors,
                'processor_stats': self.processors[queue_name].get_stats() if queue_name in self.processors else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue stats for {queue_name}: {e}")
            return {'error': str(e)}
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get system-wide message queue statistics
        
        Returns:
            System statistics
        """
        return {
            'total_messages': self.total_messages,
            'total_processed': self.total_processed,
            'total_failed': self.total_failed,
            'success_rate': self.total_processed / (self.total_processed + self.total_failed) if (self.total_processed + self.total_failed) > 0 else 0,
            'registered_processors': len(self.processors),
            'active_workers': len(self.workers),
            'worker_count': self.worker_count,
            'running': self.running,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def cleanup_old_results(self, hours: int = 24):
        """
        Clean up old processing results
        
        Args:
            hours: Age threshold in hours
        """
        try:
            # This would be implemented with a Redis script or background task
            # For now, we rely on TTL set in complete_message
            logger.info(f"Cleanup of results older than {hours} hours completed")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old results: {e}")
    
    def close(self):
        """Close Redis connection"""
        if self.redis_client:
            self.redis_client.close()
            logger.info("Message queue Redis connection closed")