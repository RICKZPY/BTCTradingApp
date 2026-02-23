"""
测试 HistoricalDataManager 管理器功能
"""

import csv
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import List

from src.historical.manager import HistoricalDataManager


def create_test_csv_files(temp_dir: Path, count: int = 3) -> List[Path]:
    """创建测试 CSV 文件"""
    files = []
    
    filenames = [
        "Deribit_BTCUSD_20240329_50000_C.csv",
        "Deribit_BTCUSD_20240329_51000_C.csv",
        "Deribit_BTCUSD_20240329_49000_P.csv",
    ]
    
    for i, filename in enumerate(filenames[:count]):
        filepath = temp_dir / filename
        
        # 创建测试数据
        test_data = []
        for j in range(10):
            timestamp = 1711670400 + (j * 3600)  # 每小时一条
            test_data.append({
                'unix': str(timestamp),
                'open': f'{0.05 + i * 0.001 + j * 0.0001:.6f}',
                'high': f'{0.055 + i * 0.001 + j * 0.0001:.6f}',
                'low': f'{0.047 + i * 0.001 + j * 0.0001:.6f}',
                'close': f'{0.052 + i * 0.001 + j * 0.0001:.6f}',
                'volume': f'{100 + j * 10}'
            })
        
        # 写入 CSV
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['unix', 'open', 'high', 'low', 'close', 'volume'])
            writer.writeheader()
            writer.writerows(test_data)
        
        files.append(filepath)
        print(f"  Created: {filename}")
    
    return files


