"""
数据和分析API接口
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime

from src.connectors.deribit_connector import DeribitConnector
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


@router.get("/options-chain", response_model=List[OptionChainResponse])
async def get_options_chain(
    currency: str = "BTC",
    kind: str = "option"
):
    """
    获取期权链数据
    
    Args:
        currency: 货币类型
        kind: 合约类型
        
    Returns:
        期权链数据列表
    """
    try:
        connector = DeribitConnector()
        options_data = await connector.get_options_chain(currency, kind)
        
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
