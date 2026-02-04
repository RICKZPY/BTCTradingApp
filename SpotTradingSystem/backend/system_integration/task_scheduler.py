"""
Task Scheduler
Handles scheduled tasks and periodic operations
"""
import logging
import asyncio
from typing import Dict, List, Callable, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
try:
    import cron_descriptor
    CRON_DESCRIPTOR_AVAILABLE = True
except ImportError:
    CRON_DESCRIPTOR_AVAILABLE = False
    cron_descriptor = None

try:
    from croniter import croniter
    CRONITER_AVAILABLE = True
except ImportError:
    CRONITER_AVAILABLE = False
    croniter = None
import threading

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class TaskType(Enum):
    """Task types"""
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    CRON = "cron"
    INTERVAL = "interval"


@dataclass
class TaskExecution:
    """Task execution record"""
    execution_id: str
    task_id: str
    status: TaskStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'execution_id': self.execution_id,
            'task_id': self.task_id,
            'status': self.status.value,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'error': self.error,
            'duration_seconds': self.duration_seconds
        }


@dataclass
class ScheduledTask:
    """Scheduled task definition"""
    task_id: str
    name: str
    task_func: Callable[[], Any]
    task_type: TaskType
    
    # Scheduling parameters
    scheduled_at: Optional[datetime] = None  # For one-time tasks
    cron_expression: Optional[str] = None    # For cron tasks
    interval_seconds: Optional[int] = None   # For interval tasks
    
    # Execution parameters
    enabled: bool = True
    max_retries: int = 3
    timeout_seconds: int = 300
    allow_overlap: bool = False
    
    # Metadata
    description: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Runtime state
    last_execution: Optional[TaskExecution] = None
    next_run: Optional[datetime] = None
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    
    def __post_init__(self):
        """Validate task configuration"""
        if not self.task_id:
            self.task_id = str(uuid.uuid4())
        
        # Validate scheduling parameters
        if self.task_type == TaskType.ONE_TIME and not self.scheduled_at:
            raise ValueError("One-time tasks must have scheduled_at")
        
        if self.task_type == TaskType.CRON and not self.cron_expression:
            raise ValueError("Cron tasks must have cron_expression")
        
        if self.task_type == TaskType.INTERVAL and not self.interval_seconds:
            raise ValueError("Interval tasks must have interval_seconds")
        
        # Calculate next run time
        self._calculate_next_run()
    
    def _calculate_next_run(self):
        """Calculate next run time based on task type"""
        now = datetime.utcnow()
        
        if self.task_type == TaskType.ONE_TIME:
            self.next_run = self.scheduled_at
        
        elif self.task_type == TaskType.CRON:
            if self.cron_expression and CRONITER_AVAILABLE:
                cron = croniter(self.cron_expression, now)
                self.next_run = cron.get_next(datetime)
            else:
                logger.warning("Cron scheduling not available - croniter not installed")
                self.next_run = now + timedelta(minutes=1)  # Fallback
        
        elif self.task_type == TaskType.INTERVAL:
            if self.interval_seconds:
                if self.last_execution and self.last_execution.completed_at:
                    self.next_run = self.last_execution.completed_at + timedelta(seconds=self.interval_seconds)
                else:
                    self.next_run = now + timedelta(seconds=self.interval_seconds)
        
        elif self.task_type == TaskType.RECURRING:
            # For recurring tasks without specific schedule, run immediately
            self.next_run = now
    
    def should_run(self, current_time: Optional[datetime] = None) -> bool:
        """Check if task should run now"""
        if not self.enabled:
            return False
        
        if not self.next_run:
            return False
        
        current_time = current_time or datetime.utcnow()
        
        # Check if it's time to run
        if current_time < self.next_run:
            return False
        
        # Check for overlap
        if not self.allow_overlap and self.last_execution:
            if self.last_execution.status == TaskStatus.RUNNING:
                return False
        
        return True
    
    def update_next_run(self):
        """Update next run time after execution"""
        if self.task_type == TaskType.ONE_TIME:
            # One-time tasks don't run again
            self.next_run = None
            self.enabled = False
        
        elif self.task_type == TaskType.CRON:
            if self.cron_expression and CRONITER_AVAILABLE:
                cron = croniter(self.cron_expression, datetime.utcnow())
                self.next_run = cron.get_next(datetime)
            else:
                # Fallback for cron tasks when croniter not available
                self.next_run = datetime.utcnow() + timedelta(minutes=1)
        
        elif self.task_type == TaskType.INTERVAL:
            if self.interval_seconds:
                self.next_run = datetime.utcnow() + timedelta(seconds=self.interval_seconds)
        
        elif self.task_type == TaskType.RECURRING:
            # Recurring tasks run continuously
            self.next_run = datetime.utcnow()
    
    def get_cron_description(self) -> Optional[str]:
        """Get human-readable description of cron expression"""
        if self.task_type == TaskType.CRON and self.cron_expression and CRON_DESCRIPTOR_AVAILABLE:
            try:
                return cron_descriptor.get_description(self.cron_expression)
            except Exception:
                return None
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get task statistics"""
        success_rate = self.success_count / self.execution_count if self.execution_count > 0 else 0
        
        return {
            'task_id': self.task_id,
            'name': self.name,
            'task_type': self.task_type.value,
            'enabled': self.enabled,
            'execution_count': self.execution_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': success_rate,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'last_execution': self.last_execution.to_dict() if self.last_execution else None,
            'cron_description': self.get_cron_description()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization"""
        return {
            'task_id': self.task_id,
            'name': self.name,
            'task_type': self.task_type.value,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'cron_expression': self.cron_expression,
            'interval_seconds': self.interval_seconds,
            'enabled': self.enabled,
            'max_retries': self.max_retries,
            'timeout_seconds': self.timeout_seconds,
            'allow_overlap': self.allow_overlap,
            'description': self.description,
            'tags': self.tags,
            'metadata': self.metadata,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'execution_count': self.execution_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count
        }


