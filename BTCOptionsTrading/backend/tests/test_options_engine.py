"""
期权定价引擎测试
测试Black-Scholes、希腊字母计算和其他定价方法
"""

import pytest
import numpy as np
from decimal import Decimal

from src.pricing.options_engine import OptionsEngine
from src.core.models import OptionType, Greeks
from src.core.exceptions import OptionsCalculationError


class TestBlackScholesPrice:
    """测试Black-Scholes定价"""
    
    @pytest.fixture
    def engine(self):
        """创建定价引擎实例"""
        return OptionsEngine()
    
    def test_call_option_pricing(self, engine):
        """测试看涨期权定价"""
        # 标准参数
        S = 100.0  # 标的价格
        K = 100.0  # 执行价格
        T = 1.0    # 1年到期
        r = 0.05   # 5%无风险利率
        sigma = 0.2  # 20%波动率
        
        price = engine.black_scholes_price(S, K, T, r, sigma, OptionType.CALL)
        
        # 验证价格在合理范围内
        assert price > 0
        assert price < S  # 看涨期权价格应小于标的价格
        
        # 使用已知结果验证（约10.45）
        assert 10.0 < price < 11.0
    
    def test_put_option_pricing(self, engine):
        """测试看跌期权定价"""
        S = 100.0
        K = 100.0
        T = 1.0
        r = 0.05
        sigma = 0.2
        
        price = engine.black_scholes_price(S, K, T, r, sigma, OptionType.PUT)
        
        # 验证价格在合理范围内
        assert price > 0
        assert price < K  # 看跌期权价格应小于执行价格
        
        # 使用已知结果验证（约5.57）
        assert 5.0 < price < 6.0
    
    def test_call_put_parity(self, engine):
        """测试看涨看跌平价关系: C - P = S - K*e^(-rT)"""
        S = 100.0
        K = 100.0
        T = 1.0
        r = 0.05
        sigma = 0.2
        
        call_price = engine.black_scholes_price(S, K, T, r, sigma, OptionType.CALL)
        put_price = engine.black_scholes_price(S, K, T, r, sigma, OptionType.PUT)
        
        parity_left = call_price - put_price
        parity_right = S - K * np.exp(-r * T)
        
        # 验证平价关系（允许小误差）
        assert abs(parity_left - parity_right) < 0.01
    
    def test_in_the_money_call(self, engine):
        """测试实值看涨期权"""
        S = 110.0  # 标的价格高于执行价
        K = 100.0
        T = 1.0
        r = 0.05
        sigma = 0.2
        
        price = engine.black_scholes_price(S, K, T, r, sigma, OptionType.CALL)
        
        # 实值期权价格应至少等于内在价值
        intrinsic_value = S - K
        assert price >= intrinsic_value
    
    def test_out_of_the_money_put(self, engine):
        """测试虚值看跌期权"""
        S = 110.0  # 标的价格高于执行价
        K = 100.0
        T = 1.0
        r = 0.05
        sigma = 0.2
        
        price = engine.black_scholes_price(S, K, T, r, sigma, OptionType.PUT)
        
        # 虚值期权价格应该较小
        assert 0 < price < 5.0
    
    def test_zero_time_to_maturity(self, engine):
        """测试到期时的期权价格"""
        S = 110.0
        K = 100.0
        T = 0.0  # 已到期
        r = 0.05
        sigma = 0.2
        
        # 看涨期权应等于内在价值
        call_price = engine.black_scholes_price(S, K, T, r, sigma, OptionType.CALL)
        assert call_price == max(S - K, 0)
        
        # 看跌期权应等于内在价值
        put_price = engine.black_scholes_price(S, K, T, r, sigma, OptionType.PUT)
        assert put_price == max(K - S, 0)
    
    def test_invalid_parameters(self, engine):
        """测试无效参数"""
        # 负的标的价格
        with pytest.raises(OptionsCalculationError):
            engine.black_scholes_price(-100, 100, 1, 0.05, 0.2, OptionType.CALL)
        
        # 负的执行价格
        with pytest.raises(OptionsCalculationError):
            engine.black_scholes_price(100, -100, 1, 0.05, 0.2, OptionType.CALL)
        
        # 负的波动率
        with pytest.raises(OptionsCalculationError):
            engine.black_scholes_price(100, 100, 1, 0.05, -0.2, OptionType.CALL)


