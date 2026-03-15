#!/usr/bin/env python3
"""
加权情绪跨式期权交易 - 状态查询 API
Status query API for weighted sentiment straddle trading system

提供持仓、订单、交易历史和系统状态的查询接口
使用独立的 Deribit Test 账户（0366QIa2）

端口: 5004
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging
import os
import sys
from dotenv import load_dotenv

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

# 直接导入 DeribitTrader，避免触发包的 __init__.py
import importlib.util
spec = importlib.util.spec_from_file_location(
    "deribit_trader",
    Path(__file__).parent / "src" / "trading" / "deribit_trader.py"
)
deribit_trader_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deribit_trader_module)
DeribitTrader = deribit_trader_module.DeribitTrader

from weighted_sentiment_news_tracker import NewsTracker

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据文件路径
LOG_DIR = Path(__file__).parent / "logs"
TRADE_LOG_FILE = LOG_DIR / "weighted_sentiment_trades.log"
CRON_LOG_FILE = LOG_DIR / "weighted_sentiment_cron.log"

app = FastAPI(
    title="加权情绪跨式期权交易状态API",
    version="2.0.0",
    description="独立的加权情绪交易系统状态查询接口（账户: 0366QIa2）"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局实例
trader: Optional[DeribitTrader] = None
news_tracker: Optional[NewsTracker] = None


@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    global trader, news_tracker
    load_dotenv()
    
    # 使用加权情绪系统的独立凭证
    api_key = os.getenv('WEIGHTED_SENTIMENT_DERIBIT_API_KEY')
    api_secret = os.getenv('WEIGHTED_SENTIMENT_DERIBIT_API_SECRET')
    
    if api_key and api_secret:
        trader = DeribitTrader(api_key, api_secret, testnet=True)
        try:
            await trader.authenticate()
            logger.info("加权情绪系统 Deribit 测试网认证成功（账户: 0366QIa2）")
        except Exception as e:
            logger.error(f"Deribit 测试网认证失败: {e}")
            trader = None
    else:
        logger.warning("未配置 WEIGHTED_SENTIMENT_DERIBIT_API_KEY，实时功能将不可用")
    
    # 初始化新闻追踪器
    try:
        news_tracker = NewsTracker()
        logger.info("新闻追踪器初始化成功")
    except Exception as e:
        logger.error(f"新闻追踪器初始化失败: {e}")
        news_tracker = None


def parse_trade_log() -> List[Dict]:
    """解析交易日志文件"""
    if not TRADE_LOG_FILE.exists():
        return []
    
    try:
        with open(TRADE_LOG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 按分隔符分割交易记录
        trade_entries = content.split('='*80)
        
        trades = []
        for entry in trade_entries:
            entry = entry.strip()
            if not entry:
                continue
            
            # 提取关键信息
            trade_info = {}
            for line in entry.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    trade_info[key.strip()] = value.strip()
            
            if trade_info:
                trades.append(trade_info)
        
        return trades
    
    except Exception as e:
        logger.error(f"解析交易日志失败: {e}")
        return []


def get_last_run_time() -> str:
    """获取最后执行时间"""
    if not CRON_LOG_FILE.exists():
        return "未知"
    
    try:
        with open(CRON_LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in reversed(lines[-100:]):
                if "执行时间:" in line:
                    parts = line.split("执行时间:")
                    if len(parts) > 1:
                        return parts[1].strip()
        return "未知"
    except Exception as e:
        logger.error(f"读取执行时间失败: {e}")
        return "错误"


@app.get("/", response_class=HTMLResponse)
async def root():
    """根路径 - 返回 HTML 页面"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>加权情绪跨式期权交易 - 状态 API</title>
        <meta charset="utf-8">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            }
            h1 {
                color: #333;
                border-bottom: 3px solid #667eea;
                padding-bottom: 10px;
            }
            h2 {
                color: #555;
                margin-top: 30px;
            }
            .info-box {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin: 15px 0;
                border-left: 4px solid #667eea;
            }
            .endpoint {
                background: #fff;
                border: 1px solid #e0e0e0;
                padding: 15px;
                margin: 10px 0;
                border-radius: 5px;
                transition: all 0.3s;
            }
            .endpoint:hover {
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                transform: translateY(-2px);
            }
            .endpoint h3 {
                margin-top: 0;
                color: #667eea;
            }
            .endpoint a {
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 8px 16px;
                text-decoration: none;
                border-radius: 4px;
                margin-top: 10px;
                transition: background 0.3s;
            }
            .endpoint a:hover {
                background: #764ba2;
            }
            code {
                background: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }
            .badge {
                display: inline-block;
                background: #28a745;
                color: white;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
            .account-info {
                background: #fff3cd;
                border: 1px solid #ffc107;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 加权情绪跨式期权交易 - 状态 API</h1>
            <span class="badge">V2.0</span>
            
            <div class="info-box">
                <p><strong>服务说明：</strong>独立的加权情绪交易系统状态查询接口</p>
                <p><strong>端口：</strong>5004</p>
                <p><strong>环境：</strong>Deribit Test</p>
            </div>
            
            <div class="account-info">
                <p><strong>⚠️ 账户隔离：</strong>本 API 使用独立的 Deribit Test 账户（0366QIa2），与 sentiment_trading_api（端口 5002）完全分离</p>
            </div>
            
            <h2>📡 可用端点</h2>
            
            <div class="endpoint">
                <h3>GET /api/status</h3>
                <p>获取系统完整状态（持仓、订单、交易历史、新闻统计）</p>
                <a href="/api/status">查看状态</a>
            </div>
            
            <div class="endpoint">
                <h3>GET /api/positions</h3>
                <p>实时获取当前持仓</p>
                <a href="/api/positions">查看持仓</a>
            </div>
            
            <div class="endpoint">
                <h3>GET /api/orders</h3>
                <p>实时获取未完成订单</p>
                <a href="/api/orders">查看订单</a>
            </div>
            
            <div class="endpoint">
                <h3>GET /api/trades</h3>
                <p>获取交易历史记录（最多10条）</p>
                <a href="/api/trades">查看交易</a>
            </div>
            
            <div class="endpoint">
                <h3>GET /api/news/history</h3>
                <p>获取新闻处理统计</p>
                <a href="/api/news/history">查看统计</a>
            </div>
            
            <div class="endpoint">
                <h3>GET /api/account</h3>
                <p>获取账户摘要信息</p>
                <a href="/api/account">查看账户</a>
            </div>
            
            <div class="endpoint">
                <h3>GET /api/health</h3>
                <p>健康检查</p>
                <a href="/api/health">检查健康</a>
            </div>
            
            <h2>🔗 相关服务</h2>
            <div class="info-box">
                <p><strong>情绪交易 API：</strong><a href="http://localhost:5002" target="_blank">http://localhost:5002</a> （账户: vXkaBDto）</p>
                <p><strong>加权情绪交易 API：</strong><a href="http://localhost:5004" target="_blank">http://localhost:5004</a> （账户: 0366QIa2）</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/api/status")
async def get_full_status():
    """获取完整状态（持仓、订单、交易历史、新闻统计）"""
    try:
        # 获取持仓
        positions = []
        position_count = 0
        if trader:
            try:
                result = await trader._make_request(
                    "get_positions",
                    {"currency": "BTC", "kind": "option"}
                )
                if result:
                    positions = result
                    position_count = len(result)
            except Exception as e:
                logger.error(f"获取持仓失败: {e}")
        
        # 获取订单
        orders = []
        order_count = 0
        if trader:
            try:
                result = await trader._make_request(
                    "get_open_orders_by_currency",
                    {"currency": "BTC", "kind": "option"}
                )
                if result:
                    orders = result
                    order_count = len(result)
            except Exception as e:
                logger.error(f"获取订单失败: {e}")
        
        # 获取交易历史
        trades = parse_trade_log()
        recent_trades = trades[-5:] if trades else []
        
        # 获取新闻统计
        total_news = news_tracker.get_history_count() if news_tracker else 0
        
        # 获取最后执行时间
        last_run = get_last_run_time()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "account": "0366QIa2",
            "system": {
                "service": "weighted-sentiment-straddle-trading",
                "version": "2.0.0",
                "last_run": last_run,
                "trader_connected": trader is not None
            },
            "data": {
                "positions": {
                    "items": positions,
                    "count": position_count
                },
                "orders": {
                    "items": orders,
                    "count": order_count
                },
                "trades": {
                    "recent": recent_trades,
                    "total_count": len(trades)
                },
                "news": {
                    "total_processed": total_news
                }
            }
        }
    
    except Exception as e:
        logger.error(f"获取完整状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@app.get("/api/positions")
async def get_positions():
    """实时获取当前持仓"""
    if not trader:
        raise HTTPException(status_code=503, detail="交易器未初始化")
    
    try:
        result = await trader._make_request(
            "get_positions",
            {"currency": "BTC", "kind": "option"}
        )
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "account": "0366QIa2",
            "data": {
                "positions": result if result else [],
                "count": len(result) if result else 0
            }
        }
    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取持仓失败: {str(e)}")


@app.get("/api/orders")
async def get_orders():
    """实时获取未完成订单"""
    if not trader:
        raise HTTPException(status_code=503, detail="交易器未初始化")
    
    try:
        result = await trader._make_request(
            "get_open_orders_by_currency",
            {"currency": "BTC", "kind": "option"}
        )
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "account": "0366QIa2",
            "data": {
                "orders": result if result else [],
                "count": len(result) if result else 0
            }
        }
    except Exception as e:
        logger.error(f"获取订单失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取订单失败: {str(e)}")


