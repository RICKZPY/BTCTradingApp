"""
数据管理功能
提供数据备份、清理和维护功能
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path
from sqlalchemy.orm import Session

from src.storage.database import DatabaseManager
from src.storage.dao import (
    OptionContractDAO, StrategyDAO, BacktestResultDAO, HistoricalDataDAO
)
from src.storage.models import (
    OptionContractModel, StrategyModel, BacktestResultModel,
    OptionPriceHistoryModel, UnderlyingPriceHistoryModel
)
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class DataManager:
    """数据管理器"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化数据管理器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def backup_strategies(self, output_file: str = None) -> str:
        """
        备份所有策略
        
        Args:
            output_file: 输出文件路径（可选）
            
        Returns:
            备份文件路径
        """
        try:
            db = self.db_manager.get_session()
            
            # 获取所有策略
            strategies = StrategyDAO.get_all(db)
            
            # 转换为字典
            backup_data = {
                "backup_time": datetime.now().isoformat(),
                "strategies": []
            }
            
            for strategy in strategies:
                strategy_data = {
                    "id": str(strategy.id),
                    "name": strategy.name,
                    "description": strategy.description,
                    "strategy_type": strategy.strategy_type,
                    "max_profit": float(strategy.max_profit) if strategy.max_profit else None,
                    "max_loss": float(strategy.max_loss) if strategy.max_loss else None,
                    "created_at": strategy.created_at.isoformat(),
                    "legs": []
                }
                
                for leg in strategy.legs:
                    leg_data = {
                        "option_contract": leg.option_contract.instrument_name,
                        "action": leg.action.value,
                        "quantity": leg.quantity,
                        "leg_order": leg.leg_order
                    }
                    strategy_data["legs"].append(leg_data)
                
                backup_data["strategies"].append(strategy_data)
            
            # 保存到文件
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = self.backup_dir / f"strategies_backup_{timestamp}.json"
            
            with open(output_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"Strategies backed up to {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Failed to backup strategies: {str(e)}")
            raise
        finally:
            db.close()
    
    def backup_backtest_results(self, output_file: str = None) -> str:
        """
        备份回测结果
        
        Args:
            output_file: 输出文件路径（可选）
            
        Returns:
            备份文件路径
        """
        try:
            db = self.db_manager.get_session()
            
            # 获取所有回测结果
            results = db.query(BacktestResultModel).all()
            
            # 转换为字典
            backup_data = {
                "backup_time": datetime.now().isoformat(),
                "backtest_results": []
            }
            
            for result in results:
                result_data = {
                    "id": str(result.id),
                    "strategy_id": str(result.strategy_id),
                    "start_date": result.start_date.isoformat(),
                    "end_date": result.end_date.isoformat(),
                    "initial_capital": float(result.initial_capital),
                    "final_capital": float(result.final_capital),
                    "total_return": result.total_return,
                    "sharpe_ratio": result.sharpe_ratio,
                    "max_drawdown": result.max_drawdown,
                    "win_rate": result.win_rate,
                    "total_trades": result.total_trades,
                    "created_at": result.created_at.isoformat()
                }
                backup_data["backtest_results"].append(result_data)
            
            # 保存到文件
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = self.backup_dir / f"backtest_results_backup_{timestamp}.json"
            
            with open(output_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"Backtest results backed up to {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Failed to backup backtest results: {str(e)}")
            raise
        finally:
            db.close()
    
    def cleanup_expired_options(self, days_old: int = 30) -> int:
        """
        清理过期的期权合约数据
        
        Args:
            days_old: 保留多少天前的数据
            
        Returns:
            删除的记录数
        """
        try:
            db = self.db_manager.get_session()
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # 查找过期的期权合约
            expired_contracts = db.query(OptionContractModel).filter(
                OptionContractModel.expiration_date < cutoff_date
            ).all()
            
            count = len(expired_contracts)
            
            # 删除过期合约（注意：需要先删除相关的价格历史）
            for contract in expired_contracts:
                # 删除价格历史
                db.query(OptionPriceHistoryModel).filter(
                    OptionPriceHistoryModel.option_contract_id == contract.id
                ).delete()
                
                # 删除合约
                db.delete(contract)
            
            db.commit()
            
            logger.info(f"Cleaned up {count} expired option contracts")
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired options: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def cleanup_old_price_history(self, days_old: int = 90) -> int:
        """
        清理旧的价格历史数据
        
        Args:
            days_old: 保留多少天的数据
            
        Returns:
            删除的记录数
        """
        try:
            db = self.db_manager.get_session()
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # 删除旧的期权价格历史
            option_count = db.query(OptionPriceHistoryModel).filter(
                OptionPriceHistoryModel.timestamp < cutoff_date
            ).delete()
            
            # 删除旧的标的价格历史
            underlying_count = db.query(UnderlyingPriceHistoryModel).filter(
                UnderlyingPriceHistoryModel.timestamp < cutoff_date
            ).delete()
            
            db.commit()
            
            total_count = option_count + underlying_count
            logger.info(f"Cleaned up {total_count} old price history records")
            return total_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old price history: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        获取数据库统计信息
        
        Returns:
            数据库统计信息字典
        """
        try:
            db = self.db_manager.get_session()
            
            stats = {
                "option_contracts": db.query(OptionContractModel).count(),
                "strategies": db.query(StrategyModel).count(),
                "backtest_results": db.query(BacktestResultModel).count(),
                "option_price_history": db.query(OptionPriceHistoryModel).count(),
                "underlying_price_history": db.query(UnderlyingPriceHistoryModel).count(),
                "timestamp": datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {str(e)}")
            raise
        finally:
            db.close()
    
    def vacuum_database(self):
        """
        执行数据库清理和优化（PostgreSQL VACUUM）
        """
        try:
            # 注意：VACUUM不能在事务中执行
            connection = self.db_manager.engine.raw_connection()
            connection.set_isolation_level(0)  # AUTOCOMMIT
            cursor = connection.cursor()
            cursor.execute("VACUUM ANALYZE")
            cursor.close()
            connection.close()
            
            logger.info("Database vacuum completed")
            
        except Exception as e:
            logger.error(f"Failed to vacuum database: {str(e)}")
            raise
