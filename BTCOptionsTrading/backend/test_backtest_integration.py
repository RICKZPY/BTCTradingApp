"""
测试回测引擎与历史数据集成
验证回测引擎能够正确使用历史数据
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from src.backtest.backtest_engine import BacktestEngine
from src.historical.manager import HistoricalDataManager
from src.core.models import (
    Strategy, StrategyLeg, OptionContract, OptionType, ActionType
)


@pytest.fixture
def historical_manager():
    """创建历史数据管理器"""
    manager = HistoricalDataManager(
        download_dir="data/downloads",
        db_path="data/test_backtest_integration.db",
        cache_size_mb=50
    )
    yield manager
    # 清理测试数据
    manager.clear_cache(clear_database=True)


@pytest.fixture
def sample_strategy():
    """创建示例策略（牛市价差）"""
    now = datetime.now()
    
    # 买入低执行价看涨期权
    long_call = OptionContract(
        instrument_name="BTC-29MAR24-50000-C",
        underlying="BTC",
        strike_price=Decimal("50000"),
        expiration_date=datetime(2024, 3, 29),
        option_type=OptionType.CALL,
        current_price=Decimal("0.05"),
        bid_price=Decimal("0.049"),
        ask_price=Decimal("0.051"),
        last_price=Decimal("0.05"),
        implied_volatility=0.8,
        delta=0.5,
        gamma=0.01,
        theta=-0.001,
        vega=0.1,
        rho=0.05,
        open_interest=100,
        volume=50,
        timestamp=now
    )
    
    # 卖出高执行价看涨期权
    short_call = OptionContract(
        instrument_name="BTC-29MAR24-51000-C",
        underlying="BTC",
        strike_price=Decimal("51000"),
        expiration_date=datetime(2024, 3, 29),
        option_type=OptionType.CALL,
        current_price=Decimal("0.03"),
        bid_price=Decimal("0.029"),
        ask_price=Decimal("0.031"),
        last_price=Decimal("0.03"),
        implied_volatility=0.8,
        delta=0.3,
        gamma=0.008,
        theta=-0.0008,
        vega=0.08,
        rho=0.03,
        open_interest=80,
        volume=40,
        timestamp=now
    )
    
    strategy = Strategy(
        name="Bull Call Spread",
        description="Bullish strategy with limited risk and reward",
        legs=[
            StrategyLeg(
                option_contract=long_call,
                action=ActionType.BUY,
                quantity=1
            ),
            StrategyLeg(
                option_contract=short_call,
                action=ActionType.SELL,
                quantity=1
            )
        ]
    )
    
    return strategy


def test_backtest_engine_initialization_with_historical_data(historical_manager):
    """测试回测引擎初始化（使用历史数据）"""
    engine = BacktestEngine(
        use_historical_data=True,
        historical_data_manager=historical_manager
    )
    
    assert engine.use_historical_data is True
    assert engine.historical_data_manager is not None
    assert engine.historical_dataset is None  # 未运行回测前为空


def test_backtest_engine_initialization_without_historical_data():
    """测试回测引擎初始化（不使用历史数据）"""
    engine = BacktestEngine(use_historical_data=False)
    
    assert engine.use_historical_data is False
    assert engine.historical_data_manager is None
    assert engine.historical_dataset is None


@pytest.mark.asyncio
async def test_backtest_with_simulated_data(sample_strategy):
    """测试使用模拟数据的回测"""
    engine = BacktestEngine(use_historical_data=False)
    
    result = await engine.run_backtest(
        strategy=sample_strategy,
        start_date=datetime(2024, 3, 1),
        end_date=datetime(2024, 3, 10),
        initial_capital=Decimal("10000"),
        underlying_symbol="BTC"
    )
    
    # 验证回测结果
    assert result is not None
    assert result.strategy_name == "Bull Call Spread"
    assert result.initial_capital == Decimal("10000")
    assert result.total_trades > 0
    assert len(result.daily_pnl) > 0


@pytest.mark.asyncio
async def test_backtest_with_historical_data_no_data(historical_manager, sample_strategy):
    """测试使用历史数据的回测（无数据情况）"""
    engine = BacktestEngine(
        use_historical_data=True,
        historical_data_manager=historical_manager
    )
    
    # 运行回测（数据库中没有数据）
    result = await engine.run_backtest(
        strategy=sample_strategy,
        start_date=datetime(2024, 3, 1),
        end_date=datetime(2024, 3, 10),
        initial_capital=Decimal("10000"),
        underlying_symbol="BTC"
    )
    
    # 即使没有历史数据，回测也应该能运行（使用Black-Scholes定价）
    assert result is not None
    assert result.strategy_name == "Bull Call Spread"
    assert engine.historical_dataset is not None
    assert len(engine.historical_dataset.options_data) == 0  # 没有数据


@pytest.mark.asyncio
async def test_data_source_switching(historical_manager, sample_strategy):
    """测试数据源切换"""
    # 测试1: 使用模拟数据
    engine1 = BacktestEngine(use_historical_data=False)
    result1 = await engine1.run_backtest(
        strategy=sample_strategy,
        start_date=datetime(2024, 3, 1),
        end_date=datetime(2024, 3, 10),
        initial_capital=Decimal("10000")
    )
    
    # 测试2: 使用历史数据
    engine2 = BacktestEngine(
        use_historical_data=True,
        historical_data_manager=historical_manager
    )
    result2 = await engine2.run_backtest(
        strategy=sample_strategy,
        start_date=datetime(2024, 3, 1),
        end_date=datetime(2024, 3, 10),
        initial_capital=Decimal("10000")
    )
    
    # 两种数据源都应该能成功运行
    assert result1 is not None
    assert result2 is not None
    assert result1.strategy_name == result2.strategy_name


def test_get_underlying_price_from_data_no_data():
    """测试从数据中获取标的价格（无数据）"""
    engine = BacktestEngine(use_historical_data=True)
    
    price = engine._get_underlying_price_from_data(datetime(2024, 3, 1))
    
    # 应该返回默认价格
    assert price == 50000.0


def test_get_option_price_from_data_no_data():
    """测试从数据中获取期权价格（无数据）"""
    engine = BacktestEngine(use_historical_data=True)
    
    price = engine._get_option_price_from_data(
        "BTC-29MAR24-50000-C",
        datetime(2024, 3, 1)
    )
    
    # 应该返回None
    assert price is None


@pytest.mark.asyncio
async def test_backtest_performance_metrics(sample_strategy):
    """测试回测性能指标计算"""
    engine = BacktestEngine(use_historical_data=False)
    
    result = await engine.run_backtest(
        strategy=sample_strategy,
        start_date=datetime(2024, 3, 1),
        end_date=datetime(2024, 3, 10),
        initial_capital=Decimal("10000")
    )
    
    # 验证性能指标
    assert hasattr(result, 'total_return')
    assert hasattr(result, 'sharpe_ratio')
    assert hasattr(result, 'max_drawdown')
    assert hasattr(result, 'win_rate')
    
    # 验证指标范围
    assert -1.0 <= result.total_return <= 10.0  # 合理的收益率范围
    assert result.max_drawdown >= 0.0  # 回撤应该是非负数
    assert 0.0 <= result.win_rate <= 1.0  # 胜率应该在0-1之间


def test_historical_data_manager_integration(historical_manager):
    """测试历史数据管理器集成"""
    # 获取统计信息
    stats = historical_manager.get_stats()
    
    assert 'cache' in stats
    assert 'download_dir' in stats
    assert 'csv_files' in stats
    
    # 验证管理器可以正常工作
    instruments = historical_manager.get_available_instruments(underlying_symbol="BTC")
    assert isinstance(instruments, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
