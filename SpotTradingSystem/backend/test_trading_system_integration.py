#!/usr/bin/env python3
"""
Test complete trading system integration framework
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from system_integration.event_bus import EventBus, Event, EventType
from system_integration.message_queue import MessageQueue, Message, MessagePriority, MessageProcessor, ProcessingResult, MessageStatus
from system_integration.task_scheduler import TaskScheduler
from system_integration.system_coordinator import SystemCoordinator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockTradingComponent:
    """Mock trading component for testing"""
    
    def __init__(self, name: str):
        self.name = name
        self.initialized = True
    
    async def health_check(self):
        """Mock health check"""
        return {'healthy': True, 'status': 'running'}


class TradingEventProcessor(MessageProcessor):
    """Test trading event processor"""
    
    def __init__(self, processor_id: str, event_bus: EventBus):
        super().__init__(processor_id)
        self.event_bus = event_bus
        self.processed_messages = []
    
    async def process(self, message: Message) -> ProcessingResult:
        """Process trading message"""
        try:
            self.processed_messages.append(message)
            payload = message.payload
            
            # Simulate different types of processing
            if payload.get('type') == 'market_data':
                # Publish price update event
                await self.event_bus.publish_new(
                    EventType.PRICE_UPDATE,
                    self.processor_id,
                    {
                        'symbol': 'BTCUSDT',
                        'price': 45000.0,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                
            elif payload.get('type') == 'analysis':
                # Publish analysis result
                await self.event_bus.publish_new(
                    EventType.SIGNAL_GENERATED,
                    self.processor_id,
                    {
                        'signal': 'BUY',
                        'confidence': 0.8,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                
            elif payload.get('type') == 'decision':
                # Publish trading decision
                await self.event_bus.publish_new(
                    EventType.TRADING_DECISION_MADE,
                    self.processor_id,
                    {
                        'action': 'BUY',
                        'quantity': 0.1,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
            
            return ProcessingResult(
                message_id=message.message_id,
                status=MessageStatus.COMPLETED,
                result=f"Processed {payload.get('type', 'unknown')}",
                processing_time=0.1
            )
            
        except Exception as e:
            return ProcessingResult(
                message_id=message.message_id,
                status=MessageStatus.FAILED,
                error=str(e),
                processing_time=0.1
            )


class TradingSystemIntegrationFramework:
    """
    Trading system integration framework for testing
    """
    
    def __init__(self):
        """Initialize framework"""
        self.coordinator = SystemCoordinator()
        self.event_bus = self.coordinator.event_bus
        self.message_queue = self.coordinator.message_queue
        self.task_scheduler = self.coordinator.task_scheduler
        
        # Mock trading components
        self.components = {
            'data_collector': MockTradingComponent('data_collector'),
            'news_analyzer': MockTradingComponent('news_analyzer'),
            'technical_analyzer': MockTradingComponent('technical_analyzer'),
            'decision_engine': MockTradingComponent('decision_engine'),
            'risk_manager': MockTradingComponent('risk_manager'),
            'order_manager': MockTradingComponent('order_manager'),
            'position_manager': MockTradingComponent('position_manager')
        }
        
        # Event tracking
        self.events_received = []
        self.trading_flow_events = []
        
        logger.info("Trading system integration framework initialized")
    
    async def initialize_components(self):
        """Initialize all components"""
        # Register components with coordinator
        for name, component in self.components.items():
            self.coordinator.register_component(name, component)
        
        # Create and register message processors
        processors = {
            'data_collection': TradingEventProcessor('data_collection', self.event_bus),
            'analysis': TradingEventProcessor('analysis', self.event_bus),
            'decision': TradingEventProcessor('decision', self.event_bus),
            'execution': TradingEventProcessor('execution', self.event_bus)
        }
        
        for queue_name, processor in processors.items():
            self.message_queue.register_processor(queue_name, processor)
        
        logger.info("All components initialized")
    
    def setup_event_handlers(self):
        """Setup event handlers"""
        # Track all trading events
        self.event_bus.subscribe(
            {
                EventType.PRICE_UPDATE,
                EventType.NEWS_RECEIVED,
                EventType.SENTIMENT_ANALYZED,
                EventType.SIGNAL_GENERATED,
                EventType.TRADING_DECISION_MADE,
                EventType.ORDER_FILLED,
                EventType.POSITION_UPDATED
            },
            self._track_events
        )
        
        # Setup trading flow handlers
        self.event_bus.subscribe(
            {EventType.PRICE_UPDATE},
            self._handle_price_update,
            async_handler=True
        )
        
        self.event_bus.subscribe(
            {EventType.SIGNAL_GENERATED},
            self._handle_signal_generated,
            async_handler=True
        )
        
        self.event_bus.subscribe(
            {EventType.TRADING_DECISION_MADE},
            self._handle_trading_decision,
            async_handler=True
        )
    
    def _track_events(self, event: Event):
        """Track all events"""
        self.events_received.append(event)
        self.trading_flow_events.append({
            'type': event.event_type.value,
            'source': event.source,
            'timestamp': event.timestamp
        })
    
    async def _handle_price_update(self, event: Event):
        """Handle price updates"""
        # Trigger analysis
        await self.message_queue.enqueue_simple(
            "analysis",
            {'type': 'analysis', 'price_data': event.data},
            MessagePriority.NORMAL
        )
    
    async def _handle_signal_generated(self, event: Event):
        """Handle signal generation"""
        # Trigger decision making
        await self.message_queue.enqueue_simple(
            "decision",
            {'type': 'decision', 'signal_data': event.data},
            MessagePriority.HIGH
        )
    
    async def _handle_trading_decision(self, event: Event):
        """Handle trading decisions"""
        # Trigger execution
        await self.message_queue.enqueue_simple(
            "execution",
            {'type': 'execution', 'decision_data': event.data},
            MessagePriority.CRITICAL
        )
    
    def setup_scheduled_tasks(self):
        """Setup scheduled tasks"""
        # Market data collection task
        self.task_scheduler.schedule_interval(
            name="market_data_collection",
            task_func=self._collect_market_data,
            interval_seconds=10,
            description="Collect market data"
        )
        
        # Portfolio monitoring task
        self.task_scheduler.schedule_interval(
            name="portfolio_monitoring",
            task_func=self._monitor_portfolio,
            interval_seconds=30,
            description="Monitor portfolio"
        )
    
    async def _collect_market_data(self):
        """Scheduled market data collection"""
        await self.message_queue.enqueue_simple(
            "data_collection",
            {'type': 'market_data'},
            MessagePriority.NORMAL
        )
    
    async def _monitor_portfolio(self):
        """Scheduled portfolio monitoring"""
        await self.event_bus.publish_new(
            EventType.POSITION_UPDATED,
            "portfolio_monitor",
            {
                'total_value': 10000.0,
                'positions': {'BTCUSDT': 0.1},
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    async def start(self):
        """Start the framework"""
        await self.initialize_components()
        self.setup_event_handlers()
        self.setup_scheduled_tasks()
        await self.coordinator.startup()
    
    async def stop(self):
        """Stop the framework"""
        await self.coordinator.shutdown()
    
    def get_status(self):
        """Get framework status"""
        return {
            'coordinator_status': self.coordinator.get_system_status(),
            'events_received': len(self.events_received),
            'trading_flow_events': len(self.trading_flow_events),
            'components': list(self.components.keys())
        }


async def test_trading_system_integration():
    """Test trading system integration framework"""
    logger.info("Testing Trading System Integration Framework...")
    
    try:
        # Mock Redis for message queue
        with patch('redis.from_url') as mock_redis:
            mock_redis_client = Mock()
            mock_redis.return_value = mock_redis_client
            
            # Setup mock Redis responses
            mock_redis_client.zadd.return_value = 1
            mock_redis_client.zrangebyscore.return_value = []
            mock_redis_client.zcard.return_value = 0
            mock_redis_client.hlen.return_value = 0
            mock_redis_client.llen.return_value = 0
            mock_redis_client.setex.return_value = True
            mock_redis_client.hset.return_value = 1
            mock_redis_client.hdel.return_value = 1
            mock_redis_client.zrem.return_value = 1
            
            # Initialize trading system framework
            framework = TradingSystemIntegrationFramework()
            
            # Start the framework
            await framework.start()
            
            # Verify components are registered
            status = framework.get_status()
            assert len(status['components']) == 7  # 7 trading components
            assert status['coordinator_status']['system_state'] == 'running'
            
            # Test event flow
            logger.info("Testing event-driven trading flow...")
            
            # Trigger market data event
            await framework.event_bus.publish_new(
                EventType.PRICE_UPDATE,
                "market_data_source",
                {
                    'symbol': 'BTCUSDT',
                    'price': 45000.0,
                    'volume': 1000.0
                }
            )
            
            # Wait for event processing
            await asyncio.sleep(1)
            
            # Verify events were processed
            status = framework.get_status()
            assert status['events_received'] > 0
            assert status['trading_flow_events'] > 0
            
            # Test scheduled tasks
            logger.info("Testing scheduled tasks...")
            
            # Wait for scheduled tasks to run
            await asyncio.sleep(12)  # Wait for market data collection task
            
            # Verify more events were generated
            new_status = framework.get_status()
            assert new_status['events_received'] > status['events_received']
            
            # Test system health
            coordinator_status = framework.coordinator.get_system_status()
            assert coordinator_status['components']['healthy'] >= 7
            
            # Stop the framework
            await framework.stop()
            
            logger.info("✓ Trading System Integration Framework test passed")
            return True
        
    except Exception as e:
        logger.error(f"✗ Trading System Integration Framework test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


async def test_end_to_end_flow():
    """Test end-to-end trading flow"""
    logger.info("Testing End-to-End Trading Flow...")
    
    try:
        # Mock Redis
        with patch('redis.from_url') as mock_redis:
            mock_redis_client = Mock()
            mock_redis.return_value = mock_redis_client
            
            # Setup mock Redis responses
            mock_redis_client.zadd.return_value = 1
            mock_redis_client.zrangebyscore.return_value = []
            mock_redis_client.zcard.return_value = 0
            mock_redis_client.hlen.return_value = 0
            mock_redis_client.llen.return_value = 0
            mock_redis_client.setex.return_value = True
            mock_redis_client.hset.return_value = 1
            mock_redis_client.hdel.return_value = 1
            mock_redis_client.zrem.return_value = 1
            
            # Create framework
            framework = TradingSystemIntegrationFramework()
            await framework.start()
            
            # Track the complete flow
            initial_events = len(framework.events_received)
            
            # Simulate complete trading flow
            logger.info("Simulating complete trading flow...")
            
            # 1. Market data arrives -> triggers analysis
            await framework.event_bus.publish_new(
                EventType.PRICE_UPDATE,
                "market_data",
                {
                    'symbol': 'BTCUSDT',
                    'price': 45000.0,
                    'volume': 1000.0
                }
            )
            
            # Wait for the cascade of events
            await asyncio.sleep(2)
            
            # Verify the flow generated multiple events
            final_events = len(framework.events_received)
            events_generated = final_events - initial_events
            
            logger.info(f"Events generated in flow: {events_generated}")
            
            # Should have generated: price_update -> signal_generated -> trading_decision
            assert events_generated >= 3
            
            # Verify event types in flow
            event_types = [event['type'] for event in framework.trading_flow_events[-events_generated:]]
            logger.info(f"Event flow: {' -> '.join(event_types)}")
            
            # Should contain the trading flow sequence
            assert 'price_update' in event_types
            assert 'signal_generated' in event_types
            assert 'trading_decision' in event_types
            
            await framework.stop()
            
            logger.info("✓ End-to-End Trading Flow test passed")
            return True
        
    except Exception as e:
        logger.error(f"✗ End-to-End Trading Flow test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


async def main():
    """Run all trading system integration tests"""
    logger.info("Starting Trading System Integration Tests")
    logger.info("="*70)
    
    tests = [
        test_trading_system_integration,
        test_end_to_end_flow
    ]
    
    passed = 0
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
        except Exception as e:
            logger.error(f"Test {test.__name__} failed with exception: {e}")
    
    logger.info("\n" + "="*70)
    logger.info(f"Trading System Integration Tests: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        logger.info("✓ ALL TRADING SYSTEM INTEGRATION TESTS PASSED")
        return True
    else:
        logger.error("✗ SOME TRADING SYSTEM INTEGRATION TESTS FAILED")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)