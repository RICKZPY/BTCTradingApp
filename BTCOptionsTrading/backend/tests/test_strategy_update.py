"""
策略更新API单元测试
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from src.core.models import Strategy, StrategyType, OptionType, ActionType, OptionContract, StrategyLeg
from src.storage.dao import StrategyDAO


class TestStrategyUpdateAPI:
    """策略更新API测试类"""
    
    def test_update_strategy_name(self, test_client, test_db):
        """测试更新策略名称"""
        # 创建测试策略
        strategy = self._create_test_strategy("原始策略名称")
        db_strategy = StrategyDAO.create(test_db, strategy)
        strategy_id = db_strategy.id
        
        # 更新策略名称
        update_data = {
            "name": "更新后的策略名称"
        }
        response = test_client.put(f"/api/strategies/{strategy_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后的策略名称"
        assert data["id"] == strategy_id
        
        # 验证数据库中的数据
        updated_strategy = StrategyDAO.get_by_id(test_db, strategy_id)
        assert updated_strategy.name == "更新后的策略名称"
    
    def test_update_strategy_description(self, test_client, test_db):
        """测试更新策略描述"""
        # 创建测试策略
        strategy = self._create_test_strategy("测试策略")
        db_strategy = StrategyDAO.create(test_db, strategy)
        strategy_id = db_strategy.id
        
        # 更新策略描述
        update_data = {
            "description": "这是更新后的描述"
        }
        response = test_client.put(f"/api/strategies/{strategy_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "这是更新后的描述"
        
        # 验证数据库中的数据
        updated_strategy = StrategyDAO.get_by_id(test_db, strategy_id)
        assert updated_strategy.description == "这是更新后的描述"
    
    def test_update_strategy_partial_fields(self, test_client, test_db):
        """测试部分字段更新"""
        # 创建测试策略
        strategy = self._create_test_strategy("测试策略", "原始描述")
        db_strategy = StrategyDAO.create(test_db, strategy)
        strategy_id = db_strategy.id
        original_name = db_strategy.name
        
        # 只更新描述，不更新名称
        update_data = {
            "description": "只更新描述"
        }
        response = test_client.put(f"/api/strategies/{strategy_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == original_name  # 名称应该保持不变
        assert data["description"] == "只更新描述"
    
    def test_update_strategy_legs(self, test_client, test_db):
        """测试更新策略腿"""
        # 创建测试策略（单腿）
        strategy = self._create_test_strategy("测试策略")
        db_strategy = StrategyDAO.create(test_db, strategy)
        strategy_id = db_strategy.id
        
        # 更新为跨式策略（两腿）
        expiry_date = (datetime.now() + timedelta(days=30)).isoformat()
        update_data = {
            "legs": [
                {
                    "option_contract": {
                        "instrument_name": "BTC-30MAR24-45000-C",
                        "underlying": "BTC",
                        "option_type": "call",
                        "strike_price": 45000,
                        "expiration_date": expiry_date
                    },
                    "action": "buy",
                    "quantity": 1
                },
                {
                    "option_contract": {
                        "instrument_name": "BTC-30MAR24-45000-P",
                        "underlying": "BTC",
                        "option_type": "put",
                        "strike_price": 45000,
                        "expiration_date": expiry_date
                    },
                    "action": "buy",
                    "quantity": 1
                }
            ]
        }
        response = test_client.put(f"/api/strategies/{strategy_id}", json=update_data)
        
        assert response.status_code == 200
        
        # 验证数据库中的策略腿数量
        updated_strategy = StrategyDAO.get_by_id(test_db, strategy_id)
        assert len(updated_strategy.legs) == 2
    
    def test_update_nonexistent_strategy(self, test_client):
        """测试更新不存在的策略"""
        fake_id = str(uuid4())
        update_data = {
            "name": "新名称"
        }
        response = test_client.put(f"/api/strategies/{fake_id}", json=update_data)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_strategy_with_invalid_data(self, test_client, test_db):
        """测试使用无效数据更新策略"""
        # 创建测试策略
        strategy = self._create_test_strategy("测试策略")
        db_strategy = StrategyDAO.create(test_db, strategy)
        strategy_id = db_strategy.id
        
        # 尝试使用无效的腿数据更新
        update_data = {
            "legs": [
                {
                    "option_contract": {
                        "instrument_name": "INVALID",
                        "underlying": "BTC",
                        "option_type": "invalid_type",  # 无效的期权类型
                        "strike_price": 45000,
                        "expiration_date": "invalid_date"  # 无效的日期格式
                    },
                    "action": "buy",
                    "quantity": 1
                }
            ]
        }
        response = test_client.put(f"/api/strategies/{strategy_id}", json=update_data)
        
        assert response.status_code == 400
    
    def test_update_strategy_preserves_other_fields(self, test_client, test_db):
        """测试更新策略时其他字段保持不变"""
        # 创建测试策略
        strategy = self._create_test_strategy("原始名称", "原始描述")
        strategy.max_profit = Decimal("1000.00")
        strategy.max_loss = Decimal("-500.00")
        db_strategy = StrategyDAO.create(test_db, strategy)
        strategy_id = db_strategy.id
        original_created_at = db_strategy.created_at
        original_strategy_type = db_strategy.strategy_type
        
        # 只更新名称
        update_data = {
            "name": "新名称"
        }
        response = test_client.put(f"/api/strategies/{strategy_id}", json=update_data)
        
        assert response.status_code == 200
        
        # 验证其他字段保持不变
        updated_strategy = StrategyDAO.get_by_id(test_db, strategy_id)
        assert updated_strategy.name == "新名称"
        assert updated_strategy.description == "原始描述"
        assert updated_strategy.strategy_type == original_strategy_type
        assert updated_strategy.max_profit == Decimal("1000.00")
        assert updated_strategy.max_loss == Decimal("-500.00")
        assert updated_strategy.created_at == original_created_at
        assert updated_strategy.updated_at > original_created_at  # updated_at应该更新
    
    def _create_test_strategy(self, name: str, description: str = None) -> Strategy:
        """创建测试策略"""
        expiry_date = datetime.now() + timedelta(days=30)
        
        contract = OptionContract(
            instrument_name="BTC-30MAR24-45000-C",
            underlying="BTC",
            option_type=OptionType.CALL,
            strike_price=Decimal("45000"),
            expiration_date=expiry_date,
            current_price=Decimal("1000"),
            bid_price=Decimal("990"),
            ask_price=Decimal("1010"),
            last_price=Decimal("1000"),
            implied_volatility=0.8,
            delta=0.5,
            gamma=0.01,
            theta=-10.0,
            vega=50.0,
            rho=20.0,
            open_interest=1000,
            volume=100,
            timestamp=datetime.now()
        )
        
        leg = StrategyLeg(
            option_contract=contract,
            action=ActionType.BUY,
            quantity=1
        )
        
        strategy = Strategy(
            name=name,
            description=description,
            strategy_type=StrategyType.SINGLE_LEG,
            legs=[leg]
        )
        
        return strategy
