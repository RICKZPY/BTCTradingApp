"""
波动率分析器
实现历史波动率计算、GARCH模型预测、波动率曲面构建等功能
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from scipy.interpolate import griddata
from scipy.optimize import minimize

from src.config.logging_config import get_logger

logger = get_logger(__name__)


class VolatilityAnalyzer:
    """波动率分析器"""
    
    def __init__(self):
        """初始化波动率分析器"""
        self.logger = logger
    
    def calculate_historical_volatility(
        self,
        prices: List[float],
        window: int = 30,
        annualize: bool = True
    ) -> float:
        """
        计算历史波动率
        
        Args:
            prices: 价格序列
            window: 时间窗口（天数）
            annualize: 是否年化
            
        Returns:
            历史波动率
        """
        if len(prices) < window:
            raise ValueError(f"价格数据不足，需要至少{window}个数据点")
        
        # 计算对数收益率
        log_returns = np.diff(np.log(prices[-window:]))
        
        # 计算标准差
        volatility = np.std(log_returns, ddof=1)
        
        # 年化（假设一年252个交易日）
        if annualize:
            volatility = volatility * np.sqrt(252)
        
        return float(volatility)
    
    def calculate_rolling_volatility(
        self,
        prices: List[float],
        windows: List[int] = [30, 60, 90]
    ) -> Dict[int, float]:
        """
        计算多个时间窗口的滚动波动率
        
        Args:
            prices: 价格序列
            windows: 时间窗口列表
            
        Returns:
            各窗口的波动率字典
        """
        result = {}
        
        for window in windows:
            try:
                vol = self.calculate_historical_volatility(prices, window)
                result[window] = vol
            except ValueError as e:
                self.logger.warning(f"计算{window}天波动率失败: {str(e)}")
                result[window] = None
        
        return result
    
    def calculate_garch_volatility(
        self,
        returns: List[float],
        forecast_horizon: int = 1
    ) -> Tuple[float, List[float]]:
        """
        使用简化的GARCH(1,1)模型预测波动率
        
        Args:
            returns: 收益率序列
            forecast_horizon: 预测期数
            
        Returns:
            (预测波动率, 历史条件波动率序列)
        """
        returns = np.array(returns)
        n = len(returns)
        
        # GARCH(1,1)参数初始值
        omega = 0.000001  # 常数项
        alpha = 0.1       # ARCH项系数
        beta = 0.85       # GARCH项系数
        
        # 初始化条件方差
        variance = np.zeros(n)
        variance[0] = np.var(returns)
        
        # 计算条件方差序列
        for t in range(1, n):
            variance[t] = omega + alpha * returns[t-1]**2 + beta * variance[t-1]
        
        # 预测未来波动率
        forecast_var = omega + alpha * returns[-1]**2 + beta * variance[-1]
        
        # 多步预测
        for _ in range(1, forecast_horizon):
            forecast_var = omega + (alpha + beta) * forecast_var
        
        forecast_vol = np.sqrt(forecast_var * 252)  # 年化
        historical_vol = np.sqrt(variance * 252)
        
        return float(forecast_vol), historical_vol.tolist()
    
    def build_volatility_surface(
        self,
        option_data: List[Dict],
        spot_price: float
    ) -> Dict:
        """
        构建隐含波动率曲面
        
        Args:
            option_data: 期权数据列表，每个元素包含:
                - strike: 执行价
                - expiry: 到期时间（年）
                - implied_vol: 隐含波动率
                - option_type: 'call' 或 'put'
            spot_price: 标的资产现价
            
        Returns:
            波动率曲面数据
        """
        if not option_data:
            raise ValueError("期权数据为空")
        
        # 提取数据
        strikes = np.array([d['strike'] for d in option_data])
        expiries = np.array([d['expiry'] for d in option_data])
        vols = np.array([d['implied_vol'] for d in option_data])
        
        # 计算moneyness (K/S)
        moneyness = strikes / spot_price
        
        # 创建网格
        moneyness_grid = np.linspace(moneyness.min(), moneyness.max(), 50)
        expiry_grid = np.linspace(expiries.min(), expiries.max(), 50)
        
        # 创建2D网格
        M, T = np.meshgrid(moneyness_grid, expiry_grid)
        
        # 插值构建曲面
        points = np.column_stack([moneyness, expiries])
        vol_surface = griddata(points, vols, (M, T), method='cubic')
        
        # 处理NaN值（使用最近邻插值填充）
        if np.any(np.isnan(vol_surface)):
            vol_surface_linear = griddata(points, vols, (M, T), method='nearest')
            vol_surface = np.where(np.isnan(vol_surface), vol_surface_linear, vol_surface)
        
        return {
            'moneyness': moneyness_grid.tolist(),
            'expiry': expiry_grid.tolist(),
            'volatility': vol_surface.tolist(),
            'spot_price': spot_price
        }
    
    def calculate_term_structure(
        self,
        option_data: List[Dict],
        spot_price: float,
        atm_threshold: float = 0.05
    ) -> List[Dict]:
        """
        计算波动率期限结构（ATM波动率）
        
        Args:
            option_data: 期权数据列表
            spot_price: 标的资产现价
            atm_threshold: ATM判断阈值（相对于现价的百分比）
            
        Returns:
            期限结构数据列表
        """
        # 按到期时间分组
        expiry_groups = {}
        
        for data in option_data:
            strike = data['strike']
            expiry = data['expiry']
            vol = data['implied_vol']
            
            # 判断是否接近ATM
            moneyness = abs(strike - spot_price) / spot_price
            if moneyness <= atm_threshold:
                if expiry not in expiry_groups:
                    expiry_groups[expiry] = []
                expiry_groups[expiry].append(vol)
        
        # 计算每个到期时间的平均ATM波动率
        term_structure = []
        for expiry in sorted(expiry_groups.keys()):
            avg_vol = np.mean(expiry_groups[expiry])
            term_structure.append({
                'expiry': expiry,
                'expiry_days': int(expiry * 365),
                'atm_volatility': float(avg_vol)
            })
        
        return term_structure
    
    def calculate_volatility_smile(
        self,
        option_data: List[Dict],
        spot_price: float,
        target_expiry: float,
        expiry_tolerance: float = 0.05
    ) -> List[Dict]:
        """
        计算波动率微笑/偏斜
        
        Args:
            option_data: 期权数据列表
            spot_price: 标的资产现价
            target_expiry: 目标到期时间（年）
            expiry_tolerance: 到期时间容差
            
        Returns:
            波动率微笑数据
        """
        # 筛选接近目标到期时间的期权
        filtered_data = [
            d for d in option_data
            if abs(d['expiry'] - target_expiry) <= expiry_tolerance
        ]
        
        if not filtered_data:
            raise ValueError(f"没有找到到期时间接近{target_expiry}年的期权")
        
        # 按执行价排序
        filtered_data.sort(key=lambda x: x['strike'])
        
        # 计算moneyness和整理数据
        smile_data = []
        for data in filtered_data:
            moneyness = data['strike'] / spot_price
            smile_data.append({
                'strike': data['strike'],
                'moneyness': float(moneyness),
                'implied_volatility': data['implied_vol'],
                'option_type': data.get('option_type', 'unknown')
            })
        
        return smile_data
    
    def compare_volatilities(
        self,
        historical_vol: float,
        implied_vol: float
    ) -> Dict:
        """
        比较历史波动率和隐含波动率
        
        Args:
            historical_vol: 历史波动率
            implied_vol: 隐含波动率
            
        Returns:
            比较结果
        """
        diff = implied_vol - historical_vol
        diff_pct = (diff / historical_vol) * 100 if historical_vol > 0 else 0
        
        # 判断市场情绪
        if diff_pct > 20:
            sentiment = "高度恐慌"
            recommendation = "考虑卖出波动率（卖出期权）"
        elif diff_pct > 10:
            sentiment = "谨慎"
            recommendation = "波动率偏高，可考虑卖出策略"
        elif diff_pct < -20:
            sentiment = "过度乐观"
            recommendation = "考虑买入波动率（买入期权）"
        elif diff_pct < -10:
            sentiment = "乐观"
            recommendation = "波动率偏低，可考虑买入策略"
        else:
            sentiment = "中性"
            recommendation = "波动率合理，可采用中性策略"
        
        return {
            'historical_volatility': historical_vol,
            'implied_volatility': implied_vol,
            'difference': diff,
            'difference_percent': diff_pct,
            'market_sentiment': sentiment,
            'trading_recommendation': recommendation
        }
    
    def detect_volatility_anomalies(
        self,
        volatility_series: List[float],
        threshold: float = 2.0
    ) -> List[Dict]:
        """
        检测波动率异常值
        
        Args:
            volatility_series: 波动率时间序列
            threshold: 异常值阈值（标准差倍数）
            
        Returns:
            异常值列表
        """
        vols = np.array(volatility_series)
        mean_vol = np.mean(vols)
        std_vol = np.std(vols)
        
        anomalies = []
        for i, vol in enumerate(vols):
            z_score = (vol - mean_vol) / std_vol if std_vol > 0 else 0
            
            if abs(z_score) > threshold:
                anomalies.append({
                    'index': i,
                    'volatility': float(vol),
                    'z_score': float(z_score),
                    'type': 'spike' if z_score > 0 else 'drop',
                    'severity': 'high' if abs(z_score) > 3 else 'medium'
                })
        
        return anomalies
    
    def calculate_volatility_cone(
        self,
        prices: List[float],
        windows: List[int] = [10, 20, 30, 60, 90, 120]
    ) -> Dict:
        """
        计算波动率锥（不同时间窗口的波动率分布）
        
        Args:
            prices: 价格序列
            windows: 时间窗口列表
            
        Returns:
            波动率锥数据
        """
        cone_data = []
        
        for window in windows:
            if len(prices) < window * 2:
                continue
            
            # 计算滚动波动率
            rolling_vols = []
            for i in range(window, len(prices)):
                vol = self.calculate_historical_volatility(
                    prices[i-window:i],
                    window=window,
                    annualize=True
                )
                rolling_vols.append(vol)
            
            if rolling_vols:
                cone_data.append({
                    'window': window,
                    'min': float(np.min(rolling_vols)),
                    'percentile_10': float(np.percentile(rolling_vols, 10)),
                    'percentile_25': float(np.percentile(rolling_vols, 25)),
                    'median': float(np.median(rolling_vols)),
                    'percentile_75': float(np.percentile(rolling_vols, 75)),
                    'percentile_90': float(np.percentile(rolling_vols, 90)),
                    'max': float(np.max(rolling_vols)),
                    'current': float(rolling_vols[-1])
                })
        
        return {
            'cone': cone_data,
            'description': '波动率锥显示不同时间窗口的历史波动率分布'
        }
