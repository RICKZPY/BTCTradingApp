"""
定时交易执行器 - 在指定时间执行交易
"""

import os
import csv
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from pathlib import Path

from src.connectors.deribit_connector import DeribitConnector
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class ScheduledTrader:
    """定时交易执行器"""
    
    def __init__(self, data_dir: str = "data/trades"):
        """
        初始化定时交易执行器
        
        Args:
            data_dir: 交易记录保存目录
        """
        self.data_dir = data_dir
        self.connector = DeribitConnector()
        
        # 确保数据目录存在
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ScheduledTrader initialized with data_dir: {self.data_dir}")
    
    def get_atm_option(self, underlying: str = "BTC", option_type: str = "call", 
                       days_ahead: int = 30) -> Optional[str]:
        """
        获取 ATM option
        
        Args:
            underlying: 标的资产
            option_type: 期权类型（call 或 put）
            days_ahead: 天数范围
            
        Returns:
            option 名称
        """
        try:
            # 获取当前价格
            current_price = self.connector.get_underlying_price(underlying)
            logger.info(f"Current {underlying} price: {current_price}")
            
            # 获取所有 option
            instruments = self.connector.get_instruments(underlying, kind="option")
            
            # 过滤条件
            now = datetime.now(timezone.utc)
            cutoff_date = now + timedelta(days=days_ahead)
            
            # 找到最接近 ATM 的 option
            best_option = None
            best_diff = float('inf')
            
            for instrument in instruments:
                try:
                    # 解析 instrument 信息
                    parts = instrument.split('-')
                    if len(parts) < 4:
                        continue
                    
                    # 检查期权类型
                    instr_type = parts[3].lower()
                    if instr_type != option_type[0]:  # c 或 p
                        continue
                    
                    # 提取 strike 价位
                    strike_price = float(parts[2])
                    
                    # 解析到期日期
                    expiry_str = parts[1]
                    day = int(expiry_str[:2])
                    month_str = expiry_str[2:5]
                    year = int(expiry_str[5:7])
                    
                    months = {
                        'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4,
                        'MAY': 5, 'JUN': 6, 'JUL': 7, 'AUG': 8,
                        'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
                    }
                    month = months.get(month_str.upper(), 1)
                    full_year = 2000 + year if year < 50 else 1900 + year
                    
                    expiry_date = datetime(full_year, month, day, tzinfo=timezone.utc)
                    
                    # 检查是否在范围内
                    if expiry_date > cutoff_date:
                        continue
                    
                    # 计算与 ATM 的差距
                    diff = abs(strike_price - current_price)
                    
                    if diff < best_diff:
                        best_diff = diff
                        best_option = instrument
                
                except Exception as e:
                    logger.warning(f"Error parsing instrument {instrument}: {e}")
                    continue
            
            if best_option:
                logger.info(f"Found ATM option: {best_option}")
                return best_option
            else:
                logger.warning("No ATM option found")
                return None
        
        except Exception as e:
            logger.error(f"Error getting ATM option: {e}")
            return None
    
    def place_order(self, instrument_name: str, side: str = "buy", 
                    amount: float = 1.0, price: Optional[float] = None) -> Optional[Dict]:
        """
        下单
        
        Args:
            instrument_name: option 名称
            side: 买卖方向（buy 或 sell）
            amount: 下单数量
            price: 下单价格（如果为 None，使用市价）
            
        Returns:
            下单结果
        """
        try:
            logger.info(f"Placing {side} order for {instrument_name}, amount: {amount}")
            
            # 获取 order book 以确定价格
            if price is None:
                orderbook = self.connector.get_orderbook(instrument_name)
                if not orderbook:
                    logger.error(f"Failed to get orderbook for {instrument_name}")
                    return None
                
                # 使用最优价格
                if side == "buy":
                    asks = orderbook.get('asks', [])
                    if asks:
                        price = asks[0][0]  # 最优 ask 价格
                else:
                    bids = orderbook.get('bids', [])
                    if bids:
                        price = bids[0][0]  # 最优 bid 价格
            
            if price is None:
                logger.error("Failed to determine order price")
                return None
            
            logger.info(f"Order price: {price}")
            
            # 下单
            order_result = self.connector.place_order(
                instrument_name=instrument_name,
                amount=amount,
                type="limit",
                side=side,
                price=price
            )
            
            if order_result:
                logger.info(f"Order placed successfully: {order_result}")
                return order_result
            else:
                logger.error("Failed to place order")
                return None
        
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    def record_order(self, order_result: Dict, filename: str = None) -> str:
        """
        记录下单结果
        
        Args:
            order_result: 下单结果
            filename: 文件名（如果为 None，使用时间戳）
            
        Returns:
            保存的文件路径
        """
        try:
            if not order_result:
                logger.warning("No order result to record")
                return ""
            
            # 生成文件名
            if filename is None:
                now = datetime.now()
                filename = f"trades_{now.strftime('%Y%m%d')}.csv"
            
            filepath = os.path.join(self.data_dir, filename)
            
            # 检查文件是否存在
            file_exists = os.path.exists(filepath)
            
            # 写入 CSV
            with open(filepath, 'a', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'timestamp', 'instrument_name', 'side', 'amount', 'price',
                    'order_id', 'status', 'filled_amount'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # 如果文件不存在，写入表头
                if not file_exists:
                    writer.writeheader()
                
                # 写入数据
                record = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'instrument_name': order_result.get('instrument_name', ''),
                    'side': order_result.get('side', ''),
                    'amount': order_result.get('amount', ''),
                    'price': order_result.get('price', ''),
                    'order_id': order_result.get('order_id', ''),
                    'status': order_result.get('status', ''),
                    'filled_amount': order_result.get('filled_amount', '')
                }
                writer.writerow(record)
            
            logger.info(f"Order recorded to {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Error recording order: {e}")
            return ""
    
    def execute_scheduled_trade(self, underlying: str = "BTC", option_type: str = "call",
                                side: str = "buy", amount: float = 1.0) -> Optional[Dict]:
        """
        执行定时交易
        
        Args:
            underlying: 标的资产
            option_type: 期权类型
            side: 买卖方向
            amount: 下单数量
            
        Returns:
            下单结果
        """
        try:
            logger.info(f"Executing scheduled trade: {option_type} {side} {amount}")
            
            # 获取 ATM option
            instrument_name = self.get_atm_option(underlying, option_type)
            if not instrument_name:
                logger.error("Failed to get ATM option")
                return None
            
            # 下单
            order_result = self.place_order(instrument_name, side, amount)
            if not order_result:
                logger.error("Failed to place order")
                return None
            
            # 记录下单结果
            self.record_order(order_result)
            
            return order_result
        
        except Exception as e:
            logger.error(f"Error executing scheduled trade: {e}")
            return None
