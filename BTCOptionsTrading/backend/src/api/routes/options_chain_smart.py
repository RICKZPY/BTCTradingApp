"""
智能期权链数据API
支持ATM数据、缓存数据、按需加载等功能
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
import math

from src.connectors.deribit_connector import DeribitConnector
from src.connectors.market_data_cache import get_cache
from src.config.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ============================================================================
# 数据模型
# ============================================================================

class OptionData(BaseModel):
    """期权数据"""
    instrument_name: str
    strike: float
    option_type: str
    mark_price: Optional[float]
    implied_volatility: Optional[float]
    delta: Optional[float]
    gamma: Optional[float]
    theta: Optional[float]
    vega: Optional[float]
    bid_price: Optional[float]
    ask_price: Optional[float]
    volume: Optional[float]
    open_interest: Optional[float]


class ATMOptionsResponse(BaseModel):
    """ATM期权响应"""
    underlying_price: float
    expiration_date: str
    expiration_timestamp: int
    atm_strike: float
    call_options: List[OptionData]
    put_options: List[OptionData]
    timestamp: str


class StrikeRangeResponse(BaseModel):
    """执行价范围响应"""
    underlying_price: float
    expiration_date: str
    expiration_timestamp: int
    min_strike: float
    max_strike: float
    atm_strike: float
    options: List[OptionData]
    timestamp: str


# ============================================================================
# 辅助函数
# ============================================================================

def format_expiry_date(expiration_date) -> str:
    """
    将expiration_date格式化为YYYY-MM-DD字符串
    处理timezone-aware和naive datetime对象
    """
    if hasattr(expiration_date, 'date'):
        # 如果是datetime对象，提取date部分（自动处理timezone）
        return expiration_date.date().isoformat()
    elif isinstance(expiration_date, str):
        # 如果已经是字符串，直接返回
        return expiration_date
    else:
        # 其他情况，尝试转换
        return str(expiration_date)


def find_atm_strike(underlying_price: float, available_strikes: List[float]) -> float:
    """
    找到最接近标的价格的执行价（ATM）
    
    Args:
        underlying_price: 标的资产价格
        available_strikes: 可用的执行价列表
        
    Returns:
        最接近的执行价
    """
    if not available_strikes:
        return float(underlying_price)
    
    # 确保所有值都是float
    underlying_price = float(underlying_price)
    available_strikes = [float(s) for s in available_strikes]
    
    # 找到最接近的执行价
    atm_strike = min(available_strikes, key=lambda x: abs(x - underlying_price))
    return float(atm_strike)


def get_strike_range(atm_strike: float, num_strikes: int = 5) -> tuple:
    """
    获取ATM周围的执行价范围
    
    Args:
        atm_strike: ATM执行价
        num_strikes: 上下各多少个执行价
        
    Returns:
        (min_strike, max_strike)
    """
    # 确保atm_strike是float
    atm_strike = float(atm_strike)
    
    # 假设执行价间隔为1000
    interval = 1000
    min_strike = atm_strike - (num_strikes * interval)
    max_strike = atm_strike + (num_strikes * interval)
    return float(min_strike), float(max_strike)


def convert_option_to_response(option) -> OptionData:
    """将OptionContract对象转换为OptionData"""
    return OptionData(
        instrument_name=option.instrument_name,
        strike=float(option.strike_price),
        option_type=option.option_type.value,
        mark_price=float(option.current_price) if option.current_price else None,
        implied_volatility=option.implied_volatility,
        delta=option.delta,
        gamma=option.gamma,
        theta=option.theta,
        vega=option.vega,
        bid_price=float(option.bid_price) if option.bid_price else None,
        ask_price=float(option.ask_price) if option.ask_price else None,
        volume=option.volume,
        open_interest=option.open_interest
    )


# ============================================================================
# API端点
# ============================================================================

@router.get("/atm", response_model=ATMOptionsResponse)
async def get_atm_options(
    currency: str = "BTC",
    expiry_date: Optional[str] = Query(None, description="到期日期 (YYYY-MM-DD)"),
    num_strikes: int = Query(5, description="ATM上下各多少个执行价")
):
    """
    获取ATM期权数据（轻量级）
    
    只返回ATM附近的期权数据，大幅减少数据量
    
    Args:
        currency: 货币类型 (BTC/ETH)
        expiry_date: 到期日期，如果不指定则返回最近的到期日
        num_strikes: ATM上下各多少个执行价（默认5个）
        
    Returns:
        ATM期权数据
    """
    connector = None
    try:
        # 尝试从缓存获取
        cache = get_cache(ttl_seconds=300)
        cache_key = f"atm_options_{currency}_{expiry_date}_{num_strikes}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"ATM options cache hit: {cache_key}")
            return cached_data
        
        connector = DeribitConnector()
        
        # 获取标的价格
        underlying_price = await connector.get_index_price(currency)
        
        # 获取期权链数据
        options_data = await connector.get_options_chain(currency)
        
        # 按到期日分组 - 使用统一的日期格式
        expiry_map = {}
        for option in options_data:
            expiry_date_str = format_expiry_date(option.expiration_date)
            if expiry_date_str not in expiry_map:
                expiry_map[expiry_date_str] = {
                    'timestamp': int(option.expiration_date.timestamp()),
                    'options': []
                }
            expiry_map[expiry_date_str]['options'].append(option)
        
        logger.info(f"Available expiry dates: {sorted(expiry_map.keys())}")
        
        # 选择到期日
        if expiry_date:
            # 规范化输入的日期格式
            if expiry_date not in expiry_map:
                logger.warning(f"Requested expiry_date '{expiry_date}' not found. Available: {sorted(expiry_map.keys())}")
                raise HTTPException(status_code=404, detail=f"No options for expiry date: {expiry_date}. Available dates: {sorted(expiry_map.keys())}")
            selected_expiry = expiry_date
        else:
            # 选择最近的到期日
            selected_expiry = min(expiry_map.keys())
        
        selected_options = expiry_map[selected_expiry]['options']
        selected_timestamp = expiry_map[selected_expiry]['timestamp']
        
        logger.info(f"Selected expiry: {selected_expiry}, options count: {len(selected_options)}")
        
        # 找到ATM执行价
        available_strikes = sorted(set(float(opt.strike_price) for opt in selected_options))
        atm_strike = find_atm_strike(underlying_price, available_strikes)
        
        # 获取ATM范围内的执行价
        min_strike, max_strike = get_strike_range(atm_strike, num_strikes)
        
        # 过滤ATM范围内的期权
        call_options = []
        put_options = []
        
        for option in selected_options:
            if min_strike <= float(option.strike_price) <= max_strike:
                option_data = convert_option_to_response(option)
                if option.option_type.value == 'call':
                    call_options.append(option_data)
                else:
                    put_options.append(option_data)
        
        # 按执行价排序
        call_options.sort(key=lambda x: x.strike)
        put_options.sort(key=lambda x: x.strike)
        
        result = ATMOptionsResponse(
            underlying_price=underlying_price,
            expiration_date=selected_expiry,
            expiration_timestamp=selected_timestamp,
            atm_strike=atm_strike,
            call_options=call_options,
            put_options=put_options,
            timestamp=datetime.now().isoformat()
        )
        
        # 存入缓存
        cache.set(cache_key, result)
        logger.info(f"ATM options retrieved: {len(call_options)} calls, {len(put_options)} puts")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ATM options: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connector:
            await connector.close()


@router.get("/strike-range", response_model=StrikeRangeResponse)
async def get_strike_range_options(
    currency: str = "BTC",
    expiry_date: Optional[str] = Query(None, description="到期日期 (YYYY-MM-DD)"),
    min_strike: Optional[float] = Query(None, description="最小执行价"),
    max_strike: Optional[float] = Query(None, description="最大执行价"),
    num_strikes: int = Query(10, description="如果不指定范围，ATM上下各多少个执行价")
):
    """
    获取指定执行价范围的期权数据
    
    支持两种模式：
    1. 指定min_strike和max_strike：返回该范围内的所有期权
    2. 不指定范围：返回ATM上下各num_strikes个执行价的期权
    
    Args:
        currency: 货币类型 (BTC/ETH)
        expiry_date: 到期日期
        min_strike: 最小执行价
        max_strike: 最大执行价
        num_strikes: 如果不指定范围，ATM上下各多少个执行价
        
    Returns:
        执行价范围内的期权数据
    """
    connector = None
    try:
        # 尝试从缓存获取
        cache = get_cache(ttl_seconds=300)
        cache_key = f"strike_range_{currency}_{expiry_date}_{min_strike}_{max_strike}_{num_strikes}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Strike range cache hit: {cache_key}")
            return cached_data
        
        connector = DeribitConnector()
        
        # 获取标的价格
        underlying_price = await connector.get_index_price(currency)
        
        # 获取期权链数据
        options_data = await connector.get_options_chain(currency)
        
        # 按到期日分组 - 使用统一的日期格式
        expiry_map = {}
        for option in options_data:
            expiry_date_str = format_expiry_date(option.expiration_date)
            if expiry_date_str not in expiry_map:
                expiry_map[expiry_date_str] = {
                    'timestamp': int(option.expiration_date.timestamp()),
                    'options': []
                }
            expiry_map[expiry_date_str]['options'].append(option)
        
        # 选择到期日
        if expiry_date:
            if expiry_date not in expiry_map:
                raise HTTPException(status_code=404, detail=f"No options for expiry date: {expiry_date}")
            selected_expiry = expiry_date
        else:
            selected_expiry = min(expiry_map.keys())
        
        selected_options = expiry_map[selected_expiry]['options']
        selected_timestamp = expiry_map[selected_expiry]['timestamp']
        
        # 确定执行价范围
        if min_strike is None or max_strike is None:
            # 使用ATM范围
            available_strikes = sorted(set(float(opt.strike_price) for opt in selected_options))
            atm_strike = find_atm_strike(underlying_price, available_strikes)
            min_strike, max_strike = get_strike_range(atm_strike, num_strikes)
        
        atm_strike = find_atm_strike(underlying_price, [float(opt.strike_price) for opt in selected_options])
        
        # 过滤范围内的期权
        filtered_options = []
        for option in selected_options:
            if min_strike <= float(option.strike_price) <= max_strike:
                filtered_options.append(convert_option_to_response(option))
        
        # 按执行价排序
        filtered_options.sort(key=lambda x: x.strike)
        
        result = StrikeRangeResponse(
            underlying_price=underlying_price,
            expiration_date=selected_expiry,
            expiration_timestamp=selected_timestamp,
            min_strike=min_strike,
            max_strike=max_strike,
            atm_strike=atm_strike,
            options=filtered_options,
            timestamp=datetime.now().isoformat()
        )
        
        # 存入缓存
        cache.set(cache_key, result)
        logger.info(f"Strike range retrieved: {len(filtered_options)} options")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strike range options: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connector:
            await connector.close()


@router.get("/cached-strikes")
async def get_cached_strikes(
    currency: str = "BTC",
    expiry_date: Optional[str] = Query(None, description="到期日期 (YYYY-MM-DD)")
):
    """
    获取缓存中的执行价列表
    
    不调用API，只返回缓存中已有的执行价
    
    Args:
        currency: 货币类型
        expiry_date: 到期日期
        
    Returns:
        缓存中的执行价列表
    """
    try:
        cache = get_cache(ttl_seconds=300)
        
        # 尝试从缓存获取完整期权链
        cache_key = f"options_chain_{currency}"
        cached_options = cache.get(cache_key)
        
        if cached_options is None:
            return {
                "currency": currency,
                "expiry_date": expiry_date,
                "strikes": [],
                "message": "No cached data available",
                "timestamp": datetime.now().isoformat()
            }
        
        # 提取执行价
        strikes_set = set()
        expiry_dates_set = set()
        
        for option in cached_options:
            strikes_set.add(float(option.strike))
            expiry_dates_set.add(format_expiry_date(option.expiration_date))
        
        # 如果指定了到期日，只返回该日期的执行价
        if expiry_date:
            filtered_strikes = set()
            for option in cached_options:
                if format_expiry_date(option.expiration_date) == expiry_date:
                    filtered_strikes.add(float(option.strike))
            strikes = sorted(list(filtered_strikes))
        else:
            strikes = sorted(list(strikes_set))
        
        return {
            "currency": currency,
            "expiry_date": expiry_date,
            "strikes": strikes,
            "available_expiry_dates": sorted(list(expiry_dates_set)),
            "count": len(strikes),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get cached strikes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
