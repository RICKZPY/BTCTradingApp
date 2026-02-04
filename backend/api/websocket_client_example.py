#!/usr/bin/env python3
"""
WebSocket client example for Bitcoin Trading System
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradingSystemWebSocketClient:
    """WebSocket client for Bitcoin Trading System"""
    
    def __init__(self, uri: str = "ws://localhost:8000/api/v1/ws/stream"):
        self.uri = uri
        self.websocket = None
        self.is_connected = False
        self.subscriptions = set()
    
    async def connect(self, client_id: str = None):
        """Connect to WebSocket server"""
        try:
            uri = self.uri
            if client_id:
                uri += f"?client_id={client_id}"
            
            self.websocket = await websockets.connect(uri)
            self.is_connected = True
            logger.info(f"Connected to WebSocket server: {uri}")
            
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket server: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("Disconnected from WebSocket server")
    
    async def send_message(self, message_type: str, data: Dict[str, Any] = None):
        """Send message to server"""
        if not self.is_connected or not self.websocket:
            raise ConnectionError("Not connected to WebSocket server")
        
        message = {
            "type": message_type,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.websocket.send(json.dumps(message))
        logger.debug(f"Sent message: {message_type}")
    
    async def subscribe(self, subscription_type: str):
        """Subscribe to a data stream"""
        await self.send_message("subscribe", {"subscription": subscription_type})
        self.subscriptions.add(subscription_type)
        logger.info(f"Subscribed to: {subscription_type}")
    
    async def unsubscribe(self, subscription_type: str):
        """Unsubscribe from a data stream"""
        await self.send_message("unsubscribe", {"subscription": subscription_type})
        self.subscriptions.discard(subscription_type)
        logger.info(f"Unsubscribed from: {subscription_type}")
    
    async def ping(self):
        """Send ping message"""
        await self.send_message("ping")
    
    async def listen(self, message_handler=None):
        """Listen for messages from server"""
        if not self.is_connected or not self.websocket:
            raise ConnectionError("Not connected to WebSocket server")
        
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    
                    if message_handler:
                        await message_handler(data)
                    else:
                        await self._default_message_handler(data)
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message: {e}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    
        except ConnectionClosed:
            logger.info("WebSocket connection closed by server")
            self.is_connected = False
        except WebSocketException as e:
            logger.error(f"WebSocket error: {e}")
            self.is_connected = False
        except Exception as e:
            logger.error(f"Unexpected error in listen loop: {e}")
            self.is_connected = False
    
    async def _default_message_handler(self, data: Dict[str, Any]):
        """Default message handler"""
        message_type = data.get("type")
        timestamp = data.get("timestamp")
        
        if message_type == "price_update":
            price_data = data.get("data", {})
            logger.info(f"Price Update: {price_data.get('symbol')} = ${price_data.get('price')}")
        
        elif message_type == "order_update":
            order_data = data.get("data", {})
            logger.info(f"Order Update: {order_data.get('order_id')} - {order_data.get('status')}")
        
        elif message_type == "portfolio_update":
            portfolio_data = data.get("data", {})
            logger.info(f"Portfolio Update: Total Value = ${portfolio_data.get('total_value')}")
        
        elif message_type == "system_alert":
            alert_data = data.get("data", {})
            level = alert_data.get("level", "info").upper()
            logger.info(f"System Alert [{level}]: {alert_data.get('message')}")
        
        elif message_type == "analysis_update":
            analysis_data = data.get("data", {})
            analysis_type = analysis_data.get("analysis_type")
            logger.info(f"Analysis Update: {analysis_type}")
        
        elif message_type == "subscribed":
            sub_data = data.get("data", {})
            logger.info(f"Subscription confirmed: {sub_data}")
        
        elif message_type == "unsubscribed":
            sub_data = data.get("data", {})
            logger.info(f"Unsubscription confirmed: {sub_data}")
        
        elif message_type == "pong":
            logger.debug("Received pong")
        
        elif message_type == "error":
            error_data = data.get("data", {})
            logger.error(f"Server error: {error_data.get('error')}")
        
        else:
            logger.info(f"Received message: {message_type} - {data}")


async def demo_websocket_client():
    """Demonstrate WebSocket client usage"""
    print("Bitcoin Trading System WebSocket Client Demo")
    print("=" * 60)
    
    client = TradingSystemWebSocketClient()
    
    try:
        # Connect to server
        print("\n1. Connecting to WebSocket server...")
        await client.connect("demo_client")
        
        # Subscribe to different data streams
        print("\n2. Subscribing to data streams...")
        await client.subscribe("price_data")
        await asyncio.sleep(1)
        
        await client.subscribe("order_updates")
        await asyncio.sleep(1)
        
        await client.subscribe("portfolio_updates")
        await asyncio.sleep(1)
        
        await client.subscribe("system_alerts")
        await asyncio.sleep(1)
        
        # Send ping
        print("\n3. Sending ping...")
        await client.ping()
        await asyncio.sleep(1)
        
        # Listen for messages for a limited time
        print("\n4. Listening for messages (30 seconds)...")
        print("   (You can trigger test data from the API endpoints)")
        
        try:
            await asyncio.wait_for(client.listen(), timeout=30.0)
        except asyncio.TimeoutError:
            print("   Demo timeout reached")
        
        # Unsubscribe from some streams
        print("\n5. Unsubscribing from some streams...")
        await client.unsubscribe("price_data")
        await client.unsubscribe("order_updates")
        
        # Listen for a bit more
        print("\n6. Listening for remaining messages (10 seconds)...")
        try:
            await asyncio.wait_for(client.listen(), timeout=10.0)
        except asyncio.TimeoutError:
            print("   Demo timeout reached")
        
    except Exception as e:
        print(f"Demo error: {e}")
    
    finally:
        # Disconnect
        print("\n7. Disconnecting...")
        await client.disconnect()
        print("Demo completed!")


async def interactive_websocket_client():
    """Interactive WebSocket client"""
    print("Interactive Bitcoin Trading System WebSocket Client")
    print("=" * 60)
    print("Commands:")
    print("  subscribe <type>   - Subscribe to data stream")
    print("  unsubscribe <type> - Unsubscribe from data stream")
    print("  ping              - Send ping")
    print("  quit              - Exit client")
    print("\nAvailable subscription types:")
    print("  price_data, order_updates, portfolio_updates, system_alerts, analysis_updates, all")
    print()
    
    client = TradingSystemWebSocketClient()
    
    try:
        await client.connect("interactive_client")
        
        # Start listening task
        listen_task = asyncio.create_task(client.listen())
        
        # Interactive command loop
        while client.is_connected:
            try:
                # Get user input (in a real implementation, you'd use aioconsole)
                print("Enter command (or 'quit'): ", end="")
                # For demo purposes, we'll just run for a bit
                await asyncio.sleep(5)
                break
                
            except KeyboardInterrupt:
                break
        
        # Cancel listen task
        listen_task.cancel()
        try:
            await listen_task
        except asyncio.CancelledError:
            pass
    
    except Exception as e:
        print(f"Client error: {e}")
    
    finally:
        await client.disconnect()


if __name__ == "__main__":
    print("WebSocket Client Options:")
    print("1. Demo client (automated)")
    print("2. Interactive client")
    
    # For this demo, we'll run the automated demo
    print("\nRunning automated demo...")
    print("Make sure the API server is running on http://localhost:8000")
    print()
    
    try:
        asyncio.run(demo_websocket_client())
    except KeyboardInterrupt:
        print("\nClient stopped by user")
    except Exception as e:
        print(f"Client error: {e}")