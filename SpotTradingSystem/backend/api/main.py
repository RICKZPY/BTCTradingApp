"""
FastAPI main application
"""
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routes import system, trading, analysis, health, websocket, backtesting
from api.models import ErrorResponse
from api.websocket import initialize_websocket_manager
from system_integration.trading_system_integration import TradingSystemIntegration, TradingSystemConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global trading system instance
trading_system: TradingSystemIntegration = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global trading_system
    
    # Startup
    logger.info("Starting Bitcoin Trading System API")
    
    try:
        # Initialize trading system with default config
        config = TradingSystemConfig()
        trading_system = TradingSystemIntegration(config)
        
        # Start the trading system
        await trading_system.start()
        logger.info("Trading system started successfully")
        
        # Initialize WebSocket manager with trading system
        initialize_websocket_manager(trading_system)
        logger.info("WebSocket manager initialized")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start trading system: {e}")
        # Continue without trading system for API-only mode
        yield
    
    finally:
        # Shutdown
        logger.info("Shutting down Bitcoin Trading System API")
        
        if trading_system:
            try:
                await trading_system.stop()
                logger.info("Trading system stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping trading system: {e}")


# Create FastAPI application
app = FastAPI(
    title="Bitcoin Trading System API",
    description="REST API for Bitcoin Trading System with automated trading capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get trading system instance
def get_trading_system() -> TradingSystemIntegration:
    """Get trading system instance"""
    if trading_system is None:
        raise HTTPException(
            status_code=503,
            detail="Trading system is not available"
        )
    return trading_system


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            message="Internal server error",
            error_code="INTERNAL_ERROR",
            details={"error": str(exc)}
        ).dict()
    )


# HTTP exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            message=exc.detail,
            error_code=f"HTTP_{exc.status_code}",
            details={"status_code": exc.status_code}
        ).dict()
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Bitcoin Trading System API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


# Include routers
app.include_router(
    system.router,
    prefix="/api/v1/system",
    tags=["System"]
)

app.include_router(
    trading.router,
    prefix="/api/v1/trading",
    tags=["Trading"]
)

app.include_router(
    analysis.router,
    prefix="/api/v1/analysis",
    tags=["Analysis"]
)

app.include_router(
    health.router,
    prefix="/api/v1/health",
    tags=["Health"]
)

app.include_router(
    websocket.router,
    prefix="/api/v1/ws",
    tags=["WebSocket"]
)

app.include_router(
    backtesting.router,
    prefix="/api/v1/backtesting",
    tags=["Backtesting"]
)


# Development server
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )