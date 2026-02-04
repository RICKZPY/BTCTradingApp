"""
Main application entry point for Bitcoin Trading System
"""
import asyncio
import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database.postgres import init_database, test_connection as test_postgres
from database.influxdb import influxdb_manager
from database.redis_client import redis_client


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management
    """
    # Startup
    logger.info("Starting Bitcoin Trading System")
    
    # Test database connections
    await startup_checks()
    
    # Initialize database
    init_database()
    
    logger.info("Bitcoin Trading System started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Bitcoin Trading System")
    
    # Close database connections
    influxdb_manager.close()
    redis_client.close()
    
    logger.info("Bitcoin Trading System shutdown complete")


async def startup_checks():
    """
    Perform startup health checks
    """
    logger.info("Performing startup health checks")
    
    # Test PostgreSQL connection
    if not test_postgres():
        logger.error("PostgreSQL connection failed")
        raise Exception("PostgreSQL connection failed")
    
    # Test InfluxDB connection
    if not influxdb_manager.test_connection():
        logger.warning("InfluxDB connection failed - time series data will not be available")
    
    # Test Redis connection
    if not redis_client.test_connection():
        logger.warning("Redis connection failed - caching and message queue will not be available")
    
    logger.info("Startup health checks completed")


# Create FastAPI application
app = FastAPI(
    title=settings.app.app_name,
    description="Automated Bitcoin Trading System with AI-powered sentiment analysis",
    version="1.0.0",
    debug=settings.app.debug,
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


@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "message": "Bitcoin Trading System API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    health_status = {
        "status": "healthy",
        "services": {
            "postgres": test_postgres(),
            "influxdb": influxdb_manager.test_connection(),
            "redis": redis_client.test_connection()
        }
    }
    
    # Overall health based on critical services
    if not health_status["services"]["postgres"]:
        health_status["status"] = "unhealthy"
    
    return health_status


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app.debug,
        log_level=settings.app.log_level.lower()
    )