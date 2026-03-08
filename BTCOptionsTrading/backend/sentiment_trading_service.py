#!/usr/bin/env python3
"""
情绪驱动自动交易服务
监听情绪API并根据情绪数据自动执行交易策略
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, time, timedelta
from typing import Dict, Optional, List
from decimal import Decimal
import os
from pathlib import Path

# 导入项目模块
import sys
sys.path.insert(0, str(Path(__file__).parent))

from src.trading.deribit_trader import DeribitTrader
from src.strategy.smart_strategy_builder import SmartStrategyBuilder, StrategyType
from src.trading.strategy_executor import StrategyExecutor
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sentiment_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 配置
SENTIMENT_API_URL = "http://43.106.51.106:5001/api/sentiment"
CHECK_TIME = time(5, 0)  # 每天早上5点检查
DATA_FILE = "data/sentiment_trading_history.json"
POSITION_FILE = "data/current_positions.json"


class SentimentTradingService:
    """情绪驱动交易服务"""
    
    def __init__(self):
        load_dotenv()
        
        # 初始化Deribit交易器（使用测试网）
        api_key = os.getenv('DERIBIT_API_KEY')
        api_secret = os.getenv('DERIBIT_API_SECRET')
        
        if not api_key or not api_secret:
            raise ValueError("请在.env文件中配置DERIBIT_API_KEY和DERIBIT_API_SECRET")
        
        self.trader = DeribitTrader(api_key, api_secret, testnet=True)
        self.executor = StrategyExecutor(self.trader)
        self.strategy_builder = SmartStrategyBuilder()
        
        # 确保数据目录存在
        Path("data").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        # 交易历史
        self.trading_history: List[Dict] = self._load_history()
        self.last_check_date: Optional[str] = None
        
    def _load_history(self) -> List[Dict]:
        """加载交易历史"""
        try:
            if Path(DATA_FILE).exists():
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载历史数据失败: {e}")
        return []
    
    def _save_history(self):
        """保存交易历史"""
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.trading_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存历史数据失败: {e}")
    
    async def fetch_sentiment_data(self) -> Optional[Dict]:
        """获取情绪数据"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(SENTIMENT_API_URL, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"成功获取情绪数据: {data}")
                        return data
                    else:
                        logger.error(f"API返回错误状态码: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"获取情绪数据失败: {e}")
            return None
    
    def analyze_sentiment(self, sentiment_data: Dict) -> str:
        """分析情绪数据，返回策略类型"""
        try:
            data = sentiment_data.get('data', {})
            negative_count = data.get('negative_count', 0)
            positive_count = data.get('positive_count', 0)
            
            logger.info(f"情绪分析: 负面={negative_count}, 正面={positive_count}")
            
            if negative_count > positive_count:
                return "bearish_news"  # 负面消息策略
            elif negative_count < positive_count:
                return "bullish_news"  # 利好消息策略
            else:
                return "mixed_news"  # 消息混杂策略
                
        except Exception as e:
            logger.error(f"分析情绪数据失败: {e}")
            return "mixed_news"  # 默认使用混杂策略
    
    async def execute_sentiment_strategy(self, strategy_type: str, sentiment_data: Dict) -> Dict:
        """执行情绪策略"""
        try:
            logger.info(f"开始执行策略: {strategy_type}")
            
            # 构建策略
            strategy = self.strategy_builder.build_from_template(
                template_id=strategy_type,
                capital=Decimal("1000"),  # 每次交易使用1000 USD
                expiry_days=7  # 使用7天后到期的期权
            )
            
            if not strategy:
                logger.error(f"构建策略失败: {strategy_type}")
                return {"success": False, "error": "策略构建失败"}
            
            # 执行策略
            result = await self.executor.execute_strategy(strategy)
            
            # 记录交易
            trade_record = {
                "timestamp": datetime.now().isoformat(),
                "strategy_type": strategy_type,
                "sentiment_data": sentiment_data,
                "execution_result": result,
                "success": result.get("success", False)
            }
            
            self.trading_history.append(trade_record)
            self._save_history()
            
            logger.info(f"策略执行完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"执行策略失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def get_positions_and_orders(self) -> Dict:
        """获取当前持仓和订单信息"""
        try:
            positions = []
            orders = []
            errors = []
            
            # 获取持仓
            try:
                positions_result = await self.trader._make_request(
                    "private/get_positions",
                    {"currency": "BTC", "kind": "option"}
                )
                if positions_result:
                    positions = positions_result
            except Exception as e:
                errors.append(f"获取持仓失败: {str(e)}")
                logger.error(f"获取持仓失败: {e}")
            
            # 获取未完成订单
            try:
                orders_result = await self.trader._make_request(
                    "private/get_open_orders_by_currency",
                    {"currency": "BTC", "kind": "option"}
                )
                if orders_result:
                    orders = orders_result
            except Exception as e:
                errors.append(f"获取订单失败: {str(e)}")
                logger.error(f"获取订单失败: {e}")
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "positions": positions,
                "open_orders": orders,
                "errors": errors if errors else None,
                "position_count": len(positions) if positions else 0,
                "order_count": len(orders) if orders else 0
            }
            
            # 保存到文件
            with open(POSITION_FILE, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            return result
            
        except Exception as e:
            logger.error(f"获取持仓和订单信息失败: {e}", exc_info=True)
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "positions": [],
                "open_orders": [],
                "errors": [str(e)]
            }
    
    async def daily_check(self):
        """每日检查和交易"""
        today = datetime.now().date().isoformat()
        
        # 避免重复执行
        if self.last_check_date == today:
            logger.info(f"今天已经执行过检查: {today}")
            return
        
        logger.info(f"开始每日检查: {today}")
        
        # 1. 获取情绪数据
        sentiment_data = await self.fetch_sentiment_data()
        if not sentiment_data:
            logger.error("无法获取情绪数据，跳过本次交易")
            return
        
        # 2. 分析情绪并选择策略
        strategy_type = self.analyze_sentiment(sentiment_data)
        logger.info(f"选择策略: {strategy_type}")
        
        # 3. 执行策略
        result = await self.execute_sentiment_strategy(strategy_type, sentiment_data)
        
        # 4. 更新持仓信息
        await self.get_positions_and_orders()
        
        # 标记今天已检查
        self.last_check_date = today
        
        logger.info(f"每日检查完成: {result}")
    
    async def run(self):
        """主运行循环"""
        logger.info("情绪驱动交易服务启动")
        
        # 连接到Deribit
        try:
            authenticated = await self.trader.authenticate()
            if not authenticated:
                logger.error("Deribit认证失败，服务无法启动")
                return
            logger.info("Deribit认证成功")
        except Exception as e:
            logger.error(f"连接Deribit失败: {e}")
            return
        
        while True:
            try:
                now = datetime.now()
                current_time = now.time()
                
                # 检查是否到了执行时间（早上5点）
                if current_time.hour == CHECK_TIME.hour and current_time.minute == CHECK_TIME.minute:
                    await self.daily_check()
                    # 等待60秒，避免在同一分钟内重复执行
                    await asyncio.sleep(60)
                else:
                    # 每分钟检查一次
                    await asyncio.sleep(60)
                    
            except Exception as e:
                logger.error(f"运行循环出错: {e}", exc_info=True)
                await asyncio.sleep(60)


async def main():
    """主函数"""
    service = SentimentTradingService()
    await service.run()


if __name__ == "__main__":
    asyncio.run(main())
