#!/usr/bin/env python3
"""
加权情绪跨式期权交易 - 数据模型
Data models for weighted sentiment straddle trading system
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class WeightedNews:
    """加权情绪新闻数据类"""
    news_id: str
    content: str
    sentiment: str
    importance_score: float   # 支持小数（API 返回 8.5 等）
    timestamp: datetime
    source: Optional[str] = None
    has_similar_high_scores: bool = False   # API 已检测到同类高频新闻
    event_category: str = ""               # 事件分类，如 "地缘冲突"

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        if not self.news_id or not self.news_id.strip():
            raise ValueError("news_id 不能为空")
        if not isinstance(self.importance_score, (int, float)):
            raise ValueError(f"importance_score 必须是数字，当前类型: {type(self.importance_score)}")
        if not (0 <= self.importance_score <= 10):
            raise ValueError(f"importance_score 必须在 0-10 范围内，当前值: {self.importance_score}")
        valid_sentiments = {"positive", "negative", "neutral"}
        if self.sentiment not in valid_sentiments:
            raise ValueError(f"sentiment 必须是 {valid_sentiments} 之一，当前值: {self.sentiment}")


@dataclass
class OptionTrade:
    """期权交易数据类
    
    表示单个期权交易（看涨或看跌），包含完整的交易详情和验证逻辑
    """
    instrument_name: str      # 期权合约名称
    option_type: str          # "call" or "put"
    strike_price: float       # 执行价格
    expiry_date: datetime     # 到期日
    premium: float            # 期权价格
    quantity: float           # 交易数量
    order_id: Optional[str] = None  # Deribit 订单ID
    
    def __post_init__(self):
        """验证数据完整性和有效性"""
        self.validate()
    
    def validate(self) -> None:
        """验证期权交易数据的有效性
        
        验证规则：
        - option_type 必须是 "call" 或 "put"
        - strike_price 必须为正数
        - premium 必须为正数
        - quantity 必须为正数
        - expiry_date 必须在未来
        
        Raises:
            ValueError: 如果验证失败
        """
        # 验证 option_type
        valid_types = {"call", "put"}
        if self.option_type not in valid_types:
            raise ValueError(
                f"option_type 必须是 {valid_types} 之一，当前值: {self.option_type}"
            )
        
        # 验证 strike_price 为正数
        if not isinstance(self.strike_price, (int, float)):
            raise ValueError(f"strike_price 必须是数字，当前类型: {type(self.strike_price)}")
        
        if self.strike_price <= 0:
            raise ValueError(f"strike_price 必须为正数，当前值: {self.strike_price}")
        
        # 验证 premium 为正数
        if not isinstance(self.premium, (int, float)):
            raise ValueError(f"premium 必须是数字，当前类型: {type(self.premium)}")
        
        if self.premium <= 0:
            raise ValueError(f"premium 必须为正数，当前值: {self.premium}")
        
        # 验证 quantity 为正数
        if not isinstance(self.quantity, (int, float)):
            raise ValueError(f"quantity 必须是数字，当前类型: {type(self.quantity)}")
        
        if self.quantity <= 0:
            raise ValueError(f"quantity 必须为正数，当前值: {self.quantity}")
        
        # 验证 expiry_date 在未来
        if not isinstance(self.expiry_date, datetime):
            raise ValueError(f"expiry_date 必须是 datetime 对象，当前类型: {type(self.expiry_date)}")
        
        if self.expiry_date <= datetime.now():
            raise ValueError(f"expiry_date 必须在未来，当前值: {self.expiry_date}")


@dataclass
class StraddleTradeResult:
    """跨式交易结果数据类
    
    表示一次完整的跨式期权交易执行结果，包含看涨和看跌期权的详细信息
    """
    success: bool                           # 交易是否成功
    news_id: str                            # 触发交易的新闻ID
    trade_time: datetime                    # 交易执行时间
    spot_price: float                       # 交易时的现货价格
    call_option: Optional[OptionTrade]      # 看涨期权交易详情
    put_option: Optional[OptionTrade]       # 看跌期权交易详情
    total_cost: float                       # 总成本（看涨期权费 + 看跌期权费）
    error_message: Optional[str] = None     # 错误信息（失败时）
    
    def __post_init__(self):
        """验证数据完整性和有效性"""
        self.validate()
    
    def validate(self) -> None:
        """验证跨式交易结果的有效性
        
        验证规则：
        - success 为 True 时，call_option 和 put_option 必须非空
        - success 为 False 时，error_message 必须提供
        - total_cost 必须为正数（当 success 为 True 时）
        
        Raises:
            ValueError: 如果验证失败
        """
        # 验证成功交易的完整性
        if self.success:
            if self.call_option is None:
                raise ValueError("成功的交易必须包含 call_option")
            
            if self.put_option is None:
                raise ValueError("成功的交易必须包含 put_option")
            
            # 验证 total_cost 为正数
            if not isinstance(self.total_cost, (int, float)):
                raise ValueError(f"total_cost 必须是数字，当前类型: {type(self.total_cost)}")
            
            if self.total_cost <= 0:
                raise ValueError(f"total_cost 必须为正数，当前值: {self.total_cost}")
        
        # 验证失败交易必须提供错误信息
        if not self.success:
            if not self.error_message:
                raise ValueError("失败的交易必须提供 error_message")
        
        # 验证 spot_price 为正数
        if not isinstance(self.spot_price, (int, float)):
            raise ValueError(f"spot_price 必须是数字，当前类型: {type(self.spot_price)}")
        
        if self.spot_price <= 0:
            raise ValueError(f"spot_price 必须为正数，当前值: {self.spot_price}")


@dataclass
class TradeRecord:
    """交易记录数据类
    
    表示数据库中存储的完整交易记录，包含新闻信息和交易详情的关联
    用于历史查询和数据分析
    """
    id: int                                 # 数据库记录ID
    news_id: str                            # 触发交易的新闻ID
    news_content: str                       # 新闻内容
    sentiment: str                          # 新闻情绪方向
    importance_score: int                   # 新闻重要性评分
    trade_time: datetime                    # 交易执行时间
    spot_price: float                       # 交易时的现货价格
    call_instrument: str                    # 看涨期权合约名称
    call_strike: float                      # 看涨期权执行价格
    call_premium: float                     # 看涨期权价格
    put_instrument: str                     # 看跌期权合约名称
    put_strike: float                       # 看跌期权执行价格
    put_premium: float                      # 看跌期权价格
    total_cost: float                       # 总成本
    success: bool                           # 交易是否成功
    error_message: Optional[str] = None     # 错误信息（失败时）
    
    def __post_init__(self):
        """验证数据完整性和有效性"""
        self.validate()
    
    def validate(self) -> None:
        """验证交易记录的有效性
        
        验证规则：
        - importance_score 必须在 1-10 范围内
        - sentiment 必须是有效值之一
        - 所有价格字段必须为正数（当 success 为 True 时）
        
        Raises:
            ValueError: 如果验证失败
        """
        # 验证 importance_score 范围
        if not isinstance(self.importance_score, int):
            raise ValueError(f"importance_score 必须是整数，当前类型: {type(self.importance_score)}")
        
        if not (1 <= self.importance_score <= 10):
            raise ValueError(f"importance_score 必须在 1-10 范围内，当前值: {self.importance_score}")
        
        # 验证 sentiment 为有效值
        valid_sentiments = {"positive", "negative", "neutral"}
        if self.sentiment not in valid_sentiments:
            raise ValueError(
                f"sentiment 必须是 {valid_sentiments} 之一，当前值: {self.sentiment}"
            )
        
        # 验证 spot_price 为正数
        if not isinstance(self.spot_price, (int, float)):
            raise ValueError(f"spot_price 必须是数字，当前类型: {type(self.spot_price)}")
        
        if self.spot_price <= 0:
            raise ValueError(f"spot_price 必须为正数，当前值: {self.spot_price}")
        
        # 对于成功的交易，验证所有价格字段为正数
        if self.success:
            # 验证 call_strike
            if not isinstance(self.call_strike, (int, float)):
                raise ValueError(f"call_strike 必须是数字，当前类型: {type(self.call_strike)}")
            
            if self.call_strike <= 0:
                raise ValueError(f"call_strike 必须为正数，当前值: {self.call_strike}")
            
            # 验证 call_premium
            if not isinstance(self.call_premium, (int, float)):
                raise ValueError(f"call_premium 必须是数字，当前类型: {type(self.call_premium)}")
            
            if self.call_premium <= 0:
                raise ValueError(f"call_premium 必须为正数，当前值: {self.call_premium}")
            
            # 验证 put_strike
            if not isinstance(self.put_strike, (int, float)):
                raise ValueError(f"put_strike 必须是数字，当前类型: {type(self.put_strike)}")
            
            if self.put_strike <= 0:
                raise ValueError(f"put_strike 必须为正数，当前值: {self.put_strike}")
            
            # 验证 put_premium
            if not isinstance(self.put_premium, (int, float)):
                raise ValueError(f"put_premium 必须是数字，当前类型: {type(self.put_premium)}")
            
            if self.put_premium <= 0:
                raise ValueError(f"put_premium 必须为正数，当前值: {self.put_premium}")
            
            # 验证 total_cost
            if not isinstance(self.total_cost, (int, float)):
                raise ValueError(f"total_cost 必须是数字，当前类型: {type(self.total_cost)}")
            
            if self.total_cost <= 0:
                raise ValueError(f"total_cost 必须为正数，当前值: {self.total_cost}")
