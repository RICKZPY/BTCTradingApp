"""
测试 CryptoDataDownloader 下载器功能
"""

import asyncio
from datetime import datetime
from src.historical.downloader import CryptoDataDownloader


async def test_downloader_basic():
    """测试基础下载功能"""
    print("=" * 60)
    print("Testing CryptoDataDownloader")
    print("=" * 60)
    
    downloader = CryptoDataDownloader(cache_dir="data/test_historical")
    
    # 测试日期（使用一个已知存在的日期）
    # 注意：这个日期可能需要根据实际可用数据调整
    test_date = datetime(2024, 3, 29)
    
    print(f"\n1. Testing file download check...")
    is_downloaded = downloader.is_file_downloaded(test_date)
    print(f"   File already downloaded: {is_downloaded}")
    
    if not is_downloaded:
        print(f"\n2. Attempting to download data for {test_date.date()}...")
        print("   Note: This will fail if the file doesn't exist on CryptoDataDownload")
        print("   or if you don't have internet connection.")
        
        try:
            path = await downloader.download_data(test_date)
            print(f"   ✓ Downloaded to: {path}")
            
            # 获取解压的文件
            files = downloader.get_extracted_files(test_date)
            print(f"   ✓ Extracted {len(files)} CSV files")
            
            if files:
                print(f"   First few files:")
                for f in files[:3]:
                    print(f"     - {f.name}")
            
        except Exception as e:
            print(f"   ✗ Download failed: {e}")
            print("   This is expected if the file doesn't exist or network is unavailable")
    else:
        print(f"\n2. File already exists, testing extraction...")
        files = downloader.get_extracted_files(test_date)
        print(f"   ✓ Found {len(files)} extracted CSV files")
    
    print(f"\n3. Testing idempotency...")
    print("   Attempting to download the same file again...")
    try:
        path = await downloader.download_data(test_date, force_redownload=False)
        print(f"   ✓ Idempotency check passed - file was not re-downloaded")
    except Exception as e:
        print(f"   ✗ Idempotency test failed: {e}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


async def test_batch_download():
    """测试批量下载功能"""
    print("\n" + "=" * 60)
    print("Testing Batch Download")
    print("=" * 60)
    
    downloader = CryptoDataDownloader(cache_dir="data/test_historical")
    
    # 测试多个日期
    test_dates = [
        datetime(2024, 3, 29),
        datetime(2024, 4, 26),
        datetime(2024, 5, 31),
    ]
    
    print(f"\nAttempting to batch download {len(test_dates)} files...")
    print("Note: This may take a while and some downloads may fail")
    
    try:
        results = await downloader.batch_download(test_dates, max_concurrent=2)
        
        success_count = sum(1 for path in results.values() if path is not None)
        print(f"\n✓ Batch download completed: {success_count}/{len(test_dates)} successful")
        
        for date, path in results.items():
            status = "✓" if path else "✗"
            print(f"  {status} {date.date()}: {path if path else 'Failed'}")
            
    except Exception as e:
        print(f"✗ Batch download failed: {e}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("\nCryptoDataDownloader Test Suite")
    print("================================\n")
    print("WARNING: These tests require internet connection and")
    print("will attempt to download real data from CryptoDataDownload.")
    print("Some tests may fail if data is not available.\n")
    
    # 运行基础测试
    asyncio.run(test_downloader_basic())
    
    # 可选：运行批量下载测试（注释掉以避免长时间运行）
    # asyncio.run(test_batch_download())
