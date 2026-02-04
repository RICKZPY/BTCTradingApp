"""
Example of how to integrate security and configuration management
with the existing FastAPI application
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import logging

from .middleware import SecurityMiddleware, create_security_exception_handler
from .integration import get_secure_config_service

logger = logging.getLogger(__name__)


def setup_security_for_app(app: FastAPI) -> None:
    """
    Setup security middleware and handlers for FastAPI app
    
    Args:
        app: FastAPI application instance
    """
    # Add security middleware
    app.add_middleware(
        SecurityMiddleware,
        excluded_paths=["/health", "/docs", "/openapi.json", "/redoc"]
    )
    
    # Add security exception handler
    app.add_exception_handler(HTTPException, create_security_exception_handler())
    
    logger.info("Security middleware and handlers configured")


def create_secure_api_routes(app: FastAPI) -> None:
    """
    Create API routes for security and configuration management
    
    Args:
        app: FastAPI application instance
    """
    
    @app.get("/api/security/status")
    async def get_security_status():
        """Get current security status"""
        try:
            service = get_secure_config_service()
            status = service.get_security_status()
            return status
        except Exception as e:
            logger.error(f"Failed to get security status: {e}")
            raise HTTPException(status_code=500, detail="Failed to get security status")
    
    @app.get("/api/security/alerts")
    async def get_security_alerts(severity: str = None, hours: int = 24):
        """Get security alerts"""
        try:
            service = get_secure_config_service()
            from datetime import datetime, timedelta
            
            since = datetime.now() - timedelta(hours=hours) if hours else None
            alerts = service.security_manager.get_security_alerts(
                severity=severity,
                since=since
            )
            
            # Convert alerts to dict for JSON serialization
            alert_dicts = []
            for alert in alerts:
                alert_dicts.append({
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "details": alert.details
                })
            
            return {"alerts": alert_dicts}
            
        except Exception as e:
            logger.error(f"Failed to get security alerts: {e}")
            raise HTTPException(status_code=500, detail="Failed to get security alerts")
    
    @app.get("/api/config")
    async def get_configuration(section: str = None):
        """Get current configuration"""
        try:
            service = get_secure_config_service()
            config = service.config_manager.get_configuration(section=section)
            return {"configuration": config}
        except Exception as e:
            logger.error(f"Failed to get configuration: {e}")
            raise HTTPException(status_code=500, detail="Failed to get configuration")
    
    @app.post("/api/config/backup")
    async def create_config_backup(description: str = ""):
        """Create configuration backup"""
        try:
            service = get_secure_config_service()
            backup_id = service.create_configuration_backup(description)
            return {"backup_id": backup_id, "message": "Backup created successfully"}
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise HTTPException(status_code=500, detail="Failed to create backup")
    
    @app.get("/api/config/backups")
    async def list_config_backups():
        """List available configuration backups"""
        try:
            service = get_secure_config_service()
            backups = service.config_manager.list_backups()
            
            # Convert backups to dict for JSON serialization
            backup_dicts = []
            for backup in backups:
                backup_dicts.append({
                    "backup_id": backup.backup_id,
                    "timestamp": backup.timestamp.isoformat(),
                    "description": backup.description,
                    "config_hash": backup.config_hash
                })
            
            return {"backups": backup_dicts}
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            raise HTTPException(status_code=500, detail="Failed to list backups")


# Example of how to use in main.py
def example_main():
    """Example of how to integrate security in main FastAPI app"""
    
    app = FastAPI(title="Bitcoin Trading System", version="1.0.0")
    
    # Setup security
    setup_security_for_app(app)
    
    # Create security API routes
    create_secure_api_routes(app)
    
    # Your existing routes would go here
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    @app.get("/api/portfolio")
    async def get_portfolio():
        # This endpoint will be protected by security middleware
        return {"portfolio": "data"}
    
    return app


if __name__ == "__main__":
    import uvicorn
    
    app = example_main()
    uvicorn.run(app, host="0.0.0.0", port=8000)