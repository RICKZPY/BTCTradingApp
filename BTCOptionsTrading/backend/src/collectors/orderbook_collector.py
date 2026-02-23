"""
Order Book 收集器 - 收集 ATM 附近的 option order book 数据
"""

import os
import csv
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple
from pathlib import Path

from src.connectors.deribit_connector import DeribitConnector
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class OrderBookCollector:
    """Order Book 收集器"""
    
    def __init__(self, data_dir: str = "data/orderbook"):
        """
        初始化 Order Book 收集器
        
        Args:
            data_dir: 数据保存目录
        """
        self.data_dir = data_dir
        self.connector = DeribitConnector()
        
        # 确保数据目录存在
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"OrderBookCollector initialized with data_dir: {self.data_dir}")
    
    def get_atm_strikes(self, underlying: str = "BTC", num_strikes: int = 4) -> List[float]:
        """
        获取 ATM 附近的价位
        
        Args:
            underlying: 标的资产（BTC 或 ETH）
            num_strikes: 返回的价位数量（默认 4 个）
            
        Returns:
            价位列表
        """
        try:
            # 在同步上下文中运行异步代码
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已经在异步上下文中，创建新的事件循环
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self._get_atm_strikes_async(underlying, num_strikes))
                    return future.result()
            else:
                return asyncio.run(self._get_atm_strikes_async(underlying, num_strikes))
        except Exception as e:
            logger.error(f"Error getting ATM strikes: {e}")
            return []
    
    async def _get_atm_strikes_async(self, underlying: str, num_strikes: int) -> List[float]:
        """异步获取 ATM 价位"""
        try:
            # 获取当前价格
            current_price = await self.connector.get_index_price(underlying)
            logger.info(f"Current {underlying} price: {current_price}")
            
            # 获取所有 option 合约
            contracts = await self.connector.get_options_chain(underlying)
            
            # 提取所有 strike 价位
            strikes = set()
            for contract in contracts:
                strikes.add(float(contract.strike_price))
            
            # 排序并找到最接近当前价格的价位
            sorted_strikes = sorted(list(strikes))
            
            # 找到 ATM 价位的索引
            atm_index = 0
            min_diff = float('inf')
            for i, strike in enumerate(sorted_strikes):
                diff = abs(strike - current_price)
                if diff < min_diff:
                    min_diff = diff
                    atm_index = i
            
            # 获取 ATM 附近的价位
            start_index = max(0, atm_index - num_strikes // 2)
            end_index = min(len(sorted_strikes), start_index + num_strikes)
            
            atm_strikes = sorted_strikes[start_index:end_index]
            logger.info(f"ATM strikes: {atm_strikes}")
            
            return atm_strikes
        
        except Exception as e:
            logger.error(f"Error getting ATM strikes: {e}")
            return []
    
    def get_options_chain(self, underlying: str = "BTC", days_ahead: int = 30) -> List[Dict]:
        """
        获取一个月内的所有 option
        
        Args:
            underlying: 标的资产
            days_ahead: 天数范围
            
        Returns:
            option 列表
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self._get_options_chain_async(underlying, days_ahead))
                    return future.result()
            else:
                return asyncio.run(self._get_options_chain_async(underlying, days_ahead))
        except Exception as e:
            logger.error(f"Error getting options chain: {e}")
            return []
    
    async def _get_options_chain_async(self, underlying: str, days_ahead: int) -> List[Dict]:
        """异步获取 option 链"""
        try:
            # 获取所有 option 合约
            contracts = await self.connector.get_options_chain(underlying)
            
            # 过滤一个月内的 option
            now = datetime.now(timezone.utc)
            cutoff_date = now + timedelta(days=days_ahead)
            
            options = []
            for contract in contracts:
                try:
                    # 检查是否在范围内
                    if contract.expiration_date <= cutoff_date:
                        options.append({
                            'instrument_name': contract.instrument_name,
                            'underlying': contract.underlying,
                            'strike_price': float(contract.strike_price),
                            'option_type': 'call' if contract.option_type.value == 'call' else 'put',
                            'expiry_date': contract.expiration_date.isoformat()
                        })
                
                except Exception as e:
                    logger.warning(f"Error processing contract: {e}")
                    continue
            
            logger.info(f"Retrieved {len(options)} options for {underlying}")
            return options
        
        except Exception as e:
            logger.error(f"Error getting options chain: {e}")
            return []
    
    def collect_orderbook(self, underlying: str = "BTC", num_strikes: int = 4) -> List[Dict]:
        """
        收集 order book 数据
        
        Args:
            underlying: 标的资产
            num_strikes: ATM 附近的价位数量
            
        Returns:
            order book 数据列表
        """
        try:
            # 在同步上下文中运行异步代码
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self._collect_orderbook_async(underlying, num_strikes))
                    return future.result()
            else:
                return asyncio.run(self._collect_orderbook_async(underlying, num_strikes))
        except Exception as e:
            logger.error(f"Error collecting orderbook: {e}")
            return []
    
    async def _collect_orderbook_async(self, underlying: str, num_strikes: int) -> List[Dict]:
        """异步收集 order book 数据"""
        try:
            # 获取 ATM 附近的价位
            atm_strikes = await self._get_atm_strikes_async(underlying, num_strikes)
            if not atm_strikes:
                logger.error("Failed to get ATM strikes")
                return []
            
            # 获取一个月内的所有 option
            options = await self._get_options_chain_async(underlying, 30)
            if not options:
                logger.error("Failed to get options chain")
                return []
            
            # 过滤 ATM 附近的 option
            atm_options = [
                opt for opt in options
                if opt['strike_price'] in atm_strikes
            ]
            
            logger.info(f"Collecting order book for {len(atm_options)} options")
            
            # 收集每个 option 的 order book
            orderbook_data = []
            timestamp = datetime.now(timezone.utc).isoformat()
            
            for option in atm_options:
                try:
                    # 获取 order book
                    instrument_name = option['instrument_name']
                    orderbook = await self.connector.get_orderbook(instrument_name)
                    
                    if not orderbook:
                        logger.warning(f"No orderbook data for {instrument_name}")
                        continue
                    
                    # 提取 bid 和 ask 数据
                    bids = orderbook.get('bids', [])
                    asks = orderbook.get('asks', [])
                    
                    # 获取最优 bid 和 ask
                    best_bid_price = bids[0][0] if bids else None
                    best_bid_size = bids[0][1] if bids else None
                    best_ask_price = asks[0][0] if asks else None
                    best_ask_size = asks[0][1] if asks else None
                    
                    # 记录数据
                    orderbook_data.append({
                        'timestamp': timestamp,
                        'instrument_name': instrument_name,
                        'strike_price': option['strike_price'],
                        'option_type': option['option_type'],
                        'expiry_date': option['expiry_date'],
                        'bid_price': best_bid_price,
                        'bid_size': best_bid_size,
                        'ask_price': best_ask_price,
                        'ask_size': best_ask_size
                    })
                
                except Exception as e:
                    logger.warning(f"Error collecting orderbook for {instrument_name}: {e}")
                    continue
            
            logger.info(f"Collected order book data for {len(orderbook_data)} options")
            return orderbook_data
        
        except Exception as e:
            logger.error(f"Error in _collect_orderbook_async: {e}")
            return []
    
    def save_to_csv(self, data: List[Dict], filename: str = None) -> str:
        """
        保存 order book 数据到 CSV
        
        Args:
            data: order book 数据列表
            filename: 文件名（如果为 None，使用时间戳）
            
        Returns:
            保存的文件路径
        """
        try:
            if not data:
                logger.warning("No data to save")
                return ""
            
            # 生成文件名
            if filename is None:
                now = datetime.now()
                filename = f"orderbook_{now.strftime('%Y%m%d_%H%M%S')}.csv"
            
            filepath = os.path.join(self.data_dir, filename)
            
            # 写入 CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'timestamp', 'instrument_name', 'strike_price', 'option_type',
                    'expiry_date', 'bid_price', 'bid_size', 'ask_price', 'ask_size'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"Order book data saved to {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
            return ""
    
    def collect_and_save(self, underlying: str = "BTC", num_strikes: int = 4) -> str:
        """
        收集并保存 order book 数据
        
        Args:
            underlying: 标的资产
            num_strikes: ATM 附近的价位数量
            
        Returns:
            保存的文件路径
        """
        try:
            # 收集数据
            data = self.collect_orderbook(underlying, num_strikes)
            
            if not data:
                logger.error("Failed to collect orderbook data")
                return ""
            
            # 保存到 CSV
            filepath = self.save_to_csv(data)
            
            return filepath
        
        except Exception as e:
            logger.error(f"Error in collect_and_save: {e}")
            return ""
