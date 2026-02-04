#!/usr/bin/env python3
"""
Simple API server startup script for testing
Avoids complex dependencies that cause issues
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime

# Create a minimal API for testing
app = FastAPI(title="Bitcoin Trading System API - Test Mode")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Bitcoin Trading System API",
        "version": "1.0.0",
        "status": "running",
        "mode": "test",
        "timestamp": datetime.utcnow().isoformat()
    }

# Import and include backtest routes
try:
    from api.routes.backtesting import router as backtest_router
    app.include_router(
        backtest_router,
        prefix="/api/v1/backtesting",
        tags=["Backtesting"]
    )
    print("✅ Backtest routes loaded successfully")
except Exception as e:
    print(f"⚠️  Could not load backtest routes: {e}")
    
    # Create fallback endpoints
    @app.get("/api/v1/backtesting/status")
    async def fallback_status():
        return {
            "success": False,
            "message": "Backtesting not available",
            "data": {"available": False, "reason": str(e)}
        }
    
    @app.post("/api/v1/backtesting/run")
    async def fallback_run():
        return {
            "success": False,
            "message": "Backtesting not available",
            "error": str(e)
        }

# Add health check
@app.get("/api/v1/health/simple")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "bitcoin-trading-system"
    }

if __name__ == "__main__":
    print("🚀 Starting Simple Bitcoin Trading API Server")
    print("=" * 50)
    print("📍 Server will be available at: http://localhost:8001")
    print("📚 API Documentation: http://localhost:8001/docs")
    print("🔧 Test Mode: Minimal dependencies")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )