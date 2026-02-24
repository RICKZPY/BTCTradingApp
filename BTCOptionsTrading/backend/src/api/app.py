"""
FastAPI应用主文件
"""

import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config.settings import Settings
from src.config.logging_config import get_logger
from src.api.routes import health, strategies, backtest, data, settings as settings_routes, websocket, historical_data, options_chain_smart, csv_data, orderbook, trading, smart_strategy, scheduled_trading, quick_trading, backtest_data
from src.monitoring import get_monitor
from src.scheduler.task_scheduler import get_scheduler

logger = get_logger(__name__)


def create_app(settings: Settings = None) -> FastAPI:
    """
    创建FastAPI应用
    
    Args:
        settings: 配置对象
        
    Returns:
        FastAPI应用实例
    """
    if settings is None:
        settings = Settings()
    
    app = FastAPI(
        title="BTC Options Trading System",
        description="Bitcoin期权交易回测系统API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应该限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 性能监控中间件
    @app.middleware("http")
    async def monitor_requests(request: Request, call_next):
        """监控请求性能"""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # 计算响应时间
            response_time_ms = (time.time() - start_time) * 1000
            
            # 记录请求
            monitor = get_monitor()
            is_error = response.status_code >= 400
            monitor.record_request(response_time_ms, is_error)
            
            # 添加响应头
            response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"
            
            return response
            
        except Exception as e:
            # 记录错误请求
            response_time_ms = (time.time() - start_time) * 1000
            monitor = get_monitor()
            monitor.record_request(response_time_ms, is_error=True)
            raise e
    
    # 注册路由
    app.include_router(health.router, tags=["Health"])
    app.include_router(strategies.router, prefix="/api/strategies", tags=["Strategies"])
    app.include_router(backtest.router, prefix="/api/backtest", tags=["Backtest"])
    app.include_router(backtest_data.router, prefix="/api/backtest", tags=["Backtest Data"])
    app.include_router(data.router, prefix="/api/data", tags=["Data"])
    app.include_router(options_chain_smart.router, prefix="/api/options", tags=["Options Chain Smart"])
    app.include_router(csv_data.router, prefix="/api/csv", tags=["CSV Data"])
    app.include_router(orderbook.router, prefix="/api/orderbook", tags=["Order Book"])
    app.include_router(trading.router, prefix="/api/trading", tags=["Trading"])
    app.include_router(smart_strategy.router, prefix="/api", tags=["Smart Strategy"])
    app.include_router(scheduled_trading.router, prefix="/api", tags=["Scheduled Trading"])
    app.include_router(quick_trading.router, prefix="/api", tags=["Quick Trading"])
    app.include_router(settings_routes.router, tags=["Settings"])
    app.include_router(websocket.router, tags=["WebSocket"])
    app.include_router(historical_data.router, tags=["Historical Data"])
    
    # 全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Global exception: {str(exc)}", exc_info=True)
        
        # 记录错误
        monitor = get_monitor()
        monitor.record_request(0, is_error=True)
        
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    # 启动事件
    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting BTC Options Trading System API")
        # 启动WebSocket后台数据流
        import asyncio
        asyncio.create_task(websocket.start_market_data_stream())
        asyncio.create_task(websocket.start_options_chain_stream())
        logger.info("WebSocket data streams started")
        
        # 启动定时任务调度器
        try:
            scheduler = get_scheduler()
            scheduler.start()
            logger.info("Task scheduler started")
        except Exception as e:
            logger.error(f"Error starting task scheduler: {e}")
    
    # 关闭事件
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down BTC Options Trading System API")
        
        # 停止定时任务调度器
        try:
            scheduler = get_scheduler()
            scheduler.stop()
            logger.info("Task scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping task scheduler: {e}")
    
    return app


# 创建应用实例
app = create_app()
