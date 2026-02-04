"""
Health check API routes
"""
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.models import HealthCheckResponse, ComponentStatus, SystemMetrics
from system_integration.trading_system_integration import TradingSystemIntegration

logger = logging.getLogger(__name__)

router = APIRouter()


def get_trading_system() -> TradingSystemIntegration:
    """Get trading system instance"""
    from api.main import trading_system
    if trading_system is None:
        raise HTTPException(
            status_code=503,
            detail="Trading system is not available"
        )
    return trading_system


@router.get("/", response_model=HealthCheckResponse)
async def health_check():
    """
    Comprehensive health check
    
    Returns:
        System health status with component details
    """
    try:
        system = get_trading_system()
        
        # Get system status
        status = system.coordinator.get_system_status()
        metrics = system.coordinator.get_metrics()
        
        # Convert component status
        components = []
        for name, comp_status in status['components']['details'].items():
            components.append(ComponentStatus(
                name=comp_status['name'],
                status=comp_status['status'],
                healthy=comp_status['healthy'],
                last_check=datetime.fromisoformat(comp_status['last_check']),
                error=comp_status.get('error'),
                metadata=comp_status.get('metadata', {})
            ))
        
        # Create system metrics
        system_metrics = SystemMetrics(
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
        
        return HealthCheckResponse(
            message="Health check completed",
            healthy=system.coordinator.is_healthy(),
            components=components,
            system_metrics=system_metrics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        
        # Return unhealthy status
        return HealthCheckResponse(
            success=False,
            message=f"Health check failed: {str(e)}",
            healthy=False,
            components=[],
            system_metrics=SystemMetrics(
                system_healthy=False,
                uptime_seconds=0.0,
                total_components=0,
                healthy_components=0,
                total_events=0,
                total_messages=0,
                total_tasks=0,
                event_success_rate=0.0,
                message_success_rate=0.0,
                task_success_rate=0.0,
                timestamp=datetime.utcnow()
            )
        )


@router.get("/simple")
async def simple_health_check():
    """
    Simple health check endpoint
    
    Returns:
        Basic health status
    """
    try:
        system = get_trading_system()
        is_healthy = system.coordinator.is_healthy()
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "bitcoin-trading-system"
        }
        
    except Exception as e:
        logger.error(f"Simple health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "bitcoin-trading-system",
            "error": str(e)
        }


@router.get("/components/{component_name}")
async def check_component_health(component_name: str):
    """
    Check health of a specific component
    
    Args:
        component_name: Name of the component to check
        
    Returns:
        Component health status
    """
    try:
        system = get_trading_system()
        
        # Trigger health check for specific component
        await system.coordinator.trigger_health_check(component_name)
        
        # Get component status
        comp_status = system.coordinator.get_component_status(component_name)
        
        if not comp_status:
            raise HTTPException(
                status_code=404,
                detail=f"Component '{component_name}' not found"
            )
        
        return {
            "success": True,
            "message": f"Component '{component_name}' health check completed",
            "component": ComponentStatus(
                name=comp_status['name'],
                status=comp_status['status'],
                healthy=comp_status['healthy'],
                last_check=datetime.fromisoformat(comp_status['last_check']),
                error=comp_status.get('error'),
                metadata=comp_status.get('metadata', {})
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Component health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check component health: {str(e)}"
        )


@router.get("/readiness")
async def readiness_check():
    """
    Kubernetes readiness probe endpoint
    
    Returns:
        Readiness status
    """
    try:
        system = get_trading_system()
        
        # Check if system is ready to serve requests
        status = system.coordinator.get_system_status()
        is_ready = status['system_state'] in ['running']
        
        if is_ready:
            return {
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=503,
                detail=f"System not ready. Current state: {status['system_state']}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"System not ready: {str(e)}"
        )


@router.get("/liveness")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint
    
    Returns:
        Liveness status
    """
    try:
        # Basic liveness check - just verify the API is responding
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Liveness check failed: {str(e)}"
        )