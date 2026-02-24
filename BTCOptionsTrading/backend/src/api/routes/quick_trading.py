"""
快速交易API路由
立即执行策略下单
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

from ...trading.strategy_executor import StrategyExecutor
from ...trading.deribit_trader import DeribitTrader
from ...storage.database import get_db
from ...storage.dao import StrategyDAO
from uuid import UUID

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quick-trading", tags=["quick-trading"])


class QuickTradeRequest(BaseModel):
    """快速交易请求"""
    strategy_id: str
    test_mode: bool = True
    api_key: Optional[str] = None
    api_secret: Optional[str] = None


class QuickTradeResponse(BaseModel):
    """快速交易响应"""
    success: bool
    message: str
    orders: List[dict]
    total_cost: float
    execution_time: str


@router.post("/execute", response_model=QuickTradeResponse)
async def execute_quick_trade(request: QuickTradeRequest):
    """
    立即执行策略交易
    
    Args:
        request: 快速交易请求
        
    Returns:
        交易执行结果
    """
    try:
        # 验证API密钥
        if not request.api_key or not request.api_secret:
            raise HTTPException(
                status_code=400,
                detail="请提供API密钥和密钥"
            )
        
        # 获取策略（包含预加载的关联数据）
        db = next(get_db())
        try:
            strategy = StrategyDAO.get_by_id(db, UUID(request.strategy_id))
            if not strategy:
                raise HTTPException(
                    status_code=404,
                    detail=f"策略不存在: {request.strategy_id}"
                )
        finally:
            db.close()
        
        # 创建交易客户端
        trader = DeribitTrader(
            api_key=request.api_key,
            api_secret=request.api_secret,
            testnet=request.test_mode
        )
        
        # 创建策略执行器
        executor = StrategyExecutor(trader)
        
        # 执行策略
        logger.info(f"开始执行快速交易，策略: {strategy.name}")
        result = await executor.execute_strategy(strategy)
        
        if result.get('success'):
            logger.info(f"快速交易执行成功")
            return QuickTradeResponse(
                success=True,
                message=f"策略 '{strategy.name}' 执行成功",
                orders=result.get('legs', []),
                total_cost=0.0,  # TODO: 计算总成本
                execution_time=result.get('execution_time', '')
            )
        else:
            error_msg = ', '.join(result.get('errors', ['执行失败']))
            logger.error(f"快速交易执行失败: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=error_msg
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"快速交易执行异常: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"执行失败: {str(e)}"
        )


@router.get("/test-connection")
async def test_connection(
    api_key: str,
    api_secret: str,
    test_mode: bool = True
):
    """
    测试API连接
    
    Args:
        api_key: API密钥
        api_secret: API密钥
        test_mode: 是否使用测试网
        
    Returns:
        连接测试结果
    """
    try:
        trader = DeribitTrader(
            api_key=api_key,
            api_secret=api_secret,
            testnet=test_mode
        )
        
        # 测试连接
        result = await trader.test_connection()
        
        if result:
            return {
                "success": True,
                "message": "API连接成功",
                "test_mode": test_mode
            }
        else:
            return {
                "success": False,
                "message": "API连接失败",
                "test_mode": test_mode
            }
            
    except Exception as e:
        logger.error(f"API连接测试失败: {e}")
        return {
            "success": False,
            "message": f"连接失败: {str(e)}",
            "test_mode": test_mode
        }
