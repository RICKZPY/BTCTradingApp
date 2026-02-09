"""
波动率分析器使用示例
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from src.volatility.volatility_analyzer import VolatilityAnalyzer


def generate_sample_prices(days=100, initial_price=45000, daily_vol=0.02):
    """生成示例价格数据"""
    np.random.seed(42)
    prices = [initial_price]
    for _ in range(days - 1):
        change = np.random.normal(0, daily_vol)
        prices.append(prices[-1] * (1 + change))
    return prices


def generate_sample_options(spot_price=45000):
    """生成示例期权数据"""
    data = []
    
    for expiry in [0.25, 0.5, 1.0]:  # 3个月、6个月、1年
        for strike_pct in [0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15]:
            strike = spot_price * strike_pct
            # 模拟波动率微笑
            vol = 0.6 + abs(strike_pct - 1.0) * 0.5 + expiry * 0.1
            
            data.append({
                'strike': strike,
                'expiry': expiry,
                'implied_vol': vol,
                'option_type': 'call' if strike_pct >= 1.0 else 'put'
            })
    
    return data


def main():
    print("=" * 60)
    print("波动率分析器测试")
    print("=" * 60)
    
    # 创建分析器
    analyzer = VolatilityAnalyzer()
    
    # 生成示例数据
    prices = generate_sample_prices()
    option_data = generate_sample_options()
    spot_price = prices[-1]
    
    print(f"\n当前价格: ${spot_price:.2f}")
    print(f"价格数据点数: {len(prices)}")
    print(f"期权数据点数: {len(option_data)}")
    
    # 1. 历史波动率
    print("\n" + "=" * 60)
    print("1. 历史波动率计算")
    print("=" * 60)
    
    vol_30 = analyzer.calculate_historical_volatility(prices, window=30)
    vol_60 = analyzer.calculate_historical_volatility(prices, window=60)
    vol_90 = analyzer.calculate_historical_volatility(prices, window=90)
    
    print(f"30天历史波动率: {vol_30:.2%}")
    print(f"60天历史波动率: {vol_60:.2%}")
    print(f"90天历史波动率: {vol_90:.2%}")
    
    # 2. GARCH预测
    print("\n" + "=" * 60)
    print("2. GARCH波动率预测")
    print("=" * 60)
    
    returns = np.diff(np.log(prices))
    forecast_vol, _ = analyzer.calculate_garch_volatility(returns.tolist(), forecast_horizon=5)
    
    print(f"GARCH预测波动率（5天后）: {forecast_vol:.2%}")
    
    # 3. 波动率曲面
    print("\n" + "=" * 60)
    print("3. 波动率曲面")
    print("=" * 60)
    
    surface = analyzer.build_volatility_surface(option_data, spot_price)
    print(f"Moneyness范围: {min(surface['moneyness']):.2f} - {max(surface['moneyness']):.2f}")
    print(f"到期时间范围: {min(surface['expiry']):.2f} - {max(surface['expiry']):.2f}年")
    print(f"曲面网格大小: {len(surface['moneyness'])} x {len(surface['expiry'])}")
    
    # 4. 期限结构
    print("\n" + "=" * 60)
    print("4. 波动率期限结构")
    print("=" * 60)
    
    term_structure = analyzer.calculate_term_structure(option_data, spot_price)
    for item in term_structure:
        print(f"到期: {item['expiry_days']}天, ATM波动率: {item['atm_volatility']:.2%}")
    
    # 5. 波动率微笑
    print("\n" + "=" * 60)
    print("5. 波动率微笑（6个月期）")
    print("=" * 60)
    
    smile = analyzer.calculate_volatility_smile(option_data, spot_price, target_expiry=0.5)
    print(f"{'执行价':<12} {'Moneyness':<12} {'隐含波动率':<15} {'类型'}")
    print("-" * 60)
    for item in smile:
        print(f"${item['strike']:<11.0f} {item['moneyness']:<12.3f} "
              f"{item['implied_volatility']:<15.2%} {item['option_type']}")
    
    # 6. 波动率比较
    print("\n" + "=" * 60)
    print("6. 历史波动率 vs 隐含波动率")
    print("=" * 60)
    
    # 使用ATM期权的隐含波动率
    atm_options = [d for d in option_data if abs(d['strike'] - spot_price) / spot_price < 0.05]
    avg_implied_vol = np.mean([d['implied_vol'] for d in atm_options])
    
    comparison = analyzer.compare_volatilities(vol_30, avg_implied_vol)
    print(f"历史波动率: {comparison['historical_volatility']:.2%}")
    print(f"隐含波动率: {comparison['implied_volatility']:.2%}")
    print(f"差异: {comparison['difference']:.2%} ({comparison['difference_percent']:.1f}%)")
    print(f"市场情绪: {comparison['market_sentiment']}")
    print(f"交易建议: {comparison['trading_recommendation']}")
    
    # 7. 异常检测
    print("\n" + "=" * 60)
    print("7. 波动率异常检测")
    print("=" * 60)
    
    # 创建包含异常的波动率序列
    vol_series = [0.5 + np.random.normal(0, 0.05) for _ in range(50)]
    vol_series[25] = 1.2  # 添加一个异常值
    
    anomalies = analyzer.detect_volatility_anomalies(vol_series, threshold=2.0)
    print(f"检测到 {len(anomalies)} 个异常值:")
    for anomaly in anomalies:
        print(f"  位置: {anomaly['index']}, 波动率: {anomaly['volatility']:.2%}, "
              f"Z-score: {anomaly['z_score']:.2f}, 类型: {anomaly['type']}, "
              f"严重程度: {anomaly['severity']}")
    
    # 8. 波动率锥
    print("\n" + "=" * 60)
    print("8. 波动率锥")
    print("=" * 60)
    
    cone = analyzer.calculate_volatility_cone(prices, windows=[10, 20, 30, 60])
    print(f"{'窗口':<8} {'最小值':<10} {'25%':<10} {'中位数':<10} {'75%':<10} {'最大值':<10} {'当前':<10}")
    print("-" * 80)
    for item in cone['cone']:
        print(f"{item['window']:<8} {item['min']:<10.2%} {item['percentile_25']:<10.2%} "
              f"{item['median']:<10.2%} {item['percentile_75']:<10.2%} "
              f"{item['max']:<10.2%} {item['current']:<10.2%}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
