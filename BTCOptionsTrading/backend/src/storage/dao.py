"""
数据访问对象（DAO）
提供数据库CRUD操作的封装
"""

from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from src.storage.models import (
    OptionContractModel, StrategyModel, StrategyLegModel,
    BacktestResultModel, TradeModel, DailyPnLModel,
    OptionPriceHistoryModel, UnderlyingPriceHistoryModel
)
from src.core.models import (
    OptionContract, Strategy, BacktestResult, Trade, DailyPnL,
    HistoricalData, OptionType, ActionType
)
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class OptionContractDAO:
    """期权合约数据访问对象"""
    
    @staticmethod
    def create(db: Session, contract: OptionContract) -> OptionContractModel:
        """创建期权合约"""
        db_contract = OptionContractModel(
            id=contract.instrument_name,  # 使用instrument_name作为ID
            instrument_name=contract.instrument_name,
            underlying=contract.underlying,
            option_type=contract.option_type,
            strike_price=contract.strike_price,
            expiration_date=contract.expiration_date
        )
        db.add(db_contract)
        db.commit()
        db.refresh(db_contract)
        return db_contract
    
    @staticmethod
    def get_by_instrument_name(db: Session, instrument_name: str) -> Optional[OptionContractModel]:
        """根据合约名称获取期权合约"""
        return db.query(OptionContractModel).filter(
            OptionContractModel.instrument_name == instrument_name
        ).first()
    
    @staticmethod
    def get_by_underlying(db: Session, underlying: str) -> List[OptionContractModel]:
        """获取指定标的的所有期权合约"""
        return db.query(OptionContractModel).filter(
            OptionContractModel.underlying == underlying
        ).all()
    
    @staticmethod
    def get_by_expiry(db: Session, expiry_date: datetime) -> List[OptionContractModel]:
        """获取指定到期日的所有期权合约"""
        return db.query(OptionContractModel).filter(
            OptionContractModel.expiration_date == expiry_date
        ).all()


class StrategyDAO:
    """策略数据访问对象"""
    
    @staticmethod
    def create(db: Session, strategy: Strategy) -> StrategyModel:
        """创建策略"""
        db_strategy = StrategyModel(
            id=str(strategy.id),  # 转换UUID为字符串
            name=strategy.name,
            description=strategy.description,
            strategy_type=strategy.strategy_type.value,
            max_profit=strategy.max_profit,
            max_loss=strategy.max_loss
        )
        db.add(db_strategy)
        db.flush()  # 获取ID但不提交
        
        # 创建策略腿
        for i, leg in enumerate(strategy.legs):
            # 确保期权合约存在
            db_contract = OptionContractDAO.get_by_instrument_name(
                db, leg.option_contract.instrument_name
            )
            if not db_contract:
                db_contract = OptionContractDAO.create(db, leg.option_contract)
            
            db_leg = StrategyLegModel(
                strategy_id=db_strategy.id,
                option_contract_id=db_contract.id,
                action=leg.action,
                quantity=leg.quantity,
                leg_order=i
            )
            db.add(db_leg)
        
        db.commit()
        db.refresh(db_strategy)
        return db_strategy
    
    @staticmethod
    def get_by_id(db: Session, strategy_id: UUID) -> Optional[StrategyModel]:
        """根据ID获取策略"""
        return db.query(StrategyModel).filter(
            StrategyModel.id == str(strategy_id)
        ).first()
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[StrategyModel]:
        """获取所有策略"""
        return db.query(StrategyModel).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_type(db: Session, strategy_type: str) -> List[StrategyModel]:
        """根据类型获取策略"""
        return db.query(StrategyModel).filter(
            StrategyModel.strategy_type == strategy_type
        ).all()
    
    @staticmethod
    def update(db: Session, strategy_id: UUID, **kwargs) -> Optional[StrategyModel]:
        """更新策略"""
        db_strategy = StrategyDAO.get_by_id(db, strategy_id)
        if db_strategy:
            for key, value in kwargs.items():
                if hasattr(db_strategy, key):
                    setattr(db_strategy, key, value)
            db.commit()
            db.refresh(db_strategy)
        return db_strategy
    
    @staticmethod
    def delete(db: Session, strategy_id: UUID) -> bool:
        """删除策略"""
        db_strategy = StrategyDAO.get_by_id(db, strategy_id)
        if db_strategy:
            db.delete(db_strategy)
            db.commit()
            return True
        return False


