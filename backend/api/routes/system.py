"""
System management API routes
"""
import logging
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.models import (
    SystemStatusResponse, SystemMetrics, ConfigResponse, UpdateConfigRequest,
    SystemControlRequest, APIResponse, ErrorResponse, TradingConfig
)
from system_integration.trading_system_integration import TradingSystemIntegration

logger = logging.getLogger(__name__)

router = APIRouter()


def get_trading_system() -> TradingSystemIntegration:
    """Get trading system instance - placeholder for dependency injection"""
    # This will be injected by the main app
    from api.main import trading_system
    if trading_system is None:
        raise HTTPException(
            status_code=503,
            detail="Trading system is not available"
        )
    return trading_system


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    """
    Get comprehensive system status
    
    Returns:
        System status including components, metrics, and health information
    """
    try:
        system = get_trading_system()
        status = system.get_system_status()
        
        return SystemStatusResponse(
            message="System status retrieved successfully",
            system_state=status['system_coordinator']['system_state'],
            start_time=datetime.fromisoformat(status['system_coordinator']['start_time']) if status['system_coordinator']['start_time'] else None,
            uptime_seconds=status['system_coordinator']['uptime_seconds'],
            components=status['system_coordinator']['components'],
            event_bus=status['system_coordinator']['event_bus'],
            message_queue=status['system_coordinator']['message_queue'],
            task_scheduler=status['system_coordinator']['task_scheduler']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system status: {str(e)}"
        )


@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics():
    """
    Get system metrics for monitoring
    
    Returns:
        System performance and health metrics
    """
    try:
        system = get_trading_system()
        metrics = system.coordinator.get_metrics()
        
        return SystemMetrics(
            system_healthy=metrics['system_healthy'],
            uptime_seconds=metrics['uptime_seconds'],
            total_components=metrics['total_components'],
            healthy_components=metrics['healthy_components'],
            total_events=metrics['total_events'],
            total_messages=metrics['total_messages'],
            total_tasks=metrics['total_tasks'],
            event_success_rate=metrics['event_success_rate'],
            message_success_rate=metrics['message_success_rate'],
            task_success_rate=metrics['task_success_rate'],
            timestamp=datetime.fromisoformat(metrics['timestamp'])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system metrics: {str(e)}"
        )


@router.post("/control", response_model=APIResponse)
async def control_system(request: SystemControlRequest):
    """
    Control system operations (start, stop, restart)
    
    Args:
        request: System control request with action
        
    Returns:
        Operation result
    """
    try:
        system = get_trading_system()
        action = request.action.lower()
        
        if action == "start":
            await system.start()
            message = "System started successfully"
            
        elif action == "stop":
            await system.stop()
            message = "System stopped successfully"
            
        elif action == "restart":
            await system.stop()
            await system.start()
            message = "System restarted successfully"
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action: {action}. Valid actions: start, stop, restart"
            )
        
        return APIResponse(
            success=True,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error controlling system: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to control system: {str(e)}"
        )


@router.get("/config", response_model=ConfigResponse)
async def get_system_config():
    """
    Get current system configuration
    
    Returns:
        Current trading system configuration
    """
    try:
        system = get_trading_system()
        config = system.config
        
        trading_config = TradingConfig(
            max_position_size=config.max_position_size,
            stop_loss_percentage=config.stop_loss_percentage,
            min_confidence_threshold=config.min_confidence_threshold,
            market_data_interval=config.market_data_interval,
            news_collection_interval=config.news_collection_interval,
            decision_interval=config.decision_interval
        )
        
        return ConfigResponse(
            message="Configuration retrieved successfully",
            config=trading_config
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system config: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system config: {str(e)}"
        )


@router.put("/config", response_model=APIResponse)
async def update_system_config(request: UpdateConfigRequest):
    """
    Update system configuration
    
    Args:
        request: Configuration update request
        
    Returns:
        Update result
    """
    try:
        system = get_trading_system()
        
        # Update configuration
        system.config.max_position_size = request.config.max_position_size
        system.config.stop_loss_percentage = request.config.stop_loss_percentage
        system.config.min_confidence_threshold = request.config.min_confidence_threshold
        system.config.market_data_interval = request.config.market_data_interval
        system.config.news_collection_interval = request.config.news_collection_interval
        system.config.decision_interval = request.config.decision_interval
        
        logger.info("System configuration updated")
        
        return APIResponse(
            success=True,
            message="Configuration updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating system config: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update system config: {str(e)}"
        )


@router.get("/logs")
async def get_system_logs(lines: int = 100):
    """
    Get recent system logs
    
    Args:
        lines: Number of log lines to retrieve
        
    Returns:
        Recent system logs
    """
    try:
        # This is a placeholder - in a real implementation, you would
        # read from log files or a logging service
        
        return {
            "success": True,
            "message": f"Retrieved {lines} log lines",
            "logs": [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": "INFO",
                    "message": "System is running normally",
                    "component": "system"
                }
            ],
            "total_lines": 1
        }
        
    except Exception as e:
        logger.error(f"Error getting system logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system logs: {str(e)}"
        )