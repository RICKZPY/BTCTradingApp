#!/usr/bin/env python3
"""
每日期权数据采集脚本

从Deribit API获取当天的期权数据并保存到数据库
可以通过cron job每天自动运行
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import csv

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.connectors.deribit_connector import DeribitConnector
from src.config.settings import Settings
from src.config.logging_config import get_logger
from src.historical.manager import HistoricalDataManager
from src.historical.models import HistoricalOptionData

logger = get_logger(__name__)


class DailyDataCollector:
    """每日数据采集器"""
    
    def __init__(
        self,
        currency: str = "BTC",
        save_to_csv: bool = True,
        save_to_db: bool = True,
        csv_dir: str = "data/daily_snapshots",
        db_path: str = "data/btc_options.db"
    ):
        """
        初始化采集器
        
        Args:
            currency: 标的资产（BTC或ETH）
            save_to_csv: 是否保存为CSV文件
            save_to_db: 是否保存到数据库
            csv_dir: CSV文件保存目录
            db_path: 数据库路径
        """
        self.currency = currency
        self.save_to_csv = save_to_csv
        self.save_to_db = save_to_db
        self.csv_dir = Path(csv_dir)
        self.db_path = db_path
        
        # 创建CSV目录
        if self.save_to_csv:
            self.csv_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化历史数据管理器
        if self.save_to_db:
            self.manager = HistoricalDataManager(
                download_dir="data/downloads",
                db_path=db_path
            )
        
        logger.info(f"DailyDataCollector initialized: currency={currency}, csv={save_to_csv}, db={save_to_db}")
    
    async def collect_options_data(self) -> List[Dict[str, Any]]:
        """
        从Deribit获取期权数据
        
        Returns:
            期权数据列表
        """
        logger.info(f"Fetching options data for {self.currency}...")
        
        # 创建Deribit连接器
        connector = DeribitConnector()
        
        try:
            # 获取期权链数据
            options_chain = await connector.get_options_chain(self.currency)
            
            logger.info(f"Retrieved {len(options_chain)} option contracts")
            return options_chain
            
        except Exception as e:
            logger.error(f"Failed to fetch options data: {str(e)}")
            raise
    
    def save_to_csv_file(self, options_data: List[Dict[str, Any]], timestamp: datetime):
        """
        保存数据到CSV文件
        
        Args:
            options_data: 期权数据列表
            timestamp: 时间戳
        """
        if not options_data:
            logger.warning("No data to save to CSV")
            return
        
        # 生成文件名：YYYYMMDD_HHMMSS_BTC_options.csv
        filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{self.currency}_options.csv"
        filepath = self.csv_dir / filename
        
        logger.info(f"Saving {len(options_data)} records to {filepath}")
        
        try:
            # CSV字段
            fieldnames = [
                'timestamp',
                'instrument_name',
                'underlying_symbol',
                'strike_price',
                'expiry_date',
                'option_type',
                'mark_price',
                'bid_price',
                'ask_price',
                'last_price',
                'volume',
                'open_interest',
                'implied_volatility',
                'delta',
                'gamma',
                'theta',
                'vega',
                'rho'
            ]
            
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for option in options_data:
                    # OptionContract is a dataclass, access attributes directly
                    row = {
                        'timestamp': timestamp.isoformat(),
                        'instrument_name': option.instrument_name,
                        'underlying_symbol': self.currency,
                        'strike_price': float(option.strike_price),
                        'expiry_date': option.expiration_date.isoformat() if option.expiration_date else '',
                        'option_type': option.option_type.value if hasattr(option.option_type, 'value') else str(option.option_type),
                        'mark_price': float(option.current_price),
                        'bid_price': float(option.bid_price),
                        'ask_price': float(option.ask_price),
                        'last_price': float(option.last_price),
                        'volume': option.volume,
                        'open_interest': option.open_interest,
                        'implied_volatility': option.implied_volatility,
                        'delta': option.delta,
                        'gamma': option.gamma,
                        'theta': option.theta,
                        'vega': option.vega,
                        'rho': option.rho
                    }
                    writer.writerow(row)
            
            logger.info(f"Successfully saved data to {filepath}")
            logger.info(f"File size: {filepath.stat().st_size / 1024:.2f} KB")
            
        except Exception as e:
            logger.error(f"Failed to save CSV file: {str(e)}")
            raise
    
    def save_to_database(self, options_data: List[Dict[str, Any]], timestamp: datetime):
        """
        保存数据到数据库
        
        Args:
            options_data: 期权数据列表
            timestamp: 时间戳
        """
        if not options_data:
            logger.warning("No data to save to database")
            return
        
        logger.info(f"Saving {len(options_data)} records to database")
        
        try:
            # 转换为HistoricalOptionData对象
            historical_records = []
            
            for option in options_data:
                record = HistoricalOptionData(
                    timestamp=timestamp,
                    instrument_name=option.instrument_name,
                    underlying_symbol=self.currency,
                    strike_price=float(option.strike_price),
                    expiry_date=option.expiration_date,
                    option_type=option.option_type.value if hasattr(option.option_type, 'value') else str(option.option_type),
                    open_price=float(option.current_price),  # 使用current_price作为开盘价
                    high_price=float(option.current_price),
                    low_price=float(option.current_price),
                    close_price=float(option.current_price),
                    volume=float(option.volume),
                    open_interest=int(option.open_interest),
                    implied_volatility=float(option.implied_volatility)
                )
                historical_records.append(record)
            
            # 保存到数据库
            self.manager.cache.store_batch(historical_records)
            
            logger.info(f"Successfully saved {len(historical_records)} records to database")
            
        except Exception as e:
            logger.error(f"Failed to save to database: {str(e)}")
            raise
    
    async def run(self):
        """运行数据采集"""
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info(f"Starting daily data collection at {start_time.isoformat()}")
        logger.info("=" * 60)
        
        try:
            # 1. 获取数据
            options_data = await self.collect_options_data()
            
            if not options_data:
                logger.warning("No options data retrieved")
                return
            
            # 2. 保存到CSV
            if self.save_to_csv:
                self.save_to_csv_file(options_data, start_time)
            
            # 3. 保存到数据库
            if self.save_to_db:
                self.save_to_database(options_data, start_time)
            
            # 4. 统计信息
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("=" * 60)
            logger.info("Collection Summary:")
            logger.info(f"  Currency: {self.currency}")
            logger.info(f"  Records collected: {len(options_data)}")
            logger.info(f"  Saved to CSV: {self.save_to_csv}")
            logger.info(f"  Saved to DB: {self.save_to_db}")
            logger.info(f"  Duration: {duration:.2f}s")
            logger.info(f"  Completed at: {end_time.isoformat()}")
            logger.info("=" * 60)
            
            return {
                'success': True,
                'records_collected': len(options_data),
                'duration': duration,
                'timestamp': start_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Data collection failed: {str(e)}")
            logger.exception("Full traceback:")
            return {
                'success': False,
                'error': str(e),
                'timestamp': start_time.isoformat()
            }


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Daily Options Data Collector')
    parser.add_argument(
        '--currency',
        type=str,
        default='BTC',
        choices=['BTC', 'ETH'],
        help='Underlying currency (default: BTC)'
    )
    parser.add_argument(
        '--csv',
        action='store_true',
        default=True,
        help='Save to CSV file (default: True)'
    )
    parser.add_argument(
        '--no-csv',
        action='store_false',
        dest='csv',
        help='Do not save to CSV file'
    )
    parser.add_argument(
        '--db',
        action='store_true',
        default=True,
        help='Save to database (default: True)'
    )
    parser.add_argument(
        '--no-db',
        action='store_false',
        dest='db',
        help='Do not save to database'
    )
    parser.add_argument(
        '--csv-dir',
        type=str,
        default='data/daily_snapshots',
        help='CSV output directory (default: data/daily_snapshots)'
    )
    parser.add_argument(
        '--db-path',
        type=str,
        default='data/btc_options.db',
        help='Database path (default: data/btc_options.db)'
    )
    
    args = parser.parse_args()
    
    # 创建采集器
    collector = DailyDataCollector(
        currency=args.currency,
        save_to_csv=args.csv,
        save_to_db=args.db,
        csv_dir=args.csv_dir,
        db_path=args.db_path
    )
    
    # 运行采集
    result = await collector.run()
    
    # 返回退出码
    sys.exit(0 if result.get('success', False) else 1)


if __name__ == '__main__':
    asyncio.run(main())