class TestGreeksCalculation:
    """测试希腊字母计算"""
    
    @pytest.fixture
    def engine(self):
        """创建定价引擎实例"""
        return OptionsEngine()
    
    def test_greeks_structure(self, engine):
        """测试希腊字母对象结构"""
        S = 100.0
        K = 100.0
        T = 1.0
        r = 0.05
        sigma = 0.2
        
        greeks = engine.calculate_greeks(S, K, T, r, sigma, OptionType.CALL)
        
        # 验证返回Greeks对象
        assert isinstance(greeks, Greeks)
        assert hasattr(greeks, 'delta')
        assert hasattr(greeks, 'gamma')
        assert hasattr(greeks, 'theta')
        assert hasattr(greeks, 'vega')
        assert hasattr(greeks, 'rho')
    
    def test_call_delta_range(self, engine):
        """测试看涨期权Delta范围"""
        S = 100.0
        K = 100.0
        T = 1.0
        r = 0.05
        sigma = 0.2
        
        greeks = engine.calculate_greeks(S, K, T, r, sigma, OptionType.CALL)
        
        # 看涨期权Delta应在0到1之间
        assert 0 <= greeks.delta <= 1
        
        # 平值期权Delta应接近0.5（允许更大范围，因为受利率影响）
        assert 0.3 < greeks.delta < 0.7
    
    def test_put_delta_range(self, engine):
        """测试看跌期权Delta范围"""
        S = 100.0
        K = 100.0
        T = 1.0
        r = 0.05
        sigma = 0.2
        
        greeks = engine.calculate_greeks(S, K, T, r, sigma, OptionType.PUT)
        
        # 看跌期权Delta应在-1到0之间
        assert -1 <= greeks.delta <= 0
        
        # 平值期权Delta应接近-0.5（允许更大范围，因为受利率影响）
        assert -0.7 < greeks.delta < -0.3
    
    def test_gamma_positive(self, engine):
        """测试Gamma为正"""
        S = 100.0
        K = 100.0
        T = 1.0
        r = 0.05
        sigma = 0.2
        
        call_greeks = engine.calculate_greeks(S, K, T, r, sigma, OptionType.CALL)
        put_greeks = engine.calculate_greeks(S, K, T, r, sigma, OptionType.PUT)
        
        # Gamma对看涨和看跌期权都应为正
        assert call_greeks.gamma > 0
        assert put_greeks.gamma > 0
        
        # 看涨和看跌的Gamma应该相同
        assert abs(call_greeks.gamma - put_greeks.gamma) < 0.0001
    
    def test_theta_negative(self, engine):
        """测试Theta为负（时间衰减）"""
        S = 100.0
        K = 100.0
        T = 1.0
        r = 0.05
        sigma = 0.2
        
        greeks = engine.calculate_greeks(S, K, T, r, sigma, OptionType.CALL)
        
        # Theta通常为负（期权价值随时间衰减）
        assert greeks.theta < 0
    
    def test_vega_positive(self, engine):
        """测试Vega为正"""
        S = 100.0
        K = 100.0
        T = 1.0
        r = 0.05
        sigma = 0.2
        
        greeks = engine.calculate_greeks(S, K, T, r, sigma, OptionType.CALL)
        
        # Vega应为正（波动率增加，期权价值增加）
        assert greeks.vega > 0


class TestBinomialTreePricing:
    """测试二叉树定价"""
    
    @pytest.fixture
    def engine(self):
        """创建定价引擎实例"""
        return OptionsEngine()
    
    def test_binomial_converges_to_bs(self, engine):
        """测试二叉树价格收敛到Black-Scholes"""
        S = 100.0
        K = 100.0
        T = 1.0
        r = 0.05
        sigma = 0.2
        
        # Black-Scholes价格
        bs_price = engine.black_scholes_price(S, K, T, r, sigma, OptionType.CALL)
        
        # 二叉树价格（步数越多越接近BS）
        binomial_price = engine.binomial_tree_price(S, K, T, r, sigma, 100, OptionType.CALL)
        
        # 应该相当接近（允许5%误差）
        assert abs(binomial_price - bs_price) / bs_price < 0.05
    
    def test_binomial_american_option(self, engine):
        """测试美式期权定价"""
        S = 100.0
        K = 110.0  # 深度实值看跌
        T = 1.0
        r = 0.05
        sigma = 0.2
        
        # 美式期权价格
        american_price = engine.binomial_tree_price(S, K, T, r, sigma, 50, OptionType.PUT)
        
        # 欧式期权价格
        european_price = engine.black_scholes_price(S, K, T, r, sigma, OptionType.PUT)
        
        # 美式期权价格应该大于等于欧式期权
        assert american_price >= european_price


class TestMonteCarloPrice:
    """测试蒙特卡洛定价"""
    
    @pytest.fixture
    def engine(self):
        """创建定价引擎实例"""
        return OptionsEngine()
    
    def test_monte_carlo_approximates_bs(self, engine):
        """测试蒙特卡洛价格接近Black-Scholes"""
        S = 100.0
        K = 100.0
        T = 1.0
        r = 0.05
        sigma = 0.2
        
        # Black-Scholes价格
        bs_price = engine.black_scholes_price(S, K, T, r, sigma, OptionType.CALL)
        
        # 蒙特卡洛价格（模拟次数越多越准确）
        mc_price = engine.monte_carlo_price(S, K, T, r, sigma, 10000, OptionType.CALL)
        
        # 应该相当接近（允许10%误差，因为是随机模拟）
        assert abs(mc_price - bs_price) / bs_price < 0.1


class TestImpliedVolatility:
    """测试隐含波动率计算"""
    
    @pytest.fixture
    def engine(self):
        """创建定价引擎实例"""
        return OptionsEngine()
    
    def test_implied_volatility_recovery(self, engine):
        """测试隐含波动率恢复"""
        S = 100.0
        K = 100.0
        T = 1.0
        r = 0.05
        sigma = 0.25  # 真实波动率
        
        # 使用真实波动率计算价格
        market_price = engine.black_scholes_price(S, K, T, r, sigma, OptionType.CALL)
        
        # 从价格反推波动率
        implied_vol = engine.implied_volatility(market_price, S, K, T, r, OptionType.CALL)
        
        # 应该恢复原始波动率（允许小误差）
        assert abs(implied_vol - sigma) < 0.01
    
    def test_implied_volatility_call_put(self, engine):
        """测试看涨和看跌期权的隐含波动率一致性"""
        S = 100.0
        K = 100.0
        T = 1.0
        r = 0.05
        sigma = 0.2
        
        # 计算期权价格
        call_price = engine.black_scholes_price(S, K, T, r, sigma, OptionType.CALL)
        put_price = engine.black_scholes_price(S, K, T, r, sigma, OptionType.PUT)
        
        # 计算隐含波动率
        call_iv = engine.implied_volatility(call_price, S, K, T, r, OptionType.CALL)
        put_iv = engine.implied_volatility(put_price, S, K, T, r, OptionType.PUT)
        
        # 看涨和看跌的隐含波动率应该相同
        assert abs(call_iv - put_iv) < 0.01
