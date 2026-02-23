"""
基础架构测试
验证项目基础组件是否正常工作
"""

import pytest
from decimal import Decimal
from datetime import datetime
from uuid import UUID

from src.core.models import (
    OptionContract, OptionType, Strategy, StrategyType, 
    BacktestResult, Greeks, Portfolio, Position
)
from src.core.interfaces import IDeribitConnector, IOptionsEngine
from src.config.settings import settings


class TestDataModels:
    """测试数据模型"""
    
    def test_option_contract_creation(self):
        """测试期权合约创建"""
        contract = OptionContract(
            instrument_name="BTC-25DEC26-50000-C",
            underlying="BTC",
            option_type=OptionType.CALL,
            strike_price=Decimal("50000"),
            expiration_date=datetime(2026, 12, 25),
            current_price=Decimal("2500"),
            bid_price=Decimal("2450"),
            ask_price=Decimal("2550"),
            last_price=Decimal("2500"),
            implied_volatility=0.8,
            delta=0.6,
            gamma=0.001,
            theta=-10.5,
            vega=25.0,
            rho=15.0,
            open_interest=100,
            volume=50,
            timestamp=datetime.now()
        )
        
        assert contract.instrument_name == "BTC-25DEC26-50000-C"
        assert contract.option_type == OptionType.CALL
        assert contract.strike_price == Decimal("50000")
        assert contract.mid_price == Decimal("2500")
        assert contract.spread == Decimal("100")
    
    def test_greeks_validation(self):
        """测试希腊字母验证"""
        # 正常情况
        greeks = Greeks(
            delta=0.6,
            gamma=0.001,
            theta=-10.5,
            vega=25.0,
            rho=15.0
        )
        assert greeks.delta == 0.6
        
        # 测试Delta范围验证
        with pytest.raises(ValueError, match="Delta must be between -1 and 1"):
            Greeks(delta=1.5, gamma=0.001, theta=-10.5, vega=25.0, rho=15.0)
        
        # 测试Gamma非负验证
        with pytest.raises(ValueError, match="Gamma must be non-negative"):
            Greeks(delta=0.6, gamma=-0.001, theta=-10.5, vega=25.0, rho=15.0)
    
    def test_strategy_creation(self):
        """测试策略创建"""
        strategy = Strategy(
            name="Long Call",
            description="买入看涨期权",
            strategy_type=StrategyType.SINGLE_LEG
        )
        
        assert isinstance(strategy.id, UUID)
        assert strategy.name == "Long Call"
        assert strategy.strategy_type == StrategyType.SINGLE_LEG
        assert len(strategy.legs) == 0
        assert isinstance(strategy.created_at, datetime)
    
    def test_backtest_result_creation(self):
        """测试回测结果创建"""
        result = BacktestResult(
            strategy_name="Test Strategy",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=Decimal("100000"),
            final_capital=Decimal("120000"),
            total_return=0.2,
            sharpe_ratio=1.5,
            max_drawdown=0.1,
            win_rate=0.6,
            total_trades=100
        )
        
        assert result.strategy_name == "Test Strategy"
        assert result.total_return == 0.2
        assert isinstance(result.id, UUID)
        assert len(result.trades) == 0
        assert isinstance(result.created_at, datetime)
    
    def test_portfolio_creation(self):
        """测试投资组合创建"""
        portfolio = Portfolio()
        
        assert isinstance(portfolio.id, UUID)
        assert len(portfolio.positions) == 0
        assert portfolio.cash_balance == Decimal(0)
        assert portfolio.total_value == Decimal(0)
        assert portfolio.total_delta == 0.0
        assert isinstance(portfolio.last_updated, datetime)


class TestConfiguration:
    """测试配置系统"""
    
    def test_settings_loading(self):
        """测试配置加载"""
        assert settings.app_name == "BTC Options Trading System"
        assert settings.app_version == "1.0.0"
        assert settings.environment in ["development", "testing", "staging", "production"]
    
    def test_database_settings(self):
        """测试数据库配置"""
        db_settings = settings.database
        # 检查数据库类型（可以是sqlite或postgresql）
        assert db_settings.db_type in ["sqlite", "postgresql"]
        
        # 如果是PostgreSQL，检查相关设置
        if db_settings.db_type == "postgresql":
            assert db_settings.postgres_host == "localhost"
            assert db_settings.postgres_port == 5432
            assert db_settings.postgres_db == "btc_options"
            assert "postgresql://" in db_settings.postgres_url
        # 如果是SQLite，检查路径
        else:
            assert "sqlite:///" in db_settings.postgres_url
            assert db_settings.sqlite_path is not None
    
    def test_deribit_settings(self):
        """测试Deribit配置"""
        deribit_settings = settings.deribit
        assert deribit_settings.test_mode == True
        assert "test.deribit.com" in deribit_settings.base_url
        assert deribit_settings.rate_limit_requests == 20
    
    def test_trading_settings(self):
        """测试交易配置"""
        trading_settings = settings.trading
        assert trading_settings.default_currency == "BTC"
        assert 0 <= trading_settings.risk_free_rate <= 1
        assert trading_settings.max_portfolio_delta > 0


class TestInterfaces:
    """测试接口定义"""
    
    def test_interface_imports(self):
        """测试接口导入"""
        # 验证接口可以正常导入
        assert IDeribitConnector is not None
        assert IOptionsEngine is not None
        
        # 验证接口是抽象基类
        from abc import ABC
        assert issubclass(IDeribitConnector, ABC)
        assert issubclass(IOptionsEngine, ABC)
    
    def test_interface_methods(self):
        """测试接口方法定义"""
        # 验证IDeribitConnector有必要的方法
        required_methods = [
            'authenticate', 'get_options_chain', 
            'get_historical_data', 'get_real_time_data'
        ]
        for method in required_methods:
            assert hasattr(IDeribitConnector, method)
        
        # 验证IOptionsEngine有必要的方法
        required_methods = [
            'black_scholes_price', 'calculate_greeks', 
            'binomial_tree_price', 'implied_volatility'
        ]
        for method in required_methods:
            assert hasattr(IOptionsEngine, method)