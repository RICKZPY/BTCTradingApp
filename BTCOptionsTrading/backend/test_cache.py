"""
测试 HistoricalDataCache 缓存功能
"""

from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal
import tempfile
import shutil

from src.historical.cache import HistoricalDataCache
from src.historical.models import HistoricalOptionData, DataSource
from src.core.models import OptionType


def create_test_data(count: int = 20) -> list:
    """创建测试数据"""
    data = []
    base_time = datetime(2024, 3, 29, 0, 0, 0)
    
    for i in range(count):
        timestamp = base_time + timedelta(hours=i)
        base_price = Decimal('0.05') + Decimal(str(i * 0.001))
        
        data.append(HistoricalOptionData(
            instrument_name='BTC-29MAR24-50000-C',
            timestamp=timestamp,
            open_price=base_price,
            high_price=base_price + Decimal('0.005'),
            low_price=base_price - Decimal('0.003'),
            close_price=base_price + Decimal('0.002'),
            volume=Decimal('100') + Decimal(str(i * 10)),
            strike_price=Decimal('50000'),
            expiry_date=datetime(2024, 3, 29),
            option_type=OptionType.CALL,
            underlying_symbol='BTC',
            data_source=DataSource.CRYPTO_DATA_DOWNLOAD
        ))
    
    return data


def test_store_and_query():
    """测试存储和查询"""
    print("\n" + "=" * 60)
    print("Test 1: Store and Query Data")
    print("=" * 60)
    
    # 创建临时数据库
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    
    try:
        cache = HistoricalDataCache(db_path=str(db_path), cache_size_mb=10)
        
        # 创建测试数据
        test_data = create_test_data(count=20)
        
        # 存储数据
        print("\n1.1 Storing data...")
        inserted = cache.store_historical_data(test_data)
        print(f"  Inserted: {inserted} records")
        assert inserted == 20, f"Expected 20 records, got {inserted}"
        
        # 查询所有数据
        print("\n1.2 Querying all data...")
        all_data = cache.query_option_data()
        print(f"  Retrieved: {len(all_data)} records")
        assert len(all_data) == 20, f"Expected 20 records, got {len(all_data)}"
        
        # 按合约查询
        print("\n1.3 Querying by instrument...")
        instrument_data = cache.query_option_data(instrument_name='BTC-29MAR24-50000-C')
        print(f"  Retrieved: {len(instrument_data)} records")
        assert len(instrument_data) == 20, f"Expected 20 records, got {len(instrument_data)}"
        
        # 按日期范围查询
        print("\n1.4 Querying by date range...")
        start_date = datetime(2024, 3, 29, 5, 0, 0)
        end_date = datetime(2024, 3, 29, 10, 0, 0)
        range_data = cache.query_option_data(start_date=start_date, end_date=end_date)
        print(f"  Retrieved: {len(range_data)} records")
        print(f"  Time range: {range_data[0].timestamp} to {range_data[-1].timestamp}")
        assert len(range_data) == 6, f"Expected 6 records, got {len(range_data)}"
        
        print("\n✓ Store and query test passed!")
        return True
        
    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir)


