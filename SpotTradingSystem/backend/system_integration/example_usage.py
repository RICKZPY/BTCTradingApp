"""
System Integration Example Usage
Demonstrates event-driven architecture, message queues, and task scheduling
"""
import sys
import os
import asyncio
from datetime import datetime, timedelta
import time
import random

# Add the backend directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from system_integration.event_bus import EventBus, Event, EventType
from system_integration.message_queue import MessageQueue, MessageProcessor, Message, MessagePriority, ProcessingResult, MessageStatus
from system_integration.task_scheduler import TaskScheduler, ScheduledTask, TaskType
from system_integration.system_coordinator import SystemCoordinator


# Sample message processors
class DataCollectionProcessor(MessageProcessor):
    """Sample processor for data collection messages"""
    
    def __init__(self):
        super().__init__("data_collection_processor")
    
    async def process(self, message: Message) -> ProcessingResult:
        """Process data collection message"""
        try:
            # Simulate data collection work
            data_source = message.payload.get('source', 'unknown')
            await asyncio.sleep(0.1)  # Simulate work
            
            result = {
                'source': data_source,
                'data_collected': True,
                'timestamp': datetime.utcnow().isoformat(),
                'records': random.randint(10, 100)
            }
            
            self.processed_count += 1
            self.last_processed = datetime.utcnow()
            
            return ProcessingResult(
                message_id=message.message_id,
                status=MessageStatus.COMPLETED,
                result=result
            )
            
        except Exception as e:
            self.error_count += 1
            return ProcessingResult(
                message_id=message.message_id,
                status=MessageStatus.FAILED,
                error=str(e)
            )


