"""
System Coordinator
Coordinates all system components and manages the overall system lifecycle
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import signal
import sys

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from system_integration.event_bus import EventBus, Event, EventType
from system_integration.message_queue import MessageQueue, MessageProcessor
from system_integration.task_scheduler import TaskScheduler, ScheduledTask, TaskType

logger = logging.getLogger(__name__)


class SystemState(Enum):
    """System states"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class ComponentStatus:
    """Component status information"""
    name: str
    status: str
    healthy: bool
    last_check: datetime
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'status': self.status,
            'healthy': self.healthy,
            'last_check': self.last_check.isoformat(),
            'error': self.error,
            'metadata': self.metadata or {}
        }


class SystemCoordinator:
    """
    System coordinator that manages all components and system lifecycle
    """
    
    def __init__(self):
        """Initialize system coordinator"""
        self.state = SystemState.STOPPED
        self.start_time: Optional[datetime] = None
        
        # Core components
        self.event_bus = EventBus()
        self.message_queue = MessageQueue()
        self.task_scheduler = TaskScheduler()
        
        # Component registry
        self.components: Dict[str, Any] = {
            'event_bus': self.event_bus,
            'message_queue': self.message_queue,
            'task_scheduler': self.task_scheduler
        }
        
        # Component health status
        self.component_status: Dict[str, ComponentStatus] = {}
        
        # System configuration
        self.health_check_interval = 30  # seconds
        self.shutdown_timeout = 30  # seconds
        
        # Event handlers
        self._setup_event_handlers()
        
        # Scheduled tasks
        self._setup_scheduled_tasks()
        
        # Signal handlers
        self._setup_signal_handlers()
        
        logger.info("System coordinator initialized")
    
    def _setup_event_handlers(self):
        """Setup system event handlers"""
        # Subscribe to system events
        self.event_bus.subscribe(
            {EventType.SYSTEM_STARTED, EventType.SYSTEM_STOPPED, EventType.ERROR_OCCURRED},
            self._handle_system_event,
            async_handler=True,
            priority=10
        )
        
        # Subscribe to health check events
        self.event_bus.subscribe(
            {EventType.HEALTH_CHECK},
            self._handle_health_check,
            async_handler=True,
            priority=5
        )
    
    def _setup_scheduled_tasks(self):
        """Setup system scheduled tasks"""
        # Health check task
        self.task_scheduler.schedule_interval(
            name="system_health_check",
            task_func=self._perform_health_check,
            interval_seconds=self.health_check_interval,
            description="Periodic system health check",
            tags=["system", "health"]
        )
        
        # Cleanup task
        self.task_scheduler.schedule_cron(
            name="system_cleanup",
            task_func=self._perform_cleanup,
            cron_expression="0 2 * * *",  # Daily at 2 AM
            description="Daily system cleanup",
            tags=["system", "cleanup"]
        )
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _handle_system_event(self, event: Event):
        """Handle system events"""
        try:
            if event.event_type == EventType.SYSTEM_STARTED:
                logger.info("System started event received")
                self.state = SystemState.RUNNING
                
            elif event.event_type == EventType.SYSTEM_STOPPED:
                logger.info("System stopped event received")
                self.state = SystemState.STOPPED
                
            elif event.event_type == EventType.ERROR_OCCURRED:
                logger.error(f"System error event: {event.data.get('error', 'Unknown error')}")
                # Could trigger alerts or recovery procedures here
                
        except Exception as e:
            logger.error(f"Error handling system event: {e}")
    
    async def _handle_health_check(self, event: Event):
        """Handle health check events"""
        try:
            component_name = event.data.get('component')
            if component_name and component_name in self.components:
                await self._check_component_health(component_name)
        except Exception as e:
            logger.error(f"Error handling health check event: {e}")
    
    def register_component(self, name: str, component: Any, 
                          health_check_func: Optional[Callable] = None):
        """
        Register a system component
        
        Args:
            name: Component name
            component: Component instance
            health_check_func: Optional health check function
        """
        self.components[name] = component
        
        # Initialize component status
        self.component_status[name] = ComponentStatus(
            name=name,
            status="registered",
            healthy=True,
            last_check=datetime.utcnow()
        )
        
        # Store health check function if provided
        if health_check_func:
            setattr(component, '_health_check', health_check_func)
        
        logger.info(f"Registered component: {name}")
    
    def unregister_component(self, name: str):
        """
        Unregister a system component
        
        Args:
            name: Component name
        """
        if name in self.components:
            del self.components[name]
        
        if name in self.component_status:
            del self.component_status[name]
        
        logger.info(f"Unregistered component: {name}")
    
    async def _check_component_health(self, component_name: str) -> bool:
        """
        Check health of a specific component
        
        Args:
            component_name: Name of component to check
            
        Returns:
            True if component is healthy
        """
        if component_name not in self.components:
            return False
        
        component = self.components[component_name]
        status = self.component_status.get(component_name)
        
        if not status:
            return False
        
        try:
            # Try component-specific health check
            if hasattr(component, '_health_check'):
                health_result = await component._health_check()
                if isinstance(health_result, dict):
                    status.healthy = health_result.get('healthy', True)
                    status.error = health_result.get('error')
                    status.metadata = health_result.get('metadata', {})
                else:
                    status.healthy = bool(health_result)
            
            # Default health checks for known components
            elif component_name == 'event_bus':
                stats = component.get_bus_stats()
                status.healthy = stats.get('total_errors', 0) < 100  # Arbitrary threshold
                status.metadata = {'total_events': stats.get('total_events', 0)}
            
            elif component_name == 'message_queue':
                stats = component.get_system_stats()
                status.healthy = stats.get('running', False)
                status.metadata = {'total_processed': stats.get('total_processed', 0)}
            
            elif component_name == 'task_scheduler':
                stats = component.get_scheduler_stats()
                status.healthy = stats.get('running', False)
                status.metadata = {'total_tasks': stats.get('total_tasks', 0)}
            
            else:
                # Generic health check - just check if component exists
                status.healthy = component is not None
            
            status.status = "healthy" if status.healthy else "unhealthy"
            status.last_check = datetime.utcnow()
            status.error = None if status.healthy else "Health check failed"
            
            return status.healthy
            
        except Exception as e:
            status.healthy = False
            status.status = "error"
            status.error = str(e)
            status.last_check = datetime.utcnow()
            
            logger.error(f"Health check failed for {component_name}: {e}")
            return False
    
    async def _perform_health_check(self):
        """Perform system-wide health check"""
        logger.debug("Performing system health check")
        
        unhealthy_components = []
        
        for component_name in self.components.keys():
            is_healthy = await self._check_component_health(component_name)
            if not is_healthy:
                unhealthy_components.append(component_name)
        
        # Publish health check event
        await self.event_bus.publish_new(
            EventType.HEALTH_CHECK,
            "system_coordinator",
            {
                'total_components': len(self.components),
                'healthy_components': len(self.components) - len(unhealthy_components),
                'unhealthy_components': unhealthy_components,
                'system_state': self.state.value
            }
        )
        
        # Update system state based on health
        if unhealthy_components and self.state == SystemState.RUNNING:
            logger.warning(f"Unhealthy components detected: {unhealthy_components}")
            # Could transition to degraded state or trigger recovery
    
    async def _perform_cleanup(self):
        """Perform system cleanup tasks"""
        logger.info("Performing system cleanup")
        
        try:
            # Clean up event bus history
            self.event_bus.clear_history()
            
            # Clean up message queue results
            self.message_queue.cleanup_old_results(hours=24)
            
            # Clean up task scheduler execution history
            self.task_scheduler.cleanup_old_executions(hours=24)
            
            logger.info("System cleanup completed")
            
        except Exception as e:
            logger.error(f"System cleanup failed: {e}")
    
    async def startup(self):
        """Start the system"""
        if self.state != SystemState.STOPPED:
            logger.warning(f"Cannot start system in state {self.state.value}")
            return
        
        logger.info("Starting system...")
        self.state = SystemState.STARTING
        self.start_time = datetime.utcnow()
        
        try:
            # Start core components
            logger.info("Starting task scheduler...")
            await self.task_scheduler.start()
            
            logger.info("Starting message queue workers...")
            await self.message_queue.start_workers()
            
            # Initialize component health status
            for component_name in self.components.keys():
                await self._check_component_health(component_name)
            
            # Publish system started event
            await self.event_bus.publish_new(
                EventType.SYSTEM_STARTED,
                "system_coordinator",
                {
                    'start_time': self.start_time.isoformat(),
                    'components': list(self.components.keys())
                }
            )
            
            self.state = SystemState.RUNNING
            logger.info("System startup completed successfully")
            
        except Exception as e:
            self.state = SystemState.ERROR
            logger.error(f"System startup failed: {e}")
            
            # Publish error event
            await self.event_bus.publish_new(
                EventType.ERROR_OCCURRED,
                "system_coordinator",
                {
                    'error': str(e),
                    'phase': 'startup'
                }
            )
            
            raise
    
    async def shutdown(self):
        """Shutdown the system gracefully"""
        if self.state == SystemState.STOPPED:
            logger.info("System already stopped")
            return
        
        logger.info("Shutting down system...")
        self.state = SystemState.STOPPING
        
        try:
            # Publish system stopping event
            await self.event_bus.publish_new(
                EventType.SYSTEM_STOPPED,
                "system_coordinator",
                {
                    'stop_time': datetime.utcnow().isoformat(),
                    'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0
                }
            )
            
            # Stop components in reverse order
            logger.info("Stopping message queue workers...")
            await self.message_queue.stop_workers()
            
            logger.info("Stopping task scheduler...")
            await self.task_scheduler.stop()
            
            # Close connections
            logger.info("Closing connections...")
            self.message_queue.close()
            self.event_bus.shutdown()
            
            self.state = SystemState.STOPPED
            logger.info("System shutdown completed")
            
        except Exception as e:
            self.state = SystemState.ERROR
            logger.error(f"System shutdown failed: {e}")
            raise
    
    async def restart(self):
        """Restart the system"""
        logger.info("Restarting system...")
        await self.shutdown()
        await asyncio.sleep(2)  # Brief pause
        await self.startup()
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status
        
        Returns:
            System status information
        """
        uptime = None
        if self.start_time and self.state == SystemState.RUNNING:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        # Component health summary
        healthy_components = sum(1 for status in self.component_status.values() if status.healthy)
        total_components = len(self.component_status)
        
        return {
            'system_state': self.state.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'uptime_seconds': uptime,
            'components': {
                'total': total_components,
                'healthy': healthy_components,
                'unhealthy': total_components - healthy_components,
                'details': {name: status.to_dict() for name, status in self.component_status.items()}
            },
            'event_bus': self.event_bus.get_bus_stats(),
            'message_queue': self.message_queue.get_system_stats(),
            'task_scheduler': self.task_scheduler.get_scheduler_stats(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_component_status(self, component_name: str) -> Optional[Dict[str, Any]]:
        """
        Get status of specific component
        
        Args:
            component_name: Name of component
            
        Returns:
            Component status or None if not found
        """
        status = self.component_status.get(component_name)
        return status.to_dict() if status else None
    
    async def trigger_health_check(self, component_name: Optional[str] = None):
        """
        Trigger manual health check
        
        Args:
            component_name: Specific component to check (optional)
        """
        if component_name:
            await self._check_component_health(component_name)
        else:
            await self._perform_health_check()
    
    async def run_forever(self):
        """
        Run the system indefinitely
        """
        try:
            await self.startup()
            
            # Keep running until shutdown
            while self.state == SystemState.RUNNING:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"System error: {e}")
        finally:
            await self.shutdown()
    
    def is_healthy(self) -> bool:
        """
        Check if system is healthy
        
        Returns:
            True if system and all components are healthy
        """
        if self.state != SystemState.RUNNING:
            return False
        
        return all(status.healthy for status in self.component_status.values())
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get system metrics for monitoring
        
        Returns:
            System metrics
        """
        status = self.get_system_status()
        
        return {
            'system_healthy': self.is_healthy(),
            'uptime_seconds': status.get('uptime_seconds', 0),
            'total_components': status['components']['total'],
            'healthy_components': status['components']['healthy'],
            'total_events': status['event_bus']['total_events'],
            'total_messages': status['message_queue']['total_messages'],
            'total_tasks': status['task_scheduler']['total_tasks'],
            'event_success_rate': status['event_bus']['success_rate'],
            'message_success_rate': status['message_queue']['success_rate'],
            'task_success_rate': status['task_scheduler']['success_rate'],
            'timestamp': datetime.utcnow().isoformat()
        }