"""
数据存储层测试
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from src.storage.database import DatabaseManager
from src.storage.dao import OptionContractDAO, StrategyDAO, BacktestResultDAO
from src.storage.data_manager import DataManager
from src.core.models import (
    OptionContract, Strategy, StrategyLeg, StrategyType,
    OptionType, ActionType, BacktestResult, Trade, DailyPnL, TradeAction
)


@pytest.fixture
def db_manager():
    """创建测试数据库管理器"""
    # 使用内存SQLite数据库进行测试
    from src.config.settings import Settings, DatabaseSettings
    
    settings = Settings()
    settings.database = DatabaseSettings()
    settings.database.url = "sqlite:///:memory:"
    
    manager = DatabaseManager(settings)
    manager.initialize()
    manager.create_tables()
    
    yield manager
    
    manager.close()


@pytest.fixture
def db_session(db_manager):
    """创建数据库会话"""
    session = db_manager.get_session()
    yield session
    session.close()


@pytest.fixture
def sample_option_contract():
    """创建示例期权合约"""
    return OptionContract(
        instrument_name="BTC-31DEC24-50000-C",
        underlying="BTC",
        option_type=OptionType.CALL,
        strike_price=Decimal("50000"),
        expiration_date=datetime(2024, 12, 31),
        current_price=Decimal("1000"),
        bid_price=Decimal("950"),
        ask_price=Decimal("1050"),
        last_price=Decimal("1000"),
        implied_volatility=0.8,
        delta=0.5,
        gamma=0.0001,
        theta=-10.0,
        vega=50.0,
        rho=5.0,
        open_interest=100,
        volume=10,
        timestamp=datetime.now()
    )


class TestOptionContractDAO:
    """期权合约DAO测试"""
    
    def test_create_option_contract(self, db_session, sample_option_contract):
        """测试创建期权合约"""
        db_contract = OptionContractDAO.create(db_session, sample_option_contract)
        
        assert db_contract is not None
        assert db_contract.instrument_name == sample_option_contract.instrument_name
        assert db_contract.underlying == sample_option_contract.underlying
        assert db_contract.option_type == sample_option_contract.option_type
    
    def test_get_by_instrument_name(self, db_session, sample_option_contract):
        """测试根据合约名称获取期权"""
        OptionContractDAO.create(db_session, sample_option_contract)
        
        db_contract = OptionContractDAO.get_by_instrument_name(
            db_session, sample_option_contract.instrument_name
        )
        
        assert db_contract is not None
        assert db_contract.instrument_name == sample_option_contract.instrument_name
    
    def test_get_by_underlying(self, db_session, sample_option_contract):
        """测试根据标的获取期权"""
        OptionContractDAO.create(db_session, sample_option_contract)
        
        contracts = OptionContractDAO.get_by_underlying(db_session, "BTC")
        
        assert len(contracts) > 0
        assert all(c.underlying == "BTC" for c in contracts)


class TestStrategyDAO:
    """策略DAO测试"""
    
    def test_create_strategy(self, db_session, sample_option_contract):
        """测试创建策略"""
        strategy = Strategy(
            id=uuid4(),
            name="Test Strategy",
            description="Test Description",
            strategy_type=StrategyType.SINGLE_LEG,
            legs=[
                StrategyLeg(
                    option_contract=sample_option_contract,
                    action=ActionType.BUY,
                    quantity=1
                )
            ],
            created_at=datetime.now()
        )
        
        db_strategy = StrategyDAO.create(db_session, strategy)
        
        assert db_strategy is not None
        assert db_strategy.name == strategy.name
        assert len(db_strategy.legs) == 1
    
    def test_get_by_id(self, db_session, sample_option_contract):
        """测试根据ID获取策略"""
        strategy = Strategy(
            id=uuid4(),
            name="Test Strategy",
            description="Test Description",
            strategy_type=StrategyType.SINGLE_LEG,
            legs=[
                StrategyLeg(
                    option_contract=sample_option_contract,
                    action=ActionType.BUY,
                    quantity=1
                )
            ],
            created_at=datetime.now()
        )
        
        db_strategy = StrategyDAO.create(db_session, strategy)
        retrieved = StrategyDAO.get_by_id(db_session, db_strategy.id)
        
        assert retrieved is not None
        assert retrieved.id == db_strategy.id
    
    def test_delete_strategy(self, db_session, sample_option_contract):
        """测试删除策略"""
        strategy = Strategy(
            id=uuid4(),
            name="Test Strategy",
            description="Test Description",
            strategy_type=StrategyType.SINGLE_LEG,
            legs=[
                StrategyLeg(
                    option_contract=sample_option_contract,
                    action=ActionType.BUY,
                    quantity=1
                )
            ],
            created_at=datetime.now()
        )
        
        db_strategy = StrategyDAO.create(db_session, strategy)
        strategy_id = db_strategy.id
        
        # 删除策略
        success = StrategyDAO.delete(db_session, strategy_id)
        assert success is True
        
        # 验证已删除
        retrieved = StrategyDAO.get_by_id(db_session, strategy_id)
        assert retrieved is None


class TestDataManager:
    """数据管理器测试"""
    
    def test_get_database_stats(self, db_manager):
        """测试获取数据库统计信息"""
        data_manager = DataManager(db_manager)
        stats = data_manager.get_database_stats()
        
        assert "option_contracts" in stats
        assert "strategies" in stats
        assert "backtest_results" in stats
        assert "timestamp" in stats
    
    def test_backup_strategies(self, db_manager, db_session, sample_option_contract):
        """测试备份策略"""
        # 创建一个策略
        strategy = Strategy(
            id=uuid4(),
            name="Test Strategy",
            description="Test Description",
            strategy_type=StrategyType.SINGLE_LEG,
            legs=[
                StrategyLeg(
                    option_contract=sample_option_contract,
                    action=ActionType.BUY,
                    quantity=1
                )
            ],
            created_at=datetime.now()
        )
        StrategyDAO.create(db_session, strategy)
        
        # 备份策略
        data_manager = DataManager(db_manager)
        backup_file = data_manager.backup_strategies()
        
        assert backup_file is not None
        import os
        assert os.path.exists(backup_file)
        
        # 清理
        os.remove(backup_file)
