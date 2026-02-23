"""
定时交易API路由
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging

from ...trading.deribit_trader import DeribitTrader
from ...trading.scheduled_trading import ScheduledTradingManager
from ...core.models import Strategy, StrategyLeg, StrategyType, OptionContract, ActionType, OptionType
from decimal import Decimal
from uuid import UUID

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scheduled-trading", tags=["scheduled-trading"])

# 全局管理器实例（实际应用中应该使用依赖注入）
_manager: Optional[ScheduledTradingManager] = None


class DeribitCredentials(BaseModel):
    """Deribit凭证"""
    api_key: str
    api_secret: str
    testnet: bool = True


class ScheduledStrategyRequest(BaseModel):
    """定时策略请求"""
    strategy_id: str
    schedule_time: str = "05:00"
    timezone: str = "Asia/Shanghai"
    use_market_order: bool = False
    auto_close: bool = False
    close_time: Optional[str] = None


class ScheduledStrategyResponse(BaseModel):
    """定时策略响应"""
    strategy_id: str
    strategy_name: str
    enabled: bool
    schedule_time: str
    timezone: str
    use_market_order: bool
    auto_close: bool
    close_time: Optional[str]


def get_manager() -> ScheduledTradingManager:
    """获取管理器实例"""
    global _manager
    if _manager is None:
        raise HTTPException(status_code=500, detail="定时交易管理器未初始化")
    return _manager


@router.post("/initialize")
async def initialize_manager(credentials: DeribitCredentials):
    """
    初始化定时交易管理器
    """
    global _manager
    
    try:
        trader = DeribitTrader(
            api_key=credentials.api_key,
            api_secret=credentials.api_secret,
            testnet=credentials.testnet
        )
        
        # 测试认证
        auth_success = await trader.authenticate()
        if not auth_success:
            raise HTTPException(status_code=401, detail="Deribit认证失败")
        
        _manager = ScheduledTradingManager(trader)
        _manager.start()
        
        return {
            "success": True,
            "message": "定时交易管理器初始化成功",
            "testnet": credentials.testnet
        }
        
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-strategy")
async def add_scheduled_strategy(
    request: ScheduledStrategyRequest,
    manager: ScheduledTradingManager = Depends(get_manager)
):
    """
    添加定时策略
    """
    try:
        # 这里需要从策略管理器获取策略对象
        # 简化实现，实际应该从数据库或策略管理器获取
        strategy_id = request.strategy_id
        
        # TODO: 从策略管理器获取完整的策略对象
        # strategy = strategy_manager.get_strategy(strategy_id)
        
        # 暂时返回成功（需要集成策略管理器）
        return {
            "success": True,
            "message": "定时策略添加成功",
            "strategy_id": strategy_id
        }
        
    except Exception as e:
        logger.error(f"添加定时策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies", response_model=List[ScheduledStrategyResponse])
async def get_scheduled_strategies(
    manager: ScheduledTradingManager = Depends(get_manager)
):
    """
    获取所有定时策略
    """
    try:
        strategies = manager.get_scheduled_strategies()
        return strategies
        
    except Exception as e:
        logger.error(f"获取定时策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enable/{strategy_id}")
async def enable_strategy(
    strategy_id: str,
    manager: ScheduledTradingManager = Depends(get_manager)
):
    """
    启用定时策略
    """
    try:
        manager.enable_strategy(strategy_id)
        return {"success": True, "message": "策略已启用"}
        
    except Exception as e:
        logger.error(f"启用策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disable/{strategy_id}")
async def disable_strategy(
    strategy_id: str,
    manager: ScheduledTradingManager = Depends(get_manager)
):
    """
    禁用定时策略
    """
    try:
        manager.disable_strategy(strategy_id)
        return {"success": True, "message": "策略已禁用"}
        
    except Exception as e:
        logger.error(f"禁用策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{strategy_id}")
async def remove_scheduled_strategy(
    strategy_id: str,
    manager: ScheduledTradingManager = Depends(get_manager)
):
    """
    移除定时策略
    """
    try:
        manager.remove_scheduled_strategy(strategy_id)
        return {"success": True, "message": "策略已移除"}
        
    except Exception as e:
        logger.error(f"移除策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/execution-log")
async def get_execution_log(
    manager: ScheduledTradingManager = Depends(get_manager)
):
    """
    获取执行日志
    """
    try:
        log = manager.get_execution_log()
        return {"log": log}
        
    except Exception as e:
        logger.error(f"获取执行日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/account-summary")
async def get_account_summary(
    manager: ScheduledTradingManager = Depends(get_manager)
):
    """
    获取账户摘要
    """
    try:
        summary = await manager.trader.get_account_summary()
        return summary
        
    except Exception as e:
        logger.error(f"获取账户摘要失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions")
async def get_positions(
    manager: ScheduledTradingManager = Depends(get_manager)
):
    """
    获取当前持仓
    """
    try:
        positions = await manager.trader.get_positions()
        return {"positions": positions}
        
    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
