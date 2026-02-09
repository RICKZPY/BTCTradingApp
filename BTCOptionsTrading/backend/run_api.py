"""
API服务启动脚本
"""

import uvicorn
from src.api.app import create_app
from src.config.settings import Settings
from src.config.logging_config import get_logger
from src.storage.database import get_db_manager

logger = get_logger(__name__)


def main():
    """启动API服务"""
    try:
        # 初始化配置
        settings = Settings()
        
        # 初始化数据库
        logger.info("Initializing database...")
        db_manager = get_db_manager()
        db_manager.create_tables()
        logger.info("Database initialized successfully")
        
        # 创建FastAPI应用
        app = create_app(settings)
        
        # 启动服务
        logger.info("Starting API server...")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False  # 生产环境关闭自动重载
        )
        
    except Exception as e:
        logger.error(f"Failed to start API server: {str(e)}")
        raise


if __name__ == "__main__":
    main()
