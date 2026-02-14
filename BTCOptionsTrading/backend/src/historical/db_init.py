"""
历史数据数据库初始化
创建历史数据相关的数据库表和索引
"""

from sqlalchemy import create_engine, Index
from src.storage.database import Base, DatabaseManager
from src.storage.models import HistoricalOptionDataModel, DataImportLogModel
from src.config.logging_config import get_logger

logger = get_logger(__name__)


def create_historical_data_tables(db_manager: DatabaseManager):
    """
    创建历史数据相关的表
    
    Args:
        db_manager: 数据库管理器实例
    """
    try:
        # 确保数据库管理器已初始化
        if db_manager.engine is None:
            db_manager.initialize()
        
        # 创建所有表
        Base.metadata.create_all(bind=db_manager.engine)
        
        # 创建额外的索引以优化查询性能
        with db_manager.engine.begin() as conn:
            # 为 historical_option_data 创建复合索引
            try:
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_historical_instrument_time 
                    ON historical_option_data(instrument_name, timestamp)
                """)
                logger.info("Created index: idx_historical_instrument_time")
            except Exception as e:
                logger.warning(f"Index idx_historical_instrument_time may already exist: {e}")
            
            try:
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_historical_expiry_strike 
                    ON historical_option_data(expiry_date, strike_price)
                """)
                logger.info("Created index: idx_historical_expiry_strike")
            except Exception as e:
                logger.warning(f"Index idx_historical_expiry_strike may already exist: {e}")
            
            try:
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_historical_underlying_time 
                    ON historical_option_data(underlying_symbol, timestamp)
                """)
                logger.info("Created index: idx_historical_underlying_time")
            except Exception as e:
                logger.warning(f"Index idx_historical_underlying_time may already exist: {e}")
            
            # 为 data_import_log 创建索引
            try:
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_import_log_status 
                    ON data_import_log(status, import_date)
                """)
                logger.info("Created index: idx_import_log_status")
            except Exception as e:
                logger.warning(f"Index idx_import_log_status may already exist: {e}")
        
        logger.info("Historical data tables and indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create historical data tables: {str(e)}")
        raise


def drop_historical_data_tables(db_manager: DatabaseManager):
    """
    删除历史数据相关的表（谨慎使用！）
    
    Args:
        db_manager: 数据库管理器实例
    """
    try:
        with db_manager.engine.begin() as conn:
            conn.execute("DROP TABLE IF EXISTS historical_option_data")
            conn.execute("DROP TABLE IF EXISTS data_import_log")
        
        logger.info("Historical data tables dropped successfully")
        
    except Exception as e:
        logger.error(f"Failed to drop historical data tables: {str(e)}")
        raise


if __name__ == "__main__":
    # 用于测试
    from src.config.settings import settings
    
    db_manager = DatabaseManager(settings)
    
    print("Creating historical data tables...")
    create_historical_data_tables(db_manager)
    print("Done!")
