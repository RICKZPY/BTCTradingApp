"""
Base classes for data collection framework

Implements the abstract base class for data collectors and the scheduling system
as specified in requirements 1.1 and 1.2.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
import structlog

from core.data_models import NewsItem, MarketData
from config import settings


logger = structlog.get_logger(__name__)


@dataclass
class CollectionTask:
    """Represents a data collection task"""
    name: str
    collector_class: type
    interval_seconds: int
    last_run: Optional[datetime] = None
    is_running: bool = False
    error_count: int = 0
    max_errors: int = 5


class DataCollector(ABC):
    """
    Abstract base class for all data collectors
    
    Implements the common interface for data collection as specified in the design.
    Each concrete collector must implement the collect_data method.
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.logger = structlog.get_logger(f"collector.{name}")
        self.is_active = True
        self.error_count = 0
        self.max_errors = 5
        
    @abstractmethod
    async def collect_data(self) -> List[Any]:
        """
        Collect data from the specific source
        
        Returns:
            List of collected data items (NewsItem, MarketData, etc.)
        """
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """
        Validate connection to the data source
        
        Returns:
            True if connection is valid, False otherwise
        """
        pass
    
    async def safe_collect(self) -> List[Any]:
        """
        Safely collect data with error handling and logging
        
        Returns:
            List of collected data items, empty list on error
        """
        if not self.is_active:
            self.logger.warning("Collector is inactive, skipping collection")
            return []
            
        try:
            self.logger.info("Starting data collection", collector=self.name)
            
            # Validate connection first
            if not await self.validate_connection():
                self.logger.error("Connection validation failed", collector=self.name)
                self._handle_error("Connection validation failed")
                return []
            
            # Collect data
            data = await self.collect_data()
            
            # Reset error count on successful collection
            self.error_count = 0
            
            self.logger.info(
                "Data collection completed successfully",
                collector=self.name,
                items_collected=len(data)
            )
            
            return data
            
        except Exception as e:
            self.logger.error(
                "Error during data collection",
                collector=self.name,
                error=str(e),
                error_type=type(e).__name__
            )
            self._handle_error(str(e))
            return []
    
    def _handle_error(self, error_message: str):
        """Handle collection errors and deactivate if too many errors"""
        self.error_count += 1
        
        if self.error_count >= self.max_errors:
            self.is_active = False
            self.logger.critical(
                "Collector deactivated due to too many errors",
                collector=self.name,
                error_count=self.error_count,
                last_error=error_message
            )
        else:
            self.logger.warning(
                "Collection error recorded",
                collector=self.name,
                error_count=self.error_count,
                max_errors=self.max_errors
            )
    
    def reset_errors(self):
        """Reset error count and reactivate collector"""
        self.error_count = 0
        self.is_active = True
        self.logger.info("Collector errors reset and reactivated", collector=self.name)


