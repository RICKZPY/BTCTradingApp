"""调试API测试"""
import sys
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from src.api.app import app
from datetime import datetime, timedelta

client = TestClient(app)

# 测试策略创建
expiry = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
strategy_data = {
    "name": "Test Long Call",
    "description": "Test strategy",
    "strategy_type": "long_call",
    "legs": [
        {
            "option": {
                "instrument_name": "BTC-30DEC23-40000-C",
                "underlying": "BTC",
                "option_type": "call",
                "strike_price": 40000.0,
                "expiration_date": expiry
            },
            "action": "buy",
            "quantity": 1
        }
    ]
}

print("发送请求...")
response = client.post("/api/strategies/", json=strategy_data)
print(f"状态码: {response.status_code}")
print(f"响应: {response.json()}")
