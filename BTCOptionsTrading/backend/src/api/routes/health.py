"""
健康检查和状态接口
"""

from fastapi import APIRouter, Query
from datetime import datetime
from typing import Optional
from src.storage.database import get_db_manager
from src.storage.data_manager import DataManager
from src.monitoring import get_monitor

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    健康检查接口
    返回系统健康状态和性能指标
    """
    monitor = get_monitor()
    health_status = monitor.get_health_status()
    
    return {
        "status": health_status.status,
        "timestamp": health_status.timestamp,
        "service": "BTC Options Trading System",
        "checks": health_status.checks,
        "issues": health_status.issues
    }


@router.get("/status")
async def system_status():
    """
    系统状态接口
    返回详细的系统状态信息
    """
    monitor = get_monitor()
    
    try:
        # 获取数据库统计
        db_manager = get_db_manager()
        data_manager = DataManager(db_manager)
        db_stats = data_manager.get_database_stats()
        
        # 获取系统指标
        metrics = monitor.get_current_metrics()
        uptime = monitor.get_uptime()
        statistics = monitor.get_statistics()
        
        return {
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "uptime": uptime,
            "performance": {
                "cpu_percent": metrics.cpu_percent,
                "memory_percent": metrics.memory_percent,
                "memory_used_mb": metrics.memory_used_mb,
                "disk_usage_percent": metrics.disk_usage_percent,
                "active_connections": metrics.active_connections
            },
            "requests": {
                "total": statistics['total_requests'],
                "errors": statistics['total_errors'],
                "error_rate": statistics['error_rate'],
                "avg_response_time_ms": statistics['avg_response_time_ms']
            },
            "database": {
                "connected": True,
                "stats": db_stats
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


@router.get("/metrics")
async def get_metrics():
    """
    获取当前性能指标
    """
    monitor = get_monitor()
    metrics = monitor.get_current_metrics()
    
    return {
        "timestamp": metrics.timestamp,
        "cpu_percent": metrics.cpu_percent,
        "memory_percent": metrics.memory_percent,
        "memory_used_mb": metrics.memory_used_mb,
        "memory_available_mb": metrics.memory_available_mb,
        "disk_usage_percent": metrics.disk_usage_percent,
        "active_connections": metrics.active_connections,
        "request_count": metrics.request_count,
        "error_count": metrics.error_count,
        "avg_response_time_ms": metrics.avg_response_time_ms
    }


@router.get("/metrics/history")
async def get_metrics_history(minutes: Optional[int] = Query(10, ge=1, le=60)):
    """
    获取历史性能指标
    
    Args:
        minutes: 获取最近N分钟的数据（1-60分钟）
    """
    monitor = get_monitor()
    history = monitor.get_metrics_history(minutes=minutes)
    
    return {
        "period_minutes": minutes,
        "data_points": len(history),
        "history": history
    }


@router.get("/statistics")
async def get_statistics():
    """
    获取请求统计信息
    """
    monitor = get_monitor()
    statistics = monitor.get_statistics()
    uptime = monitor.get_uptime()
    
    return {
        "uptime": uptime,
        "requests": statistics
    }


@router.post("/metrics/reset")
async def reset_metrics():
    """
    重置监控计数器
    需要管理员权限（生产环境应添加认证）
    """
    monitor = get_monitor()
    monitor.reset_counters()
    
    return {
        "status": "success",
        "message": "Metrics counters reset",
        "timestamp": datetime.now().isoformat()
    }
