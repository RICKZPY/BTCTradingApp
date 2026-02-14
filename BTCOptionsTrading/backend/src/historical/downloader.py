"""
CryptoDataDownload 数据下载器
从 CryptoDataDownload 网站下载 Deribit 期权历史数据
"""

import asyncio
import aiohttp
import zipfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from decimal import Decimal
import time

from src.historical.models import DataFileInfo, DataSource
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class CryptoDataDownloader:
    """CryptoDataDownload 数据下载器"""
    
    # CryptoDataDownload 基础 URL
    BASE_URL = "https://www.cryptodatadownload.com/data/deribit/"
    
    # 重试配置
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # 秒
    RETRY_BACKOFF_MULTIPLIER = 2  # 指数退避倍数
    
    def __init__(self, cache_dir: str = "data/historical"):
        """
        初始化下载器
        
        Args:
            cache_dir: 缓存目录路径
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 下载进度跟踪
        self.download_progress: Dict[str, float] = {}
        
        # 下载历史记录（用于幂等性检查）
        self.download_history: Dict[str, datetime] = {}
        
        logger.info(f"CryptoDataDownloader initialized with cache_dir: {self.cache_dir}")
    
    async def list_available_data(
        self,
        symbol: str = "BTC"
    ) -> List[DataFileInfo]:
        """
        列出可用的历史数据文件
        
        Args:
            symbol: 标的符号（BTC, ETH等）
            
        Returns:
            数据文件信息列表
        """
        logger.info(f"Listing available data for {symbol}")
        
        # 注意：CryptoDataDownload 没有提供 API 来列出文件
        # 这里我们需要手动维护一个已知的文件列表
        # 或者通过网页爬取来获取（需要额外的实现）
        
        # 暂时返回一个示例列表
        # 实际使用时，用户需要手动指定要下载的到期日
        available_files = []
        
        logger.warning("list_available_data is not fully implemented. "
                      "CryptoDataDownload does not provide an API to list files. "
                      "Users need to manually specify expiry dates to download.")
        
        return available_files
    
    async def download_data(
        self,
        expiry_date: datetime,
        symbol: str = "BTC",
        force_redownload: bool = False
    ) -> Path:
        """
        下载指定到期日的期权数据（带重试和幂等性）
        
        Args:
            expiry_date: 期权到期日
            symbol: 标的符号
            force_redownload: 是否强制重新下载
            
        Returns:
            下载文件的本地路径
        """
        # 构建文件名（根据 CryptoDataDownload 的命名规则）
        # 格式示例: Deribit_BTCUSD_20240329.zip
        date_str = expiry_date.strftime("%Y%m%d")
        filename = f"Deribit_{symbol}USD_{date_str}.zip"
        local_path = self.cache_dir / filename
        
        # 幂等性检查：文件是否已存在且有效
        if local_path.exists() and not force_redownload:
            # 验证现有文件
            if self._verify_zip_file(local_path):
                logger.info(f"File already exists and is valid: {local_path}, skipping download")
                self.download_history[filename] = datetime.now()
                return local_path
            else:
                logger.warning(f"Existing file is invalid, will re-download: {local_path}")
                local_path.unlink()
        
        # 构建下载 URL
        url = f"{self.BASE_URL}{filename}"
        
        # 带重试的下载
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                logger.info(f"Downloading {filename} from {url} (attempt {attempt + 1}/{self.MAX_RETRIES})")
                
                await self._download_file(url, local_path, filename)
                
                # 验证下载的文件
                if not self._verify_zip_file(local_path):
                    raise Exception(f"Downloaded file is not a valid ZIP: {local_path}")
                
                # 解压文件
                extract_dir = self.cache_dir / f"{symbol}_{date_str}"
                self._extract_zip(local_path, extract_dir)
                
                # 记录成功下载
                self.download_history[filename] = datetime.now()
                logger.info(f"Successfully downloaded and extracted {filename}")
                
                return local_path
                
            except asyncio.TimeoutError as e:
                last_error = e
                logger.error(f"Download timeout for {url} (attempt {attempt + 1}/{self.MAX_RETRIES})")
                
            except aiohttp.ClientError as e:
                last_error = e
                logger.error(f"Network error downloading {url}: {str(e)} (attempt {attempt + 1}/{self.MAX_RETRIES})")
                
            except Exception as e:
                last_error = e
                logger.error(f"Failed to download {url}: {str(e)} (attempt {attempt + 1}/{self.MAX_RETRIES})")
            
            # 清理部分下载的文件
            if local_path.exists():
                try:
                    local_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to clean up partial download: {e}")
            
            # 如果不是最后一次尝试，等待后重试（指数退避）
            if attempt < self.MAX_RETRIES - 1:
                delay = self.RETRY_DELAY * (self.RETRY_BACKOFF_MULTIPLIER ** attempt)
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
        
        # 所有重试都失败
        error_msg = f"Failed to download {filename} after {self.MAX_RETRIES} attempts"
        logger.error(error_msg)
        if last_error:
            raise Exception(f"{error_msg}: {str(last_error)}") from last_error
        else:
            raise Exception(error_msg)
    
    async def _download_file(self, url: str, local_path: Path, filename: str):
        """
        执行实际的文件下载
        
        Args:
            url: 下载 URL
            local_path: 本地保存路径
            filename: 文件名（用于进度跟踪）
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=300)) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                
                # 获取文件大小
                total_size = int(response.headers.get('content-length', 0))
                
                # 下载文件
                downloaded_size = 0
                with open(local_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 更新进度
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            self.download_progress[filename] = progress
                            
                            # 每 10% 记录一次日志
                            if int(progress) % 10 == 0 and int(progress) > 0:
                                logger.debug(f"Download progress for {filename}: {progress:.1f}%")
    
    def _verify_zip_file(self, file_path: Path) -> bool:
        """
        验证 ZIP 文件的完整性
        
        Args:
            file_path: ZIP 文件路径
            
        Returns:
            是否为有效的 ZIP 文件
        """
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # 测试 ZIP 文件完整性
                bad_file = zip_ref.testzip()
                if bad_file:
                    logger.error(f"Corrupted file in ZIP: {bad_file}")
                    return False
                
                # 检查是否包含 CSV 文件
                csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                if not csv_files:
                    logger.error("No CSV files found in ZIP")
                    return False
                
                logger.info(f"ZIP file verified, contains {len(csv_files)} CSV files")
                return True
                
        except zipfile.BadZipFile:
            logger.error(f"Invalid ZIP file: {file_path}")
            return False
        except Exception as e:
            logger.error(f"Error verifying ZIP file: {str(e)}")
            return False
    
    def _extract_zip(self, zip_path: Path, extract_dir: Path) -> List[Path]:
        """
        解压 ZIP 文件
        
        Args:
            zip_path: ZIP 文件路径
            extract_dir: 解压目标目录
            
        Returns:
            解压出的文件路径列表
        """
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        extracted_files = []
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 解压所有文件
                zip_ref.extractall(extract_dir)
                
                # 获取解压的文件列表
                for filename in zip_ref.namelist():
                    file_path = extract_dir / filename
                    if file_path.exists():
                        extracted_files.append(file_path)
                
                logger.info(f"Extracted {len(extracted_files)} files to {extract_dir}")
                
        except Exception as e:
            logger.error(f"Failed to extract ZIP file: {str(e)}")
            raise
        
        return extracted_files
    
    async def batch_download(
        self,
        expiry_dates: List[datetime],
        symbol: str = "BTC",
        max_concurrent: int = 3
    ) -> Dict[datetime, Optional[Path]]:
        """
        批量下载多个到期日的数据
        
        Args:
            expiry_dates: 到期日列表
            symbol: 标的符号
            max_concurrent: 最大并发下载数
            
        Returns:
            到期日到文件路径的映射（失败的为 None）
        """
        logger.info(f"Starting batch download for {len(expiry_dates)} expiry dates with max_concurrent={max_concurrent}")
        
        results: Dict[datetime, Optional[Path]] = {}
        semaphore = asyncio.Semaphore(max_concurrent)
        
        # 统计信息
        total_count = len(expiry_dates)
        completed_count = 0
        success_count = 0
        failure_count = 0
        
        async def download_with_semaphore(expiry_date: datetime):
            nonlocal completed_count, success_count, failure_count
            
            async with semaphore:
                try:
                    path = await self.download_data(expiry_date, symbol)
                    results[expiry_date] = path
                    success_count += 1
                    logger.info(f"✓ Successfully downloaded data for {expiry_date.date()} ({success_count}/{total_count})")
                except Exception as e:
                    results[expiry_date] = None
                    failure_count += 1
                    logger.error(f"✗ Failed to download data for {expiry_date.date()}: {str(e)} ({failure_count} failures)")
                finally:
                    completed_count += 1
                    progress = (completed_count / total_count) * 100
                    logger.info(f"Batch progress: {completed_count}/{total_count} ({progress:.1f}%)")
        
        # 创建所有下载任务
        tasks = [download_with_semaphore(expiry_date) for expiry_date in expiry_dates]
        
        # 并发执行
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"Batch download completed: {success_count} successful, {failure_count} failed out of {total_count} total")
        
        return results
    
    def get_download_progress(self, filename: str) -> float:
        """
        获取下载进度
        
        Args:
            filename: 文件名
            
        Returns:
            下载进度（0-100）
        """
        return self.download_progress.get(filename, 0.0)
    
    def is_file_downloaded(self, expiry_date: datetime, symbol: str = "BTC") -> bool:
        """
        检查文件是否已下载
        
        Args:
            expiry_date: 到期日
            symbol: 标的符号
            
        Returns:
            文件是否已下载且有效
        """
        date_str = expiry_date.strftime("%Y%m%d")
        filename = f"Deribit_{symbol}USD_{date_str}.zip"
        local_path = self.cache_dir / filename
        
        if not local_path.exists():
            return False
        
        # 验证文件有效性
        return self._verify_zip_file(local_path)
    
    def get_extracted_files(self, expiry_date: datetime, symbol: str = "BTC") -> List[Path]:
        """
        获取已解压的文件列表
        
        Args:
            expiry_date: 到期日
            symbol: 标的符号
            
        Returns:
            文件路径列表
        """
        date_str = expiry_date.strftime("%Y%m%d")
        extract_dir = self.cache_dir / f"{symbol}_{date_str}"
        
        if not extract_dir.exists():
            return []
        
        # 查找所有 CSV 文件
        csv_files = list(extract_dir.glob("*.csv"))
        
        logger.info(f"Found {len(csv_files)} CSV files in {extract_dir}")
        
        return csv_files
    
    def clear_cache(self, older_than_days: Optional[int] = None):
        """
        清理缓存
        
        Args:
            older_than_days: 清理多少天前的文件（None表示清理全部）
        """
        logger.info(f"Clearing cache in {self.cache_dir}")
        
        if older_than_days is None:
            # 清理所有文件
            import shutil
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info("All cache cleared")
        else:
            # 清理旧文件
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(days=older_than_days)
            
            removed_count = 0
            for file_path in self.cache_dir.rglob("*"):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_path.unlink()
                        removed_count += 1
            
            logger.info(f"Removed {removed_count} old files from cache")


# 用于测试的辅助函数
async def test_downloader():
    """测试下载器功能"""
    downloader = CryptoDataDownloader()
    
    # 测试下载单个文件
    test_date = datetime(2024, 3, 29)
    
    try:
        path = await downloader.download_data(test_date)
        print(f"Downloaded to: {path}")
        
        # 获取解压的文件
        files = downloader.get_extracted_files(test_date)
        print(f"Extracted files: {len(files)}")
        for f in files[:5]:  # 只显示前5个
            print(f"  - {f.name}")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_downloader())
