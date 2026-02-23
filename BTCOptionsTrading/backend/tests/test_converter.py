"""
测试 HistoricalDataConverter 转换器功能
"""

import csv
from pathlib import Path
from datetime import datetime
from decimal import Decimal

from src.historical.converter import HistoricalDataConverter
from src.historical.models import OptionInfo
from src.core.models import OptionType


def create_test_csv_file():
    """创建测试 CSV 文件"""
    test_dir = Path("data/test_csv")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建一个测试 CSV 文件
    # 文件名格式: Deribit_BTCUSD_20240329_50000_C.csv
    filename = "Deribit_BTCUSD_20240329_50000_C.csv"
    filepath = test_dir / filename
    
    # 创建测试数据
    test_data = [
        {
            'unix': '1711670400',  # 2024-03-29 00:00:00
            'open': '0.0500',
            'high': '0.0550',
            'low': '0.0450',
            'close': '0.0525',
            'volume': '100.5'
        },
        {
            'unix': '1711674000',  # 2024-03-29 01:00:00
            'open': '0.0525',
            'high': '0.0575',
            'low': '0.0500',
            'close': '0.0550',
            'volume': '150.25'
        },
        {
            'unix': '1711677600',  # 2024-03-29 02:00:00
            'open': '0.0550',
            'high': '0.0600',
            'low': '0.0525',
            'close': '0.0580',
            'volume': '200.75'
        }
    ]
    
    # 写入 CSV 文件
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['unix', 'open', 'high', 'low', 'close', 'volume'])
        writer.writeheader()
        writer.writerows(test_data)
    
    print(f"✓ Created test CSV file: {filepath}")
    return filepath


def test_filename_parsing():
    """测试文件名解析"""
    print("\n" + "=" * 60)
    print("Test 1: Filename Parsing")
    print("=" * 60)
    
    converter = HistoricalDataConverter()
    
    test_cases = [
        ("Deribit_BTCUSD_20240329_50000_C.csv", {
            'symbol': 'BTC',
            'date': datetime(2024, 3, 29),
            'strike': Decimal('50000'),
            'type': OptionType.CALL
        }),
        ("Deribit_ETHUSD_20240426_3000_P.csv", {
            'symbol': 'ETH',
            'date': datetime(2024, 4, 26),
            'strike': Decimal('3000'),
            'type': OptionType.PUT
        }),
    ]
    
    for filename, expected in test_cases:
        try:
            option_info = converter.extract_option_info(filename)
            
            assert option_info.symbol == expected['symbol'], f"Symbol mismatch: {option_info.symbol} != {expected['symbol']}"
            assert option_info.expiry_date == expected['date'], f"Date mismatch: {option_info.expiry_date} != {expected['date']}"
            assert option_info.strike_price == expected['strike'], f"Strike mismatch: {option_info.strike_price} != {expected['strike']}"
            assert option_info.option_type == expected['type'], f"Type mismatch: {option_info.option_type} != {expected['type']}"
            
            print(f"✓ {filename}")
            print(f"  Instrument: {option_info.to_instrument_name()}")
            
        except Exception as e:
            print(f"✗ {filename}: {e}")
            return False
    
    print("\n✓ All filename parsing tests passed!")
    return True


