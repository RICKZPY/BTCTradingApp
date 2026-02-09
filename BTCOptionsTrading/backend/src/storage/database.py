"""
数据库连接管理
提供SQLAlchemy数据库连接和会话管理
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from src.config.settings import Settings
from src.config.logging_config import get_logger

logger = get_logger(__name__)

# 创建基类
Base = declarative_base()


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, settings: Settings = None):
        """
        初始化数据库管理器
        
        Args:
            settings: 配置对象
        """
        self.settings = settings or Settings()
        self.engine = None
        self.SessionLocal = None
        
    def initialize(self):
        """初始化数据库连接"""
        try:
            # 构建数据库URL
            db_url = self._build_database_url()
            
            # 为SQLite添加特殊配置
            engine_kwargs = {
                'echo': False  # 生产环境关闭SQL日志
            }
            
            if db_url.startswith('sqlite'):
                # SQLite特殊配置：支持多线程
                engine_kwargs['connect_args'] = {'check_same_thread': False}
                engine_kwargs['poolclass'] = NullPool
            else:
                engine_kwargs['poolclass'] = NullPool
            
            # 创建引擎
            self.engine = create_engine(db_url, **engine_kwargs)
            
            # 创建会话工厂
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    def _build_database_url(self) -> str:
        """
        构建数据库连接URL
        
        Returns:
            数据库连接字符串
        """
        db_settings = self.settings.database
        
        # 使用postgres_url属性
        return db_settings.postgres_url
    
    def create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {str(e)}")
            raise
    
    def drop_tables(self):
        """删除所有表（谨慎使用）"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop tables: {str(e)}")
            raise
    
    def get_session(self) -> Session:
        """
        获取数据库会话
        
        Returns:
            SQLAlchemy会话对象
        """
        if self.SessionLocal is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.SessionLocal()
    
    def close(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")


# 全局数据库管理器实例
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """
    获取全局数据库管理器实例
    
    Returns:
        DatabaseManager实例
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        _db_manager.initialize()
    return _db_manager


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话（用于依赖注入）
    
    Yields:
        数据库会话
    """
    db_manager = get_db_manager()
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()
