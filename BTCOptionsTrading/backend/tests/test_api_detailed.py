"""详细的API测试调试"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from src.api.app import create_app
from src.config.settings import Settings
from src.storage.database import DatabaseManager

# 创建测试配置
settings = Settings()
settings.database.postgres_host = ""
settings.database.postgres_port = 0
settings.database.postgres_db = ":memory:"
settings.database.postgres_user = ""
settings.database.postgres_password = ""

# 创建测试数据库
db_manager = DatabaseManager(settings)
db_manager.engine = create_engine("sqlite:///:memory:", poolclass=NullPool)
db_manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_manager.engine)
db_manager.create_tables()

# 创建应用
app = create_app(settings)
client = TestClient(app)

# 测试策略创建
print("=" * 60)
print("测试策略创建")
print("=" * 60)

expiry = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")
strategy_data = {
    "name": "Test Call Option",
    "description": "Buy call option",
    "strategy_type": "single_leg",
    "legs": [
        {
            "option_contract": {
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

print(f"\n请求数据:")
import json
print(json.dumps(strategy_data, indent=2))

response = client.post("/api/strategies/", json=strategy_data)
print(f"\n状态码: {response.status_code}")
print(f"响应: {json.dumps(response.json(), indent=2)}")

# 清理
db_manager.drop_tables()
db_manager.close()
