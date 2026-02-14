"""
历史数据转换器
将 CryptoDataDownload 的 CSV 格式数据转换为系统内部格式
"""

import csv
import re
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

from src.historical.models import (
    OptionOHLCV, OptionInfo, HistoricalOptionData, 
    DataSource, ValidationResult
)
from src.core.models import OptionType
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class HistoricalDataConverter:
    """历史数据转换器"""
    
    # 文件名正则表达式
    # 格式: Deribit_BTCUSD_20240329_50000_C.csv
    FILENAME_PATTERN = re.compile(
        r'Deribit_([A-Z]+)USD_(\d{8})_(\d+)_([CP])\.csv'
    )
    
    def __init__(self):
        """初始化转换器"""
        logger.info("HistoricalDataConverter initialized")
    
    def parse_csv_file(self, csv_path: Path) -> List[OptionOHLCV]:
        """
        解析 CSV 文件
        
        Args:
            csv_path: CSV 文件路径
            
        Returns:
            期权 OHLCV 数据列表
        """
        logger.info(f"Parsing CSV file: {csv_path}")
        
        ohlcv_data = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                # 跳过可能的头部注释行
                lines = f.readlines()
                
                # 查找实际的 CSV 头部
                header_index = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('unix') or line.strip().startswith('timestamp'):
                        header_index = i
                        break
                
                # 从头部开始解析
                reader = csv.DictReader(lines[header_index:])
                
                for row_num, row in enumerate(reader, start=header_index + 1):
                    try:
                        # 解析时间戳
                        timestamp = self._parse_timestamp(row)
                        
                        # 解析 OHLCV 数据
                        ohlcv = OptionOHLCV(
                            timestamp=timestamp,
                            open=Decimal(str(row.get('open', row.get('Open', '0')))),
                            high=Decimal(str(row.get('high', row.get('High', '0')))),
                            low=Decimal(str(row.get('low', row.get('Low', '0')))),
                            close=Decimal(str(row.get('close', row.get('Close', '0')))),
                            volume=Decimal(str(row.get('volume', row.get('Volume', '0'))))
                        )
                        
                        ohlcv_data.append(ohlcv)
                        
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Failed to parse row {row_num} in {csv_path.name}: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"Unexpected error parsing row {row_num} in {csv_path.name}: {e}")
                        continue
            
            logger.info(f"Successfully parsed {len(ohlcv_data)} records from {csv_path.name}")
            return ohlcv_data
            
        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to parse CSV file {csv_path}: {str(e)}")
            raise
    
    def _parse_timestamp(self, row: dict) -> datetime:
        """
        解析时间戳
        
        Args:
            row: CSV 行数据
            
        Returns:
            datetime 对象
        """
        # 尝试不同的时间戳字段名
        timestamp_fields = ['unix', 'timestamp', 'date', 'Date', 'Timestamp']
        
        for field in timestamp_fields:
            if field in row and row[field]:
                value = row[field].strip()
                
                # 尝试解析 Unix 时间戳
                if value.isdigit():
                    return datetime.fromtimestamp(int(value))
                
                # 尝试解析 ISO 格式
                try:
                    return datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    pass
                
                # 尝试其他常见格式
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S']:
                    try:
                        return datetime.strptime(value, fmt)
                    except:
                        continue
        
        raise ValueError(f"Could not parse timestamp from row: {row}")
    
    def extract_option_info(self, filename: str) -> OptionInfo:
        """
        从文件名提取期权信息
        
        文件名格式: Deribit_BTCUSD_20240329_50000_C.csv
        
        Args:
            filename: 文件名
            
        Returns:
            期权信息
        """
        match = self.FILENAME_PATTERN.match(filename)
        
        if not match:
            raise ValueError(f"Invalid filename format: {filename}")
        
        symbol, date_str, strike_str, option_type_str = match.groups()
        
        # 解析日期
        expiry_date = datetime.strptime(date_str, '%Y%m%d')
        
        # 解析执行价
        strike_price = Decimal(strike_str)
        
        # 解析期权类型
        option_type = OptionType.CALL if option_type_str == 'C' else OptionType.PUT
        
        option_info = OptionInfo(
            symbol=symbol,
            expiry_date=expiry_date,
            strike_price=strike_price,
            option_type=option_type
        )
        
        logger.debug(f"Extracted option info from {filename}: {option_info.to_instrument_name()}")
        
        return option_info
    
    def convert_to_internal_format(
        self,
        ohlcv_data: List[OptionOHLCV],
        option_info: OptionInfo,
        data_source: DataSource = DataSource.CRYPTO_DATA_DOWNLOAD
    ) -> List[HistoricalOptionData]:
        """
        转换为系统内部格式
        
        Args:
            ohlcv_data: OHLCV 数据列表
            option_info: 期权信息
            data_source: 数据源
            
        Returns:
            系统内部格式的历史数据列表
        """
        logger.info(f"Converting {len(ohlcv_data)} records to internal format")
        
        instrument_name = option_info.to_instrument_name()
        historical_data = []
        
        for ohlcv in ohlcv_data:
            try:
                data = HistoricalOptionData(
                    instrument_name=instrument_name,
                    timestamp=ohlcv.timestamp,
                    open_price=ohlcv.open,
                    high_price=ohlcv.high,
                    low_price=ohlcv.low,
                    close_price=ohlcv.close,
                    volume=ohlcv.volume,
                    strike_price=option_info.strike_price,
                    expiry_date=option_info.expiry_date,
                    option_type=option_info.option_type,
                    underlying_symbol=option_info.symbol,
                    data_source=data_source
                )
                
                historical_data.append(data)
                
            except Exception as e:
                logger.warning(f"Failed to convert OHLCV data: {e}")
                continue
        
        logger.info(f"Successfully converted {len(historical_data)} records")
        return historical_data
    
    def process_file(
        self,
        csv_path: Path,
        data_source: DataSource = DataSource.CRYPTO_DATA_DOWNLOAD
    ) -> List[HistoricalOptionData]:
        """
        处理单个 CSV 文件（解析 + 转换）
        
        Args:
            csv_path: CSV 文件路径
            data_source: 数据源
            
        Returns:
            历史数据列表
        """
        logger.info(f"Processing file: {csv_path}")
        
        try:
            # 提取期权信息
            option_info = self.extract_option_info(csv_path.name)
            
            # 解析 CSV
            ohlcv_data = self.parse_csv_file(csv_path)
            
            # 转换为内部格式
            historical_data = self.convert_to_internal_format(
                ohlcv_data, option_info, data_source
            )
            
            logger.info(f"Successfully processed {csv_path.name}: {len(historical_data)} records")
            return historical_data
            
        except Exception as e:
            logger.error(f"Failed to process file {csv_path}: {str(e)}")
            # 不抛出异常，返回空列表以继续处理其他文件
            return []
    
    def process_files_parallel(
        self,
        csv_paths: List[Path],
        max_workers: Optional[int] = None
    ) -> List[HistoricalOptionData]:
        """
        并行处理多个 CSV 文件
        
        Args:
            csv_paths: CSV 文件路径列表
            max_workers: 最大工作进程数（None 表示使用 CPU 核心数）
            
        Returns:
            所有文件的历史数据列表
        """
        if max_workers is None:
            max_workers = mp.cpu_count()
        
        logger.info(f"Processing {len(csv_paths)} files in parallel with {max_workers} workers")
        
        all_data = []
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_path = {
                executor.submit(self.process_file, path): path 
                for path in csv_paths
            }
            
            # 收集结果
            completed = 0
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                completed += 1
                
                try:
                    data = future.result()
                    all_data.extend(data)
                    logger.info(f"Progress: {completed}/{len(csv_paths)} files processed")
                except Exception as e:
                    logger.error(f"Failed to process {path}: {e}")
        
        logger.info(f"Parallel processing completed: {len(all_data)} total records from {len(csv_paths)} files")
        return all_data
    
    def validate_converted_data(
        self,
        data: List[HistoricalOptionData]
    ) -> ValidationResult:
        """
        验证转换后的数据
        
        Args:
            data: 历史数据列表
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        if not data:
            errors.append("No data to validate")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        # 检查时间戳排序
        timestamps = [d.timestamp for d in data]
        if timestamps != sorted(timestamps):
            warnings.append("Data is not sorted by timestamp")
        
        # 检查重复时间戳
        if len(timestamps) != len(set(timestamps)):
            warnings.append("Duplicate timestamps found")
        
        # 检查价格有效性
        for i, d in enumerate(data):
            if d.low_price > d.high_price:
                errors.append(f"Record {i}: Low price > High price")
            if d.open_price < d.low_price or d.open_price > d.high_price:
                errors.append(f"Record {i}: Open price outside Low-High range")
            if d.close_price < d.low_price or d.close_price > d.high_price:
                errors.append(f"Record {i}: Close price outside Low-High range")
            if d.volume < 0:
                errors.append(f"Record {i}: Negative volume")
        
        is_valid = len(errors) == 0
        
        logger.info(f"Validation completed: {len(errors)} errors, {len(warnings)} warnings")
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            stats={
                'total_records': len(data),
                'time_range': (min(timestamps), max(timestamps)) if timestamps else None
            }
        )


# 用于并行处理的辅助函数
def _process_file_worker(csv_path: Path) -> List[HistoricalOptionData]:
    """
    工作进程函数（用于并行处理）
    
    Args:
        csv_path: CSV 文件路径
        
    Returns:
        历史数据列表
    """
    converter = HistoricalDataConverter()
    return converter.process_file(csv_path)
