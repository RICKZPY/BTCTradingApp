"""
Event Bus
Implements event-driven architecture for system communication
"""
import logging
import asyncio
from typing import Dict, List, Callable, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)


class EventType(Enum):
    """System event types"""
    # Market data events
    PRICE_UPDATE = "price_update"
    MARKET_DATA_RECEIVED = "market_data_received"
    
    # News and analysis events
    NEWS_RECEIVED = "news_received"
    SENTIMENT_ANALYZED = "sentiment_analyzed"
    IMPACT_ASSESSED = "impact_assessed"
    
    # Technical analysis events
    INDICATORS_CALCULATED = "indicators_calculated"
    SIGNAL_GENERATED = "signal_generated"
    
    # Decision engine events
    MARKET_CONDITIONS_ASSESSED = "market_conditions_assessed"
    TRADING_DECISION_MADE = "trading_decision_made"
    
    # Risk management events
    RISK_ASSESSED = "risk_assessed"
    POSITION_SIZED = "position_sized"
    STOP_LOSS_CALCULATED = "stop_loss_calculated"
    PROTECTION_TRIGGERED = "protection_triggered"
    
    # Trading execution events
    ORDER_PLACED = "order_placed"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    POSITION_UPDATED = "position_updated"
    
    # System events
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "system_stopped"
    ERROR_OCCURRED = "error_occurred"
    HEALTH_CHECK = "health_check"
    
    # Alert events
    RISK_ALERT = "risk_alert"
    PERFORMANCE_ALERT = "performance_alert"
    SYSTEM_ALERT = "system_alert"


