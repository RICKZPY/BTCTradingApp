"""
历史数据缓存层
提供高效的数据存储和查询功能
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Tuple
from collections import OrderedDict
import json

from src.historical.models import (
    HistoricalOptionData, CoverageStats, DataSource
)
from src.core.models import OptionType
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class HistoricalDataCache:
    """历史数据缓存"""
    
    def __init__(
        self,
        db_path: str = "data/historical_options.db",
        cache_size_mb: int = 100
    ):
        """
        初始化缓存
        
        Args:
            db_path: 数据库文件路径
            cache_size_mb: 内存缓存大小（MB）
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # LRU 缓存（内存）
        self.cache_size_mb = cache_size_mb
        self.memory_cache: OrderedDict[str, List[HistoricalOptionData]] = OrderedDict()
        self.cache_size_bytes = 0
        self.max_cache_bytes = cache_size_mb * 1024 * 1024
        
        # 初始化数据库
        self._init_database()
        
        logger.info(f"HistoricalDataCache initialized: db={db_path}, cache_size={cache_size_mb}MB")
    
    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 创建历史数据表（如果不存在）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_option_data (
                id TEXT PRIMARY KEY,
                instrument_name TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                open_price REAL NOT NULL,
                high_price REAL NOT NULL,
                low_price REAL NOT NULL,
                close_price REAL NOT NULL,
                volume REAL NOT NULL,
                strike_price REAL NOT NULL,
                expiry_date INTEGER NOT NULL,
                option_type TEXT NOT NULL,
                underlying_symbol TEXT NOT NULL,
                data_source TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_instrument_timestamp 
            ON historical_option_data(instrument_name, timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON historical_option_data(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expiry 
            ON historical_option_data(expiry_date)
        """)
        
        conn.commit()
        conn.close()
        
        logger.debug("Database initialized")
    
    def store_historical_data(
        self,
        data: List[HistoricalOptionData],
        batch_size: int = 1000
    ) -> int:
        """
        存储历史数据到数据库
        
        Args:
            data: 历史数据列表
            batch_size: 批量插入大小
            
        Returns:
            成功插入的记录数
        """
        if not data:
            logger.warning("No data to store")
            return 0
        
        logger.info(f"Storing {len(data)} records to database")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        inserted_count = 0
        
        try:
            # 批量插入
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                
                records = [
                    (
                        str(d.id),
                        d.instrument_name,
                        int(d.timestamp.timestamp()),
                        float(d.open_price),
                        float(d.high_price),
                        float(d.low_price),
                        float(d.close_price),
                        float(d.volume),
                        float(d.strike_price),
                        int(d.expiry_date.timestamp()),
                        d.option_type.value,
                        d.underlying_symbol,
                        d.data_source.value,
                        int(datetime.now().timestamp())
                    )
                    for d in batch
                ]
                
                cursor.executemany("""
                    INSERT OR REPLACE INTO historical_option_data
                    (id, instrument_name, timestamp, open_price, high_price, low_price,
                     close_price, volume, strike_price, expiry_date, option_type,
                     underlying_symbol, data_source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, records)
                
                inserted_count += len(batch)
                
                if (i + batch_size) % 10000 == 0:
                    logger.debug(f"Inserted {inserted_count}/{len(data)} records")
            
            conn.commit()
            logger.info(f"Successfully stored {inserted_count} records")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to store data: {e}")
            raise
        finally:
            conn.close()
        
        return inserted_count

    
    def query_option_data(
        self,
        instrument_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        underlying_symbol: Optional[str] = None,
        use_cache: bool = True
    ) -> List[HistoricalOptionData]:
        """
        查询期权数据
        
        Args:
            instrument_name: 期权合约名称
            start_date: 开始日期
            end_date: 结束日期
            underlying_symbol: 标的资产符号
            use_cache: 是否使用内存缓存
            
        Returns:
            历史数据列表
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(
            instrument_name, start_date, end_date, underlying_symbol
        )
        
        # 检查内存缓存
        if use_cache and cache_key in self.memory_cache:
            logger.debug(f"Cache hit: {cache_key}")
            # 更新 LRU 顺序
            self.memory_cache.move_to_end(cache_key)
            return self.memory_cache[cache_key]
        
        # 从数据库查询
        logger.debug(f"Cache miss, querying database: {cache_key}")
        data = self._query_from_database(
            instrument_name, start_date, end_date, underlying_symbol
        )
        
        # 更新内存缓存
        if use_cache and data:
            self._add_to_cache(cache_key, data)
        
        return data
    
    def _generate_cache_key(
        self,
        instrument_name: Optional[str],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        underlying_symbol: Optional[str]
    ) -> str:
        """生成缓存键"""
        parts = [
            instrument_name or "all",
            start_date.isoformat() if start_date else "none",
            end_date.isoformat() if end_date else "none",
            underlying_symbol or "all"
        ]
        return "|".join(parts)
    
    def _query_from_database(
        self,
        instrument_name: Optional[str],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        underlying_symbol: Optional[str]
    ) -> List[HistoricalOptionData]:
        """从数据库查询数据"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 构建查询
        query = "SELECT * FROM historical_option_data WHERE 1=1"
        params = []
        
        if instrument_name:
            query += " AND instrument_name = ?"
            params.append(instrument_name)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(int(start_date.timestamp()))
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(int(end_date.timestamp()))
        
        if underlying_symbol:
            query += " AND underlying_symbol = ?"
            params.append(underlying_symbol)
        
        query += " ORDER BY timestamp ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # 转换为数据模型
        data = []
        for row in rows:
            data.append(HistoricalOptionData(
                id=row[0],
                instrument_name=row[1],
                timestamp=datetime.fromtimestamp(row[2]),
                open_price=Decimal(str(row[3])),
                high_price=Decimal(str(row[4])),
                low_price=Decimal(str(row[5])),
                close_price=Decimal(str(row[6])),
                volume=Decimal(str(row[7])),
                strike_price=Decimal(str(row[8])),
                expiry_date=datetime.fromtimestamp(row[9]),
                option_type=OptionType(row[10]),
                underlying_symbol=row[11],
                data_source=DataSource(row[12])
            ))
        
        logger.debug(f"Queried {len(data)} records from database")
        return data
    
    def _add_to_cache(self, key: str, data: List[HistoricalOptionData]):
        """添加数据到内存缓存"""
        # 估算数据大小（粗略估计）
        data_size = len(data) * 200  # 每条记录约 200 字节
        
        # 如果数据太大，不缓存
        if data_size > self.max_cache_bytes:
            logger.debug(f"Data too large to cache: {data_size} bytes")
            return
        
        # LRU 淘汰
        while self.cache_size_bytes + data_size > self.max_cache_bytes and self.memory_cache:
            oldest_key, oldest_data = self.memory_cache.popitem(last=False)
            oldest_size = len(oldest_data) * 200
            self.cache_size_bytes -= oldest_size
            logger.debug(f"Evicted from cache: {oldest_key} ({oldest_size} bytes)")
        
        # 添加到缓存
        self.memory_cache[key] = data
        self.cache_size_bytes += data_size
        logger.debug(f"Added to cache: {key} ({data_size} bytes)")
    
    def get_available_dates(
        self,
        instrument_name: Optional[str] = None,
        underlying_symbol: Optional[str] = None
    ) -> List[datetime]:
        """
        获取可用的日期列表
        
        Args:
            instrument_name: 期权合约名称
            underlying_symbol: 标的资产符号
            
        Returns:
            日期列表
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        query = "SELECT DISTINCT timestamp FROM historical_option_data WHERE 1=1"
        params = []
        
        if instrument_name:
            query += " AND instrument_name = ?"
            params.append(instrument_name)
        
        if underlying_symbol:
            query += " AND underlying_symbol = ?"
            params.append(underlying_symbol)
        
        query += " ORDER BY timestamp ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        dates = [datetime.fromtimestamp(row[0]) for row in rows]
        
        logger.debug(f"Found {len(dates)} available dates")
        return dates
    
    def get_available_instruments(
        self,
        underlying_symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[str]:
        """
        获取可用的期权合约列表
        
        Args:
            underlying_symbol: 标的资产符号
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            合约名称列表
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        query = "SELECT DISTINCT instrument_name FROM historical_option_data WHERE 1=1"
        params = []
        
        if underlying_symbol:
            query += " AND underlying_symbol = ?"
            params.append(underlying_symbol)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(int(start_date.timestamp()))
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(int(end_date.timestamp()))
        
        query += " ORDER BY instrument_name ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        instruments = [row[0] for row in rows]
        
        logger.debug(f"Found {len(instruments)} available instruments")
        return instruments
    
    def clear_cache(self, clear_database: bool = False):
        """
        清理缓存
        
        Args:
            clear_database: 是否同时清理数据库
        """
        # 清理内存缓存
        self.memory_cache.clear()
        self.cache_size_bytes = 0
        logger.info("Memory cache cleared")
        
        # 清理数据库
        if clear_database:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("DELETE FROM historical_option_data")
            conn.commit()
            conn.close()
            logger.info("Database cleared")
    
    def get_cache_stats(self) -> Dict:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 数据库统计
        cursor.execute("SELECT COUNT(*) FROM historical_option_data")
        db_record_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT instrument_name) FROM historical_option_data")
        db_instrument_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM historical_option_data")
        time_range = cursor.fetchone()
        
        conn.close()
        
        stats = {
            'memory_cache': {
                'entries': len(self.memory_cache),
                'size_bytes': self.cache_size_bytes,
                'size_mb': self.cache_size_bytes / (1024 * 1024),
                'max_size_mb': self.cache_size_mb
            },
            'database': {
                'record_count': db_record_count,
                'instrument_count': db_instrument_count,
                'time_range': (
                    datetime.fromtimestamp(time_range[0]) if time_range[0] else None,
                    datetime.fromtimestamp(time_range[1]) if time_range[1] else None
                )
            }
        }
        
        return stats
    
    def get_coverage_stats(
        self,
        start_date: datetime,
        end_date: datetime,
        underlying_symbol: Optional[str] = None
    ) -> CoverageStats:
        """
        获取数据覆盖率统计
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            underlying_symbol: 标的资产符号
            
        Returns:
            覆盖率统计
        """
        from datetime import timedelta
        
        # 查询数据
        data = self.query_option_data(
            start_date=start_date,
            end_date=end_date,
            underlying_symbol=underlying_symbol,
            use_cache=False
        )
        
        if not data:
            return CoverageStats(
                start_date=start_date,
                end_date=end_date,
                total_days=0,
                days_with_data=0,
                coverage_percentage=0.0,
                missing_dates=[],
                strikes_covered=[],
                expiries_covered=[]
            )
        
        # 按日期分组
        dates_with_data = set()
        strikes = set()
        expiries = set()
        
        for d in data:
            dates_with_data.add(d.timestamp.date())
            strikes.add(d.strike_price)
            expiries.add(d.expiry_date.date())
        
        # 计算总天数
        total_days = (end_date - start_date).days + 1
        days_with_data = len(dates_with_data)
        
        # 找出缺失的日期
        all_dates = {start_date.date() + timedelta(days=i) for i in range(total_days)}
        missing_dates = sorted([
            datetime.combine(d, datetime.min.time()) 
            for d in (all_dates - dates_with_data)
        ])
        
        coverage_percentage = days_with_data / total_days if total_days > 0 else 0.0
        
        stats = CoverageStats(
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            days_with_data=days_with_data,
            coverage_percentage=coverage_percentage,
            missing_dates=missing_dates[:100],  # 限制返回数量
            strikes_covered=sorted(strikes),
            expiries_covered=sorted([datetime.combine(d, datetime.min.time()) for d in expiries])
        )
        
        logger.info(
            f"Coverage stats: {days_with_data}/{total_days} days "
            f"({coverage_percentage:.1%}), "
            f"{len(strikes)} strikes, {len(expiries)} expiries"
        )
        
        return stats
