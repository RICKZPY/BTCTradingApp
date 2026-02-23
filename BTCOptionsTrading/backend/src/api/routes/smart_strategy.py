"""
智能策略API路由
支持相对时间和相对价格的策略创建
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

from ...strategy.smart_strategy_builder import (
    SmartStrategyBuilder,
    SmartStrategyTemplate,
    SmartStrategyLeg,
    RelativeExpiry,
    RelativeStrike,
    PREDEFINED_TEMPLATES
)
from ...core.models import StrategyType, OptionType, ActionType
from ...connectors.deribit_connector import DeribitConnector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/smart-strategy", tags=["smart-strategy"])


class SmartLegRequest(BaseModel):
    """智能策略腿请求"""
    option_type: str  # "call" or "put"
    action: str  # "buy" or "sell"
    quantity: int
    relative_expiry: str  # "T+1", "T+7", etc.
    relative_strike: str  # "ATM", "ITM+1", "OTM+1", etc.


class SmartStrategyRequest(BaseModel):
    """智能策略请求"""
    name: str
    description: str
    strategy_type: str
    legs: List[SmartLegRequest]
    underlying: str = "BTC"


class RelativeOption(BaseModel):
    """相对选项"""
    value: str
    label: str
    description: str


@router.get("/relative-expiries")
async def get_relative_expiries():
    """
    获取所有相对到期日选项
    """
    expiries = [
        {"value": "T+1", "label": "明天", "description": "1天后到期"},
        {"value": "T+2", "label": "后天", "description": "2天后到期"},
        {"value": "T+7", "label": "一周", "description": "7天后到期"},
        {"value": "T+14", "label": "两周", "description": "14天后到期"},
        {"value": "T+30", "label": "一个月", "description": "30天后到期"},
        {"value": "T+60", "label": "两个月", "description": "60天后到期"},
        {"value": "T+90", "label": "三个月", "description": "90天后到期"}
    ]
    return {"expiries": expiries}


@router.get("/relative-strikes")
async def get_relative_strikes():
    """
    获取所有相对行权价选项
    """
    strikes = [
        {"value": "ITM+3", "label": "实值第3档", "description": "深度实值"},
        {"value": "ITM+2", "label": "实值第2档", "description": "实值"},
        {"value": "ITM+1", "label": "实值第1档", "description": "轻度实值"},
        {"value": "ATM", "label": "平值", "description": "当前价格附近"},
        {"value": "OTM+1", "label": "虚值第1档", "description": "轻度虚值"},
        {"value": "OTM+2", "label": "虚值第2档", "description": "虚值"},
        {"value": "OTM+3", "label": "虚值第3档", "description": "深度虚值"}
    ]
    return {"strikes": strikes}


@router.get("/templates")
async def get_predefined_templates():
    """
    获取预定义的策略模板
    """
    templates = []
    for key, template in PREDEFINED_TEMPLATES.items():
        templates.append({
            "id": key,
            "name": template.name,
            "description": template.description,
            "strategy_type": template.strategy_type.value,
            "legs": [leg.to_dict() for leg in template.legs]
        })
    
    return {"templates": templates}


@router.post("/build")
async def build_smart_strategy(request: SmartStrategyRequest):
    """
    根据智能模板构建实际策略
    """
    try:
        # 创建智能策略腿
        smart_legs = []
        for leg_req in request.legs:
            smart_leg = SmartStrategyLeg(
                option_type=OptionType(leg_req.option_type),
                action=ActionType(leg_req.action),
                quantity=leg_req.quantity,
                relative_expiry=RelativeExpiry(leg_req.relative_expiry),
                relative_strike=RelativeStrike(leg_req.relative_strike)
            )
            smart_legs.append(smart_leg)
        
        # 创建模板
        template = SmartStrategyTemplate(
            name=request.name,
            description=request.description,
            strategy_type=StrategyType(request.strategy_type),
            legs=smart_legs
        )
        
        # 构建策略
        connector = DeribitConnector()
        builder = SmartStrategyBuilder(connector)
        strategy = await builder.build_strategy(template, request.underlying)
        
        # 转换为响应格式
        response = {
            "id": str(strategy.id),
            "name": strategy.name,
            "description": strategy.description,
            "strategy_type": strategy.strategy_type.value,
            "legs": [
                {
                    "instrument_name": leg.option_contract.instrument_name,
                    "option_type": leg.option_contract.option_type.value,
                    "strike_price": float(leg.option_contract.strike_price),
                    "expiration_date": leg.option_contract.expiration_date.isoformat(),
                    "action": leg.action.value,
                    "quantity": leg.quantity,
                    "current_price": float(leg.option_contract.current_price),
                    "bid_price": float(leg.option_contract.bid_price),
                    "ask_price": float(leg.option_contract.ask_price),
                    "delta": leg.option_contract.delta,
                    "gamma": leg.option_contract.gamma,
                    "theta": leg.option_contract.theta,
                    "vega": leg.option_contract.vega
                }
                for leg in strategy.legs
            ],
            "total_cost": float(strategy.total_cost),
            "net_delta": strategy.net_delta
        }
        
        return response
        
    except Exception as e:
        logger.error(f"构建智能策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/build-from-template/{template_id}")
async def build_from_template(template_id: str, underlying: str = "BTC"):
    """
    从预定义模板构建策略
    """
    try:
        if template_id not in PREDEFINED_TEMPLATES:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        template = PREDEFINED_TEMPLATES[template_id]
        
        # 构建策略
        connector = DeribitConnector()
        builder = SmartStrategyBuilder(connector)
        strategy = await builder.build_strategy(template, underlying)
        
        # 转换为响应格式
        response = {
            "id": str(strategy.id),
            "name": strategy.name,
            "description": strategy.description,
            "strategy_type": strategy.strategy_type.value,
            "legs": [
                {
                    "instrument_name": leg.option_contract.instrument_name,
                    "option_type": leg.option_contract.option_type.value,
                    "strike_price": float(leg.option_contract.strike_price),
                    "expiration_date": leg.option_contract.expiration_date.isoformat(),
                    "action": leg.action.value,
                    "quantity": leg.quantity,
                    "current_price": float(leg.option_contract.current_price),
                    "bid_price": float(leg.option_contract.bid_price),
                    "ask_price": float(leg.option_contract.ask_price),
                    "delta": leg.option_contract.delta
                }
                for leg in strategy.legs
            ],
            "total_cost": float(strategy.total_cost),
            "net_delta": strategy.net_delta
        }
        
        return response
        
    except Exception as e:
        logger.error(f"从模板构建策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview")
async def preview_strategy(
    option_type: str,
    relative_expiry: str,
    relative_strike: str,
    underlying: str = "BTC"
):
    """
    预览单个期权合约（用于UI实时显示）
    """
    try:
        connector = DeribitConnector()
        builder = SmartStrategyBuilder(connector)
        
        # 创建临时模板
        template = SmartStrategyTemplate(
            name="预览",
            description="预览",
            strategy_type=StrategyType.SINGLE_LEG,
            legs=[
                SmartStrategyLeg(
                    option_type=OptionType(option_type),
                    action=ActionType.BUY,
                    quantity=1,
                    relative_expiry=RelativeExpiry(relative_expiry),
                    relative_strike=RelativeStrike(relative_strike)
                )
            ]
        )
        
        strategy = await builder.build_strategy(template, underlying)
        
        if not strategy.legs:
            return {"error": "未找到匹配的合约"}
        
        leg = strategy.legs[0]
        return {
            "instrument_name": leg.option_contract.instrument_name,
            "strike_price": float(leg.option_contract.strike_price),
            "expiration_date": leg.option_contract.expiration_date.isoformat(),
            "current_price": float(leg.option_contract.current_price),
            "bid_price": float(leg.option_contract.bid_price),
            "ask_price": float(leg.option_contract.ask_price),
            "delta": leg.option_contract.delta,
            "implied_volatility": leg.option_contract.implied_volatility
        }
        
    except Exception as e:
        logger.error(f"预览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
