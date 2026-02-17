"""
历史数据管理器
协调下载、转换、验证、存储等所有历史数据操作
"""

import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict
from decimal import Decimal

from src.historical.downloader import CryptoDataDownloader
from src.historical.converter import HistoricalDataConverter
from src.historical.validator import HistoricalDataValidator
from src.historical.cache import HistoricalDataCache
from src.historical.models import (
    HistoricalOptionData, ImportResult, UpdateResult,
    BacktestDataSet, DataQualityReport, CoverageStats
)
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class HistoricalDataManager:
    """历史数据管理器"""
    
    def __init__(
        self,
        download_dir: str = "data/downloads",
        db_path: str = "data/historical_options.db",
        cache_size_mb: int = 100,
        min_free_space_gb: float = 1.0
    ):
        """
        初始化管理器
        
        Args:
            download_dir: 下载目录
            db_path: 数据库路径
            cache_size_mb: 缓存大小（MB）
            min_free_space_gb: 最小可用空间（GB）
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.min_free_space_gb = min_free_space_gb
        
        # 初始化各个组件
        self.downloader = CryptoDataDownloader(cache_dir=str(self.download_dir))
        self.converter = HistoricalDataConverter()
        self.validator = HistoricalDataValidator()
        self.cache = HistoricalDataCache(db_path=db_path, cache_size_mb=cache_size_mb)
        
        logger.info(
            f"HistoricalDataManager initialized: "
            f"download_dir={download_dir}, db_path={db_path}"
        )
        
        # 检查存储空间
        self._check_storage_space()
    
    def import_historical_data(
        self,
        file_paths: Optional[List[Path]] = None,
        download_first: bool = False,
        validate: bool = True,
        generate_report: bool = True
    ) -> ImportResult:
        """
        导入历史数据
        
        完整流程：下载 -> 转换 -> 验证 -> 存储
        
        Args:
            file_paths: CSV 文件路径列表（如果为 None，则处理下载目录中的所有文件）
            download_first: 是否先下载数据
            validate: 是否验证数据
            generate_report: 是否生成质量报告
            
        Returns:
            导入结果
        """
        logger.info("Starting historical data import")
        start_time = time.time()
        
        # 步骤 1: 下载数据（如果需要）
        if download_first:
            logger.info("Step 1: Downloading data...")
            try:
                # 这里需要用户提供具体的下载参数
                # 暂时跳过自动下载
                logger.warning("Auto-download not implemented, skipping...")
            except Exception as e:
                logger.error(f"Download failed: {e}")
        
        # 步骤 2: 确定要处理的文件
        if file_paths is None:
            # 扫描下载目录
            file_paths = list(self.download_dir.glob("**/*.csv"))
            logger.info(f"Found {len(file_paths)} CSV files in download directory")
        
        if not file_paths:
            logger.warning("No files to import")
            return ImportResult(
                success_count=0,
                failure_count=0,
                total_count=0,
                import_duration_seconds=time.time() - start_time
            )
        
        # 步骤 3: 转换数据
        logger.info(f"Step 2: Converting {len(file_paths)} files...")
        all_data = []
        failed_files = []
        
        for file_path in file_paths:
            try:
                data = self.converter.process_file(file_path)
                if data:
                    all_data.extend(data)
                else:
                    failed_files.append(str(file_path))
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                failed_files.append(str(file_path))
        
        logger.info(f"Converted {len(all_data)} records from {len(file_paths)} files")
        
        # 步骤 4: 验证数据（如果需要）
        quality_report = None
        if validate and all_data:
            logger.info("Step 3: Validating data...")
            quality_report = self.validator.generate_quality_report(all_data)
            logger.info(
                f"Validation complete: quality_score={quality_report.quality_score:.1f}, "
                f"issues={len(quality_report.issues)}"
            )
        
        # 步骤 5: 存储数据
        records_imported = 0
        if all_data:
            logger.info(f"Step 4: Storing {len(all_data)} records...")
            try:
                records_imported = self.cache.store_historical_data(all_data)
                logger.info(f"Successfully stored {records_imported} records")
            except Exception as e:
                logger.error(f"Failed to store data: {e}")
        
        # 计算结果
        success_count = len(file_paths) - len(failed_files)
        duration = time.time() - start_time
        
        result = ImportResult(
            success_count=success_count,
            failure_count=len(failed_files),
            total_count=len(file_paths),
            quality_report=quality_report if generate_report else None,
            failed_files=failed_files,
            import_duration_seconds=duration,
            records_imported=records_imported
        )
        
        logger.info(
            f"Import complete: {success_count}/{len(file_paths)} files successful, "
            f"{records_imported} records imported, duration={duration:.1f}s"
        )
        
        return result

    
    def update_historical_data(
        self,
        check_remote: bool = True
    ) -> UpdateResult:
        """
        更新历史数据
        
        检测远程新数据并下载导入
        
        Args:
            check_remote: 是否检查远程新数据
            
        Returns:
            更新结果
        """
        logger.info("Starting historical data update")
        
        new_files_found = 0
        files_downloaded = 0
        files_imported = 0
        errors = []
        
        try:
            # 步骤 1: 检查远程新数据
            if check_remote:
                logger.info("Checking for new data...")
                # 这里需要实现检查逻辑
                # 暂时返回空结果
                logger.warning("Remote check not fully implemented")
            
            # 步骤 2: 下载新文件
            # TODO: 实现下载逻辑
            
            # 步骤 3: 导入新文件
            # TODO: 实现导入逻辑
            
        except Exception as e:
            error_msg = f"Update failed: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        result = UpdateResult(
            new_files_found=new_files_found,
            files_downloaded=files_downloaded,
            files_imported=files_imported,
            errors=errors
        )
        
        logger.info(
            f"Update complete: {new_files_found} new files found, "
            f"{files_downloaded} downloaded, {files_imported} imported"
        )
        
        return result
    
    def get_data_for_backtest(
        self,
        start_date: datetime,
        end_date: datetime,
        instruments: Optional[List[str]] = None,
        underlying_symbol: str = "BTC",
        check_completeness: bool = True
    ) -> BacktestDataSet:
        """
        获取回测数据集
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            instruments: 期权合约列表（如果为 None，则获取所有）
            underlying_symbol: 标的资产符号
            check_completeness: 是否检查数据完整性
            
        Returns:
            回测数据集
        """
        logger.info(
            f"Loading backtest data: {start_date} to {end_date}, "
            f"symbol={underlying_symbol}"
        )
        
        # 查询数据
        if instruments:
            # 按合约查询
            options_data = {}
            for instrument in instruments:
                data = self.cache.query_option_data(
                    instrument_name=instrument,
                    start_date=start_date,
                    end_date=end_date
                )
                if data:
                    options_data[instrument] = data
        else:
            # 查询所有合约
            all_data = self.cache.query_option_data(
                start_date=start_date,
                end_date=end_date,
                underlying_symbol=underlying_symbol
            )
            
            # 按合约分组
            options_data = {}
            for d in all_data:
                if d.instrument_name not in options_data:
                    options_data[d.instrument_name] = []
                options_data[d.instrument_name].append(d)
        
        # 获取覆盖率统计
        coverage_stats = None
        if check_completeness:
            coverage_stats = self.cache.get_coverage_stats(
                start_date=start_date,
                end_date=end_date,
                underlying_symbol=underlying_symbol
            )
            
            # 检查数据缺失
            if coverage_stats.coverage_percentage < 0.9:  # 少于 90% 覆盖率
                logger.warning(
                    f"Low data coverage: {coverage_stats.coverage_percentage:.1%}, "
                    f"missing {len(coverage_stats.missing_dates)} dates"
                )
        
        dataset = BacktestDataSet(
            start_date=start_date,
            end_date=end_date,
            options_data=options_data,
            underlying_data=[],  # TODO: 添加标的资产数据
            coverage_stats=coverage_stats
        )
        
        logger.info(
            f"Loaded backtest data: {len(options_data)} instruments, "
            f"coverage={coverage_stats.coverage_percentage:.1%}" if coverage_stats else ""
        )
        
        return dataset
    
    def get_available_instruments(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        underlying_symbol: Optional[str] = None
    ) -> List[str]:
        """
        获取可用的期权合约列表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            underlying_symbol: 标的资产符号
            
        Returns:
            合约名称列表
        """
        return self.cache.get_available_instruments(
            underlying_symbol=underlying_symbol,
            start_date=start_date,
            end_date=end_date
        )
    
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
        return self.cache.get_available_dates(
            instrument_name=instrument_name,
            underlying_symbol=underlying_symbol
        )
    
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
        return self.cache.get_coverage_stats(
            start_date=start_date,
            end_date=end_date,
            underlying_symbol=underlying_symbol
        )
    
    def validate_data_quality(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        instrument_name: Optional[str] = None
    ) -> DataQualityReport:
        """
        验证数据质量
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            instrument_name: 期权合约名称
            
        Returns:
            数据质量报告
        """
        logger.info("Validating data quality...")
        
        # 查询数据
        data = self.cache.query_option_data(
            instrument_name=instrument_name,
            start_date=start_date,
            end_date=end_date
        )
        
        if not data:
            logger.warning("No data found for validation")
            return DataQualityReport(
                total_records=0,
                missing_records=0,
                anomaly_records=0,
                coverage_percentage=0.0,
                time_range=(datetime.now(), datetime.now()),
                issues=[]
            )
        
        # 生成质量报告
        report = self.validator.generate_quality_report(
            data,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(
            f"Quality validation complete: score={report.quality_score:.1f}, "
            f"issues={len(report.issues)}"
        )
        
        return report
    
    def clear_cache(self, clear_database: bool = False):
        """
        清理缓存
        
        Args:
            clear_database: 是否同时清理数据库
        """
        logger.info(f"Clearing cache (clear_database={clear_database})")
        self.cache.clear_cache(clear_database=clear_database)
    
    def export_data(
        self,
        start_date: datetime,
        end_date: datetime,
        output_path: str,
        format: str = 'csv',
        instruments: Optional[List[str]] = None,
        underlying_symbol: Optional[str] = None,
        compress: bool = False
    ) -> Dict:
        """
        导出历史数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            output_path: 输出文件路径
            format: 导出格式 ('csv', 'json', 'parquet')
            instruments: 期权合约列表（如果为 None，则导出所有）
            underlying_symbol: 标的资产符号
            compress: 是否压缩输出文件
            
        Returns:
            导出结果字典
        """
        import csv
        import json
        import gzip
        
        logger.info(
            f"Exporting data: {start_date} to {end_date}, "
            f"format={format}, compress={compress}"
        )
        
        # 查询数据
        if instruments:
            # 按合约查询
            all_data = []
            for instrument in instruments:
                data = self.cache.query_option_data(
                    instrument_name=instrument,
                    start_date=start_date,
                    end_date=end_date
                )
                all_data.extend(data)
        else:
            # 查询所有数据
            all_data = self.cache.query_option_data(
                start_date=start_date,
                end_date=end_date,
                underlying_symbol=underlying_symbol
            )
        
        if not all_data:
            logger.warning("No data to export")
            return {
                'success': False,
                'records_exported': 0,
                'file_path': None,
                'error': 'No data found for the specified criteria'
            }
        
        # 排序数据
        all_data.sort(key=lambda x: (x.instrument_name, x.timestamp))
        
        # 创建输出目录
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 根据格式导出
        try:
            if format == 'csv':
                self._export_csv(all_data, output_file, compress)
            elif format == 'json':
                self._export_json(all_data, output_file, compress)
            elif format == 'parquet':
                self._export_parquet(all_data, output_file, compress)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # 获取文件大小
            file_size = output_file.stat().st_size
            
            logger.info(
                f"Export complete: {len(all_data)} records exported to {output_file}, "
                f"size={file_size / 1024:.2f} KB"
            )
            
            return {
                'success': True,
                'records_exported': len(all_data),
                'file_path': str(output_file),
                'file_size_bytes': file_size,
                'format': format,
                'compressed': compress
            }
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return {
                'success': False,
                'records_exported': 0,
                'file_path': None,
                'error': str(e)
            }
    
    def _export_csv(
        self,
        data: List[HistoricalOptionData],
        output_file: Path,
        compress: bool
    ):
        """导出为 CSV 格式"""
        # 添加 .gz 扩展名（如果压缩）
        if compress and not str(output_file).endswith('.gz'):
            output_file = Path(str(output_file) + '.gz')
        
        # 打开文件（压缩或非压缩）
        if compress:
            file_handle = gzip.open(output_file, 'wt', encoding='utf-8')
        else:
            file_handle = open(output_file, 'w', encoding='utf-8', newline='')
        
        try:
            writer = csv.writer(file_handle)
            
            # 写入表头
            writer.writerow([
                'instrument_name', 'timestamp', 'open_price', 'high_price',
                'low_price', 'close_price', 'volume', 'strike_price',
                'expiry_date', 'option_type', 'underlying_symbol', 'data_source'
            ])
            
            # 写入数据
            for d in data:
                writer.writerow([
                    d.instrument_name,
                    d.timestamp.isoformat(),
                    float(d.open_price),
                    float(d.high_price),
                    float(d.low_price),
                    float(d.close_price),
                    float(d.volume),
                    float(d.strike_price),
                    d.expiry_date.isoformat(),
                    d.option_type.value,
                    d.underlying_symbol,
                    d.data_source.value
                ])
        finally:
            file_handle.close()
    
    def _export_json(
        self,
        data: List[HistoricalOptionData],
        output_file: Path,
        compress: bool
    ):
        """导出为 JSON 格式"""
        import json
        import gzip
        
        # 添加 .gz 扩展名（如果压缩）
        if compress and not str(output_file).endswith('.gz'):
            output_file = Path(str(output_file) + '.gz')
        
        # 转换为字典列表
        data_dicts = []
        for d in data:
            data_dicts.append({
                'instrument_name': d.instrument_name,
                'timestamp': d.timestamp.isoformat(),
                'open_price': float(d.open_price),
                'high_price': float(d.high_price),
                'low_price': float(d.low_price),
                'close_price': float(d.close_price),
                'volume': float(d.volume),
                'strike_price': float(d.strike_price),
                'expiry_date': d.expiry_date.isoformat(),
                'option_type': d.option_type.value,
                'underlying_symbol': d.underlying_symbol,
                'data_source': d.data_source.value
            })
        
        # 写入文件
        if compress:
            with gzip.open(output_file, 'wt', encoding='utf-8') as f:
                json.dump(data_dicts, f, indent=2)
        else:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data_dicts, f, indent=2)
    
    def _export_parquet(
        self,
        data: List[HistoricalOptionData],
        output_file: Path,
        compress: bool
    ):
        """导出为 Parquet 格式"""
        try:
            import pandas as pd
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError:
            raise ImportError(
                "Parquet export requires pandas and pyarrow. "
                "Install with: pip install pandas pyarrow"
            )
        
        # 转换为 DataFrame
        data_dicts = []
        for d in data:
            data_dicts.append({
                'instrument_name': d.instrument_name,
                'timestamp': d.timestamp,
                'open_price': float(d.open_price),
                'high_price': float(d.high_price),
                'low_price': float(d.low_price),
                'close_price': float(d.close_price),
                'volume': float(d.volume),
                'strike_price': float(d.strike_price),
                'expiry_date': d.expiry_date,
                'option_type': d.option_type.value,
                'underlying_symbol': d.underlying_symbol,
                'data_source': d.data_source.value
            })
        
        df = pd.DataFrame(data_dicts)
        
        # 写入 Parquet 文件
        compression = 'snappy' if compress else None
        df.to_parquet(output_file, compression=compression, index=False)
    
    def _check_storage_space(self, required_gb: float = None) -> bool:
        """
        检查存储空间
        
        Args:
            required_gb: 需要的空间（GB），如果为 None 则使用最小值
            
        Returns:
            是否有足够空间
            
        Raises:
            RuntimeError: 如果空间不足
        """
        required = required_gb or self.min_free_space_gb
        
        # 获取磁盘使用情况
        stat = shutil.disk_usage(self.download_dir)
        free_gb = stat.free / (1024 ** 3)
        total_gb = stat.total / (1024 ** 3)
        used_gb = stat.used / (1024 ** 3)
        
        logger.info(
            f"Storage check: free={free_gb:.2f}GB, "
            f"used={used_gb:.2f}GB, total={total_gb:.2f}GB"
        )
        
        if free_gb < required:
            error_msg = (
                f"Insufficient storage space: {free_gb:.2f}GB free, "
                f"{required:.2f}GB required. "
                f"Please free up space or clear old data."
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # 警告如果空间不足 2GB
        if free_gb < 2.0:
            logger.warning(
                f"Low storage space: {free_gb:.2f}GB free. "
                f"Consider clearing old data."
            )
        
        return True
    
    def get_storage_info(self) -> Dict:
        """
        获取存储信息
        
        Returns:
            存储信息字典
        """
        stat = shutil.disk_usage(self.download_dir)
        
        return {
            'free_gb': stat.free / (1024 ** 3),
            'used_gb': stat.used / (1024 ** 3),
            'total_gb': stat.total / (1024 ** 3),
            'free_percentage': (stat.free / stat.total) * 100,
            'min_required_gb': self.min_free_space_gb
        }
    
    def handle_error(
        self,
        error: Exception,
        operation: str,
        context: Optional[Dict] = None,
        notify: bool = True
    ) -> Dict:
        """
        处理错误
        
        Args:
            error: 异常对象
            operation: 操作名称
            context: 上下文信息
            notify: 是否发送通知
            
        Returns:
            错误信息字典
        """
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'operation': operation,
            'timestamp': datetime.now().isoformat(),
            'context': context or {}
        }
        
        # 记录错误
        logger.error(
            f"Error in {operation}",
            error_type=error_info['error_type'],
            error_message=error_info['error_message'],
            context=error_info['context']
        )
        
        # 发送通知（如果需要）
        if notify:
            self._send_error_notification(error_info)
        
        return error_info
    
    def _send_error_notification(self, error_info: Dict):
        """
        发送错误通知
        
        Args:
            error_info: 错误信息
        """
        # 这里可以实现各种通知方式：
        # - 邮件通知
        # - Slack/Discord webhook
        # - 系统通知
        # - 写入专门的错误日志文件
        
        # 目前只记录到日志
        logger.warning(
            "Error notification",
            **error_info
        )
        
        # TODO: 实现实际的通知机制
        # 例如：
        # - 发送邮件
        # - 调用 webhook
        # - 写入监控系统
    
    def get_stats(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        cache_stats = self.cache.get_cache_stats()
        storage_info = self.get_storage_info()
        
        stats = {
            'cache': cache_stats,
            'storage': storage_info,
            'download_dir': str(self.download_dir),
            'csv_files': len(list(self.download_dir.glob("**/*.csv")))
        }
        
        return stats
