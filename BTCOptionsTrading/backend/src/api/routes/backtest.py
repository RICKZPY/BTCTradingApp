"""
回测API接口
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal

from src.storage.database import get_db
from src.storage.dao import BacktestResultDAO, StrategyDAO
from src.backtest.backtest_engine import BacktestEngine
from src.pricing.options_engine import OptionsEngine
from sqlalchemy.orm import Session

router = APIRouter()


# Pydantic模型
class BacktestRequest(BaseModel):
    """回测请求模型"""
    strategy_id: str
    start_date: datetime
    end_date: datetime
    initial_capital: float = Field(default=100000.0, gt=0)
    underlying_symbol: str = "BTC"


class BacktestResultResponse(BaseModel):
    """回测结果响应模型"""
    id: str
    strategy_id: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[float]
    win_rate: Optional[float]
    total_trades: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class TradeResponse(BaseModel):
    """交易记录响应模型"""
    timestamp: datetime
    action: str
    instrument_name: str
    quantity: int
    price: float
    pnl: Optional[float]
    portfolio_value: Optional[float]


class DailyPnLResponse(BaseModel):
    """每日盈亏响应模型"""
    date: datetime
    portfolio_value: float
    daily_pnl: float
    cumulative_pnl: float


@router.post("/run", response_model=BacktestResultResponse)
async def run_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    运行回测
    
    Args:
        request: 回测请求
        background_tasks: 后台任务
        db: 数据库会话
        
    Returns:
        回测结果
    """
    try:
        # 获取策略
        strategy_id = UUID(request.strategy_id)
        db_strategy = StrategyDAO.get_by_id(db, strategy_id)
        if not db_strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # 转换为核心模型
        from src.core.models import (
            Strategy, StrategyLeg, OptionContract,
            StrategyType, OptionType, ActionType
        )
        
        legs = []
        for db_leg in db_strategy.legs:
            # 创建期权合约，提供所有必需字段的默认值
            contract = OptionContract(
                instrument_name=db_leg.option_contract.instrument_name,
                underlying=db_leg.option_contract.underlying,
                option_type=db_leg.option_contract.option_type,
                strike_price=Decimal(str(db_leg.option_contract.strike_price)),
                expiration_date=db_leg.option_contract.expiration_date,
                current_price=Decimal("0"),
                bid_price=Decimal("0"),
                ask_price=Decimal("0"),
                last_price=Decimal("0"),
                implied_volatility=0.8,  # 默认80%波动率
                delta=0.0,
                gamma=0.0,
                theta=0.0,
                vega=0.0,
                rho=0.0,
                open_interest=0,
                volume=0,
                timestamp=datetime.now()
            )
            leg = StrategyLeg(
                option_contract=contract,
                action=db_leg.action,
                quantity=db_leg.quantity
            )
            legs.append(leg)
        
        strategy = Strategy(
            id=db_strategy.id,
            name=db_strategy.name,
            description=db_strategy.description,
            strategy_type=StrategyType(db_strategy.strategy_type),
            legs=legs
        )
        
        # 创建回测引擎
        pricing_engine = OptionsEngine()
        backtest_engine = BacktestEngine(pricing_engine)
        
        # 运行回测（这里使用模拟数据，实际应该从数据库加载）
        # TODO: 从数据库加载真实历史数据
        result = await backtest_engine.run_backtest(
            strategy=strategy,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=Decimal(str(request.initial_capital)),
            underlying_symbol=request.underlying_symbol
        )
        
        # 保存结果到数据库
        db_result = BacktestResultDAO.create(db, result, strategy_id)
        
        return BacktestResultResponse(
            id=str(db_result.id),
            strategy_id=str(db_result.strategy_id),
            start_date=db_result.start_date,
            end_date=db_result.end_date,
            initial_capital=float(db_result.initial_capital),
            final_capital=float(db_result.final_capital),
            total_return=db_result.total_return,
            sharpe_ratio=db_result.sharpe_ratio,
            max_drawdown=db_result.max_drawdown,
            win_rate=db_result.win_rate,
            total_trades=db_result.total_trades,
            created_at=db_result.created_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/results", response_model=List[BacktestResultResponse])
async def list_backtest_results(
    strategy_id: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    获取回测结果列表
    
    Args:
        strategy_id: 策略ID（可选）
        limit: 返回记录数
        db: 数据库会话
        
    Returns:
        回测结果列表
    """
    if strategy_id:
        results = BacktestResultDAO.get_by_strategy(db, UUID(strategy_id))
    else:
        results = BacktestResultDAO.get_recent(db, limit=limit)
    
    return [
        BacktestResultResponse(
            id=str(r.id),
            strategy_id=str(r.strategy_id),
            start_date=r.start_date,
            end_date=r.end_date,
            initial_capital=float(r.initial_capital),
            final_capital=float(r.final_capital),
            total_return=r.total_return,
            sharpe_ratio=r.sharpe_ratio,
            max_drawdown=r.max_drawdown,
            win_rate=r.win_rate,
            total_trades=r.total_trades,
            created_at=r.created_at
        )
        for r in results
    ]


@router.get("/results/{result_id}", response_model=BacktestResultResponse)
async def get_backtest_result(
    result_id: UUID,
    db: Session = Depends(get_db)
):
    """
    获取回测结果详情
    
    Args:
        result_id: 回测结果ID
        db: 数据库会话
        
    Returns:
        回测结果详情
    """
    result = BacktestResultDAO.get_by_id(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Backtest result not found")
    
    return BacktestResultResponse(
        id=str(result.id),
        strategy_id=str(result.strategy_id),
        start_date=result.start_date,
        end_date=result.end_date,
        initial_capital=float(result.initial_capital),
        final_capital=float(result.final_capital),
        total_return=result.total_return,
        sharpe_ratio=result.sharpe_ratio,
        max_drawdown=result.max_drawdown,
        win_rate=result.win_rate,
        total_trades=result.total_trades,
        created_at=result.created_at
    )


@router.get("/results/{result_id}/trades", response_model=List[TradeResponse])
async def get_backtest_trades(
    result_id: UUID,
    db: Session = Depends(get_db)
):
    """
    获取回测交易记录
    
    Args:
        result_id: 回测结果ID
        db: 数据库会话
        
    Returns:
        交易记录列表
    """
    result = BacktestResultDAO.get_by_id(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Backtest result not found")
    
    return [
        TradeResponse(
            timestamp=trade.timestamp,
            action=trade.action,
            instrument_name=trade.option_contract_id,  # TODO: 获取实际的instrument_name
            quantity=trade.quantity,
            price=float(trade.price),
            pnl=float(trade.pnl) if trade.pnl else None,
            portfolio_value=float(trade.portfolio_value) if trade.portfolio_value else None
        )
        for trade in result.trades
    ]


@router.get("/results/{result_id}/daily-pnl", response_model=List[DailyPnLResponse])
async def get_backtest_daily_pnl(
    result_id: UUID,
    db: Session = Depends(get_db)
):
    """
    获取回测每日盈亏
    
    Args:
        result_id: 回测结果ID
        db: 数据库会话
        
    Returns:
        每日盈亏列表
    """
    result = BacktestResultDAO.get_by_id(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Backtest result not found")
    
    return [
        DailyPnLResponse(
            date=daily.date,
            portfolio_value=float(daily.portfolio_value),
            daily_pnl=float(daily.daily_pnl),
            cumulative_pnl=float(daily.cumulative_pnl)
        )
        for daily in result.daily_pnl
    ]


@router.delete("/results/{result_id}")
async def delete_backtest_result(
    result_id: UUID,
    db: Session = Depends(get_db)
):
    """
    删除回测结果
    
    Args:
        result_id: 回测结果ID
        db: 数据库会话
        
    Returns:
        删除结果
    """
    success = BacktestResultDAO.delete(db, result_id)
    if not success:
        raise HTTPException(status_code=404, detail="Backtest result not found")
    
    return {"message": "Backtest result deleted successfully"}