def test_cache_functionality():
    """测试缓存功能"""
    print("\n" + "=" * 60)
    print("Test 2: Cache Functionality")
    print("=" * 60)
    
    # 创建临时数据库
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    
    try:
        cache = HistoricalDataCache(db_path=str(db_path), cache_size_mb=1)
        
        # 创建并存储测试数据
        test_data = create_test_data(count=20)
        cache.store_historical_data(test_data)
        
        # 第一次查询（缓存未命中）
        print("\n2.1 First query (cache miss)...")
        data1 = cache.query_option_data(instrument_name='BTC-29MAR24-50000-C')
        print(f"  Retrieved: {len(data1)} records")
        
        # 第二次查询（缓存命中）
        print("\n2.2 Second query (cache hit)...")
        data2 = cache.query_option_data(instrument_name='BTC-29MAR24-50000-C')
        print(f"  Retrieved: {len(data2)} records")
        
        # 验证数据一致性
        assert len(data1) == len(data2), "Cache data mismatch"
        
        # 检查缓存统计
        print("\n2.3 Cache statistics...")
        stats = cache.get_cache_stats()
        print(f"  Memory cache entries: {stats['memory_cache']['entries']}")
        print(f"  Memory cache size: {stats['memory_cache']['size_mb']:.2f} MB")
        print(f"  Database records: {stats['database']['record_count']}")
        
        print("\n✓ Cache functionality test passed!")
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def test_available_data():
    """测试可用数据查询"""
    print("\n" + "=" * 60)
    print("Test 3: Available Data Queries")
    print("=" * 60)
    
    # 创建临时数据库
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    
    try:
        cache = HistoricalDataCache(db_path=str(db_path))
        
        # 创建多个合约的测试数据
        test_data = []
        
        # BTC-29MAR24-50000-C
        for i in range(10):
            timestamp = datetime(2024, 3, 29, i, 0, 0)
            test_data.append(HistoricalOptionData(
                instrument_name='BTC-29MAR24-50000-C',
                timestamp=timestamp,
                open_price=Decimal('0.05'),
                high_price=Decimal('0.055'),
                low_price=Decimal('0.047'),
                close_price=Decimal('0.052'),
                volume=Decimal('100'),
                strike_price=Decimal('50000'),
                expiry_date=datetime(2024, 3, 29),
                option_type=OptionType.CALL,
                underlying_symbol='BTC',
                data_source=DataSource.CRYPTO_DATA_DOWNLOAD
            ))
        
        # BTC-29MAR24-51000-C
        for i in range(10):
            timestamp = datetime(2024, 3, 29, i, 0, 0)
            test_data.append(HistoricalOptionData(
                instrument_name='BTC-29MAR24-51000-C',
                timestamp=timestamp,
                open_price=Decimal('0.04'),
                high_price=Decimal('0.045'),
                low_price=Decimal('0.037'),
                close_price=Decimal('0.042'),
                volume=Decimal('100'),
                strike_price=Decimal('51000'),
                expiry_date=datetime(2024, 3, 29),
                option_type=OptionType.CALL,
                underlying_symbol='BTC',
                data_source=DataSource.CRYPTO_DATA_DOWNLOAD
            ))
        
        cache.store_historical_data(test_data)
        
        # 查询可用日期
        print("\n3.1 Querying available dates...")
        dates = cache.get_available_dates()
        print(f"  Found {len(dates)} unique timestamps")
        
        # 查询可用合约
        print("\n3.2 Querying available instruments...")
        instruments = cache.get_available_instruments(underlying_symbol='BTC')
        print(f"  Found {len(instruments)} instruments:")
        for inst in instruments:
            print(f"    - {inst}")
        
        assert len(instruments) == 2, f"Expected 2 instruments, got {len(instruments)}"
        
        print("\n✓ Available data queries test passed!")
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def test_coverage_stats():
    """测试覆盖率统计"""
    print("\n" + "=" * 60)
    print("Test 4: Coverage Statistics")
    print("=" * 60)
    
    # 创建临时数据库
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    
    try:
        cache = HistoricalDataCache(db_path=str(db_path))
        
        # 创建测试数据（有间隙）
        test_data = []
        base_time = datetime(2024, 3, 29, 0, 0, 0)
        
        for i in range(20):
            # 跳过某些小时
            if i in [5, 6, 10, 11, 12]:
                continue
            
            timestamp = base_time + timedelta(hours=i)
            test_data.append(HistoricalOptionData(
                instrument_name='BTC-29MAR24-50000-C',
                timestamp=timestamp,
                open_price=Decimal('0.05'),
                high_price=Decimal('0.055'),
                low_price=Decimal('0.047'),
                close_price=Decimal('0.052'),
                volume=Decimal('100'),
                strike_price=Decimal('50000'),
                expiry_date=datetime(2024, 3, 29),
                option_type=OptionType.CALL,
                underlying_symbol='BTC',
                data_source=DataSource.CRYPTO_DATA_DOWNLOAD
            ))
        
        cache.store_historical_data(test_data)
        
        # 获取覆盖率统计
        print("\n4.1 Calculating coverage...")
        stats = cache.get_coverage_stats(
            start_date=datetime(2024, 3, 29, 0, 0, 0),
            end_date=datetime(2024, 3, 29, 23, 0, 0)
        )
        
        print(f"  Total days: {stats.total_days}")
        print(f"  Days with data: {stats.days_with_data}")
        print(f"  Coverage: {stats.coverage_percentage:.1%}")
        print(f"  Missing dates: {len(stats.missing_dates)}")
        print(f"  Strikes covered: {len(stats.strikes_covered)}")
        
        assert stats.total_days == 1, f"Expected 1 day, got {stats.total_days}"
        assert stats.days_with_data == 1, f"Expected 1 day with data, got {stats.days_with_data}"
        
        print("\n✓ Coverage statistics test passed!")
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def test_cache_clear():
    """测试缓存清理"""
    print("\n" + "=" * 60)
    print("Test 5: Cache Clear")
    print("=" * 60)
    
    # 创建临时数据库
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    
    try:
        cache = HistoricalDataCache(db_path=str(db_path))
        
        # 创建并存储测试数据
        test_data = create_test_data(count=20)
        cache.store_historical_data(test_data)
        
        # 查询数据（填充缓存）
        cache.query_option_data()
        
        # 检查缓存统计
        stats_before = cache.get_cache_stats()
        print(f"\n5.1 Before clear:")
        print(f"  Memory cache entries: {stats_before['memory_cache']['entries']}")
        print(f"  Database records: {stats_before['database']['record_count']}")
        
        # 清理内存缓存
        print("\n5.2 Clearing memory cache...")
        cache.clear_cache(clear_database=False)
        
        stats_after = cache.get_cache_stats()
        print(f"  Memory cache entries: {stats_after['memory_cache']['entries']}")
        print(f"  Database records: {stats_after['database']['record_count']}")
        
        assert stats_after['memory_cache']['entries'] == 0, "Memory cache not cleared"
        assert stats_after['database']['record_count'] == 20, "Database should not be cleared"
        
        # 清理数据库
        print("\n5.3 Clearing database...")
        cache.clear_cache(clear_database=True)
        
        stats_final = cache.get_cache_stats()
        print(f"  Database records: {stats_final['database']['record_count']}")
        
        assert stats_final['database']['record_count'] == 0, "Database not cleared"
        
        print("\n✓ Cache clear test passed!")
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("HistoricalDataCache Test Suite")
    print("=" * 60)
    
    results = {
        "Store and Query": test_store_and_query(),
        "Cache Functionality": test_cache_functionality(),
        "Available Data": test_available_data(),
        "Coverage Statistics": test_coverage_stats(),
        "Cache Clear": test_cache_clear(),
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
