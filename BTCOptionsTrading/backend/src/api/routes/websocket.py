"""
WebSocket路由 - 实时数据推送
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import json
from datetime import datetime

from src.config.logging_config import get_logger
from src.connectors.deribit_connector import DeribitConnector
from src.config.settings import Settings

logger = get_logger(__name__)

router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 存储活跃的WebSocket连接
        self.active_connections: Set[WebSocket] = set()
        # 存储每个连接订阅的数据类型
        self.subscriptions: Dict[WebSocket, Set[str]] = {}
        
    async def connect(self, websocket: WebSocket):
        """接受新的WebSocket连接"""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.subscriptions[websocket] = set()
        logger.info(f"New WebSocket connection. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        self.active_connections.discard(websocket)
        self.subscriptions.pop(websocket, None)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
        
    def subscribe(self, websocket: WebSocket, channel: str):
        """订阅数据频道"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].add(channel)
            logger.info(f"WebSocket subscribed to channel: {channel}")
            
    def unsubscribe(self, websocket: WebSocket, channel: str):
        """取消订阅数据频道"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].discard(channel)
            logger.info(f"WebSocket unsubscribed from channel: {channel}")
            
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送消息给特定连接"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message to websocket: {str(e)}")
            
    async def broadcast(self, message: dict, channel: str = None):
        """广播消息给所有订阅了指定频道的连接"""
        disconnected = []
        for connection in self.active_connections:
            # 如果指定了频道，只发送给订阅了该频道的连接
            if channel and channel not in self.subscriptions.get(connection, set()):
                continue
                
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to websocket: {str(e)}")
                disconnected.append(connection)
                
        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection)


# 全局连接管理器实例
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket端点 - 处理实时数据推送
    
    客户端可以发送以下消息格式：
    {
        "action": "subscribe" | "unsubscribe" | "ping",
        "channel": "options_chain" | "portfolio" | "market_data",
        "params": {...}  # 可选参数
    }
    
    服务器推送消息格式：
    {
        "type": "options_chain" | "portfolio" | "market_data" | "error" | "pong",
        "data": {...},
        "timestamp": "2024-02-09T12:00:00Z"
    }
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            action = message.get("action")
            channel = message.get("channel")
            
            if action == "subscribe":
                if channel:
                    manager.subscribe(websocket, channel)
                    await manager.send_personal_message({
                        "type": "subscription_confirmed",
                        "channel": channel,
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
                else:
                    await manager.send_personal_message({
                        "type": "error",
                        "message": "Channel is required for subscription",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
                    
            elif action == "unsubscribe":
                if channel:
                    manager.unsubscribe(websocket, channel)
                    await manager.send_personal_message({
                        "type": "subscription_cancelled",
                        "channel": channel,
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
                    
            elif action == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
                
            else:
                await manager.send_personal_message({
                    "type": "error",
                    "message": f"Unknown action: {action}",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", exc_info=True)
        manager.disconnect(websocket)


async def start_market_data_stream():
    """
    启动市场数据流
    定期从Deribit获取数据并推送给订阅的客户端
    """
    settings = Settings()
    connector = DeribitConnector(settings)
    
    while True:
        try:
            # 如果有客户端订阅了market_data频道
            if any("market_data" in subs for subs in manager.subscriptions.values()):
                # 获取BTC价格
                try:
                    price_data = await connector.get_underlying_price("BTC")
                    await manager.broadcast({
                        "type": "market_data",
                        "data": {
                            "symbol": "BTC",
                            "price": price_data.get("price"),
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        "timestamp": datetime.utcnow().isoformat()
                    }, channel="market_data")
                except Exception as e:
                    logger.error(f"Error fetching market data: {str(e)}")
                    
            # 每5秒更新一次
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"Error in market data stream: {str(e)}")
            await asyncio.sleep(5)


async def start_options_chain_stream():
    """
    启动期权链数据流
    定期更新期权链数据并推送给订阅的客户端
    """
    settings = Settings()
    connector = DeribitConnector(settings)
    
    while True:
        try:
            # 如果有客户端订阅了options_chain频道
            if any("options_chain" in subs for subs in manager.subscriptions.values()):
                # 获取期权链数据
                try:
                    options_data = await connector.get_options_chain("BTC")
                    await manager.broadcast({
                        "type": "options_chain",
                        "data": {
                            "currency": "BTC",
                            "options": options_data[:10],  # 只发送前10个合约，避免数据量过大
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        "timestamp": datetime.utcnow().isoformat()
                    }, channel="options_chain")
                except Exception as e:
                    logger.error(f"Error fetching options chain: {str(e)}")
                    
            # 每10秒更新一次
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"Error in options chain stream: {str(e)}")
            await asyncio.sleep(10)
