"""
定时任务管理器 - 使用 APScheduler 管理定时任务
"""

import pytz
from datetime import datetime, timezone
from typing import Optional, Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config.logging_config import get_logger
from src.collectors.orderbook_collector import OrderBookCollector
from src.traders.scheduled_trader import ScheduledTrader

logger = get_logger(__name__)


class TaskScheduler:
    """定时任务管理器"""
    
    def __init__(self):
        """初始化定时任务管理器"""
        self.scheduler = BackgroundScheduler()
        self.orderbook_collector = OrderBookCollector()
        self.scheduled_trader = ScheduledTrader()
        
        logger.info("TaskScheduler initialized")
    
    def schedule_orderbook_collection(self, hour: int = 5, minute: int = 0, 
                                     underlying: str = "BTC", num_strikes: int = 4) -> str:
        """
        定时收集 order book
        
        Args:
            hour: 小时（北京时间）
            minute: 分钟
            underlying: 标的资产
            num_strikes: 价位数量
            
        Returns:
            任务 ID
        """
        try:
            # 北京时间转 UTC
            # 北京时间 = UTC + 8
            # 所以 UTC 时间 = 北京时间 - 8
            utc_hour = (hour - 8) % 24
            
            logger.info(f"Scheduling orderbook collection at {hour}:00 Beijing time (UTC {utc_hour}:00)")
            
            # 创建定时任务
            job = self.scheduler.add_job(
                func=self._collect_orderbook_task,
                trigger=CronTrigger(hour=utc_hour, minute=minute, timezone='UTC'),
                id='orderbook_collection',
                name='Order Book Collection',
                replace_existing=True,
                args=[underlying, num_strikes]
            )
            
            logger.info(f"Orderbook collection scheduled: {job.id}")
            return job.id
        
        except Exception as e:
            logger.error(f"Error scheduling orderbook collection: {e}")
            return ""
    
    def schedule_trading(self, hour: int = 5, minute: int = 0,
                        underlying: str = "BTC", option_type: str = "call",
                        side: str = "buy", amount: float = 1.0) -> str:
        """
        定时下单
        
        Args:
            hour: 小时（北京时间）
            minute: 分钟
            underlying: 标的资产
            option_type: 期权类型
            side: 买卖方向
            amount: 下单数量
            
        Returns:
            任务 ID
        """
        try:
            # 北京时间转 UTC
            utc_hour = (hour - 8) % 24
            
            logger.info(f"Scheduling trading at {hour}:00 Beijing time (UTC {utc_hour}:00)")
            
            # 创建定时任务
            job = self.scheduler.add_job(
                func=self._trading_task,
                trigger=CronTrigger(hour=utc_hour, minute=minute, timezone='UTC'),
                id='scheduled_trading',
                name='Scheduled Trading',
                replace_existing=True,
                args=[underlying, option_type, side, amount]
            )
            
            logger.info(f"Trading scheduled: {job.id}")
            return job.id
        
        except Exception as e:
            logger.error(f"Error scheduling trading: {e}")
            return ""
    
    def _collect_orderbook_task(self, underlying: str, num_strikes: int):
        """
        Order book 收集任务
        
        Args:
            underlying: 标的资产
            num_strikes: 价位数量
        """
        try:
            logger.info(f"Starting orderbook collection task for {underlying}")
            result = self.orderbook_collector.collect_and_save(underlying, num_strikes)
            logger.info(f"Orderbook collection completed: {result}")
        except Exception as e:
            logger.error(f"Error in orderbook collection task: {e}")
    
    def _trading_task(self, underlying: str, option_type: str, side: str, amount: float):
        """
        交易任务
        
        Args:
            underlying: 标的资产
            option_type: 期权类型
            side: 买卖方向
            amount: 下单数量
        """
        try:
            logger.info(f"Starting trading task: {option_type} {side} {amount}")
            result = self.scheduled_trader.execute_scheduled_trade(
                underlying, option_type, side, amount
            )
            if result:
                logger.info(f"Trading completed: {result}")
            else:
                logger.warning("Trading failed")
        except Exception as e:
            logger.error(f"Error in trading task: {e}")
    
    def start(self):
        """启动定时任务调度器"""
        try:
            if not self.scheduler.running:
                self.scheduler.start()
                logger.info("TaskScheduler started")
            else:
                logger.warning("TaskScheduler is already running")
        except Exception as e:
            logger.error(f"Error starting TaskScheduler: {e}")
    
    def stop(self):
        """停止定时任务调度器"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("TaskScheduler stopped")
            else:
                logger.warning("TaskScheduler is not running")
        except Exception as e:
            logger.error(f"Error stopping TaskScheduler: {e}")
    
    def get_jobs(self):
        """获取所有定时任务"""
        return self.scheduler.get_jobs()
    
    def remove_job(self, job_id: str):
        """移除定时任务"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Job removed: {job_id}")
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {e}")
    
    def pause_job(self, job_id: str):
        """暂停定时任务"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.pause()
                logger.info(f"Job paused: {job_id}")
            else:
                logger.warning(f"Job not found: {job_id}")
        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {e}")
    
    def resume_job(self, job_id: str):
        """恢复定时任务"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.resume()
                logger.info(f"Job resumed: {job_id}")
            else:
                logger.warning(f"Job not found: {job_id}")
        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {e}")


# 全局任务调度器实例
_scheduler_instance: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    """获取全局任务调度器实例"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = TaskScheduler()
    return _scheduler_instance