class TaskScheduler:
    """
    Task scheduler for managing scheduled and periodic tasks
    """
    
    def __init__(self):
        """Initialize task scheduler"""
        self.tasks: Dict[str, ScheduledTask] = {}
        self.execution_history: List[TaskExecution] = []
        self.max_history = 1000
        
        # Scheduler state
        self.running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        self.check_interval = 1  # Check every second
        
        # Statistics
        self.total_executions = 0
        self.total_successes = 0
        self.total_failures = 0
        
        logger.info("Task scheduler initialized")
    
    def schedule_task(self, task: ScheduledTask) -> str:
        """
        Schedule a task
        
        Args:
            task: Task to schedule
            
        Returns:
            Task ID
        """
        self.tasks[task.task_id] = task
        logger.info(f"Scheduled task {task.task_id}: {task.name}")
        return task.task_id
    
    def schedule_one_time(self, name: str, task_func: Callable[[], Any],
                         scheduled_at: datetime, **kwargs) -> str:
        """
        Schedule a one-time task
        
        Args:
            name: Task name
            task_func: Function to execute
            scheduled_at: When to execute
            **kwargs: Additional task parameters
            
        Returns:
            Task ID
        """
        task = ScheduledTask(
            task_id=str(uuid.uuid4()),
            name=name,
            task_func=task_func,
            task_type=TaskType.ONE_TIME,
            scheduled_at=scheduled_at,
            **kwargs
        )
        
        return self.schedule_task(task)
    
    def schedule_cron(self, name: str, task_func: Callable[[], Any],
                     cron_expression: str, **kwargs) -> str:
        """
        Schedule a cron task
        
        Args:
            name: Task name
            task_func: Function to execute
            cron_expression: Cron expression
            **kwargs: Additional task parameters
            
        Returns:
            Task ID
        """
        task = ScheduledTask(
            task_id=str(uuid.uuid4()),
            name=name,
            task_func=task_func,
            task_type=TaskType.CRON,
            cron_expression=cron_expression,
            **kwargs
        )
        
        return self.schedule_task(task)
    
    def schedule_interval(self, name: str, task_func: Callable[[], Any],
                         interval_seconds: int, **kwargs) -> str:
        """
        Schedule an interval task
        
        Args:
            name: Task name
            task_func: Function to execute
            interval_seconds: Interval in seconds
            **kwargs: Additional task parameters
            
        Returns:
            Task ID
        """
        task = ScheduledTask(
            task_id=str(uuid.uuid4()),
            name=name,
            task_func=task_func,
            task_type=TaskType.INTERVAL,
            interval_seconds=interval_seconds,
            **kwargs
        )
        
        return self.schedule_task(task)
    
    def unschedule_task(self, task_id: str) -> bool:
        """
        Unschedule a task
        
        Args:
            task_id: Task ID to remove
            
        Returns:
            True if task was removed
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            
            # Cancel if currently running
            if task.last_execution and task.last_execution.status == TaskStatus.RUNNING:
                task.last_execution.status = TaskStatus.CANCELLED
            
            del self.tasks[task_id]
            logger.info(f"Unscheduled task {task_id}")
            return True
        
        logger.warning(f"Task {task_id} not found for unscheduling")
        return False
    
    def enable_task(self, task_id: str) -> bool:
        """Enable a task"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            self.tasks[task_id]._calculate_next_run()
            logger.info(f"Enabled task {task_id}")
            return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """Disable a task"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            logger.info(f"Disabled task {task_id}")
            return True
        return False
    
    async def execute_task(self, task: ScheduledTask) -> TaskExecution:
        """
        Execute a task
        
        Args:
            task: Task to execute
            
        Returns:
            Task execution record
        """
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        execution = TaskExecution(
            execution_id=execution_id,
            task_id=task.task_id,
            status=TaskStatus.RUNNING,
            started_at=start_time
        )
        
        # Update task state
        task.last_execution = execution
        task.execution_count += 1
        self.total_executions += 1
        
        try:
            # Execute task with timeout
            if asyncio.iscoroutinefunction(task.task_func):
                result = await asyncio.wait_for(
                    task.task_func(),
                    timeout=task.timeout_seconds
                )
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, task.task_func),
                    timeout=task.timeout_seconds
                )
            
            # Task completed successfully
            execution.status = TaskStatus.COMPLETED
            execution.result = result
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = (execution.completed_at - start_time).total_seconds()
            
            task.success_count += 1
            self.total_successes += 1
            
            logger.info(f"Task {task.task_id} completed successfully in {execution.duration_seconds:.2f}s")
            
        except asyncio.TimeoutError:
            execution.status = TaskStatus.FAILED
            execution.error = f"Task timed out after {task.timeout_seconds} seconds"
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = (execution.completed_at - start_time).total_seconds()
            
            task.failure_count += 1
            self.total_failures += 1
            
            logger.error(f"Task {task.task_id} timed out")
            
        except Exception as e:
            execution.status = TaskStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = (execution.completed_at - start_time).total_seconds()
            
            task.failure_count += 1
            self.total_failures += 1
            
            logger.error(f"Task {task.task_id} failed: {e}")
        
        # Update next run time
        task.update_next_run()
        
        # Add to history
        self.execution_history.append(execution)
        if len(self.execution_history) > self.max_history:
            self.execution_history = self.execution_history[-self.max_history:]
        
        return execution
    
    async def scheduler_loop(self):
        """Main scheduler loop"""
        logger.info("Task scheduler loop started")
        
        while self.running:
            try:
                current_time = datetime.utcnow()
                tasks_to_run = []
                
                # Find tasks that should run
                for task in self.tasks.values():
                    if task.should_run(current_time):
                        tasks_to_run.append(task)
                
                # Execute tasks
                for task in tasks_to_run:
                    try:
                        # Execute task asynchronously
                        asyncio.create_task(self.execute_task(task))
                    except Exception as e:
                        logger.error(f"Failed to start task {task.task_id}: {e}")
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(self.check_interval)
        
        logger.info("Task scheduler loop stopped")
    
    async def start(self):
        """Start the task scheduler"""
        if self.running:
            logger.warning("Task scheduler already running")
            return
        
        self.running = True
        self.scheduler_task = asyncio.create_task(self.scheduler_loop())
        logger.info("Task scheduler started")
    
    async def stop(self):
        """Stop the task scheduler"""
        if not self.running:
            return
        
        self.running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
            self.scheduler_task = None
        
        logger.info("Task scheduler stopped")
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    def get_tasks(self, enabled_only: bool = False, 
                 task_type: Optional[TaskType] = None,
                 tags: Optional[List[str]] = None) -> List[ScheduledTask]:
        """
        Get tasks with optional filtering
        
        Args:
            enabled_only: Only return enabled tasks
            task_type: Filter by task type
            tags: Filter by tags (task must have all specified tags)
            
        Returns:
            List of matching tasks
        """
        tasks = list(self.tasks.values())
        
        if enabled_only:
            tasks = [t for t in tasks if t.enabled]
        
        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        
        if tags:
            tasks = [t for t in tasks if all(tag in t.tags for tag in tags)]
        
        return tasks
    
    def get_execution_history(self, task_id: Optional[str] = None,
                            limit: int = 100) -> List[TaskExecution]:
        """
        Get execution history
        
        Args:
            task_id: Filter by task ID (optional)
            limit: Maximum number of executions to return
            
        Returns:
            List of task executions
        """
        executions = self.execution_history
        
        if task_id:
            executions = [e for e in executions if e.task_id == task_id]
        
        return executions[-limit:] if limit > 0 else executions
    
    def get_scheduler_stats(self) -> Dict[str, Any]:
        """
        Get scheduler statistics
        
        Returns:
            Scheduler statistics
        """
        enabled_tasks = len([t for t in self.tasks.values() if t.enabled])
        running_tasks = len([t for t in self.tasks.values() 
                           if t.last_execution and t.last_execution.status == TaskStatus.RUNNING])
        
        success_rate = self.total_successes / self.total_executions if self.total_executions > 0 else 0
        
        return {
            'running': self.running,
            'total_tasks': len(self.tasks),
            'enabled_tasks': enabled_tasks,
            'running_tasks': running_tasks,
            'total_executions': self.total_executions,
            'total_successes': self.total_successes,
            'total_failures': self.total_failures,
            'success_rate': success_rate,
            'execution_history_size': len(self.execution_history),
            'check_interval': self.check_interval,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def cleanup_old_executions(self, hours: int = 24):
        """
        Clean up old execution history
        
        Args:
            hours: Age threshold in hours
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        self.execution_history = [
            e for e in self.execution_history
            if e.started_at > cutoff_time
        ]
        
        logger.info(f"Cleaned up execution history older than {hours} hours")