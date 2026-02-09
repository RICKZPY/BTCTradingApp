"""
期权定价引擎使用示例
演示Black-Scholes定价、希腊字母计算和其他定价方法
"""

from src.pricing.options_engine import OptionsEngine
from src.core.models import OptionType
from src.config.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    """主函数"""
    engine = OptionsEngine()
    
    # 设置参数
    S = 45000.0  # BTC当前价格
    K = 45000.0  # 执行价格（平值期权）
    T = 30 / 365  # 30天到期
    r = 0.05  # 5%无风险利率
    sigma = 0.8  # 80%波动率（BTC典型波动率）
    
    logger.info("=== 期权定价引擎测试 ===")
    logger.info(f"\n参数设置:")
    logger.info(f"  标的价格 (S): ${S:,.2f}")
    logger.info(f"  执行价格 (K): ${K:,.2f}")
    logger.info(f"  到期时间 (T): {T*365:.0f} 天")
    logger.info(f"  无风险利率 (r): {r*100:.1f}%")
    logger.info(f"  波动率 (σ): {sigma*100:.1f}%")
    
    # 1. Black-Scholes定价
    logger.info("\n1. Black-Scholes定价:")
    call_price = engine.black_scholes_price(S, K, T, r, sigma, OptionType.CALL)
    put_price = engine.black_scholes_price(S, K, T, r, sigma, OptionType.PUT)
    
    logger.info(f"  看涨期权价格: ${call_price:,.2f}")
    logger.info(f"  看跌期权价格: ${put_price:,.2f}")
    
    # 验证看涨看跌平价关系
    import numpy as np
    parity_left = call_price - put_price
    parity_right = S - K * np.exp(-r * T)
    logger.info(f"  平价关系验证: {abs(parity_left - parity_right) < 0.01}")
    
    # 2. 希腊字母计算
    logger.info("\n2. 希腊字母计算:")
    call_greeks = engine.calculate_greeks(S, K, T, r, sigma, OptionType.CALL)
    put_greeks = engine.calculate_greeks(S, K, T, r, sigma, OptionType.PUT)
    
    logger.info(f"\n  看涨期权希腊字母:")
    logger.info(f"    Delta: {call_greeks.delta:.4f} (标的价格变化$1的影响)")
    logger.info(f"    Gamma: {call_greeks.gamma:.6f} (Delta的变化率)")
    logger.info(f"    Theta: {call_greeks.theta:.4f} (每日时间衰减)")
    logger.info(f"    Vega:  {call_greeks.vega:.4f} (波动率变化1%的影响)")
    logger.info(f"    Rho:   {call_greeks.rho:.4f} (利率变化1%的影响)")
    
    logger.info(f"\n  看跌期权希腊字母:")
    logger.info(f"    Delta: {put_greeks.delta:.4f}")
    logger.info(f"    Gamma: {put_greeks.gamma:.6f}")
    logger.info(f"    Theta: {put_greeks.theta:.4f}")
    logger.info(f"    Vega:  {put_greeks.vega:.4f}")
    logger.info(f"    Rho:   {put_greeks.rho:.4f}")
    
    # 3. 二叉树定价（美式期权）
    logger.info("\n3. 二叉树定价（美式期权）:")
    binomial_call = engine.binomial_tree_price(S, K, T, r, sigma, 50, OptionType.CALL)
    binomial_put = engine.binomial_tree_price(S, K, T, r, sigma, 50, OptionType.PUT)
    
    logger.info(f"  看涨期权: ${binomial_call:,.2f}")
    logger.info(f"  看跌期权: ${binomial_put:,.2f}")
    logger.info(f"  与BS差异 (Call): ${abs(binomial_call - call_price):,.2f}")
    logger.info(f"  与BS差异 (Put): ${abs(binomial_put - put_price):,.2f}")
    
    # 4. 蒙特卡洛定价
    logger.info("\n4. 蒙特卡洛模拟定价:")
    mc_call = engine.monte_carlo_price(S, K, T, r, sigma, 10000, OptionType.CALL)
    mc_put = engine.monte_carlo_price(S, K, T, r, sigma, 10000, OptionType.PUT)
    
    logger.info(f"  看涨期权: ${mc_call:,.2f}")
    logger.info(f"  看跌期权: ${mc_put:,.2f}")
    logger.info(f"  与BS差异 (Call): ${abs(mc_call - call_price):,.2f}")
    logger.info(f"  与BS差异 (Put): ${abs(mc_put - put_price):,.2f}")
    
    # 5. 隐含波动率计算
    logger.info("\n5. 隐含波动率计算:")
    market_call_price = call_price  # 使用BS价格作为"市场价格"
    implied_vol = engine.implied_volatility(market_call_price, S, K, T, r, OptionType.CALL)
    
    logger.info(f"  市场价格: ${market_call_price:,.2f}")
    logger.info(f"  隐含波动率: {implied_vol*100:.2f}%")
    logger.info(f"  原始波动率: {sigma*100:.2f}%")
    logger.info(f"  误差: {abs(implied_vol - sigma)*100:.4f}%")
    
    # 6. 不同执行价格的期权价格
    logger.info("\n6. 不同执行价格的期权价格:")
    strikes = [40000, 42500, 45000, 47500, 50000]
    
    logger.info(f"\n  {'执行价':<10} {'看涨价格':<12} {'看跌价格':<12} {'Call Delta':<12} {'Put Delta':<12}")
    logger.info(f"  {'-'*10} {'-'*12} {'-'*12} {'-'*12} {'-'*12}")
    
    for strike in strikes:
        call_p = engine.black_scholes_price(S, strike, T, r, sigma, OptionType.CALL)
        put_p = engine.black_scholes_price(S, strike, T, r, sigma, OptionType.PUT)
        call_g = engine.calculate_greeks(S, strike, T, r, sigma, OptionType.CALL)
        put_g = engine.calculate_greeks(S, strike, T, r, sigma, OptionType.PUT)
        
        logger.info(
            f"  ${strike:<9,.0f} ${call_p:<11,.2f} ${put_p:<11,.2f} "
            f"{call_g.delta:<12.4f} {put_g.delta:<12.4f}"
        )
    
    logger.info("\n=== 测试完成 ===")


if __name__ == "__main__":
    main()
