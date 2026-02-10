"""
策略管理API接口
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime

from src.storage.database import get_db
from src.storage.dao import StrategyDAO, OptionContractDAO
from src.storage.models import StrategyLegModel
from src.core.models import Strategy, StrategyType, OptionType, ActionType
from src.strategy.strategy_manager import StrategyManager
from sqlalchemy.orm import Session

router = APIRouter()


# Pydantic模型
class OptionContractRequest(BaseModel):
    """期权合约请求模型"""
    instrument_name: str
    underlying: str
    option_type: str
    strike_price: float
    expiration_date: datetime


class StrategyLegRequest(BaseModel):
    """策略腿请求模型"""
    option_contract: OptionContractRequest
    action: str
    quantity: int


class StrategyCreateRequest(BaseModel):
    """创建策略请求模型"""
    name: str
    description: Optional[str] = None
    strategy_type: str
    legs: List[StrategyLegRequest]


class StrategyUpdateRequest(BaseModel):
    """更新策略请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    legs: Optional[List[StrategyLegRequest]] = None


class StrategyResponse(BaseModel):
    """策略响应模型"""
    id: str
    name: str
    description: Optional[str]
    strategy_type: str
    max_profit: Optional[float]
    max_loss: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/", response_model=StrategyResponse)
async def create_strategy(
    request: StrategyCreateRequest,
    db: Session = Depends(get_db)
):
    """
    创建新策略
    
    Args:
        request: 策略创建请求
        db: 数据库会话
        
    Returns:
        创建的策略信息
    """
    try:
        # 转换为核心模型
        from src.core.models import OptionContract, StrategyLeg
        from decimal import Decimal
        
        legs = []
        for leg_req in request.legs:
            # 创建期权合约，为缺失字段提供默认值
            contract = OptionContract(
                instrument_name=leg_req.option_contract.instrument_name,
                underlying=leg_req.option_contract.underlying,
                option_type=OptionType(leg_req.option_contract.option_type),
                strike_price=Decimal(str(leg_req.option_contract.strike_price)),
                expiration_date=leg_req.option_contract.expiration_date,
                # 以下字段使用默认值（在回测时会更新）
                current_price=Decimal('0'),
                bid_price=Decimal('0'),
                ask_price=Decimal('0'),
                last_price=Decimal('0'),
                implied_volatility=0.0,
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
                action=ActionType(leg_req.action),
                quantity=leg_req.quantity
            )
            legs.append(leg)
        
        strategy = Strategy(
            name=request.name,
            description=request.description,
            strategy_type=StrategyType(request.strategy_type),
            legs=legs
        )
        
        # 保存到数据库
        db_strategy = StrategyDAO.create(db, strategy)
        
        return StrategyResponse(
            id=str(db_strategy.id),
            name=db_strategy.name,
            description=db_strategy.description,
            strategy_type=db_strategy.strategy_type,
            max_profit=float(db_strategy.max_profit) if db_strategy.max_profit else None,
            max_loss=float(db_strategy.max_loss) if db_strategy.max_loss else None,
            created_at=db_strategy.created_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[StrategyResponse])
