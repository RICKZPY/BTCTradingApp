"""
期权定价引擎实现
提供Black-Scholes、二叉树、蒙特卡洛等定价方法
"""

import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq
from typing import Optional

from src.core.interfaces import IOptionsEngine
from src.core.models import Greeks, OptionType
from src.core.exceptions import OptionsCalculationError
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class OptionsEngine(IOptionsEngine):
    """期权定价引擎"""
    
    def __init__(self):
        """初始化定价引擎"""
        logger.info("Options pricing engine initialized")
    
    def black_scholes_price(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: OptionType
    ) -> float:
        """
        Black-Scholes期权定价公式
        
        Args:
            S: 标的资产当前价格
            K: 执行价格
            T: 到期时间（年）
            r: 无风险利率
            sigma: 波动率
            option_type: 期权类型（看涨/看跌）
            
        Returns:
            期权理论价格
            
        Raises:
            OptionsCalculationError: 参数无效时抛出
        """
        try:
            # 参数验证
            self._validate_parameters(S, K, T, r, sigma)
            
            # 处理到期情况
            if T <= 0:
                if option_type == OptionType.CALL:
                    return max(S - K, 0)
                else:
                    return max(K - S, 0)
            
            # 计算d1和d2
            d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            # 计算期权价格
            if option_type == OptionType.CALL:
                price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
            else:  # PUT
                price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
            
            return float(price)
            
        except Exception as e:
            logger.error(f"Black-Scholes pricing failed: {str(e)}")
            raise OptionsCalculationError(f"Black-Scholes pricing failed: {str(e)}")
    
    def calculate_greeks(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: OptionType
    ) -> Greeks:
        """
        计算期权希腊字母
        
        Args:
            S: 标的资产当前价格
            K: 执行价格
            T: 到期时间（年）
            r: 无风险利率
            sigma: 波动率
            option_type: 期权类型
            
        Returns:
            Greeks对象，包含所有希腊字母
        """
        try:
            # 参数验证
            self._validate_parameters(S, K, T, r, sigma)
            
            # 处理到期情况
            if T <= 0:
                delta = 1.0 if (option_type == OptionType.CALL and S > K) else 0.0
                if option_type == OptionType.PUT:
                    delta = -1.0 if S < K else 0.0
                return Greeks(delta=delta, gamma=0.0, theta=0.0, vega=0.0, rho=0.0)
            
            # 计算d1和d2
            d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            # 计算Delta
            if option_type == OptionType.CALL:
                delta = norm.cdf(d1)
            else:  # PUT
                delta = norm.cdf(d1) - 1
            
            # 计算Gamma（看涨和看跌相同）
            gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
            
            # 计算Vega（看涨和看跌相同）
            vega = S * norm.pdf(d1) * np.sqrt(T)
            
            # 计算Theta
            if option_type == OptionType.CALL:
                theta = (
                    -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                    - r * K * np.exp(-r * T) * norm.cdf(d2)
                )
            else:  # PUT
                theta = (
                    -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                    + r * K * np.exp(-r * T) * norm.cdf(-d2)
                )
            
            # 计算Rho
            if option_type == OptionType.CALL:
                rho = K * T * np.exp(-r * T) * norm.cdf(d2)
            else:  # PUT
                rho = -K * T * np.exp(-r * T) * norm.cdf(-d2)
            
            # 转换为每日值（Theta和Vega通常以每日为单位）
            theta_daily = theta / 365
            vega_percent = vega / 100  # Vega通常表示为波动率变化1%的影响
            
            return Greeks(
                delta=float(delta),
                gamma=float(gamma),
                theta=float(theta_daily),
                vega=float(vega_percent),
                rho=float(rho)
            )
            
        except Exception as e:
            logger.error(f"Greeks calculation failed: {str(e)}")
            raise OptionsCalculationError(f"Greeks calculation failed: {str(e)}")
    
    def binomial_tree_price(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        steps: int,
        option_type: OptionType
    ) -> float:
        """
        二叉树期权定价（支持美式期权）
        
        Args:
            S: 标的资产当前价格
            K: 执行价格
            T: 到期时间（年）
            r: 无风险利率
            sigma: 波动率
            steps: 二叉树步数
            option_type: 期权类型
            
        Returns:
            期权价格
        """
        try:
            # 参数验证
            self._validate_parameters(S, K, T, r, sigma)
            
            if steps <= 0:
                raise ValueError("Steps must be positive")
            
            # 计算参数
            dt = T / steps
            u = np.exp(sigma * np.sqrt(dt))  # 上涨因子
            d = 1 / u  # 下跌因子
            p = (np.exp(r * dt) - d) / (u - d)  # 风险中性概率
            
            # 初始化价格树
            prices = np.zeros(steps + 1)
            
            # 计算到期时的标的价格
            for i in range(steps + 1):
                prices[i] = S * (u ** (steps - i)) * (d ** i)
            
            # 计算到期时的期权价值
            if option_type == OptionType.CALL:
                values = np.maximum(prices - K, 0)
            else:  # PUT
                values = np.maximum(K - prices, 0)
            
            # 向后递推计算期权价值
            for step in range(steps - 1, -1, -1):
                for i in range(step + 1):
                    # 计算持有价值
                    hold_value = np.exp(-r * dt) * (p * values[i] + (1 - p) * values[i + 1])
                    
                    # 计算提前行权价值（美式期权）
                    current_price = S * (u ** (step - i)) * (d ** i)
                    if option_type == OptionType.CALL:
                        exercise_value = max(current_price - K, 0)
                    else:  # PUT
                        exercise_value = max(K - current_price, 0)
                    
                    # 取最大值（美式期权可以提前行权）
                    values[i] = max(hold_value, exercise_value)
            
            return float(values[0])
            
        except Exception as e:
            logger.error(f"Binomial tree pricing failed: {str(e)}")
            raise OptionsCalculationError(f"Binomial tree pricing failed: {str(e)}")
    
    def monte_carlo_price(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        simulations: int,
        option_type: OptionType
    ) -> float:
        """
        蒙特卡洛模拟期权定价
        
        Args:
            S: 标的资产当前价格
            K: 执行价格
            T: 到期时间（年）
            r: 无风险利率
            sigma: 波动率
            simulations: 模拟次数
            option_type: 期权类型
            
        Returns:
            期权价格
        """
        try:
            # 参数验证
            self._validate_parameters(S, K, T, r, sigma)
            
            if simulations <= 0:
                raise ValueError("Simulations must be positive")
            
            # 设置随机种子以保证可重复性
            np.random.seed(42)
            
            # 生成随机路径
            Z = np.random.standard_normal(simulations)
            ST = S * np.exp((r - 0.5 * sigma ** 2) * T + sigma * np.sqrt(T) * Z)
            
            # 计算期权收益
            if option_type == OptionType.CALL:
                payoffs = np.maximum(ST - K, 0)
            else:  # PUT
                payoffs = np.maximum(K - ST, 0)
            
            # 折现到现在
            price = np.exp(-r * T) * np.mean(payoffs)
            
            return float(price)
            
        except Exception as e:
            logger.error(f"Monte Carlo pricing failed: {str(e)}")
            raise OptionsCalculationError(f"Monte Carlo pricing failed: {str(e)}")
    
    def implied_volatility(
        self,
        market_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: OptionType
    ) -> float:
        """
        计算隐含波动率（使用Newton-Raphson方法）
        
        Args:
            market_price: 市场价格
            S: 标的资产当前价格
            K: 执行价格
            T: 到期时间（年）
            r: 无风险利率
            option_type: 期权类型
            
        Returns:
            隐含波动率
        """
        try:
            # 参数验证
            if market_price <= 0:
                raise ValueError("Market price must be positive")
            if S <= 0 or K <= 0:
                raise ValueError("Prices must be positive")
            if T <= 0:
                raise ValueError("Time to maturity must be positive")
            
            # 定义目标函数
            def objective(sigma):
                try:
                    bs_price = self.black_scholes_price(S, K, T, r, sigma, option_type)
                    return bs_price - market_price
                except:
                    return float('inf')
            
            # 使用Brent方法求解
            try:
                iv = brentq(objective, 0.001, 5.0, maxiter=100)
                return float(iv)
            except ValueError:
                # 如果Brent方法失败，尝试使用简单的二分法
                logger.warning("Brent method failed, using bisection")
                
                # 二分法
                low, high = 0.001, 5.0
                for _ in range(100):
                    mid = (low + high) / 2
                    price = self.black_scholes_price(S, K, T, r, mid, option_type)
                    
                    if abs(price - market_price) < 0.001:
                        return float(mid)
                    
                    if price < market_price:
                        low = mid
                    else:
                        high = mid
                
                return float((low + high) / 2)
                
        except Exception as e:
            logger.error(f"Implied volatility calculation failed: {str(e)}")
            raise OptionsCalculationError(f"Implied volatility calculation failed: {str(e)}")
    
    def _validate_parameters(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float
    ):
        """
        验证定价参数
        
        Args:
            S: 标的价格
            K: 执行价格
            T: 到期时间
            r: 无风险利率
            sigma: 波动率
            
        Raises:
            ValueError: 参数无效时抛出
        """
        if S <= 0:
            raise ValueError(f"Underlying price must be positive, got {S}")
        if K <= 0:
            raise ValueError(f"Strike price must be positive, got {K}")
        if T < 0:
            raise ValueError(f"Time to maturity must be non-negative, got {T}")
        if r < 0 or r > 1:
            raise ValueError(f"Risk-free rate must be between 0 and 1, got {r}")
        if sigma <= 0 or sigma > 5:
            raise ValueError(f"Volatility must be between 0 and 5, got {sigma}")
