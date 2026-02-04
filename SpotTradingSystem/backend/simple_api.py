#!/usr/bin/env python3
"""
Simple API server for testing frontend connectivity
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn

app = FastAPI(title="Simple Bitcoin Trading API")

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
    return {"message": "Simple Bitcoin Trading API", "status": "running"}

@app.get("/api/v1/health/")
async def health_check():
    return {
        "success": True,
        "message": "API is healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/system/status")
async def get_system_status():
    return {
        "success": True,
        "message": "System status retrieved successfully",
        "data": {
            "system_state": "running",
            "start_time": datetime.utcnow().isoformat(),
            "uptime_seconds": 3600,
            "components": {
                "total": 5,
                "healthy": 5,
                "unhealthy": 0,
                "details": {
                    "data_collector": "healthy",
                    "news_analyzer": "healthy",
                    "decision_engine": "healthy",
                    "order_manager": "healthy",
                    "position_manager": "healthy"
                }
            }
        }
    }

@app.get("/api/v1/trading/portfolio")
async def get_portfolio():
    return {
        "success": True,
        "message": "Portfolio retrieved successfully",
        "data": {
            "portfolio": {
                "total_value": 10500.0,
                "available_balance": 5000.0,
                "positions": [
                    {
                        "symbol": "BTCUSDT",
                        "quantity": 0.1,
                        "average_price": 45000.0,
                        "current_price": 45500.0,
                        "current_value": 4550.0,
                        "unrealized_pnl": 50.0,
                        "unrealized_pnl_percent": 1.11,
                        "side": "LONG",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ],
                "total_unrealized_pnl": 50.0,
                "total_unrealized_pnl_percent": 0.48,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    }

@app.get("/api/v1/trading/market-data/{symbol}")
async def get_market_data(symbol: str):
    return {
        "success": True,
        "message": "Market data retrieved successfully",
        "data": {
            "data": {
                "symbol": symbol,
                "price": 45500.0,
                "volume": 1250.0,
                "change_24h": 500.0,
                "change_24h_percent": 1.11,
                "high_24h": 46000.0,
                "low_24h": 44500.0,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    }

if __name__ == "__main__":
    print("Starting Simple Bitcoin Trading API on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")