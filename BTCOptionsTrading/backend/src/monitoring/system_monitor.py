"""
系统监控模块
提供性能监控、健康检查和错误追踪功能
"""

import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque
from dataclasses import dataclass, asdict

from src.config.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    active_connections: int
    request_count: int
    error_count: int
    avg_response_time_ms: float


@dataclass
class HealthStatus:
    """健康状态"""
    status: str  # healthy, degraded, unhealthy
    timestamp: str
    checks: Dict[str, bool]
    metrics: Dict[str, any]
    issues: List[str]


class SystemMonitor:
    """系统监控器"""
    
    def __init__(self, max_history: int = 100):
        """
        初始化系统监控器
        
        Args:
            max_history: 保留的历史记录数量
        """
        self.max_history = max_history
        self.metrics_history = deque(maxlen=max_history)
        self.request_times = deque(maxlen=1000)  # 最近1000个请求的响应时间
        self.error_count = 0
        self.request_count = 0
        self.start_time = datetime.now()
        
        # 健康检查阈值
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_usage_percent': 90.0,
            'error_rate': 0.05,  # 5%错误率
            'avg_response_time_ms': 1000.0  # 1秒
        }
        
        logger.info("System monitor initialized")
    
    def record_request(self, response_time_ms: float, is_error: bool = False):
        """
        记录请求
        
        Args:
            response_time_ms: 响应时间（毫秒）
            is_error: 是否为错误请求
        """
        self.request_count += 1
        self.request_times.append(response_time_ms)
        
        if is_error:
            self.error_count += 1
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """获取当前性能指标"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        memory_available_mb = memory.available / (1024 * 1024)
        
        # 磁盘使用情况
        disk = psutil.disk_usage('/')
        disk_usage_percent = disk.percent
        
        # 网络连接数
        try:
            connections = len(psutil.net_connections())
        except:
            connections = 0
        
        # 平均响应时间
        avg_response_time = sum(self.request_times) / len(self.request_times) if self.request_times else 0.0
        
        metrics = PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            disk_usage_percent=disk_usage_percent,
            active_connections=connections,
            request_count=self.request_count,
            error_count=self.error_count,
            avg_response_time_ms=avg_response_time
        )
        
        # 保存到历史记录
        self.metrics_history.append(metrics)
        
        return metrics
    
    def get_health_status(self) -> HealthStatus:
        """获取系统健康状态"""
        metrics = self.get_current_metrics()
        
        # 执行健康检查
        checks = {
            'cpu': metrics.cpu_percent < self.thresholds['cpu_percent'],
            'memory': metrics.memory_percent < self.thresholds['memory_percent'],
            'disk': metrics.disk_usage_percent < self.thresholds['disk_usage_percent'],
            'error_rate': self._get_error_rate() < self.thresholds['error_rate'],
            'response_time': metrics.avg_response_time_ms < self.thresholds['avg_response_time_ms']
        }
        
        # 收集问题
        issues = []
        if not checks['cpu']:
            issues.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
        if not checks['memory']:
            issues.append(f"High memory usage: {metrics.memory_percent:.1f}%")
        if not checks['disk']:
            issues.append(f"High disk usage: {metrics.disk_usage_percent:.1f}%")
        if not checks['error_rate']:
            issues.append(f"High error rate: {self._get_error_rate():.2%}")
        if not checks['response_time']:
            issues.append(f"Slow response time: {metrics.avg_response_time_ms:.1f}ms")
        
        # 确定整体状态
        if all(checks.values()):
            status = "healthy"
        elif sum(checks.values()) >= len(checks) * 0.6:  # 60%以上检查通过
            status = "degraded"
        else:
            status = "unhealthy"
        
        return HealthStatus(
            status=status,
            timestamp=datetime.now().isoformat(),
            checks=checks,
            metrics=asdict(metrics),
            issues=issues
        )
    
    def get_uptime(self) -> Dict[str, any]:
        """获取系统运行时间"""
        uptime = datetime.now() - self.start_time
        
        return {
            'start_time': self.start_time.isoformat(),
            'uptime_seconds': uptime.total_seconds(),
            'uptime_formatted': str(uptime).split('.')[0]  # 去掉微秒
        }
    
    def get_statistics(self) -> Dict[str, any]:
        """获取统计信息"""
        error_rate = self._get_error_rate()
        
        return {
            'total_requests': self.request_count,
            'total_errors': self.error_count,
            'error_rate': error_rate,
            'success_rate': 1.0 - error_rate,
            'avg_response_time_ms': sum(self.request_times) / len(self.request_times) if self.request_times else 0.0,
            'min_response_time_ms': min(self.request_times) if self.request_times else 0.0,
            'max_response_time_ms': max(self.request_times) if self.request_times else 0.0
        }
    
    def get_metrics_history(self, minutes: int = 10) -> List[Dict]:
        """
        获取历史指标
        
        Args:
            minutes: 获取最近N分钟的数据
            
        Returns:
            历史指标列表
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        history = []
        for metrics in self.metrics_history:
            timestamp = datetime.fromisoformat(metrics.timestamp)
            if timestamp >= cutoff_time:
                history.append(asdict(metrics))
        
        return history
    
    def _get_error_rate(self) -> float:
        """计算错误率"""
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count
    
    def reset_counters(self):
        """重置计数器"""
        self.request_count = 0
        self.error_count = 0
        self.request_times.clear()
        logger.info("Monitor counters reset")


# 全局监控器实例
_monitor = None


def get_monitor() -> SystemMonitor:
    """获取全局监控器实例"""
    global _monitor
    if _monitor is None:
        _monitor = SystemMonitor()
    return _monitor