@dataclass
class Event:
    """System event"""
    event_id: str
    event_type: EventType
    source: str
    data: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None
    priority: int = 0  # Higher number = higher priority
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate event data"""
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        
        if not self.timestamp:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'source': self.source,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'correlation_id': self.correlation_id,
            'priority': self.priority,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary"""
        return cls(
            event_id=data['event_id'],
            event_type=EventType(data['event_type']),
            source=data['source'],
            data=data['data'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            correlation_id=data.get('correlation_id'),
            priority=data.get('priority', 0),
            metadata=data.get('metadata', {})
        )


class EventHandler:
    """Event handler wrapper"""
    
    def __init__(self, handler: Callable[[Event], Any], 
                 event_types: Set[EventType],
                 async_handler: bool = False,
                 priority: int = 0):
        self.handler = handler
        self.event_types = event_types
        self.async_handler = async_handler
        self.priority = priority
        self.handler_id = str(uuid.uuid4())
        self.call_count = 0
        self.error_count = 0
        self.last_called = None
        self.last_error = None
    
    def can_handle(self, event: Event) -> bool:
        """Check if this handler can handle the event"""
        return event.event_type in self.event_types
    
    async def handle(self, event: Event) -> Any:
        """Handle the event"""
        try:
            self.call_count += 1
            self.last_called = datetime.utcnow()
            
            if self.async_handler:
                if asyncio.iscoroutinefunction(self.handler):
                    result = await self.handler(event)
                else:
                    # Run sync handler in thread pool
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, self.handler, event)
            else:
                result = self.handler(event)
            
            return result
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logger.error(f"Event handler {self.handler_id} failed: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics"""
        return {
            'handler_id': self.handler_id,
            'event_types': [et.value for et in self.event_types],
            'priority': self.priority,
            'call_count': self.call_count,
            'error_count': self.error_count,
            'success_rate': (self.call_count - self.error_count) / self.call_count if self.call_count > 0 else 0,
            'last_called': self.last_called.isoformat() if self.last_called else None,
            'last_error': self.last_error
        }


class EventBus:
    """
    Event bus for system-wide event handling
    """
    
    def __init__(self, max_workers: int = 10):
        """
        Initialize event bus
        
        Args:
            max_workers: Maximum number of worker threads
        """
        self.handlers: List[EventHandler] = []
        self.event_history: List[Event] = []
        self.max_history = 1000
        
        # Threading
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.lock = threading.RLock()
        
        # Statistics
        self.total_events = 0
        self.total_handlers_called = 0
        self.total_errors = 0
        
        # Event filtering
        self.event_filters: List[Callable[[Event], bool]] = []
        
        logger.info(f"Event bus initialized with {max_workers} workers")
    
    def subscribe(self, event_types: Set[EventType], handler: Callable[[Event], Any],
                 async_handler: bool = False, priority: int = 0) -> str:
        """
        Subscribe to events
        
        Args:
            event_types: Set of event types to handle
            handler: Event handler function
            async_handler: Whether handler is async
            priority: Handler priority (higher = called first)
            
        Returns:
            Handler ID for unsubscribing
        """
        with self.lock:
            event_handler = EventHandler(handler, event_types, async_handler, priority)
            self.handlers.append(event_handler)
            
            # Sort handlers by priority (highest first)
            self.handlers.sort(key=lambda h: h.priority, reverse=True)
            
            logger.info(f"Subscribed handler {event_handler.handler_id} to {len(event_types)} event types")
            return event_handler.handler_id
    
    def unsubscribe(self, handler_id: str) -> bool:
        """
        Unsubscribe event handler
        
        Args:
            handler_id: Handler ID to remove
            
        Returns:
            True if handler was removed
        """
        with self.lock:
            for i, handler in enumerate(self.handlers):
                if handler.handler_id == handler_id:
                    del self.handlers[i]
                    logger.info(f"Unsubscribed handler {handler_id}")
                    return True
            
            logger.warning(f"Handler {handler_id} not found for unsubscribe")
            return False
    
    def add_filter(self, filter_func: Callable[[Event], bool]):
        """
        Add event filter
        
        Args:
            filter_func: Function that returns True if event should be processed
        """
        self.event_filters.append(filter_func)
        logger.info("Added event filter")
    
    def remove_filter(self, filter_func: Callable[[Event], bool]):
        """Remove event filter"""
        if filter_func in self.event_filters:
            self.event_filters.remove(filter_func)
            logger.info("Removed event filter")
    
    async def publish(self, event: Event) -> List[Any]:
        """
        Publish event to all subscribers
        
        Args:
            event: Event to publish
            
        Returns:
            List of handler results
        """
        # Apply filters
        for filter_func in self.event_filters:
            try:
                if not filter_func(event):
                    logger.debug(f"Event {event.event_id} filtered out")
                    return []
            except Exception as e:
                logger.error(f"Event filter error: {e}")
        
        # Add to history
        with self.lock:
            self.event_history.append(event)
            if len(self.event_history) > self.max_history:
                self.event_history = self.event_history[-self.max_history:]
            
            self.total_events += 1
        
        # Find matching handlers
        matching_handlers = []
        with self.lock:
            for handler in self.handlers:
                if handler.can_handle(event):
                    matching_handlers.append(handler)
        
        if not matching_handlers:
            logger.debug(f"No handlers for event {event.event_type.value}")
            return []
        
        # Execute handlers
        results = []
        for handler in matching_handlers:
            try:
                with self.lock:
                    self.total_handlers_called += 1
                
                result = await handler.handle(event)
                results.append(result)
                
            except Exception as e:
                with self.lock:
                    self.total_errors += 1
                
                logger.error(f"Handler {handler.handler_id} failed for event {event.event_id}: {e}")
                # Continue with other handlers
        
        logger.debug(f"Published event {event.event_type.value} to {len(matching_handlers)} handlers")
        return results
    
    def publish_sync(self, event: Event) -> List[Any]:
        """
        Publish event synchronously
        
        Args:
            event: Event to publish
            
        Returns:
            List of handler results
        """
        # Check if we're already in an async context
        try:
            loop = asyncio.get_running_loop()
            # If we're in an async context, we can't use run_until_complete
            # Instead, create a task and wait for it
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.publish(event))
                return future.result()
        except RuntimeError:
            # No running loop, safe to create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.publish(event))
            finally:
                loop.close()
    
    def create_event(self, event_type: EventType, source: str, data: Dict[str, Any],
                    correlation_id: Optional[str] = None, priority: int = 0) -> Event:
        """
        Create a new event
        
        Args:
            event_type: Type of event
            source: Source component
            data: Event data
            correlation_id: Optional correlation ID
            priority: Event priority
            
        Returns:
            Created event
        """
        return Event(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            source=source,
            data=data,
            timestamp=datetime.utcnow(),
            correlation_id=correlation_id,
            priority=priority
        )
    
    async def publish_new(self, event_type: EventType, source: str, data: Dict[str, Any],
                         correlation_id: Optional[str] = None, priority: int = 0) -> List[Any]:
        """
        Create and publish new event
        
        Args:
            event_type: Type of event
            source: Source component
            data: Event data
            correlation_id: Optional correlation ID
            priority: Event priority
            
        Returns:
            List of handler results
        """
        event = self.create_event(event_type, source, data, correlation_id, priority)
        return await self.publish(event)
    
    def get_event_history(self, event_type: Optional[EventType] = None, 
                         limit: int = 100) -> List[Event]:
        """
        Get event history
        
        Args:
            event_type: Filter by event type (optional)
            limit: Maximum number of events to return
            
        Returns:
            List of historical events
        """
        with self.lock:
            events = self.event_history
            
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            
            return events[-limit:] if limit > 0 else events
    
    def get_handler_stats(self) -> List[Dict[str, Any]]:
        """
        Get statistics for all handlers
        
        Returns:
            List of handler statistics
        """
        with self.lock:
            return [handler.get_stats() for handler in self.handlers]
    
    def get_bus_stats(self) -> Dict[str, Any]:
        """
        Get event bus statistics
        
        Returns:
            Bus statistics
        """
        with self.lock:
            return {
                'total_events': self.total_events,
                'total_handlers': len(self.handlers),
                'total_handlers_called': self.total_handlers_called,
                'total_errors': self.total_errors,
                'success_rate': (self.total_handlers_called - self.total_errors) / self.total_handlers_called if self.total_handlers_called > 0 else 0,
                'event_history_size': len(self.event_history),
                'active_filters': len(self.event_filters),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def clear_history(self):
        """Clear event history"""
        with self.lock:
            self.event_history.clear()
            logger.info("Event history cleared")
    
    def shutdown(self):
        """Shutdown event bus"""
        logger.info("Shutting down event bus")
        
        # Clear handlers
        with self.lock:
            self.handlers.clear()
            self.event_filters.clear()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("Event bus shutdown complete")