@app.get("/api/trades")
async def get_trades(limit: int = 10):
    """获取交易历史记录"""
    try:
        trades = parse_trade_log()
        
        # 返回最近的N条记录
        recent_trades = trades[-limit:] if len(trades) > limit else trades
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "account": "0366QIa2",
            "data": {
                "trades": recent_trades,
                "total_count": len(trades),
                "returned_count": len(recent_trades)
            }
        }
    except Exception as e:
        logger.error(f"获取交易历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取交易历史失败: {str(e)}")


@app.get("/api/news/history")
async def get_news_history():
    """获取新闻处理统计"""
    if not news_tracker:
        raise HTTPException(status_code=503, detail="新闻追踪器未初始化")
    
    try:
        total_news = news_tracker.get_history_count()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "total_news_processed": total_news,
                "high_score_threshold": 7
            }
        }
    except Exception as e:
        logger.error(f"获取新闻统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取新闻统计失败: {str(e)}")


@app.get("/api/account")
async def get_account_summary():
    """获取账户摘要信息"""
    if not trader:
        raise HTTPException(status_code=503, detail="交易器未初始化")
    
    try:
        result = await trader.get_account_summary("BTC")
        
        if not result:
            raise HTTPException(status_code=500, detail="无法获取账户信息")
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "account": "0366QIa2",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取账户信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取账户信息失败: {str(e)}")


@app.get("/api/health")
async def health_check():
    """健康检查"""
    load_dotenv()
    
    # 检查配置
    has_config = bool(
        os.getenv('WEIGHTED_SENTIMENT_DERIBIT_API_KEY') and 
        os.getenv('WEIGHTED_SENTIMENT_DERIBIT_API_SECRET')
    )
    
    # 检查日志文件
    trade_log_exists = TRADE_LOG_FILE.exists()
    cron_log_exists = CRON_LOG_FILE.exists()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "weighted-sentiment-straddle-trading",
        "version": "2.0.0",
        "account": "0366QIa2",
        "checks": {
            "trader_initialized": trader is not None,
            "news_tracker_initialized": news_tracker is not None,
            "has_api_config": has_config,
            "trade_log_exists": trade_log_exists,
            "cron_log_exists": cron_log_exists
        },
        "last_run": get_last_run_time()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5004)

