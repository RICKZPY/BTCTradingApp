#!/usr/bin/env python3
"""
Example usage of the Bitcoin Trading System API
"""
import asyncio
import aiohttp
import json
from datetime import datetime


class TradingSystemAPIClient:
    """Simple API client for the trading system"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get(self, endpoint: str):
        """Make GET request"""
        async with self.session.get(f"{self.base_url}{endpoint}") as response:
            return await response.json()
    
    async def post(self, endpoint: str, data: dict):
        """Make POST request"""
        async with self.session.post(
            f"{self.base_url}{endpoint}",
            json=data,
            headers={"Content-Type": "application/json"}
        ) as response:
            return await response.json()
    
    async def put(self, endpoint: str, data: dict):
        """Make PUT request"""
        async with self.session.put(
            f"{self.base_url}{endpoint}",
            json=data,
            headers={"Content-Type": "application/json"}
        ) as response:
            return await response.json()
    
    async def delete(self, endpoint: str):
        """Make DELETE request"""
        async with self.session.delete(f"{self.base_url}{endpoint}") as response:
            return await response.json()


async def demo_api_usage():
    """Demonstrate API usage"""
    print("Bitcoin Trading System API Demo")
    print("=" * 50)
    
    async with TradingSystemAPIClient() as client:
        
        # 1. Check API root
        print("\n1. Checking API root...")
        root = await client.get("/")
        print(f"API Status: {root}")
        
        # 2. Health check
        print("\n2. Performing health check...")
        health = await client.get("/api/v1/health/simple")
        print(f"Health Status: {health['status']}")
        
        # 3. Get system status
        print("\n3. Getting system status...")
        try:
            status = await client.get("/api/v1/system/status")
            print(f"System State: {status['system_state']}")
            print(f"Components: {status['components']['total']}")
        except Exception as e:
            print(f"System status error: {e}")
        
        # 4. Get system metrics
        print("\n4. Getting system metrics...")
        try:
            metrics = await client.get("/api/v1/system/metrics")
            print(f"System Healthy: {metrics['system_healthy']}")
            print(f"Total Events: {metrics['total_events']}")
        except Exception as e:
            print(f"System metrics error: {e}")
        
        # 5. Get portfolio
        print("\n5. Getting portfolio...")
        try:
            portfolio = await client.get("/api/v1/trading/portfolio")
            print(f"Portfolio Value: ${portfolio['portfolio']['total_value']}")
            print(f"Positions: {len(portfolio['portfolio']['positions'])}")
        except Exception as e:
            print(f"Portfolio error: {e}")
        
        # 6. Get market data
        print("\n6. Getting market data...")
        try:
            market_data = await client.get("/api/v1/trading/market-data/BTCUSDT")
            print(f"BTC Price: ${market_data['data']['price']}")
            print(f"24h Change: {market_data['data']['change_24h_percent']}%")
        except Exception as e:
            print(f"Market data error: {e}")
        
        # 7. Get current analysis
        print("\n7. Getting current analysis...")
        try:
            analysis = await client.get("/api/v1/analysis/current")
            if analysis['sentiment']:
                print(f"Sentiment Score: {analysis['sentiment']['sentiment_score']}")
            if analysis['technical']:
                print(f"Technical Signal: {analysis['technical']['signal_type']}")
            if analysis['decision']:
                print(f"Trading Decision: {analysis['decision']['action']}")
        except Exception as e:
            print(f"Analysis error: {e}")
        
        # 8. Get order history
        print("\n8. Getting order history...")
        try:
            orders = await client.get("/api/v1/trading/orders?limit=5")
            print(f"Total Orders: {orders['data']['total_count']}")
            for order in orders['data']['orders']:
                print(f"  Order {order['order_id']}: {order['side']} {order['quantity']} {order['symbol']} @ {order['status']}")
        except Exception as e:
            print(f"Order history error: {e}")
        
        # 9. Trigger analysis
        print("\n9. Triggering analysis...")
        try:
            trigger = await client.post("/api/v1/analysis/trigger", {})
            print(f"Analysis triggered: {trigger['message']}")
        except Exception as e:
            print(f"Trigger analysis error: {e}")
        
        # 10. Place a test order (commented out for safety)
        print("\n10. Placing test order (simulation)...")
        try:
            # Uncomment to actually place an order
            # order_request = {
            #     "symbol": "BTCUSDT",
            #     "side": "BUY",
            #     "type": "MARKET",
            #     "quantity": 0.001
            # }
            # order_result = await client.post("/api/v1/trading/orders", order_request)
            # print(f"Order placed: {order_result['message']}")
            print("Order placement skipped (simulation mode)")
        except Exception as e:
            print(f"Order placement error: {e}")
    
    print("\n" + "=" * 50)
    print("API Demo completed!")


async def test_api_endpoints():
    """Test all API endpoints"""
    print("Testing API Endpoints")
    print("=" * 30)
    
    endpoints = [
        ("GET", "/"),
        ("GET", "/api/v1/health/"),
        ("GET", "/api/v1/health/simple"),
        ("GET", "/api/v1/health/readiness"),
        ("GET", "/api/v1/health/liveness"),
        ("GET", "/api/v1/system/status"),
        ("GET", "/api/v1/system/metrics"),
        ("GET", "/api/v1/system/config"),
        ("GET", "/api/v1/trading/portfolio"),
        ("GET", "/api/v1/trading/orders"),
        ("GET", "/api/v1/trading/market-data/BTCUSDT"),
        ("GET", "/api/v1/analysis/current"),
        ("GET", "/api/v1/analysis/sentiment"),
        ("GET", "/api/v1/analysis/technical"),
        ("GET", "/api/v1/analysis/decision"),
        ("GET", "/api/v1/analysis/history"),
    ]
    
    async with TradingSystemAPIClient() as client:
        for method, endpoint in endpoints:
            try:
                if method == "GET":
                    response = await client.get(endpoint)
                    status = "✓" if response.get('success', True) else "✗"
                    print(f"{status} {method} {endpoint}")
                else:
                    print(f"? {method} {endpoint} (not tested)")
            except Exception as e:
                print(f"✗ {method} {endpoint} - Error: {str(e)[:50]}...")


if __name__ == "__main__":
    print("Starting API client demo...")
    print("Make sure the API server is running on http://localhost:8000")
    print()
    
    # Run the demo
    asyncio.run(demo_api_usage())
    
    print("\n" + "=" * 50)
    
    # Run endpoint tests
    asyncio.run(test_api_endpoints())