async def list_strategies(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取策略列表
    
    Args:
        skip: 跳过记录数
        limit: 返回记录数
        db: 数据库会话
        
    Returns:
        策略列表
    """
    strategies = StrategyDAO.get_all(db, skip=skip, limit=limit)
    return [
        StrategyResponse(
            id=str(s.id),
            name=s.name,
            description=s.description,
            strategy_type=s.strategy_type,
            max_profit=float(s.max_profit) if s.max_profit else None,
            max_loss=float(s.max_loss) if s.max_loss else None,
            created_at=s.created_at
        )
        for s in strategies
    ]


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: UUID,
    db: Session = Depends(get_db)
):
    """
    获取策略详情
    
    Args:
        strategy_id: 策略ID
        db: 数据库会话
        
    Returns:
        策略详情
    """
    strategy = StrategyDAO.get_by_id(db, strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    return StrategyResponse(
        id=str(strategy.id),
        name=strategy.name,
        description=strategy.description,
        strategy_type=strategy.strategy_type,
        max_profit=float(strategy.max_profit) if strategy.max_profit else None,
        max_loss=float(strategy.max_loss) if strategy.max_loss else None,
        created_at=strategy.created_at
    )


@router.delete("/{strategy_id}")
async def delete_strategy(
    strategy_id: UUID,
    db: Session = Depends(get_db)
):
    """
    删除策略
    
    Args:
        strategy_id: 策略ID
        db: 数据库会话
        
    Returns:
        删除结果
    """
    success = StrategyDAO.delete(db, strategy_id)
    if not success:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    return {"message": "Strategy deleted successfully"}


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: UUID,
    request: StrategyUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    更新策略
    
    Args:
        strategy_id: 策略ID
        request: 策略更新请求
        db: 数据库会话
        
    Returns:
        更新后的策略信息
    """
    # 检查策略是否存在
    db_strategy = StrategyDAO.get_by_id(db, strategy_id)
    if not db_strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    try:
        # 准备更新数据
        update_data = {}
        
        # 更新基本字段
        if request.name is not None:
            update_data['name'] = request.name
        if request.description is not None:
            update_data['description'] = request.description
        
        # 如果需要更新策略腿
        if request.legs is not None:
            from src.core.models import OptionContract, StrategyLeg
            from decimal import Decimal
            
            # 删除旧的策略腿
            db.query(StrategyLegModel).filter(
                StrategyLegModel.strategy_id == str(strategy_id)
            ).delete()
            
            # 创建新的策略腿
            for i, leg_req in enumerate(request.legs):
                # 创建期权合约
                contract = OptionContract(
                    instrument_name=leg_req.option_contract.instrument_name,
                    underlying=leg_req.option_contract.underlying,
                    option_type=OptionType(leg_req.option_contract.option_type),
                    strike_price=Decimal(str(leg_req.option_contract.strike_price)),
                    expiration_date=leg_req.option_contract.expiration_date,
                    current_price=Decimal('0'),
                    bid_price=Decimal('0'),
                    ask_price=Decimal('0'),
                    last_price=Decimal('0'),
                    implied_volatility=0.0,
                    delta=0.0,
                    gamma=0.0,
                    theta=0.0,
                    vega=0.0,
                    rho=0.0,
                    open_interest=0,
                    volume=0,
                    timestamp=datetime.now()
                )
                
                # 确保期权合约存在
                db_contract = OptionContractDAO.get_by_instrument_name(
                    db, contract.instrument_name
                )
                if not db_contract:
                    db_contract = OptionContractDAO.create(db, contract)
                
                # 创建策略腿
                db_leg = StrategyLegModel(
                    strategy_id=str(strategy_id),
                    option_contract_id=db_contract.id,
                    action=leg_req.action,
                    quantity=leg_req.quantity,
                    leg_order=i
                )
                db.add(db_leg)
        
        # 更新策略基本信息
        if update_data:
            for key, value in update_data.items():
                setattr(db_strategy, key, value)
        
        # 更新updated_at时间戳
        db_strategy.updated_at = datetime.now()
        
        db.commit()
        db.refresh(db_strategy)
        
        return StrategyResponse(
            id=str(db_strategy.id),
            name=db_strategy.name,
            description=db_strategy.description,
            strategy_type=db_strategy.strategy_type,
            max_profit=float(db_strategy.max_profit) if db_strategy.max_profit else None,
            max_loss=float(db_strategy.max_loss) if db_strategy.max_loss else None,
            created_at=db_strategy.created_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates/list")
async def list_strategy_templates():
    """
    获取策略模板列表
    
    Returns:
        策略模板列表
    """
    return {
        "templates": [
            {
                "type": "single_leg",
                "name": "单腿期权",
                "description": "买入或卖出单个期权合约"
            },
            {
                "type": "straddle",
                "name": "跨式策略",
                "description": "同时买入/卖出相同执行价的看涨和看跌期权"
            },
            {
                "type": "strangle",
                "name": "宽跨式策略",
                "description": "买入/卖出不同执行价的看涨和看跌期权"
            },
            {
                "type": "iron_condor",
                "name": "铁鹰策略",
                "description": "四腿复合策略，适合低波动市场"
            },
            {
                "type": "butterfly",
                "name": "蝶式策略",
                "description": "三腿价差策略，适合预期价格不变"
            }
        ]
    }
