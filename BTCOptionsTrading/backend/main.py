"""
BTC期权交易系统主入口
"""

import asyncio
from pathlib import Path

from src.config.logging_config import setup_logging, get_logger
from src.config.settings import settings


def main():
    """主函数"""
    # 设置日志
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info(
        "Starting BTC Options Trading System",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment
    )
    
    # 验证配置
    try:
        # 检查必要的配置
        if not settings.deribit.api_key and settings.environment != "development":
            logger.warning("Deribit API key not configured")
        
        logger.info("Configuration validated successfully")
        
    except Exception as e:
        logger.error("Configuration validation failed", error=str(e))
        return 1
    
    logger.info("System initialization completed")
    return 0


if __name__ == "__main__":
    exit(main())