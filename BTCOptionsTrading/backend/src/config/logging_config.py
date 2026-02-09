"""
日志配置模块
使用structlog进行结构化日志记录
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any, Dict

import structlog
from structlog.stdlib import LoggerFactory

from .settings import settings


def setup_logging() -> None:
    """设置日志系统"""
    
    # 创建日志目录
    log_dir = Path(settings.logging.file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 配置标准库logging
    logging.basicConfig(
        format=settings.logging.format,
        level=getattr(logging, settings.logging.level),
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.handlers.RotatingFileHandler(
                settings.logging.file_path,
                maxBytes=settings.logging.max_file_size,
                backupCount=settings.logging.backup_count,
                encoding='utf-8'
            )
        ]
    )
    
    # 配置structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.environment == "production" 
            else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """获取结构化日志记录器"""
    return structlog.get_logger(name)


class LoggerMixin:
    """日志记录器混入类"""
    
    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """获取类专用的日志记录器"""
        return get_logger(self.__class__.__name__)
    
    def log_method_call(self, method_name: str, **kwargs) -> None:
        """记录方法调用"""
        self.logger.debug(
            "Method called",
            method=method_name,
            class_name=self.__class__.__name__,
            **kwargs
        )
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """记录错误"""
        self.logger.error(
            "Error occurred",
            error_type=type(error).__name__,
            error_message=str(error),
            class_name=self.__class__.__name__,
            context=context or {}
        )
    
    def log_performance(self, operation: str, duration: float, **kwargs) -> None:
        """记录性能指标"""
        self.logger.info(
            "Performance metric",
            operation=operation,
            duration_seconds=duration,
            class_name=self.__class__.__name__,
            **kwargs
        )