def test_import_data():
    """测试数据导入"""
    print("\n" + "=" * 60)
    print("Test 1: Import Historical Data")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    download_dir = Path(temp_dir) / "downloads"
    download_dir.mkdir()
    db_path = Path(temp_dir) / "test.db"
    
    try:
        # 创建测试文件
        print("\n1.1 Creating test CSV files...")
        test_files = create_test_csv_files(download_dir, count=3)
        
        # 初始化管理器
        print("\n1.2 Initializing manager...")
        manager = HistoricalDataManager(
            download_dir=str(download_dir),
            db_path=str(db_path),
            cache_size_mb=10
        )
        
        # 导入数据
        print("\n1.3 Importing data...")
        result = manager.import_historical_data(
            file_paths=test_files,
            validate=True,
            generate_report=True
        )
        
        print(f"\n  Import Results:")
        print(f"    Success: {result.success_count}/{result.total_count} files")
        print(f"    Records imported: {result.records_imported}")
        print(f"    Duration: {result.import_duration_seconds:.2f}s")
        
        if result.quality_report:
            print(f"    Quality score: {result.quality_report.quality_score:.1f}/100")
            print(f"    Coverage: {result.quality_report.coverage_percentage:.1%}")
        
        if result.failed_files:
            print(f"    Failed files: {len(result.failed_files)}")
        
        assert result.success_count == 3, f"Expected 3 successful imports, got {result.success_count}"
        assert result.records_imported == 30, f"Expected 30 records, got {result.records_imported}"
        
        print("\n✓ Import data test passed!")
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def test_get_backtest_data():
    """测试获取回测数据"""
    print("\n" + "=" * 60)
    print("Test 2: Get Backtest Data")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    download_dir = Path(temp_dir) / "downloads"
    download_dir.mkdir()
    db_path = Path(temp_dir) / "test.db"
    
    try:
        # 创建并导入测试数据
        print("\n2.1 Setting up test data...")
        test_files = create_test_csv_files(download_dir, count=3)
        
        manager = HistoricalDataManager(
            download_dir=str(download_dir),
            db_path=str(db_path)
        )
        
        manager.import_historical_data(file_paths=test_files, validate=False)
        
        # 获取回测数据
        print("\n2.2 Loading backtest data...")
        start_date = datetime(2024, 3, 29, 0, 0, 0)
        end_date = datetime(2024, 3, 29, 23, 0, 0)
        
        dataset = manager.get_data_for_backtest(
            start_date=start_date,
            end_date=end_date,
            underlying_symbol="BTC",
            check_completeness=True
        )
        
        print(f"\n  Backtest Dataset:")
        print(f"    Time range: {dataset.start_date} to {dataset.end_date}")
        print(f"    Instruments: {len(dataset.options_data)}")
        
        for instrument, data in dataset.options_data.items():
            print(f"      {instrument}: {len(data)} records")
        
        if dataset.coverage_stats:
            print(f"    Coverage: {dataset.coverage_stats.coverage_percentage:.1%}")
            print(f"    Days with data: {dataset.coverage_stats.days_with_data}/{dataset.coverage_stats.total_days}")
        
        assert len(dataset.options_data) == 3, f"Expected 3 instruments, got {len(dataset.options_data)}"
        
        print("\n✓ Get backtest data test passed!")
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def test_available_data_queries():
    """测试可用数据查询"""
    print("\n" + "=" * 60)
    print("Test 3: Available Data Queries")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    download_dir = Path(temp_dir) / "downloads"
    download_dir.mkdir()
    db_path = Path(temp_dir) / "test.db"
    
    try:
        # 创建并导入测试数据
        print("\n3.1 Setting up test data...")
        test_files = create_test_csv_files(download_dir, count=3)
        
        manager = HistoricalDataManager(
            download_dir=str(download_dir),
            db_path=str(db_path)
        )
        
        manager.import_historical_data(file_paths=test_files, validate=False)
        
        # 查询可用合约
        print("\n3.2 Querying available instruments...")
        instruments = manager.get_available_instruments(underlying_symbol="BTC")
        print(f"  Found {len(instruments)} instruments:")
        for inst in instruments:
            print(f"    - {inst}")
        
        assert len(instruments) == 3, f"Expected 3 instruments, got {len(instruments)}"
        
        # 查询可用日期
        print("\n3.3 Querying available dates...")
        dates = manager.get_available_dates(underlying_symbol="BTC")
        print(f"  Found {len(dates)} unique timestamps")
        print(f"  First: {dates[0]}")
        print(f"  Last: {dates[-1]}")
        
        print("\n✓ Available data queries test passed!")
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def test_coverage_stats():
    """测试覆盖率统计"""
    print("\n" + "=" * 60)
    print("Test 4: Coverage Statistics")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    download_dir = Path(temp_dir) / "downloads"
    download_dir.mkdir()
    db_path = Path(temp_dir) / "test.db"
    
    try:
        # 创建并导入测试数据
        print("\n4.1 Setting up test data...")
        test_files = create_test_csv_files(download_dir, count=2)
        
        manager = HistoricalDataManager(
            download_dir=str(download_dir),
            db_path=str(db_path)
        )
        
        manager.import_historical_data(file_paths=test_files, validate=False)
        
        # 获取覆盖率统计
        print("\n4.2 Calculating coverage...")
        stats = manager.get_coverage_stats(
            start_date=datetime(2024, 3, 29, 0, 0, 0),
            end_date=datetime(2024, 3, 29, 23, 0, 0),
            underlying_symbol="BTC"
        )
        
        print(f"\n  Coverage Statistics:")
        print(f"    Total days: {stats.total_days}")
        print(f"    Days with data: {stats.days_with_data}")
        print(f"    Coverage: {stats.coverage_percentage:.1%}")
        print(f"    Strikes covered: {len(stats.strikes_covered)}")
        print(f"    Missing dates: {len(stats.missing_dates)}")
        
        print("\n✓ Coverage statistics test passed!")
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def test_data_quality_validation():
    """测试数据质量验证"""
    print("\n" + "=" * 60)
    print("Test 5: Data Quality Validation")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    download_dir = Path(temp_dir) / "downloads"
    download_dir.mkdir()
    db_path = Path(temp_dir) / "test.db"
    
    try:
        # 创建并导入测试数据
        print("\n5.1 Setting up test data...")
        test_files = create_test_csv_files(download_dir, count=2)
        
        manager = HistoricalDataManager(
            download_dir=str(download_dir),
            db_path=str(db_path)
        )
        
        manager.import_historical_data(file_paths=test_files, validate=False)
        
        # 验证数据质量
        print("\n5.2 Validating data quality...")
        report = manager.validate_data_quality(
            start_date=datetime(2024, 3, 29, 0, 0, 0),
            end_date=datetime(2024, 3, 29, 23, 0, 0)
        )
        
        print(f"\n  Quality Report:")
        print(f"    Total records: {report.total_records}")
        print(f"    Quality score: {report.quality_score:.1f}/100")
        print(f"    Coverage: {report.coverage_percentage:.1%}")
        print(f"    Issues: {len(report.issues)}")
        
        if report.issues:
            print(f"\n  Sample issues:")
            for issue in report.issues[:3]:
                print(f"    - [{issue.severity.value}] {issue.message}")
        
        print("\n✓ Data quality validation test passed!")
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def test_manager_stats():
    """测试管理器统计"""
    print("\n" + "=" * 60)
    print("Test 6: Manager Statistics")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    download_dir = Path(temp_dir) / "downloads"
    download_dir.mkdir()
    db_path = Path(temp_dir) / "test.db"
    
    try:
        # 创建并导入测试数据
        print("\n6.1 Setting up test data...")
        test_files = create_test_csv_files(download_dir, count=2)
        
        manager = HistoricalDataManager(
            download_dir=str(download_dir),
            db_path=str(db_path)
        )
        
        manager.import_historical_data(file_paths=test_files, validate=False)
        
        # 获取统计信息
        print("\n6.2 Getting statistics...")
        stats = manager.get_stats()
        
        print(f"\n  Manager Statistics:")
        print(f"    Download directory: {stats['download_dir']}")
        print(f"    CSV files: {stats['csv_files']}")
        print(f"    Database records: {stats['cache']['database']['record_count']}")
        print(f"    Memory cache entries: {stats['cache']['memory_cache']['entries']}")
        
        print("\n✓ Manager statistics test passed!")
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("HistoricalDataManager Test Suite")
    print("=" * 60)
    
    results = {
        "Import Data": test_import_data(),
        "Get Backtest Data": test_get_backtest_data(),
        "Available Data Queries": test_available_data_queries(),
        "Coverage Statistics": test_coverage_stats(),
        "Data Quality Validation": test_data_quality_validation(),
        "Manager Statistics": test_manager_stats(),
    }
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
