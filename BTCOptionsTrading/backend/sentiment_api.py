#!/usr/bin/env python3
"""
情绪交易状态API
提供持仓、订单和交易历史的查询接口
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging
import os
from dotenv import load_dotenv

# 导入交易模块
import sys
sys.path.insert(0, str(Path(__file__).parent))

from src.trading.deribit_trader import DeribitTrader

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据文件路径
DATA_FILE = "data/sentiment_trading_history.json"
POSITION_FILE = "data/current_positions.json"

app = FastAPI(title="情绪交易状态API", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局trader实例
trader: Optional[DeribitTrader] = None


@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    global trader
    load_dotenv()
    
    api_key = os.getenv('DERIBIT_API_KEY')
    api_secret = os.getenv('DERIBIT_API_SECRET')
    
    if api_key and api_secret:
        trader = DeribitTrader(api_key, api_secret, testnet=True)
        try:
            await trader.authenticate()
            logger.info("Deribit认证成功")
        except Exception as e:
            logger.error(f"Deribit认证失败: {e}")


def load_json_file(filepath: str) -> Optional[Dict]:
    """加载JSON文件"""
    try:
        if Path(filepath).exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"加载文件失败 {filepath}: {e}")
    return None


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "情绪交易状态API",
        "version": "1.0.0",
        "endpoints": {
            "positions": "/api/positions - 获取当前持仓",
            "orders": "/api/orders - 获取未完成订单",
            "history": "/api/history - 获取交易历史",
            "status": "/api/status - 获取完整状态",
            "live_positions": "/api/live/positions - 实时获取持仓",
            "live_orders": "/api/live/orders - 实时获取订单"
        }
    }


@app.get("/api/positions")
async def get_positions():
    """获取当前持仓（从缓存文件）"""
    data = load_json_file(POSITION_FILE)
    if not data:
        raise HTTPException(status_code=404, detail="未找到持仓数据")
    
    return {
        "status": "success",
        "timestamp": data.get("timestamp"),
        "data": {
            "positions": data.get("positions", []),
            "position_count": data.get("position_count", 0),
            "errors": data.get("errors")
        }
    }


@app.get("/api/orders")
async def get_orders():
    """获取未完成订单（从缓存文件）"""
    data = load_json_file(POSITION_FILE)
    if not data:
        raise HTTPException(status_code=404, detail="未找到订单数据")
    
    return {
        "status": "success",
        "timestamp": data.get("timestamp"),
        "data": {
            "open_orders": data.get("open_orders", []),
            "order_count": data.get("order_count", 0),
            "errors": data.get("errors")
        }
    }


@app.get("/api/history")
async def get_history(limit: int = 10):
    """获取交易历史"""
    history = load_json_file(DATA_FILE)
    if not history:
        return {
            "status": "success",
            "data": {
                "trades": [],
                "total_count": 0
            }
        }
    
    # 返回最近的N条记录
    recent_trades = history[-limit:] if len(history) > limit else history
    
    return {
        "status": "success",
        "data": {
            "trades": recent_trades,
            "total_count": len(history),
            "returned_count": len(recent_trades)
        }
    }


@app.get("/api/status")
async def get_full_status():
    """获取完整状态（持仓、订单、历史）"""
    position_data = load_json_file(POSITION_FILE)
    history_data = load_json_file(DATA_FILE)
    
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "positions": {
                "items": position_data.get("positions", []) if position_data else [],
                "count": position_data.get("position_count", 0) if position_data else 0,
                "last_update": position_data.get("timestamp") if position_data else None
            },
            "orders": {
                "items": position_data.get("open_orders", []) if position_data else [],
                "count": position_data.get("order_count", 0) if position_data else 0,
                "last_update": position_data.get("timestamp") if position_data else None
            },
            "history": {
                "recent_trades": history_data[-5:] if history_data else [],
                "total_count": len(history_data) if history_data else 0
            },
            "errors": position_data.get("errors") if position_data else None
        }
    }


@app.get("/api/live/positions")
async def get_live_positions():
    """实时从Deribit获取持仓"""
    if not trader:
        raise HTTPException(status_code=503, detail="交易器未初始化")
    
    try:
        result = await trader._make_request(
            "private/get_positions",
            {"currency": "BTC", "kind": "option"}
        )
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "positions": result if result else [],
                "count": len(result) if result else 0
            }
        }
    except Exception as e:
        logger.error(f"获取实时持仓失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取持仓失败: {str(e)}")


@app.get("/api/live/orders")
async def get_live_orders():
    """实时从Deribit获取订单"""
    if not trader:
        raise HTTPException(status_code=503, detail="交易器未初始化")
    
    try:
        result = await trader._make_request(
            "private/get_open_orders_by_currency",
            {"currency": "BTC", "kind": "option"}
        )
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "orders": result if result else [],
                "count": len(result) if result else 0
            }
        }
    except Exception as e:
        logger.error(f"获取实时订单失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取订单失败: {str(e)}")


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "trader_initialized": trader is not None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5002)