class BacktestResultDAO:
    """回测结果数据访问对象"""
    
    @staticmethod
    def create(db: Session, result: BacktestResult, strategy_id: UUID) -> BacktestResultModel:
        """创建回测结果"""
        db_result = BacktestResultModel(
            id=str(result.id),  # 转换UUID为字符串
            strategy_id=str(strategy_id),  # 转换UUID为字符串
            start_date=result.start_date,
            end_date=result.end_date,
            initial_capital=result.initial_capital,
            final_capital=result.final_capital,
            total_return=result.total_return,
            sharpe_ratio=result.sharpe_ratio,
            max_drawdown=result.max_drawdown,
            win_rate=result.win_rate,
            total_trades=result.total_trades
        )
        db.add(db_result)
        db.flush()
        
        # 创建交易记录
        for trade in result.trades:
            # 确保期权合约存在
            db_contract = OptionContractDAO.get_by_instrument_name(
                db, trade.option_contract.instrument_name
            )
            if not db_contract:
                db_contract = OptionContractDAO.create(db, trade.option_contract)
            
            db_trade = TradeModel(
                id=str(trade.id),  # 转换UUID为字符串
                backtest_id=db_result.id,
                timestamp=trade.timestamp,
                action=trade.action.value,
                option_contract_id=db_contract.id,
                quantity=trade.quantity,
                price=trade.price,
                pnl=trade.pnl,
                portfolio_value=trade.portfolio_value,
                commission=trade.commission
            )
            db.add(db_trade)
        
        # 创建每日盈亏记录
        for daily in result.daily_pnl:
            db_daily = DailyPnLModel(
                backtest_id=db_result.id,
                date=daily.date,
                portfolio_value=daily.portfolio_value,
                daily_pnl=daily.daily_pnl,
                cumulative_pnl=daily.cumulative_pnl,
                realized_pnl=daily.realized_pnl,
                unrealized_pnl=daily.unrealized_pnl
            )
            db.add(db_daily)
        
        db.commit()
        db.refresh(db_result)
        return db_result
    
    @staticmethod
    def get_by_id(db: Session, result_id: UUID) -> Optional[BacktestResultModel]:
        """根据ID获取回测结果"""
        return db.query(BacktestResultModel).filter(
            BacktestResultModel.id == str(result_id)
        ).first()
    
    @staticmethod
    def get_by_strategy(db: Session, strategy_id: UUID) -> List[BacktestResultModel]:
        """获取策略的所有回测结果"""
        return db.query(BacktestResultModel).filter(
            BacktestResultModel.strategy_id == str(strategy_id)
        ).order_by(desc(BacktestResultModel.created_at)).all()
    
    @staticmethod
    def get_recent(db: Session, limit: int = 10) -> List[BacktestResultModel]:
        """获取最近的回测结果"""
        return db.query(BacktestResultModel).order_by(
            desc(BacktestResultModel.created_at)
        ).limit(limit).all()
    
    @staticmethod
    def delete(db: Session, result_id: UUID) -> bool:
        """删除回测结果"""
        db_result = BacktestResultDAO.get_by_id(db, result_id)
        if db_result:
            db.delete(db_result)
            db.commit()
            return True
        return False


class HistoricalDataDAO:
    """历史数据访问对象"""
    
    @staticmethod
    def save_option_price(
        db: Session,
        contract_id: UUID,
        timestamp: datetime,
        bid: Decimal,
        ask: Decimal,
        last: Decimal,
        iv: float,
        greeks: dict
    ) -> OptionPriceHistoryModel:
        """保存期权价格历史"""
        db_price = OptionPriceHistoryModel(
            option_contract_id=contract_id,
            timestamp=timestamp,
            bid_price=bid,
            ask_price=ask,
            last_price=last,
            implied_volatility=iv,
            delta=greeks.get('delta'),
            gamma=greeks.get('gamma'),
            theta=greeks.get('theta'),
            vega=greeks.get('vega'),
            rho=greeks.get('rho'),
            volume=greeks.get('volume', 0),
            open_interest=greeks.get('open_interest', 0)
        )
        db.add(db_price)
        db.commit()
        return db_price
    
    @staticmethod
    def get_option_prices(
        db: Session,
        contract_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> List[OptionPriceHistoryModel]:
        """获取期权价格历史"""
        return db.query(OptionPriceHistoryModel).filter(
            and_(
                OptionPriceHistoryModel.option_contract_id == contract_id,
                OptionPriceHistoryModel.timestamp >= start_date,
                OptionPriceHistoryModel.timestamp <= end_date
            )
        ).order_by(OptionPriceHistoryModel.timestamp).all()
    
    @staticmethod
    def save_underlying_price(
        db: Session,
        symbol: str,
        timestamp: datetime,
        open_price: Decimal,
        high: Decimal,
        low: Decimal,
        close: Decimal,
        volume: int
    ) -> UnderlyingPriceHistoryModel:
        """保存标的资产价格历史"""
        db_price = UnderlyingPriceHistoryModel(
            symbol=symbol,
            timestamp=timestamp,
            open_price=open_price,
            high_price=high,
            low_price=low,
            close_price=close,
            volume=volume
        )
        db.add(db_price)
        db.commit()
        return db_price
    
    @staticmethod
    def get_underlying_prices(
        db: Session,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[UnderlyingPriceHistoryModel]:
        """获取标的资产价格历史"""
        return db.query(UnderlyingPriceHistoryModel).filter(
            and_(
                UnderlyingPriceHistoryModel.symbol == symbol,
                UnderlyingPriceHistoryModel.timestamp >= start_date,
                UnderlyingPriceHistoryModel.timestamp <= end_date
            )
        ).order_by(UnderlyingPriceHistoryModel.timestamp).all()