def test_csv_parsing():
    """测试 CSV 解析"""
    print("\n" + "=" * 60)
    print("Test 2: CSV Parsing")
    print("=" * 60)
    
    # 创建测试文件
    csv_path = create_test_csv_file()
    
    converter = HistoricalDataConverter()
    
    try:
        # 解析 CSV
        ohlcv_data = converter.parse_csv_file(csv_path)
        
        print(f"\n✓ Parsed {len(ohlcv_data)} records")
        
        # 验证数据
        assert len(ohlcv_data) == 3, f"Expected 3 records, got {len(ohlcv_data)}"
        
        # 检查第一条记录
        first = ohlcv_data[0]
        print(f"\nFirst record:")
        print(f"  Timestamp: {first.timestamp}")
        print(f"  Open: {first.open}")
        print(f"  High: {first.high}")
        print(f"  Low: {first.low}")
        print(f"  Close: {first.close}")
        print(f"  Volume: {first.volume}")
        
        # 验证 OHLC 关系
        for i, data in enumerate(ohlcv_data):
            assert data.low <= data.open <= data.high, f"Record {i}: Invalid OHLC relationship"
            assert data.low <= data.close <= data.high, f"Record {i}: Invalid OHLC relationship"
        
        print("\n✓ All OHLC relationships are valid")
        print("✓ CSV parsing test passed!")
        return True
        
    except Exception as e:
        print(f"✗ CSV parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_conversion():
    """测试数据转换"""
    print("\n" + "=" * 60)
    print("Test 3: Data Conversion")
    print("=" * 60)
    
    csv_path = Path("data/test_csv/Deribit_BTCUSD_20240329_50000_C.csv")
    
    if not csv_path.exists():
        csv_path = create_test_csv_file()
    
    converter = HistoricalDataConverter()
    
    try:
        # 完整处理流程
        historical_data = converter.process_file(csv_path)
        
        print(f"\n✓ Converted {len(historical_data)} records to internal format")
        
        # 检查第一条记录
        if historical_data:
            first = historical_data[0]
            print(f"\nFirst converted record:")
            print(f"  Instrument: {first.instrument_name}")
            print(f"  Timestamp: {first.timestamp}")
            print(f"  Close Price: {first.close_price}")
            print(f"  Strike: {first.strike_price}")
            print(f"  Expiry: {first.expiry_date.date()}")
            print(f"  Type: {first.option_type.value}")
            print(f"  Underlying: {first.underlying_symbol}")
            print(f"  Source: {first.data_source.value}")
        
        # 验证数据
        validation_result = converter.validate_converted_data(historical_data)
        
        print(f"\nValidation Results:")
        print(f"  Valid: {validation_result.is_valid}")
        print(f"  Errors: {len(validation_result.errors)}")
        print(f"  Warnings: {len(validation_result.warnings)}")
        
        if validation_result.errors:
            print(f"\n  Errors:")
            for error in validation_result.errors[:5]:  # 只显示前5个
                print(f"    - {error}")
        
        if validation_result.warnings:
            print(f"\n  Warnings:")
            for warning in validation_result.warnings[:5]:
                print(f"    - {warning}")
        
        print("\n✓ Data conversion test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Data conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parallel_processing():
    """测试并行处理"""
    print("\n" + "=" * 60)
    print("Test 4: Parallel Processing")
    print("=" * 60)
    
    # 创建多个测试文件
    test_dir = Path("data/test_csv")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    test_files = [
        "Deribit_BTCUSD_20240329_50000_C.csv",
        "Deribit_BTCUSD_20240329_51000_C.csv",
        "Deribit_BTCUSD_20240329_49000_P.csv",
    ]
    
    created_files = []
    
    # 创建测试文件
    for filename in test_files:
        filepath = test_dir / filename
        
        test_data = [
            {
                'unix': '1711670400',
                'open': '0.0500',
                'high': '0.0550',
                'low': '0.0450',
                'close': '0.0525',
                'volume': '100.5'
            },
            {
                'unix': '1711674000',
                'open': '0.0525',
                'high': '0.0575',
                'low': '0.0500',
                'close': '0.0550',
                'volume': '150.25'
            }
        ]
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['unix', 'open', 'high', 'low', 'close', 'volume'])
            writer.writeheader()
            writer.writerows(test_data)
        
        created_files.append(filepath)
    
    print(f"✓ Created {len(created_files)} test files")
    
    converter = HistoricalDataConverter()
    
    try:
        # 并行处理
        all_data = converter.process_files_parallel(created_files, max_workers=2)
        
        print(f"\n✓ Processed {len(created_files)} files in parallel")
        print(f"✓ Total records: {len(all_data)}")
        
        # 按合约分组
        by_instrument = {}
        for data in all_data:
            if data.instrument_name not in by_instrument:
                by_instrument[data.instrument_name] = []
            by_instrument[data.instrument_name].append(data)
        
        print(f"\nRecords by instrument:")
        for instrument, records in by_instrument.items():
            print(f"  {instrument}: {len(records)} records")
        
        print("\n✓ Parallel processing test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Parallel processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("HistoricalDataConverter Test Suite")
    print("=" * 60)
    
    results = {
        "Filename Parsing": test_filename_parsing(),
        "CSV Parsing": test_csv_parsing(),
        "Data Conversion": test_data_conversion(),
        "Parallel Processing": test_parallel_processing(),
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
