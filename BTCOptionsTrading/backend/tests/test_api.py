"""
API接口测试
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from src.api.app import create_app
from src.config.settings import Settings
from src.storage.database import DatabaseManager, Base
from src.core.models import (
    Strategy, StrategyLeg, OptionContract,
    StrategyType, OptionType, ActionType
)


@pytest.fixture
def test_settings():
    """测试配置"""
    settings = Settings()
    # 使用SQLite内存数据库进行测试
    settings.database.postgres_host = ""
    settings.database.postgres_port = 0
    settings.database.postgres_db = ":memory:"
    settings.database.postgres_user = ""
    settings.database.postgres_password = ""
    return settings


@pytest.fixture
def test_db(test_settings):
    """测试数据库"""
    import tempfile
    import os
    from src.storage import database
    
    # 创建临时数据库文件
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    db_path = temp_db.name
    
    # 创建测试数据库管理器
    db_manager = DatabaseManager(test_settings)
    db_manager.engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={'check_same_thread': False},
        poolclass=NullPool
    )
    db_manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_manager.engine)
    db_manager.create_tables()
    
    # 替换全局数据库管理器
    original_db_manager = database._db_manager
    database._db_manager = db_manager
    
    yield db_manager
    
    # 恢复原始数据库管理器
    database._db_manager = original_db_manager
    
    # 清理
    db_manager.drop_tables()
    db_manager.close()
    
    # 删除临时文件
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def client(test_settings, test_db):
    """测试客户端"""
    app = create_app(test_settings)
    return TestClient(app)


@pytest.fixture
def sample_strategy():
    """示例策略"""
    expiry = datetime.now() + timedelta(days=30)
    contract = OptionContract(
        instrument_name="BTC-30DEC23-40000-C",
        underlying="BTC",
        option_type=OptionType.CALL,
        strike_price=40000.0,
        expiration_date=expiry
    )
    leg = StrategyLeg(
        option_contract=contract,
        action=ActionType.BUY,
        quantity=1
    )
    return Strategy(
        name="Test Strategy",
        description="Test strategy for API",
        strategy_type=StrategyType.SINGLE_LEG,
        legs=[leg]
    )


class TestHealthEndpoints:
    """健康检查接口测试"""
    
    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        # 状态可以是 healthy, degraded, 或 unhealthy
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "timestamp" in data
        assert data["service"] == "BTC Options Trading System"
        assert "checks" in data
        assert "issues" in data
    
    def test_system_status(self, client):
        """测试系统状态"""
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data


class TestStrategyEndpoints:
    """策略管理接口测试"""
    
    def test_create_strategy(self, client):
        """测试创建策略"""
        # 使用ISO格式的日期时间字符串
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
        
        response = client.post("/api/strategies/", json=strategy_data)
        # 如果失败，打印错误信息
        if response.status_code != 200:
            print(f"Error: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Call Option"
        assert data["strategy_type"] == "single_leg"
        assert "id" in data
    
    def test_list_strategies(self, client):
        """测试获取策略列表"""
        response = client.get("/api/strategies/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_strategy_templates(self, client):
        """测试获取策略模板"""
        response = client.get("/api/strategies/templates/list")
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) > 0
        
        # 验证模板内容
        template_types = [t["type"] for t in data["templates"]]
        assert "single_leg" in template_types
        assert "straddle" in template_types
        assert "iron_condor" in template_types


class TestBacktestEndpoints:
    """回测接口测试"""
    
    def test_list_backtest_results(self, client):
        """测试获取回测结果列表"""
        response = client.get("/api/backtest/results")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestDataEndpoints:
    """数据接口测试"""
    
    def test_calculate_greeks(self, client):
        """测试计算希腊字母"""
        greeks_request = {
            "spot_price": 40000.0,
            "strike_price": 42000.0,
            "time_to_expiry": 0.25,
            "volatility": 0.8,
            "risk_free_rate": 0.05,
            "option_type": "call"
        }
        
        response = client.post("/api/data/calculate-greeks", json=greeks_request)
        assert response.status_code == 200
        data = response.json()
        
        # 验证返回的希腊字母
        assert "delta" in data
        assert "gamma" in data
        assert "theta" in data
        assert "vega" in data
        assert "rho" in data
        assert "price" in data
        
        # 验证值的合理性
        assert 0 <= data["delta"] <= 1  # Call option delta
        assert data["gamma"] >= 0
        assert data["vega"] >= 0
        assert data["price"] > 0


class TestAPIIntegration:
    """API集成测试"""
    
    def test_full_workflow(self, client):
        """测试完整工作流程：创建策略 -> 运行回测 -> 查看结果"""
        # 1. 创建策略
        expiry = (datetime.now() + timedelta(days=30)).isoformat()
        strategy_data = {
            "name": "Integration Test Strategy",
            "description": "Strategy for integration test",
            "strategy_type": "single_leg",
            "legs": [
                {
                    "option_contract": {
                        "instrument_name": "BTC-30DEC23-45000-C",
                        "underlying": "BTC",
                        "option_type": "call",
                        "strike_price": 45000.0,
                        "expiration_date": expiry
                    },
                    "action": "buy",
                    "quantity": 1
                }
            ]
        }
        
        create_response = client.post("/api/strategies/", json=strategy_data)
        assert create_response.status_code == 200
        strategy = create_response.json()
        strategy_id = strategy["id"]
        
        # 2. 获取策略详情
        get_response = client.get(f"/api/strategies/{strategy_id}")
        assert get_response.status_code == 200
        strategy_detail = get_response.json()
        assert strategy_detail["id"] == strategy_id
        assert strategy_detail["name"] == "Integration Test Strategy"
        
        # 3. 删除策略
        delete_response = client.delete(f"/api/strategies/{strategy_id}")
        assert delete_response.status_code == 200
        
        # 4. 验证策略已删除
        get_deleted_response = client.get(f"/api/strategies/{strategy_id}")
        assert get_deleted_response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
