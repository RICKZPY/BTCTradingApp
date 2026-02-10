"""
数据和分析API接口
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime

from src.connectors.deribit_connector import DeribitConnector
from src.connectors.market_data_cache import get_cache
from src.pricing.options_engine import OptionsEngine
from src.core.models import OptionType

router = APIRouter()


# Pydantic模型
class OptionChainRequest(BaseModel):
    """期权链请求模型"""
    currency: str = "BTC"
    kind: str = "option"


class OptionChainResponse(BaseModel):
    """期权链响应模型"""
    instrument_name: str
    strike: float
    option_type: str
    expiration_timestamp: int
    bid_price: Optional[float]
    ask_price: Optional[float]
    last_price: Optional[float]
    mark_price: Optional[float]
    implied_volatility: Optional[float]
    delta: Optional[float]
    gamma: Optional[float]
    theta: Optional[float]
    vega: Optional[float]
    volume: Optional[float]
    open_interest: Optional[float]


class GreeksCalculationRequest(BaseModel):
    """希腊字母计算请求"""
    spot_price: float
    strike_price: float
    time_to_expiry: float
    volatility: float
    risk_free_rate: float = 0.05
    option_type: str = "call"


class GreeksResponse(BaseModel):
    """希腊字母响应"""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    price: float


class EnhancedOptionData(BaseModel):
    """增强的期权数据"""
    instrument_name: str
    strike: float
    option_type: str
    bid_price: Optional[float]
    ask_price: Optional[float]
    last_price: Optional[float]
    mark_price: Optional[float]
    implied_volatility: Optional[float]
    delta: Optional[float]
    gamma: Optional[float]
    theta: Optional[float]
    vega: Optional[float]
    volume: Optional[float]
    open_interest: Optional[float]


class ExpiryGroup(BaseModel):
    """到期日分组"""
    expiration_date: str
    expiration_timestamp: int
    days_to_expiry: int
    options: List[EnhancedOptionData]


class EnhancedOptionsChainResponse(BaseModel):
    """增强的期权链响应"""
    currency: str
    underlying_price: float
    timestamp: str
    expiry_groups: List[ExpiryGroup]


@router.get("/options-chain", response_model=List[OptionChainResponse])
async def get_options_chain(
    currency: str = "BTC"
):
    """
    获取期权链数据
    
    Args:
        currency: 货币类型
        
    Returns:
        期权链数据列表
    """
    try:
        connector = DeribitConnector()
        options_data = await connector.get_options_chain(currency)
        
        result = []
        for option in options_data:
            result.append(OptionChainResponse(
                instrument_name=option.get("instrument_name", ""),
                strike=option.get("strike", 0),
                option_type=option.get("option_type", ""),
                expiration_timestamp=option.get("expiration_timestamp", 0),
                bid_price=option.get("bid_price"),
                ask_price=option.get("ask_price"),
                last_price=option.get("last_price"),
                mark_price=option.get("mark_price"),
                implied_volatility=option.get("mark_iv"),
                delta=option.get("greeks", {}).get("delta"),
                gamma=option.get("greeks", {}).get("gamma"),
                theta=option.get("greeks", {}).get("theta"),
                vega=option.get("greeks", {}).get("vega"),
                volume=option.get("stats", {}).get("volume"),
                open_interest=option.get("open_interest")
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/options-chain-enhanced", response_model=EnhancedOptionsChainResponse)
async def get_options_chain_enhanced(
    currency: str = "BTC",
    use_cache: bool = True
):
    """
    获取增强的期权链数据（按到期日分组）
    
    Args:
        currency: 货币类型
        use_cache: 是否使用缓存（默认True）
        
    Returns:
        按到期日分组的期权链数据，包含标的价格和到期天数
    """
    try:
        cache = get_cache(ttl_seconds=300)  # 5分钟TTL
        cache_key = f"options_chain_enhanced_{currency}"
        
        # 尝试从缓存获取
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return cached_data
        
        connector = DeribitConnector()
        
        # 获取标的价格
        underlying_price = await connector.get_index_price(currency)
        
        # 获取期权链数据
        options_data = await connector.get_options_chain(currency)
        
        # 按到期日分组
        expiry_map = {}
        for option in options_data:
            expiry_timestamp = option.expiration_date.timestamp() if hasattr(option.expiration_date, 'timestamp') else 0
            expiry_date_str = option.expiration_date.strftime("%Y-%m-%d") if hasattr(option.expiration_date, 'strftime') else ""
            
            # 计算到期天数
            days_to_expiry = (option.expiration_date - datetime.now()).days if hasattr(option.expiration_date, '__sub__') else 0
            
            if expiry_date_str not in expiry_map:
                expiry_map[expiry_date_str] = {
                    'expiration_date': expiry_date_str,
                    'expiration_timestamp': int(expiry_timestamp),
                    'days_to_expiry': days_to_expiry,
                    'options': []
                }
            
            # 添加期权数据
            expiry_map[expiry_date_str]['options'].append(EnhancedOptionData(
                instrument_name=option.instrument_name,
                strike=float(option.strike_price),
                option_type=option.option_type.value,
                bid_price=float(option.bid_price) if option.bid_price else None,
                ask_price=float(option.ask_price) if option.ask_price else None,
                last_price=float(option.last_price) if option.last_price else None,
                mark_price=float(option.current_price) if option.current_price else None,
                implied_volatility=option.implied_volatility,
                delta=option.delta,
                gamma=option.gamma,
                theta=option.theta,
                vega=option.vega,
                volume=option.volume,
                open_interest=option.open_interest
            ))
        
        # 转换为列表并按到期日排序
        expiry_groups = [
            ExpiryGroup(**group_data)
            for group_data in sorted(expiry_map.values(), key=lambda x: x['expiration_timestamp'])
        ]
        
        result = EnhancedOptionsChainResponse(
            currency=currency,
            underlying_price=underlying_price,
            timestamp=datetime.now().isoformat(),
            expiry_groups=expiry_groups
        )
        
        # 存入缓存
        if use_cache:
            cache.set(cache_key, result)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-greeks", response_model=GreeksResponse)
async def calculate_greeks(request: GreeksCalculationRequest):
    """
    计算期权希腊字母
    
    Args:
        request: 希腊字母计算请求
        
    Returns:
        希腊字母计算结果
    """
    try:
        engine = OptionsEngine()
        
        # 计算期权价格
        option_type = OptionType.CALL if request.option_type.lower() == "call" else OptionType.PUT
        price = engine.black_scholes_price(
            spot_price=request.spot_price,
            strike_price=request.strike_price,
            time_to_expiry=request.time_to_expiry,
            volatility=request.volatility,
            risk_free_rate=request.risk_free_rate,
            option_type=option_type
        )
        
        # 计算希腊字母
        greeks = engine.calculate_greeks(
            spot_price=request.spot_price,
            strike_price=request.strike_price,
            time_to_expiry=request.time_to_expiry,
            volatility=request.volatility,
            risk_free_rate=request.risk_free_rate,
            option_type=option_type
        )
        
        return GreeksResponse(
            delta=greeks.delta,
            gamma=greeks.gamma,
            theta=greeks.theta,
            vega=greeks.vega,
            rho=greeks.rho,
            price=price
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/underlying-price/{symbol}")
async def get_underlying_price(symbol: str = "BTC"):
    """
    获取标的资产当前价格
    
    Args:
        symbol: 资产符号
        
    Returns:
        当前价格信息
    """
    try:
        connector = DeribitConnector()
        index_price = await connector.get_index_price(symbol)
        
        return {
            "symbol": symbol,
            "price": index_price,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/volatility-surface/{currency}")
async def get_volatility_surface(currency: str = "BTC"):
    """
    获取波动率曲面数据
    
    Args:
        currency: 货币类型
        
    Returns:
        波动率曲面数据
    """
    try:
        connector = DeribitConnector()
        surface_data = await connector.get_volatility_surface(currency)
        
        return {
            "currency": currency,
            "data": surface_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats():
    """
    获取缓存统计信息
    
    Returns:
        缓存统计数据
    """
    cache = get_cache()
    stats = cache.get_stats()
    return {
        "cache_stats": stats,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/cache/clear")
async def clear_cache():
    """
    清空所有缓存
    
    Returns:
        操作结果
    """
    cache = get_cache()
    cache.clear()
    return {
        "message": "Cache cleared successfully",
        "timestamp": datetime.now().isoformat()
    }


@router.post("/cache/cleanup")
async def cleanup_cache():
    """
    清理过期的缓存条目
    
    Returns:
        清理结果
    """
    cache = get_cache()
    cleaned_count = cache.cleanup_expired()
    return {
        "message": f"Cleaned up {cleaned_count} expired entries",
        "cleaned_count": cleaned_count,
        "timestamp": datetime.now().isoformat()
    }
