#!/usr/bin/env python3
"""
波动率信号融合模块
Multi-dimensional signal fusion for volatility trading

核心思路：
1. 新闻情绪评分（已有）
2. 隐含波动率水平（IV Rank）
3. 现货价格动量
4. 期权偏斜度（Skew）
5. 成交量异常

目标：提高信号质量，降低假信号
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import statistics


class VolatilitySignalFusion:
    """波动率信号融合器"""
    
    def __init__(self, deribit_trader):
        self.trader = deribit_trader
        self.historical_iv = []  # 存储历史 IV 数据
        self.historical_prices = []  # 存储历史价格
    
    async def get_current_iv(self, expiry_days: int = 7) -> float:
        """获取当前隐含波动率（ATM IV）"""
        try:
            # 获取 ATM 期权的 IV
            spot_price = await self.get_spot_price()
            instruments = await self.get_options_near_strike(spot_price, expiry_days)
            
            if not instruments:
                return 0.0
            
            # 计算 ATM Call 和 Put 的平均 IV
            ivs = []
            for inst in instruments[:4]:  # 取最接近的 4 个合约
                iv = await self.get_instrument_iv(inst['instrument_name'])
                if iv > 0:
                    ivs.append(iv)
            
            return statistics.mean(ivs) if ivs else 0.0
        
        except Exception as e:
            print(f"获取 IV 失败: {e}")
            return 0.0
    
    async def calculate_iv_rank(self, current_iv: float, lookback_days: int = 30) -> float:
        """
        计算 IV Rank (0-100)
        
        IV Rank = (当前IV - 最低IV) / (最高IV - 最低IV) * 100
        
        低 IV Rank (<30) = 买入机会
        高 IV Rank (>70) = 卖出机会
        """
        if not self.historical_iv or len(self.historical_iv) < 10:
            return 50.0  # 默认中位数
        
        recent_iv = self.historical_iv[-lookback_days:]
        min_iv = min(recent_iv)
        max_iv = max(recent_iv)
        
        if max_iv == min_iv:
            return 50.0
        
        iv_rank = ((current_iv - min_iv) / (max_iv - min_iv)) * 100
        return iv_rank
    
    async def calculate_momentum(self, lookback_hours: int = 24) -> float:
        """
        计算价格动量 (-1 到 1)
        
        正动量 + 正面新闻 = 强看涨
        负动量 + 负面新闻 = 强看跌
        """
        if len(self.historical_prices) < 2:
            return 0.0
        
        recent_prices = self.historical_prices[-lookback_hours:]
        price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        
        # 归一化到 -1 到 1
        return max(-1.0, min(1.0, price_change * 10))
    
    async def calculate_skew(self, spot_price: float, expiry_days: int = 7) -> float:
        """
        计算期权偏斜度
        
        Skew = Put IV - Call IV
        
        正偏斜（Put IV > Call IV）= 市场恐慌
        负偏斜（Call IV > Put IV）= 市场贪婪
        """
        try:
            # 获取 OTM Put 和 Call 的 IV
            put_strike = spot_price * 0.95  # 5% OTM Put
            call_strike = spot_price * 1.05  # 5% OTM Call
            
            put_iv = await self.get_strike_iv(put_strike, 'put', expiry_days)
            call_iv = await self.get_strike_iv(call_strike, 'call', expiry_days)
            
            if put_iv > 0 and call_iv > 0:
                return put_iv - call_iv
            
            return 0.0
        
        except Exception as e:
            print(f"计算 Skew 失败: {e}")
            return 0.0
    
    async def generate_composite_signal(
        self, 
        news_score: int,
        news_sentiment: str
    ) -> Dict:
        """
        生成综合交易信号
        
        Returns:
            {
                'action': 'BUY_STRADDLE' | 'BUY_CALL' | 'BUY_PUT' | 'WAIT',
                'confidence': 0-100,
                'position_size': 0.0-1.0,
                'reasoning': str
            }
        """
        # 1. 获取所有信号
        spot_price = await self.get_spot_price()
        current_iv = await self.get_current_iv()
        iv_rank = await self.calculate_iv_rank(current_iv)
        momentum = await self.calculate_momentum()
        skew = await self.calculate_skew(spot_price)
        
        # 更新历史数据
        self.historical_iv.append(current_iv)
        self.historical_prices.append(spot_price)
        
        # 保持最近 720 小时（30天）的数据
        if len(self.historical_iv) > 720:
            self.historical_iv = self.historical_iv[-720:]
        if len(self.historical_prices) > 720:
            self.historical_prices = self.historical_prices[-720:]
        
        # 2. 信号融合逻辑
        signal = {
            'action': 'WAIT',
            'confidence': 0,
            'position_size': 0.0,
            'reasoning': []
        }
        
        confidence_score = 0
        
        # 规则 1: 新闻评分（基础信号）
        if news_score >= 7:
            confidence_score += 30
            signal['reasoning'].append(f"高评分新闻 ({news_score}/10)")
        else:
            signal['reasoning'].append(f"新闻评分不足 ({news_score}/10)")
            return signal  # 评分不足，直接返回
        
        # 规则 2: IV Rank（入场时机）
        if iv_rank < 30:
            confidence_score += 25
            signal['reasoning'].append(f"低 IV 环境 (Rank: {iv_rank:.1f})")
        elif iv_rank < 50:
            confidence_score += 10
            signal['reasoning'].append(f"中等 IV 环境 (Rank: {iv_rank:.1f})")
        else:
            signal['reasoning'].append(f"高 IV 环境 (Rank: {iv_rank:.1f})，不适合买入")
            return signal
        
        # 规则 3: 动量与情绪一致性
        if news_sentiment == 'positive' and momentum > 0.2:
            confidence_score += 20
            signal['action'] = 'BUY_CALL'
            signal['reasoning'].append("正面新闻 + 正动量 → 看涨")
        elif news_sentiment == 'negative' and momentum < -0.2:
            confidence_score += 20
            signal['action'] = 'BUY_PUT'
            signal['reasoning'].append("负面新闻 + 负动量 → 看跌")
        elif abs(momentum) < 0.1:
            confidence_score += 15
            signal['action'] = 'BUY_STRADDLE'
            signal['reasoning'].append("无明确方向 → 跨式策略")
        else:
            confidence_score += 5
            signal['action'] = 'BUY_STRADDLE'
            signal['reasoning'].append("新闻与动量不一致 → 跨式策略")
        
        # 规则 4: Skew 调整
        if abs(skew) > 0.05:
            confidence_score += 10
            signal['reasoning'].append(f"显著偏斜 ({skew:.3f})")
        
        # 规则 5: 评分越高，仓位越大
        if news_score >= 9:
            position_multiplier = 1.0  # 满仓
        elif news_score >= 8:
            position_multiplier = 0.7
        else:
            position_multiplier = 0.5
        
        # 3. 最终决策
        signal['confidence'] = min(confidence_score, 100)
        signal['position_size'] = position_multiplier if confidence_score >= 50 else 0.0
        
        if signal['confidence'] < 50:
            signal['action'] = 'WAIT'
            signal['reasoning'].append(f"信心不足 ({signal['confidence']})")
        
        return signal
    
    # ===== 辅助方法 =====
    
    async def get_spot_price(self) -> float:
        """获取 BTC 现货价格"""
        try:
            url = f"{self.trader.base_url}/public/get_index_price"
            params = {"index_name": "btc_usd"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    return data['result']['index_price']
        except:
            return 0.0
    
    async def get_options_near_strike(self, strike: float, expiry_days: int) -> List[Dict]:
        """获取接近指定执行价的期权"""
        # 实现略（参考 weighted_sentiment_cron.py 中的逻辑）
        return []
    
    async def get_instrument_iv(self, instrument_name: str) -> float:
        """获取合约的隐含波动率"""
        try:
            url = f"{self.trader.base_url}/public/ticker"
            params = {"instrument_name": instrument_name}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    return data['result'].get('mark_iv', 0.0) / 100  # 转换为小数
        except:
            return 0.0
    
    async def get_strike_iv(self, strike: float, option_type: str, expiry_days: int) -> float:
        """获取指定执行价的 IV"""
        # 实现略
        return 0.0