class AnalysisProcessor(MessageProcessor):
    """Sample processor for analysis messages"""
    
    def __init__(self):
        super().__init__("analysis_processor")
    
    async def process(self, message: Message) -> ProcessingResult:
        """Process analysis message"""
        try:
            # Simulate analysis work
            analysis_type = message.payload.get('type', 'sentiment')
            await asyncio.sleep(0.2)  # Simulate work
            
            result = {
                'analysis_type': analysis_type,
                'confidence': random.uniform(0.6, 0.95),
                'result': 'positive' if random.random() > 0.5 else 'negative',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.processed_count += 1
            self.last_processed = datetime.utcnow()
            
            return ProcessingResult(
                message_id=message.message_id,
                status=MessageStatus.COMPLETED,
                result=result
            )
            
        except Exception as e:
            self.error_count += 1
            return ProcessingResult(
                message_id=message.message_id,
                status=MessageStatus.FAILED,
                error=str(e)
            )


async def demonstrate_event_bus():
    """Demonstrate event bus functionality"""
    print("=== Event Bus Demo ===")
    
    # Create event bus
    event_bus = EventBus()
    
    # Event handlers
    def handle_price_update(event: Event):
        price = event.data.get('price', 0)
        symbol = event.data.get('symbol', 'UNKNOWN')
        print(f"  Price Update Handler: {symbol} = ${price:,.2f}")
        return f"processed_price_{symbol}"
    
    def handle_trading_decision(event: Event):
        action = event.data.get('action', 'UNKNOWN')
        confidence = event.data.get('confidence', 0)
        print(f"  Trading Decision Handler: {action} with {confidence:.1%} confidence")
        return f"processed_decision_{action}"
    
    async def handle_system_event(event: Event):
        event_type = event.event_type.value
        print(f"  System Event Handler: {event_type}")
        await asyncio.sleep(0.01)  # Simulate async work
        return f"processed_system_{event_type}"
    
    # Subscribe to events
    price_handler_id = event_bus.subscribe(
        {EventType.PRICE_UPDATE},
        handle_price_update
    )
    
    decision_handler_id = event_bus.subscribe(
        {EventType.TRADING_DECISION_MADE},
        handle_trading_decision
    )
    
    system_handler_id = event_bus.subscribe(
        {EventType.SYSTEM_STARTED, EventType.SYSTEM_STOPPED},
        handle_system_event,
        async_handler=True,
        priority=10
    )
    
    print(f"Subscribed {len(event_bus.handlers)} event handlers")
    
    # Publish events
    print("\nPublishing events...")
    
    # Price update event
    price_event = event_bus.create_event(
        EventType.PRICE_UPDATE,
        "market_data_collector",
        {'symbol': 'BTCUSDT', 'price': 45000.0, 'volume': 1500000}
    )
    
    results = await event_bus.publish(price_event)
    print(f"Price event results: {results}")
    
    # Trading decision event
    decision_event = event_bus.create_event(
        EventType.TRADING_DECISION_MADE,
        "decision_engine",
        {'action': 'BUY', 'confidence': 0.85, 'amount': 0.05}
    )
    
    results = await event_bus.publish(decision_event)
    print(f"Decision event results: {results}")
    
    # System event (async)
    results = await event_bus.publish_new(
        EventType.SYSTEM_STARTED,
        "system_coordinator",
        {'start_time': datetime.utcnow().isoformat()}
    )
    print(f"System event results: {results}")
    
    # Get statistics
    stats = event_bus.get_bus_stats()
    print(f"\nEvent Bus Stats:")
    print(f"  Total Events: {stats['total_events']}")
    print(f"  Total Handlers: {stats['total_handlers']}")
    print(f"  Success Rate: {stats['success_rate']:.1%}")
    
    # Cleanup
    event_bus.shutdown()
    
    return event_bus


async def demonstrate_message_queue():
    """Demonstrate message queue functionality"""
    print("\n=== Message Queue Demo ===")
    
    # Try to create message queue, fall back to mock if Redis unavailable
    try:
        message_queue = MessageQueue()
        # Test Redis connection
        message_queue.redis_client.ping()
        print("Message queue initialized with Redis")
        use_mock = False
    except Exception as e:
        print(f"Redis not available, using mock message queue: {e}")
        use_mock = True
        
        # Create a mock message queue for demo
        class MockMessageQueue:
            def __init__(self):
                self.queues = {}
                self.processors = {}
                self.total_messages = 0
                self.total_processed = 0
                self.running = False
            
            def register_processor(self, queue_name, processor):
                self.processors[queue_name] = processor
                print(f"Registered processor for {queue_name}")
            
            async def enqueue_simple(self, queue_name, payload, priority=MessagePriority.NORMAL, **kwargs):
                if queue_name not in self.queues:
                    self.queues[queue_name] = []
                
                message_id = f"msg_{len(self.queues[queue_name])}"
                self.queues[queue_name].append({
                    'id': message_id,
                    'payload': payload,
                    'priority': priority
                })
                self.total_messages += 1
                print(f"Enqueued message to {queue_name}: {payload}")
                return message_id
            
            async def process_queue_messages(self, queue_name, count=5):
                """Simulate processing messages"""
                if queue_name not in self.queues or not self.queues[queue_name]:
                    return
                
                processor = self.processors.get(queue_name)
                if not processor:
                    return
                
                messages_to_process = self.queues[queue_name][:count]
                self.queues[queue_name] = self.queues[queue_name][count:]
                
                for msg_data in messages_to_process:
                    # Create mock message
                    message = Message(
                        message_id=msg_data['id'],
                        queue_name=queue_name,
                        payload=msg_data['payload'],
                        priority=msg_data['priority'],
                        created_at=datetime.utcnow()
                    )
                    
                    # Process message
                    result = await processor.process(message)
                    if result.status == MessageStatus.COMPLETED:
                        self.total_processed += 1
                        print(f"  Processed {message.message_id}: {result.result}")
            
            def get_system_stats(self):
                return {
                    'total_messages': self.total_messages,
                    'total_processed': self.total_processed,
                    'running': self.running
                }
        
        message_queue = MockMessageQueue()
    
    # Register processors
    data_processor = DataCollectionProcessor()
    analysis_processor = AnalysisProcessor()
    
    message_queue.register_processor("data_collection", data_processor)
    message_queue.register_processor("analysis", analysis_processor)
    
    # Enqueue messages
    print("\nEnqueuing messages...")
    
    # Data collection messages
    await message_queue.enqueue_simple(
        "data_collection",
        {"source": "coindesk", "type": "news"},
        MessagePriority.HIGH
    )
    
    await message_queue.enqueue_simple(
        "data_collection",
        {"source": "binance", "type": "market_data"},
        MessagePriority.NORMAL
    )
    
    # Analysis messages
    await message_queue.enqueue_simple(
        "analysis",
        {"type": "sentiment", "text": "Bitcoin price surges to new highs"},
        MessagePriority.NORMAL
    )
    
    await message_queue.enqueue_simple(
        "analysis",
        {"type": "technical", "symbol": "BTCUSDT"},
        MessagePriority.LOW
    )
    
    # Process messages
    print("\nProcessing messages...")
    if use_mock:
        await message_queue.process_queue_messages("data_collection")
        await message_queue.process_queue_messages("analysis")
    else:
        # For real Redis queue, we would start workers
        print("  (In production, workers would process messages automatically)")
    
    # Get statistics
    stats = message_queue.get_system_stats()
    print(f"\nMessage Queue Stats:")
    print(f"  Total Messages: {stats['total_messages']}")
    print(f"  Total Processed: {stats['total_processed']}")
    
    return message_queue


async def demonstrate_task_scheduler():
    """Demonstrate task scheduler functionality"""
    print("\n=== Task Scheduler Demo ===")
    
    # Create task scheduler
    scheduler = TaskScheduler()
    
    # Sample tasks
    def data_collection_task():
        print(f"  Data Collection Task executed at {datetime.utcnow().strftime('%H:%M:%S')}")
        return {"collected": random.randint(50, 200), "source": "market_data"}
    
    def analysis_task():
        print(f"  Analysis Task executed at {datetime.utcnow().strftime('%H:%M:%S')}")
        return {"analyzed": random.randint(10, 50), "type": "sentiment"}
    
    async def async_cleanup_task():
        print(f"  Cleanup Task (async) executed at {datetime.utcnow().strftime('%H:%M:%S')}")
        await asyncio.sleep(0.1)  # Simulate async work
        return {"cleaned": True, "items": random.randint(5, 20)}
    
    def failing_task():
        print(f"  Failing Task executed at {datetime.utcnow().strftime('%H:%M:%S')}")
        raise Exception("Simulated task failure")
    
    # Schedule tasks
    print("Scheduling tasks...")
    
    # One-time task
    one_time_id = scheduler.schedule_one_time(
        "one_time_data_collection",
        data_collection_task,
        datetime.utcnow() + timedelta(seconds=2),
        description="One-time data collection"
    )
    
    # Interval task
    interval_id = scheduler.schedule_interval(
        "periodic_analysis",
        analysis_task,
        interval_seconds=3,
        description="Periodic analysis every 3 seconds"
    )
    
    # Cron task (every minute)
    cron_id = scheduler.schedule_cron(
        "cleanup_task",
        async_cleanup_task,
        "*/1 * * * *",  # Every minute
        description="Cleanup task every minute"
    )
    
    # Task that will fail
    failing_id = scheduler.schedule_interval(
        "failing_task",
        failing_task,
        interval_seconds=5,
        max_retries=2,
        description="Task that demonstrates failure handling"
    )
    
    print(f"Scheduled {len(scheduler.tasks)} tasks")
    
    # Start scheduler
    await scheduler.start()
    print("Task scheduler started")
    
    # Let it run for a bit
    print("\nRunning tasks for 10 seconds...")
    await asyncio.sleep(10)
    
    # Get task statistics
    print("\nTask Statistics:")
    for task in scheduler.get_tasks():
        stats = task.get_stats()
        print(f"  {stats['name']}:")
        print(f"    Executions: {stats['execution_count']}")
        print(f"    Success Rate: {stats['success_rate']:.1%}")
        print(f"    Next Run: {stats['next_run']}")
    
    # Get scheduler stats
    scheduler_stats = scheduler.get_scheduler_stats()
    print(f"\nScheduler Stats:")
    print(f"  Total Executions: {scheduler_stats['total_executions']}")
    print(f"  Success Rate: {scheduler_stats['success_rate']:.1%}")
    print(f"  Running Tasks: {scheduler_stats['running_tasks']}")
    
    # Stop scheduler
    await scheduler.stop()
    print("Task scheduler stopped")
    
    return scheduler


async def demonstrate_system_coordinator():
    """Demonstrate system coordinator functionality"""
    print("\n=== System Coordinator Demo ===")
    
    # Create system coordinator
    coordinator = SystemCoordinator()
    
    # Register additional components (simulated)
    class MockTradingEngine:
        def __init__(self):
            self.running = True
        
        async def _health_check(self):
            return {
                'healthy': self.running,
                'metadata': {'orders_processed': random.randint(10, 100)}
            }
    
    class MockDataCollector:
        def __init__(self):
            self.active = True
        
        async def _health_check(self):
            return {
                'healthy': self.active,
                'metadata': {'sources_active': random.randint(3, 8)}
            }
    
    # Register mock components
    trading_engine = MockTradingEngine()
    data_collector = MockDataCollector()
    
    coordinator.register_component("trading_engine", trading_engine)
    coordinator.register_component("data_collector", data_collector)
    
    print(f"Registered {len(coordinator.components)} components")
    
    # Start system
    print("\nStarting system...")
    await coordinator.startup()
    
    # Let system run briefly
    print("System running...")
    await asyncio.sleep(3)
    
    # Get system status
    status = coordinator.get_system_status()
    print(f"\nSystem Status:")
    print(f"  State: {status['system_state']}")
    print(f"  Uptime: {status['uptime_seconds']:.1f} seconds")
    print(f"  Components: {status['components']['healthy']}/{status['components']['total']} healthy")
    
    # Component details
    print(f"\nComponent Health:")
    for name, details in status['components']['details'].items():
        health_icon = "✓" if details['healthy'] else "✗"
        print(f"  {health_icon} {name}: {details['status']}")
    
    # Trigger manual health check
    print("\nTriggering manual health check...")
    await coordinator.trigger_health_check()
    
    # Get metrics
    metrics = coordinator.get_metrics()
    print(f"\nSystem Metrics:")
    print(f"  System Healthy: {metrics['system_healthy']}")
    print(f"  Total Events: {metrics['total_events']}")
    print(f"  Event Success Rate: {metrics['event_success_rate']:.1%}")
    
    # Simulate component failure
    print("\nSimulating component failure...")
    data_collector.active = False
    await coordinator.trigger_health_check("data_collector")
    
    updated_status = coordinator.get_component_status("data_collector")
    print(f"Data Collector Status: {updated_status['status']} (healthy: {updated_status['healthy']})")
    
    # Shutdown system
    print("\nShutting down system...")
    await coordinator.shutdown()
    
    final_status = coordinator.get_system_status()
    print(f"Final State: {final_status['system_state']}")
    
    return coordinator


async def demonstrate_integrated_workflow():
    """Demonstrate integrated system workflow"""
    print("\n=== Integrated Workflow Demo ===")
    
    # Create system coordinator
    coordinator = SystemCoordinator()
    
    # Get references to core components
    event_bus = coordinator.event_bus
    message_queue = coordinator.message_queue
    task_scheduler = coordinator.task_scheduler
    
    # Create workflow components
    workflow_events = []
    
    def workflow_event_handler(event: Event):
        workflow_events.append({
            'type': event.event_type.value,
            'source': event.source,
            'timestamp': event.timestamp.isoformat(),
            'data': event.data
        })
        print(f"  Workflow Event: {event.event_type.value} from {event.source}")
    
    # Subscribe to workflow events
    event_bus.subscribe(
        {EventType.PRICE_UPDATE, EventType.TRADING_DECISION_MADE, EventType.ORDER_PLACED},
        workflow_event_handler
    )
    
    # Create workflow task
    async def trading_workflow_task():
        """Simulated trading workflow"""
        print("  Executing trading workflow...")
        
        # Step 1: Collect market data
        await event_bus.publish_new(
            EventType.PRICE_UPDATE,
            "market_data_collector",
            {'symbol': 'BTCUSDT', 'price': 45000 + random.randint(-1000, 1000)}
        )
        
        # Step 2: Analyze and make decision
        await asyncio.sleep(0.1)
        await event_bus.publish_new(
            EventType.TRADING_DECISION_MADE,
            "decision_engine",
            {
                'action': 'BUY' if random.random() > 0.5 else 'SELL',
                'confidence': random.uniform(0.6, 0.9),
                'amount': random.uniform(0.01, 0.1)
            }
        )
        
        # Step 3: Execute order
        await asyncio.sleep(0.1)
        await event_bus.publish_new(
            EventType.ORDER_PLACED,
            "trading_executor",
            {
                'order_id': f"ORDER_{random.randint(1000, 9999)}",
                'status': 'FILLED',
                'executed_price': 45000 + random.randint(-500, 500)
            }
        )
        
        return {"workflow_completed": True, "steps": 3}
    
    # Schedule workflow task
    workflow_task_id = task_scheduler.schedule_interval(
        "trading_workflow",
        trading_workflow_task,
        interval_seconds=5,
        description="Main trading workflow"
    )
    
    # Start system
    print("Starting integrated system...")
    await coordinator.startup()
    
    # Run workflow
    print("Running integrated workflow for 12 seconds...")
    await asyncio.sleep(12)
    
    # Show results
    print(f"\nWorkflow Results:")
    print(f"  Events Generated: {len(workflow_events)}")
    print(f"  Event Types: {set(e['type'] for e in workflow_events)}")
    
    # Show system metrics
    metrics = coordinator.get_metrics()
    print(f"\nSystem Metrics:")
    print(f"  Total Events: {metrics['total_events']}")
    print(f"  Total Tasks: {metrics['total_tasks']}")
    print(f"  System Healthy: {metrics['system_healthy']}")
    
    # Shutdown
    print("\nShutting down integrated system...")
    await coordinator.shutdown()
    
    return coordinator


async def main():
    """Run all system integration demonstrations"""
    print("System Integration Demonstration")
    print("=" * 60)
    
    try:
        # Individual component demonstrations
        await demonstrate_event_bus()
        await demonstrate_message_queue()
        await demonstrate_task_scheduler()
        await demonstrate_system_coordinator()
        await demonstrate_integrated_workflow()
        
        print("\n" + "=" * 60)
        print("System integration demonstration completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  ✓ Event-driven architecture with pub/sub messaging")
        print("  ✓ Asynchronous message queue processing")
        print("  ✓ Flexible task scheduling (one-time, interval, cron)")
        print("  ✓ System coordination and health monitoring")
        print("  ✓ Integrated workflow orchestration")
        print("  ✓ Graceful startup and shutdown procedures")
        
    except Exception as e:
        print(f"Error during demonstration: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())