class DataCollectionScheduler:
    """
    Asynchronous data collection scheduler
    
    Manages multiple data collectors and schedules their execution based on
    configured intervals. Implements requirements 1.1 and 1.2.
    """
    
    def __init__(self, queue_manager=None):
        self.tasks: Dict[str, CollectionTask] = {}
        self.collectors: Dict[str, DataCollector] = {}
        self.queue_manager = queue_manager
        self.is_running = False
        self.logger = structlog.get_logger("scheduler")
        self._stop_event = asyncio.Event()
        
    def register_collector(
        self,
        collector: DataCollector,
        interval_seconds: int,
        start_immediately: bool = True
    ):
        """
        Register a data collector with the scheduler
        
        Args:
            collector: DataCollector instance
            interval_seconds: Collection interval in seconds
            start_immediately: Whether to start collection immediately
        """
        task = CollectionTask(
            name=collector.name,
            collector_class=type(collector),
            interval_seconds=interval_seconds,
            last_run=None if start_immediately else datetime.now()
        )
        
        self.tasks[collector.name] = task
        self.collectors[collector.name] = collector
        
        self.logger.info(
            "Collector registered",
            collector=collector.name,
            interval=interval_seconds,
            start_immediately=start_immediately
        )
    
    def unregister_collector(self, collector_name: str):
        """Remove a collector from the scheduler"""
        if collector_name in self.tasks:
            del self.tasks[collector_name]
            del self.collectors[collector_name]
            self.logger.info("Collector unregistered", collector=collector_name)
    
    async def start(self):
        """Start the scheduler"""
        if self.is_running:
            self.logger.warning("Scheduler is already running")
            return
            
        self.is_running = True
        self._stop_event.clear()
        
        self.logger.info("Starting data collection scheduler")
        
        try:
            await self._run_scheduler_loop()
        except Exception as e:
            self.logger.error("Scheduler error", error=str(e))
        finally:
            self.is_running = False
            self.logger.info("Data collection scheduler stopped")
    
    async def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return
            
        self.logger.info("Stopping data collection scheduler")
        self._stop_event.set()
        
        # Wait for any running tasks to complete
        running_tasks = [
            task for task in self.tasks.values() 
            if task.is_running
        ]
        
        if running_tasks:
            self.logger.info(
                "Waiting for running tasks to complete",
                running_tasks=[task.name for task in running_tasks]
            )
            
            # Give tasks up to 30 seconds to complete
            for _ in range(30):
                if not any(task.is_running for task in self.tasks.values()):
                    break
                await asyncio.sleep(1)
    
    async def _run_scheduler_loop(self):
        """Main scheduler loop"""
        while not self._stop_event.is_set():
            try:
                # Check each task to see if it needs to run
                current_time = datetime.now()
                
                for task_name, task in self.tasks.items():
                    if await self._should_run_task(task, current_time):
                        # Run task asynchronously without blocking
                        asyncio.create_task(self._run_collection_task(task))
                
                # Sleep for a short interval before checking again
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error("Error in scheduler loop", error=str(e))
                await asyncio.sleep(30)  # Wait longer on error
    
    async def _should_run_task(self, task: CollectionTask, current_time: datetime) -> bool:
        """Check if a task should run based on its schedule"""
        if task.is_running:
            return False
            
        if task.last_run is None:
            return True
            
        time_since_last_run = current_time - task.last_run
        return time_since_last_run.total_seconds() >= task.interval_seconds
    
    async def _run_collection_task(self, task: CollectionTask):
        """Run a single collection task"""
        if task.is_running:
            return
            
        task.is_running = True
        task.last_run = datetime.now()
        
        try:
            collector = self.collectors[task.name]
            
            self.logger.info("Running collection task", task=task.name)
            
            # Collect data
            data = await collector.safe_collect()
            
            # Send data to queue if available
            if self.queue_manager and data:
                await self.queue_manager.enqueue_data(task.name, data)
            
            # Reset error count on successful run
            task.error_count = 0
            
            self.logger.info(
                "Collection task completed",
                task=task.name,
                items_collected=len(data)
            )
            
        except Exception as e:
            task.error_count += 1
            self.logger.error(
                "Error running collection task",
                task=task.name,
                error=str(e),
                error_count=task.error_count
            )
            
            # Deactivate task if too many errors
            if task.error_count >= task.max_errors:
                collector = self.collectors[task.name]
                collector.is_active = False
                self.logger.critical(
                    "Collection task deactivated due to errors",
                    task=task.name,
                    error_count=task.error_count
                )
        finally:
            task.is_running = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status information"""
        return {
            'is_running': self.is_running,
            'registered_tasks': len(self.tasks),
            'active_collectors': sum(
                1 for collector in self.collectors.values() 
                if collector.is_active
            ),
            'tasks': {
                name: {
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'is_running': task.is_running,
                    'error_count': task.error_count,
                    'collector_active': self.collectors[name].is_active
                }
                for name, task in self.tasks.items()
            }
        }
    
    async def force_run_task(self, task_name: str) -> bool:
        """Force run a specific task immediately"""
        if task_name not in self.tasks:
            self.logger.error("Task not found", task=task_name)
            return False
            
        task = self.tasks[task_name]
        if task.is_running:
            self.logger.warning("Task is already running", task=task_name)
            return False
            
        self.logger.info("Force running task", task=task_name)
        await self._run_collection_task(task)
        return True