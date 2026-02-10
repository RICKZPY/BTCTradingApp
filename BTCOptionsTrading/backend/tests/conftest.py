"""
Pytest配置和共享fixtures
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from src.core.models import (
    OptionContract, OptionType, Greeks, MarketData, 
    Strategy, StrategyLeg, ActionType, StrategyType
)
from src.api.app import create_app
from src.config.settings import Settings
from src.storage.database import DatabaseManager, Base


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
    """测试数据库会话"""
    # 创建SQLite内存数据库
    engine = create_engine("sqlite:///:memory:", poolclass=NullPool)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 创建会话
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def test_client(test_settings, test_db):
    """测试客户端"""
    app = create_app(test_settings)
    
    # 覆盖数据库依赖
    from src.storage.database import get_db
    
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    return TestClient(app)


@pytest.fixture
def sample_option_contract() -> OptionContract:
    """示例期权合约"""
    return OptionContract(
        instrument_name="BTC-29DEC23-50000-C",
        underlying="BTC",
        option_type=OptionType.CALL,
        strike_price=Decimal("50000"),
        expiration_date=datetime(2023, 12, 29),
        current_price=Decimal("2500"),
        bid_price=Decimal("2450"),
        ask_price=Decimal("2550"),
        last_price=Decimal("2500"),
        implied_volatility=0.8,
        delta=0.6,
        gamma=0.001,
        theta=-50,
        vega=100,
        rho=25,
        open_interest=1000,
        volume=50,
        timestamp=datetime.now()
    )


@pytest.fixture
def sample_put_contract() -> OptionContract:
    """示例看跌期权合约"""
    return OptionContract(
        instrument_name="BTC-29DEC23-50000-P",
        underlying="BTC",
        option_type=OptionType.PUT,
        strike_price=Decimal("50000"),
        expiration_date=datetime(2023, 12, 29),
        current_price=Decimal("1500"),
        bid_price=Decimal("1450"),
        ask_price=Decimal("1550"),
        last_price=Decimal("1500"),
        implied_volatility=0.8,
        delta=-0.4,
        gamma=0.001,
        theta=-45,
        vega=100,
        rho=-20,
        open_interest=800,
        volume=30,
        timestamp=datetime.now()
    )


@pytest.fixture
def sample_market_data() -> MarketData:
    """示例市场数据"""
    return MarketData(
        symbol="BTC-USD",
        price=Decimal("48000"),
        bid=Decimal("47950"),
        ask=Decimal("48050"),
        volume=1000,
        timestamp=datetime.now()
    )


@pytest.fixture
def sample_strategy(sample_option_contract, sample_put_contract) -> Strategy:
    """示例跨式策略"""
    call_leg = StrategyLeg(
        option_contract=sample_option_contract,
        action=ActionType.BUY,
        quantity=1
    )
    
    put_leg = StrategyLeg(
        option_contract=sample_put_contract,
        action=ActionType.BUY,
        quantity=1
    )
    
    return Strategy(
        name="Long Straddle",
        description="买入跨式策略",
        strategy_type=StrategyType.STRADDLE,
        legs=[call_leg, put_leg],
        max_profit=None,  # 无限
        max_loss=Decimal("4000"),  # 权利金总和
        breakeven_points=[Decimal("46000"), Decimal("54000")]
    )


@pytest.fixture
def sample_greeks() -> Greeks:
    """示例希腊字母"""
    return Greeks(
        delta=0.5,
        gamma=0.001,
        theta=-30,
        vega=80,
        rho=15
    )