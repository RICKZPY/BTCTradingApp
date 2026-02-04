"""
WebSocket implementation for real-time data streaming
"""
import logging
import asyncio
import json
from typing import Dict, List, Set, Any, Optional
from datetime import datetime
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from system_integration.event_bus import Event, EventType
from system_integration.trading_system_integration import TradingSystemIntegration

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WebSocket message types"""
    # Client to server
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PING = "ping"
    
    # Server to client
    PRICE_UPDATE = "price_update"
    ORDER_UPDATE = "order_update"
    PORTFOLIO_UPDATE = "portfolio_update"
    SYSTEM_ALERT = "system_alert"
    ANALYSIS_UPDATE = "analysis_update"
    PONG = "pong"
    ERROR = "error"
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"


class SubscriptionType(str, Enum):
    """Subscription types"""
    PRICE_DATA = "price_data"
    ORDER_UPDATES = "order_updates"
    PORTFOLIO_UPDATES = "portfolio_updates"
    SYSTEM_ALERTS = "system_alerts"
    ANALYSIS_UPDATES = "analysis_updates"
    ALL = "all"


class WebSocketMessage:
    """WebSocket message wrapper"""
    
    def __init__(self, message_type: MessageType, data: Any = None, 
                 subscription: Optional[str] = None, timestamp: Optional[datetime] = None):
        self.type = message_type
        self.data = data
        self.subscription = subscription
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "type": self.type.value,
            "data": self.data,
            "subscription": self.subscription,
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WebSocketMessage':
        """Create from JSON string"""
        data = json.loads(json_str)
        return cls(
            message_type=MessageType(data["type"]),
            data=data.get("data"),
            subscription=data.get("subscription"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None
        )


class WebSocketConnection:
    """WebSocket connection wrapper"""
    
    def __init__(self, websocket: WebSocket, connection_id: str):
        self.websocket = websocket
        self.connection_id = connection_id
        self.subscriptions: Set[SubscriptionType] = set()
        self.connected_at = datetime.utcnow()
        self.last_ping = datetime.utcnow()
        self.is_active = True
    
    async def send_message(self, message: WebSocketMessage):
        """Send message to client"""
        try:
            if self.websocket.client_state == WebSocketState.CONNECTED:
                await self.websocket.send_text(message.to_json())
            else:
                self.is_active = False
        except Exception as e:
            logger.error(f"Error sending message to {self.connection_id}: {e}")
            self.is_active = False
    
    async def send_json(self, data: Dict[str, Any]):
        """Send JSON data to client"""
        try:
            if self.websocket.client_state == WebSocketState.CONNECTED:
                await self.websocket.send_json(data)
            else:
                self.is_active = False
        except Exception as e:
            logger.error(f"Error sending JSON to {self.connection_id}: {e}")
            self.is_active = False
    
    def subscribe(self, subscription_type: SubscriptionType):
        """Subscribe to a data type"""
        self.subscriptions.add(subscription_type)
        logger.info(f"Connection {self.connection_id} subscribed to {subscription_type.value}")
    
    def unsubscribe(self, subscription_type: SubscriptionType):
        """Unsubscribe from a data type"""
        self.subscriptions.discard(subscription_type)
        logger.info(f"Connection {self.connection_id} unsubscribed from {subscription_type.value}")
    
    def is_subscribed_to(self, subscription_type: SubscriptionType) -> bool:
        """Check if subscribed to a data type"""
        return subscription_type in self.subscriptions or SubscriptionType.ALL in self.subscriptions


class WebSocketManager:
    """WebSocket connection manager"""
    
    def __init__(self, trading_system: Optional[TradingSystemIntegration] = None):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.trading_system = trading_system
        self.message_queue = asyncio.Queue()
        self.is_running = False
        self.broadcast_task = None
        
        # Setup event handlers if trading system is available
        if self.trading_system:
            self._setup_event_handlers()
        
        logger.info("WebSocket manager initialized")
    
    def _setup_event_handlers(self):
        """Setup event handlers for trading system events"""
        if not self.trading_system:
            return
        
        # Subscribe to relevant events
        self.trading_system.event_bus.subscribe(
            {EventType.PRICE_UPDATE},
            self._handle_price_update,
            async_handler=True
        )
        
        self.trading_system.event_bus.subscribe(
            {EventType.ORDER_FILLED, EventType.ORDER_PLACED, EventType.ORDER_CANCELLED},
            self._handle_order_update,
            async_handler=True
        )
        
        self.trading_system.event_bus.subscribe(
            {EventType.POSITION_UPDATED},
            self._handle_portfolio_update,
            async_handler=True
        )
        
        self.trading_system.event_bus.subscribe(
            {EventType.SYSTEM_ALERT, EventType.RISK_ALERT, EventType.ERROR_OCCURRED},
            self._handle_system_alert,
            async_handler=True
        )
        
        self.trading_system.event_bus.subscribe(
            {EventType.SENTIMENT_ANALYZED, EventType.SIGNAL_GENERATED, EventType.TRADING_DECISION_MADE},
            self._handle_analysis_update,
            async_handler=True
        )
    
    async def _handle_price_update(self, event: Event):
        """Handle price update events"""
        message = WebSocketMessage(
            MessageType.PRICE_UPDATE,
            data={
                "symbol": event.data.get("symbol"),
                "price": event.data.get("price"),
                "volume": event.data.get("volume"),
                "change": event.data.get("change"),
                "timestamp": event.data.get("timestamp", event.timestamp.isoformat())
            },
            subscription=SubscriptionType.PRICE_DATA.value
        )
        await self.message_queue.put(message)
    
    async def _handle_order_update(self, event: Event):
        """Handle order update events"""
        message = WebSocketMessage(
            MessageType.ORDER_UPDATE,
            data={
                "order_id": event.data.get("order_id"),
                "symbol": event.data.get("symbol"),
                "side": event.data.get("side"),
                "quantity": event.data.get("quantity"),
                "price": event.data.get("price"),
                "status": event.data.get("status"),
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat()
            },
            subscription=SubscriptionType.ORDER_UPDATES.value
        )
        await self.message_queue.put(message)
    
    async def _handle_portfolio_update(self, event: Event):
        """Handle portfolio update events"""
        message = WebSocketMessage(
            MessageType.PORTFOLIO_UPDATE,
            data={
                "total_value": event.data.get("total_value"),
                "available_balance": event.data.get("available_balance"),
                "positions": event.data.get("positions"),
                "unrealized_pnl": event.data.get("unrealized_pnl"),
                "timestamp": event.timestamp.isoformat()
            },
            subscription=SubscriptionType.PORTFOLIO_UPDATES.value
        )
        await self.message_queue.put(message)
    
    async def _handle_system_alert(self, event: Event):
        """Handle system alert events"""
        alert_level = "error" if event.event_type == EventType.ERROR_OCCURRED else "warning"
        
        message = WebSocketMessage(
            MessageType.SYSTEM_ALERT,
            data={
                "level": alert_level,
                "title": event.data.get("title", f"System {alert_level.title()}"),
                "message": event.data.get("message", str(event.data)),
                "component": event.source,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat()
            },
            subscription=SubscriptionType.SYSTEM_ALERTS.value
        )
        await self.message_queue.put(message)
    
    async def _handle_analysis_update(self, event: Event):
        """Handle analysis update events"""
        message = WebSocketMessage(
            MessageType.ANALYSIS_UPDATE,
            data={
                "analysis_type": event.event_type.value,
                "result": event.data,
                "timestamp": event.timestamp.isoformat()
            },
            subscription=SubscriptionType.ANALYSIS_UPDATES.value
        )
        await self.message_queue.put(message)
    
    async def connect(self, websocket: WebSocket, connection_id: str) -> WebSocketConnection:
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        connection = WebSocketConnection(websocket, connection_id)
        self.connections[connection_id] = connection
        
        logger.info(f"WebSocket connection established: {connection_id}")
        
        # Send welcome message
        welcome_message = WebSocketMessage(
            MessageType.SUBSCRIBED,
            data={
                "connection_id": connection_id,
                "message": "Connected to Bitcoin Trading System",
                "available_subscriptions": [sub.value for sub in SubscriptionType]
            }
        )
        await connection.send_message(welcome_message)
        
        # Start broadcast task if not running
        if not self.is_running:
            await self.start_broadcast()
        
        return connection
    
    async def disconnect(self, connection_id: str):
        """Disconnect WebSocket connection"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            connection.is_active = False
            del self.connections[connection_id]
            logger.info(f"WebSocket connection disconnected: {connection_id}")
    
    async def handle_message(self, connection_id: str, message_data: str):
        """Handle incoming message from client"""
        try:
            message = WebSocketMessage.from_json(message_data)
            connection = self.connections.get(connection_id)
            
            if not connection:
                return
            
            if message.type == MessageType.SUBSCRIBE:
                subscription_type = SubscriptionType(message.data.get("subscription"))
                connection.subscribe(subscription_type)
                
                response = WebSocketMessage(
                    MessageType.SUBSCRIBED,
                    data={"subscription": subscription_type.value}
                )
                await connection.send_message(response)
            
            elif message.type == MessageType.UNSUBSCRIBE:
                subscription_type = SubscriptionType(message.data.get("subscription"))
                connection.unsubscribe(subscription_type)
                
                response = WebSocketMessage(
                    MessageType.UNSUBSCRIBED,
                    data={"subscription": subscription_type.value}
                )
                await connection.send_message(response)
            
            elif message.type == MessageType.PING:
                connection.last_ping = datetime.utcnow()
                response = WebSocketMessage(MessageType.PONG)
                await connection.send_message(response)
            
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
            error_message = WebSocketMessage(
                MessageType.ERROR,
                data={"error": str(e)}
            )
            if connection_id in self.connections:
                await self.connections[connection_id].send_message(error_message)
    
    async def start_broadcast(self):
        """Start the broadcast task"""
        if self.is_running:
            return
        
        self.is_running = True
        self.broadcast_task = asyncio.create_task(self._broadcast_loop())
        logger.info("WebSocket broadcast started")
    
    async def stop_broadcast(self):
        """Stop the broadcast task"""
        self.is_running = False
        if self.broadcast_task:
            self.broadcast_task.cancel()
            try:
                await self.broadcast_task
            except asyncio.CancelledError:
                pass
        logger.info("WebSocket broadcast stopped")
    
    async def _broadcast_loop(self):
        """Main broadcast loop"""
        while self.is_running:
            try:
                # Get message from queue with timeout
                try:
                    message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                    await self._broadcast_message(message)
                except asyncio.TimeoutError:
                    # Timeout is normal, continue loop
                    pass
                
                # Clean up inactive connections
                await self._cleanup_connections()
                
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(1)
    
    async def _broadcast_message(self, message: WebSocketMessage):
        """Broadcast message to subscribed connections"""
        if not message.subscription:
            return
        
        subscription_type = SubscriptionType(message.subscription)
        
        # Find connections subscribed to this message type
        target_connections = [
            conn for conn in self.connections.values()
            if conn.is_active and conn.is_subscribed_to(subscription_type)
        ]
        
        if not target_connections:
            return
        
        # Send message to all target connections
        tasks = [conn.send_message(message) for conn in target_connections]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.debug(f"Broadcasted {message.type.value} to {len(target_connections)} connections")
    
    async def _cleanup_connections(self):
        """Clean up inactive connections"""
        inactive_connections = [
            conn_id for conn_id, conn in self.connections.items()
            if not conn.is_active
        ]
        
        for conn_id in inactive_connections:
            await self.disconnect(conn_id)
    
    async def broadcast_custom_message(self, message_type: MessageType, data: Any, 
                                     subscription_type: SubscriptionType):
        """Broadcast custom message"""
        message = WebSocketMessage(
            message_type,
            data=data,
            subscription=subscription_type.value
        )
        await self.message_queue.put(message)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        active_connections = sum(1 for conn in self.connections.values() if conn.is_active)
        
        subscription_counts = {}
        for sub_type in SubscriptionType:
            count = sum(
                1 for conn in self.connections.values()
                if conn.is_active and conn.is_subscribed_to(sub_type)
            )
            subscription_counts[sub_type.value] = count
        
        return {
            "total_connections": len(self.connections),
            "active_connections": active_connections,
            "subscription_counts": subscription_counts,
            "queue_size": self.message_queue.qsize(),
            "is_broadcasting": self.is_running
        }


# Global WebSocket manager instance
websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """Get WebSocket manager instance"""
    global websocket_manager
    if websocket_manager is None:
        websocket_manager = WebSocketManager()
    return websocket_manager


def initialize_websocket_manager(trading_system: TradingSystemIntegration):
    """Initialize WebSocket manager with trading system"""
    global websocket_manager
    websocket_manager = WebSocketManager(trading_system)
    return websocket_manager