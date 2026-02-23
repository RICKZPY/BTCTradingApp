"""
定时交易调度器
支持配置定时执行策略
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import logging
from pathlib import Path
import json
from uuid import UUID

from ..core.models import Strategy
from .deribit_trader import DeribitTrader
from .strategy_executor import StrategyExecutor

logger = logging.getLogger(__name__)


class ScheduledTradingConfig:
    """定时交易配置"""
    
    def __init__(
        self,
        strategy_id: str,
        strategy_name: str,
        enabled: bool = True,
        schedule_time: str = "05:00",  # 北京时间
        timezone: str = "Asia/Shanghai",
        use_market_order: bool = False,
        auto_close: bool = False,
        close_time: Optional[str] = None
    ):
        self.strategy_id = strategy_id
        self.strategy_name = strategy_name
        self.enabled = enabled
        self.schedule_time = schedule_time
        self.timezone = timezone
        self.use_market_order = use_market_order
        self.auto_close = auto_close
        self.close_time = close_time
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "enabled": self.enabled,
            "schedule_time": self.schedule_time,
            "timezone": self.timezone,
            "use_market_order": self.use_market_order,
            "auto_close": self.auto_close,
            "close_time": self.close_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ScheduledTradingConfig':
        """从字典创建"""
        return cls(**data)


class ScheduledTradingManager:
    """定时交易管理器"""
    
    def __init__(
        self,
        trader: DeribitTrader,
        config_file: str = "data/scheduled_trades.json"
    ):
        """
        初始化管理器
        
        Args:
            trader: Deribit交易客户端
            config_file: 配置文件路径
        """
        self.trader = trader
        self.executor = StrategyExecutor(trader)
        self.scheduler = AsyncIOScheduler()
        self.config_file = Path(config_file)
        self.scheduled_configs: Dict[str, ScheduledTradingConfig] = {}
        self.strategies: Dict[str, Strategy] = {}
        
        # 加载配置
        self._load_configs()
    
    def _load_configs(self):
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for config_data in data.get('scheduled_trades', []):
                        config = ScheduledTradingConfig.from_dict(config_data)
                        self.scheduled_configs[config.strategy_id] = config
                logger.info(f"加载了 {len(self.scheduled_configs)} 个定时交易配置")
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
        else:
            logger.info("配置文件不存在，创建新配置")
            self._save_configs()
    
    def _save_configs(self):
        """保存配置文件"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "scheduled_trades": [
                config.to_dict() for config in self.scheduled_configs.values()
            ]
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"保存了 {len(self.scheduled_configs)} 个定时交易配置")
    
    def add_scheduled_strategy(
        self,
        strategy: Strategy,
        schedule_time: str = "05:00",
        timezone: str = "Asia/Shanghai",
        use_market_order: bool = False,
        auto_close: bool = False,
        close_time: Optional[str] = None
    ) -> str:
        """
        添加定时策略
        
        Args:
            strategy: 策略对象
            schedule_time: 执行时间 (HH:MM格式)
            timezone: 时区
            use_market_order: 是否使用市价单
            auto_close: 是否自动平仓
            close_time: 平仓时间
            
        Returns:
            策略ID
        """
        strategy_id = str(strategy.id)
        
        # 保存策略
        self.strategies[strategy_id] = strategy
        
        # 创建配置
        config = ScheduledTradingConfig(
            strategy_id=strategy_id,
            strategy_name=strategy.name,
            enabled=True,
            schedule_time=schedule_time,
            timezone=timezone,
            use_market_order=use_market_order,
            auto_close=auto_close,
            close_time=close_time
        )
        
        self.scheduled_configs[strategy_id] = config
        self._save_configs()
        
        # 添加到调度器
        self._schedule_strategy(config)
        
        logger.info(f"添加定时策略: {strategy.name}, 执行时间: {schedule_time}")
        return strategy_id
    
    def _schedule_strategy(self, config: ScheduledTradingConfig):
        """
        将策略添加到调度器
        
        Args:
            config: 定时配置
        """
        if not config.enabled:
            return
        
        # 解析时间
        hour, minute = map(int, config.schedule_time.split(':'))
        tz = pytz.timezone(config.timezone)
        
        # 创建cron触发器（每天执行）
        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            timezone=tz
        )
        
        # 添加任务
        job_id = f"strategy_{config.strategy_id}"
        self.scheduler.add_job(
            self._execute_scheduled_strategy,
            trigger=trigger,
            args=[config.strategy_id],
            id=job_id,
            replace_existing=True
        )
        
        logger.info(f"已调度策略 {config.strategy_name} 在 {config.schedule_time} ({config.timezone})")
        
        # 如果需要自动平仓，也添加平仓任务
        if config.auto_close and config.close_time:
            close_hour, close_minute = map(int, config.close_time.split(':'))
            close_trigger = CronTrigger(
                hour=close_hour,
                minute=close_minute,
                timezone=tz
            )
            
            close_job_id = f"close_{config.strategy_id}"
            self.scheduler.add_job(
                self._close_scheduled_strategy,
                trigger=close_trigger,
                args=[config.strategy_id],
                id=close_job_id,
                replace_existing=True
            )
            
            logger.info(f"已调度平仓任务在 {config.close_time}")
    
    async def _execute_scheduled_strategy(self, strategy_id: str):
        """
        执行定时策略
        
        Args:
            strategy_id: 策略ID
        """
        logger.info(f"定时执行策略: {strategy_id}")
        
        config = self.scheduled_configs.get(strategy_id)
        strategy = self.strategies.get(strategy_id)
        
        if not config or not strategy:
            logger.error(f"找不到策略或配置: {strategy_id}")
            return
        
        try:
            result = await self.executor.execute_strategy(
                strategy=strategy,
                use_market_order=config.use_market_order
            )
            
            logger.info(f"策略执行结果: {result}")
            
        except Exception as e:
            logger.error(f"执行策略时出错: {e}")
    
    async def _close_scheduled_strategy(self, strategy_id: str):
        """
        平仓定时策略
        
        Args:
            strategy_id: 策略ID
        """
        logger.info(f"定时平仓策略: {strategy_id}")
        
        strategy = self.strategies.get(strategy_id)
        
        if not strategy:
            logger.error(f"找不到策略: {strategy_id}")
            return
        
        try:
            result = await self.executor.close_strategy_positions(strategy)
            logger.info(f"平仓结果: {result}")
            
        except Exception as e:
            logger.error(f"平仓时出错: {e}")
    
    def remove_scheduled_strategy(self, strategy_id: str):
        """
        移除定时策略
        
        Args:
            strategy_id: 策略ID
        """
        if strategy_id in self.scheduled_configs:
            del self.scheduled_configs[strategy_id]
            self._save_configs()
            
            # 从调度器移除
            job_id = f"strategy_{strategy_id}"
            close_job_id = f"close_{strategy_id}"
            
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            if self.scheduler.get_job(close_job_id):
                self.scheduler.remove_job(close_job_id)
            
            logger.info(f"移除定时策略: {strategy_id}")
    
    def enable_strategy(self, strategy_id: str):
        """启用策略"""
        if strategy_id in self.scheduled_configs:
            self.scheduled_configs[strategy_id].enabled = True
            self._save_configs()
            self._schedule_strategy(self.scheduled_configs[strategy_id])
    
    def disable_strategy(self, strategy_id: str):
        """禁用策略"""
        if strategy_id in self.scheduled_configs:
            self.scheduled_configs[strategy_id].enabled = False
            self._save_configs()
            
            job_id = f"strategy_{strategy_id}"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
    
    def start(self):
        """启动调度器"""
        # 加载所有启用的策略
        for config in self.scheduled_configs.values():
            if config.enabled:
                self._schedule_strategy(config)
        
        self.scheduler.start()
        logger.info("定时交易调度器已启动")
    
    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        logger.info("定时交易调度器已停止")
    
    def get_scheduled_strategies(self) -> List[Dict]:
        """获取所有定时策略"""
        return [config.to_dict() for config in self.scheduled_configs.values()]
    
    def get_execution_log(self) -> List[Dict]:
        """获取执行日志"""
        return self.executor.get_execution_log()
