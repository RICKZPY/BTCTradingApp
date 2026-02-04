"""
WebSocket routes for real-time data streaming
"""
import logging
import uuid
from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.websocket import (
    WebSocketManager, get_websocket_manager, MessageType, SubscriptionType
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/stream")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str = Query(None, description="Optional client ID"),
    manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    WebSocket endpoint for real-time data streaming
    
    Supports the following message types:
    - subscribe: Subscribe to data streams
    - unsubscribe: Unsubscribe from data streams
    - ping: Heartbeat message
    
    Available subscriptions:
    - price_data: Real-time price updates
    - order_updates: Order execution updates
    - portfolio_updates: Portfolio changes
    - system_alerts: System alerts and warnings
    - analysis_updates: Analysis results
    - all: Subscribe to all data streams
    """
    # Generate connection ID
    connection_id = client_id or str(uuid.uuid4())
    
    try:
        # Accept connection
        connection = await manager.connect(websocket, connection_id)
        
        # Handle messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                await manager.handle_message(connection_id, data)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket client {connection_id} disconnected")
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message from {connection_id}: {e}")
                # Send error message to client
                await manager.broadcast_custom_message(
                    MessageType.ERROR,
                    {"error": str(e)},
                    SubscriptionType.ALL
                )
    
    except Exception as e:
        logger.error(f"WebSocket connection error for {connection_id}: {e}")
    
    finally:
        # Clean up connection
        await manager.disconnect(connection_id)


@router.get("/connections")
async def get_websocket_connections(
    manager: WebSocketManager = Depends(get_websocket_manager)
) -> Dict[str, Any]:
    """
    Get WebSocket connection statistics
    
    Returns:
        Connection statistics and status
    """
    stats = manager.get_connection_stats()
    
    return {
        "success": True,
        "message": "WebSocket connection statistics",
        "data": stats
    }


@router.post("/broadcast")
async def broadcast_message(
    message_type: str,
    subscription_type: str,
    data: Dict[str, Any],
    manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    Broadcast custom message to WebSocket clients
    
    Args:
        message_type: Type of message to broadcast
        subscription_type: Subscription type to target
        data: Message data
        
    Returns:
        Broadcast confirmation
    """
    try:
        # Validate message type and subscription type
        msg_type = MessageType(message_type)
        sub_type = SubscriptionType(subscription_type)
        
        # Broadcast message
        await manager.broadcast_custom_message(msg_type, data, sub_type)
        
        return {
            "success": True,
            "message": f"Message broadcasted to {subscription_type} subscribers",
            "data": {
                "message_type": message_type,
                "subscription_type": subscription_type,
                "data": data
            }
        }
        
    except ValueError as e:
        return {
            "success": False,
            "message": f"Invalid message or subscription type: {e}",
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        return {
            "success": False,
            "message": f"Failed to broadcast message: {e}",
            "error": str(e)
        }


@router.post("/test-data")
async def send_test_data(
    data_type: str = "price_update",
    manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    Send test data to WebSocket clients for testing
    
    Args:
        data_type: Type of test data to send
        
    Returns:
        Test data send confirmation
    """
    try:
        if data_type == "price_update":
            await manager.broadcast_custom_message(
                MessageType.PRICE_UPDATE,
                {
                    "symbol": "BTCUSDT",
                    "price": 45000.0 + (hash(str(uuid.uuid4())) % 1000),  # Random price variation
                    "volume": 1000.0,
                    "change": 1.5,
                    "timestamp": "2024-01-01T12:00:00Z"
                },
                SubscriptionType.PRICE_DATA
            )
        
        elif data_type == "order_update":
            await manager.broadcast_custom_message(
                MessageType.ORDER_UPDATE,
                {
                    "order_id": f"test-order-{uuid.uuid4()}",
                    "symbol": "BTCUSDT",
                    "side": "BUY",
                    "quantity": 0.1,
                    "price": 45000.0,
                    "status": "FILLED",
                    "event_type": "order_filled"
                },
                SubscriptionType.ORDER_UPDATES
            )
        
        elif data_type == "portfolio_update":
            await manager.broadcast_custom_message(
                MessageType.PORTFOLIO_UPDATE,
                {
                    "total_value": 10000.0,
                    "available_balance": 5000.0,
                    "positions": {
                        "BTCUSDT": {
                            "quantity": 0.1,
                            "value": 4500.0
                        }
                    },
                    "unrealized_pnl": 100.0
                },
                SubscriptionType.PORTFOLIO_UPDATES
            )
        
        elif data_type == "system_alert":
            await manager.broadcast_custom_message(
                MessageType.SYSTEM_ALERT,
                {
                    "level": "warning",
                    "title": "Test Alert",
                    "message": "This is a test system alert",
                    "component": "test_system"
                },
                SubscriptionType.SYSTEM_ALERTS
            )
        
        elif data_type == "analysis_update":
            await manager.broadcast_custom_message(
                MessageType.ANALYSIS_UPDATE,
                {
                    "analysis_type": "sentiment_analyzed",
                    "result": {
                        "sentiment_score": 0.7,
                        "confidence": 0.8,
                        "key_topics": ["bitcoin", "bullish", "market"]
                    }
                },
                SubscriptionType.ANALYSIS_UPDATES
            )
        
        else:
            return {
                "success": False,
                "message": f"Unknown test data type: {data_type}",
                "available_types": [
                    "price_update", "order_update", "portfolio_update",
                    "system_alert", "analysis_update"
                ]
            }
        
        return {
            "success": True,
            "message": f"Test {data_type} data sent to WebSocket clients"
        }
        
    except Exception as e:
        logger.error(f"Error sending test data: {e}")
        return {
            "success": False,
            "message": f"Failed to send test data: {e}",
            "error": str(e)
        }