"""
波动率分析器测试
"""

import pytest
import numpy as np
from src.volatility.volatility_analyzer import VolatilityAnalyzer


@pytest.fixture
def analyzer():
    """创建波动率分析器实例"""
    return VolatilityAnalyzer()


@pytest.fixture
def sample_prices():
    """生成示例价格数据"""
    np.random.seed(42)
    # 生成100天的价格数据，初始价格45000，日波动率2%
    prices = [45000]
    for _ in range(99):
        change = np.random.normal(0, 0.02)
        prices.append(prices[-1] * (1 + change))
    return prices


@pytest.fixture
def sample_option_data():
    """生成示例期权数据"""
    spot = 45000
    data = []
    
    # 生成不同执行价和到期时间的期权
    for expiry in [0.25, 0.5, 1.0]:  # 3个月、6个月、1年
        for strike_pct in [0.9, 0.95, 1.0, 1.05, 1.1]:
            strike = spot * strike_pct
            # 模拟隐含波动率（ATM最低，两端较高）
            vol = 0.6 + abs(strike_pct - 1.0) * 0.5
            
            data.append({
                'strike': strike,
                'expiry': expiry,
                'implied_vol': vol,
                'option_type': 'call'
            })
    
    return data


def test_historical_volatility(analyzer, sample_prices):
    """测试历史波动率计算"""
    vol = analyzer.calculate_historical_volatility(sample_prices, window=30)
    
    assert isinstance(vol, float)
    assert vol > 0
    assert vol < 2.0  # 年化波动率应该在合理范围内


def test_historical_volatility_insufficient_data(analyzer):
    """测试数据不足时的错误处理"""
    prices = [100, 101, 102]
    
    with pytest.raises(ValueError):
        analyzer.calculate_historical_volatility(prices, window=30)


def test_rolling_volatility(analyzer, sample_prices):
    """测试滚动波动率计算"""
    result = analyzer.calculate_rolling_volatility(sample_prices, windows=[30, 60, 90])
    
    assert isinstance(result, dict)
    assert 30 in result
    assert 60 in result
    assert 90 in result
    assert all(isinstance(v, (float, type(None))) for v in result.values())


def test_garch_volatility(analyzer, sample_prices):
    """测试GARCH波动率预测"""
    # 计算收益率
    returns = np.diff(np.log(sample_prices))
    
    forecast_vol, historical_vols = analyzer.calculate_garch_volatility(returns.tolist())
    
    assert isinstance(forecast_vol, float)
    assert forecast_vol > 0
    assert len(historical_vols) == len(returns)


def test_volatility_surface(analyzer, sample_option_data):
    """测试波动率曲面构建"""
    surface = analyzer.build_volatility_surface(sample_option_data, spot_price=45000)
    
    assert 'moneyness' in surface
    assert 'expiry' in surface
    assert 'volatility' in surface
    assert 'spot_price' in surface
    assert surface['spot_price'] == 45000
    assert len(surface['moneyness']) > 0
    assert len(surface['expiry']) > 0


def test_term_structure(analyzer, sample_option_data):
    """测试波动率期限结构"""
    term_structure = analyzer.calculate_term_structure(sample_option_data, spot_price=45000)
    
    assert isinstance(term_structure, list)
    assert len(term_structure) > 0
    
    for item in term_structure:
        assert 'expiry' in item
        assert 'expiry_days' in item
        assert 'atm_volatility' in item
        assert item['atm_volatility'] > 0


def test_volatility_smile(analyzer, sample_option_data):
    """测试波动率微笑"""
    smile = analyzer.calculate_volatility_smile(
        sample_option_data,
        spot_price=45000,
        target_expiry=0.5
    )
    
    assert isinstance(smile, list)
    assert len(smile) > 0
    
    for item in smile:
        assert 'strike' in item
        assert 'moneyness' in item
        assert 'implied_volatility' in item


def test_compare_volatilities(analyzer):
    """测试波动率比较"""
    result = analyzer.compare_volatilities(
        historical_vol=0.5,
        implied_vol=0.6
    )
    
    assert 'historical_volatility' in result
    assert 'implied_volatility' in result
    assert 'difference' in result
    assert 'difference_percent' in result
    assert 'market_sentiment' in result
    assert 'trading_recommendation' in result
    
    assert abs(result['difference'] - 0.1) < 0.001  # 使用近似比较
    assert abs(result['difference_percent'] - 20.0) < 0.001  # 使用近似比较


def test_detect_anomalies(analyzer):
    """测试波动率异常检测"""
    # 创建包含异常值的序列
    vols = [0.5] * 20 + [1.5] + [0.5] * 20  # 中间有一个异常高值
    
    anomalies = analyzer.detect_volatility_anomalies(vols, threshold=2.0)
    
    assert isinstance(anomalies, list)
    assert len(anomalies) > 0
    
    # 应该检测到异常值
    assert any(a['type'] == 'spike' for a in anomalies)


def test_volatility_cone(analyzer, sample_prices):
    """测试波动率锥"""
    cone = analyzer.calculate_volatility_cone(sample_prices, windows=[10, 20, 30])
    
    assert 'cone' in cone
    assert 'description' in cone
    assert isinstance(cone['cone'], list)
    
    for item in cone['cone']:
        assert 'window' in item
        assert 'min' in item
        assert 'max' in item
        assert 'median' in item
        assert 'current' in item
        assert item['min'] <= item['median'] <= item['max']
