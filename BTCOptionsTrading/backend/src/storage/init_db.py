"""
数据库初始化脚本
创建数据库表和初始数据
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.storage.database import DatabaseManager, Base
from src.storage.models import (
    OptionContractModel, StrategyModel, StrategyLegModel,
    BacktestResultModel, TradeModel, DailyPnLModel,
    OptionPriceHistoryModel, UnderlyingPriceHistoryModel
)
from src.config.settings import settings
from src.config.logging_config import get_logger

logger = get_logger(__name__)


def init_database():
    """初始化数据库"""
    try:
        logger.info("Starting database initialization...")
        
        # 创建数据库管理器
        db_manager = DatabaseManager(settings)
        db_manager.initialize()
        
        # 创建所有表
        logger.info("Creating database tables...")
        db_manager.create_tables()
        
        logger.info("Database initialization completed successfully!")
        
        # 显示创建的表
        logger.info("Created tables:")
        for table in Base.metadata.sorted_tables:
            logger.info(f"  - {table.name}")
        
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False
    finally:
        if 'db_manager' in locals():
            db_manager.close()


def drop_database():
    """删除所有数据库表（谨慎使用）"""
    try:
        logger.warning("Starting database drop operation...")
        
        # 创建数据库管理器
        db_manager = DatabaseManager(settings)
        db_manager.initialize()
        
        # 删除所有表
        logger.warning("Dropping all database tables...")
        db_manager.drop_tables()
        
        logger.warning("Database drop completed!")
        
        return True
        
    except Exception as e:
        logger.error(f"Database drop failed: {str(e)}")
        return False
    finally:
        if 'db_manager' in locals():
            db_manager.close()


def reset_database():
    """重置数据库（删除并重新创建）"""
    logger.warning("Resetting database...")
    
    if drop_database():
        return init_database()
    return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database management script")
    parser.add_argument(
        "action",
        choices=["init", "drop", "reset"],
        help="Action to perform: init (create tables), drop (delete tables), reset (drop and recreate)"
    )
    
    args = parser.parse_args()
    
    if args.action == "init":
        success = init_database()
    elif args.action == "drop":
        # 需要确认
        confirm = input("Are you sure you want to drop all tables? (yes/no): ")
        if confirm.lower() == "yes":
            success = drop_database()
        else:
            print("Operation cancelled")
            success = False
    elif args.action == "reset":
        confirm = input("Are you sure you want to reset the database? (yes/no): ")
        if confirm.lower() == "yes":
            success = reset_database()
        else:
            print("Operation cancelled")
            success = False
    
    sys.exit(0 if success else 1)
