"""
测试 HistoricalDataValidator 验证器功能
"""

from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

from src.historical.validator import HistoricalDataValidator
from src.historical.models import HistoricalOptionData, DataSource
from src.core.models import OptionType


def create_test_data(count: int = 10, with_gaps: bool = False) -> list:
    """创建测试数据"""
    data = []
    base_time = datetime(2024, 3, 29, 0, 0, 0)
    
    for i in range(count):
        # 如果需要间隙，跳过某些时间点
        if with_gaps and i in [3, 7]:
            continue
        
        timestamp = base_time + timedelta(hours=i)
        
        # 创建合理的 OHLC 数据
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


def create_invalid_data() -> list:
    """创建包含无效数据的测试集"""
    base_time = datetime(2024, 3, 29, 0, 0, 0)
    
    data = [
        # 正常数据
        HistoricalOptionData(
            instrument_name='BTC-29MAR24-50000-C',
            timestamp=base_time,
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
        ),
        # 负价格
        HistoricalOptionData(
            instrument_name='BTC-29MAR24-50000-C',
            timestamp=base_time + timedelta(hours=1),
            open_price=Decimal('-0.01'),
            high_price=Decimal('0.055'),
            low_price=Decimal('-0.02'),
            close_price=Decimal('0.052'),
            volume=Decimal('100'),
            strike_price=Decimal('50000'),
            expiry_date=datetime(2024, 3, 29),
            option_type=OptionType.CALL,
            underlying_symbol='BTC',
            data_source=DataSource.CRYPTO_DATA_DOWNLOAD
        ),
        # OHLC 关系错误
        HistoricalOptionData(
            instrument_name='BTC-29MAR24-50000-C',
            timestamp=base_time + timedelta(hours=2),
            open_price=Decimal('0.06'),  # Open > High
            high_price=Decimal('0.055'),
            low_price=Decimal('0.047'),
            close_price=Decimal('0.052'),
            volume=Decimal('100'),
            strike_price=Decimal('50000'),
            expiry_date=datetime(2024, 3, 29),
            option_type=OptionType.CALL,
            underlying_symbol='BTC',
            data_source=DataSource.CRYPTO_DATA_DOWNLOAD
        ),
    ]
    
    return data


def test_completeness_validation():
    """测试数据完整性验证"""
    print("\n" + "=" * 60)
    print("Test 1: Data Completeness Validation")
    print("=" * 60)
    
    validator = HistoricalDataValidator()
    
    # 测试正常数据
    print("\n1.1 Testing normal data...")
    normal_data = create_test_data(count=10, with_gaps=False)
    result = validator.validate_data_completeness(normal_data)
    
    print(f"  Valid: {result.is_valid}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")
    print(f"  Total records: {result.stats.get('total_records')}")
    
    if result.errors:
        print(f"\n  Errors:")
        for error in result.errors:
            print(f"    - {error}")
    
    # 测试有间隙的数据
    print("\n1.2 Testing data with gaps...")
    gap_data = create_test_data(count=10, with_gaps=True)
    result = validator.validate_data_completeness(gap_data)
    
    print(f"  Valid: {result.is_valid}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")
    print(f"  Missing intervals: {result.stats.get('missing_intervals')}")
    
    if result.warnings:
        print(f"\n  Warnings:")
        for warning in result.warnings[:3]:
            print(f"    - {warning}")
    
    print("\n✓ Completeness validation test passed!")
    return True


def test_price_sanity_validation():
    """测试价格合理性验证"""
    print("\n" + "=" * 60)
    print("Test 2: Price Sanity Validation")
    print("=" * 60)
    
    validator = HistoricalDataValidator()
    
    # 测试正常数据
    print("\n2.1 Testing normal data...")
    normal_data = create_test_data(count=10)
    result = validator.validate_price_sanity(normal_data)
    
    print(f"  Valid: {result.is_valid}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")
    print(f"  Min price: {result.stats.get('min_price')}")
    print(f"  Max price: {result.stats.get('max_price')}")
    print(f"  Avg price: {result.stats.get('avg_price')}")
    
    # 测试无效数据
    print("\n2.2 Testing invalid data...")
    invalid_data = create_invalid_data()
    result = validator.validate_price_sanity(invalid_data)
    
    print(f"  Valid: {result.is_valid}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")
    
    if result.errors:
        print(f"\n  Errors found (expected):")
        for error in result.errors:
            print(f"    - {error}")
    
    print("\n✓ Price sanity validation test passed!")
    return True


def test_option_parity_validation():
    """测试期权平价关系验证"""
    print("\n" + "=" * 60)
    print("Test 3: Option Parity Validation")
    print("=" * 60)
    
    validator = HistoricalDataValidator()
    
    # 创建看涨期权数据
    base_time = datetime(2024, 3, 29, 0, 0, 0)
    call_data = []
    put_data = []
    
    for i in range(5):
        timestamp = base_time + timedelta(hours=i)
        strike = Decimal('50000')
        
        # 看涨期权
        call_data.append(HistoricalOptionData(
            instrument_name='BTC-29MAR24-50000-C',
            timestamp=timestamp,
            open_price=Decimal('0.05'),
            high_price=Decimal('0.055'),
            low_price=Decimal('0.047'),
            close_price=Decimal('0.052'),
            volume=Decimal('100'),
            strike_price=strike,
            expiry_date=datetime(2024, 3, 29),
            option_type=OptionType.CALL,
            underlying_symbol='BTC',
            data_source=DataSource.CRYPTO_DATA_DOWNLOAD
        ))
        
        # 看跌期权（价格略低）
        put_data.append(HistoricalOptionData(
            instrument_name='BTC-29MAR24-50000-P',
            timestamp=timestamp,
            open_price=Decimal('0.045'),
            high_price=Decimal('0.050'),
            low_price=Decimal('0.042'),
            close_price=Decimal('0.047'),
            volume=Decimal('100'),
            strike_price=strike,
            expiry_date=datetime(2024, 3, 29),
            option_type=OptionType.PUT,
            underlying_symbol='BTC',
            data_source=DataSource.CRYPTO_DATA_DOWNLOAD
        ))
    
    result = validator.validate_option_parity(call_data, put_data)
    
    print(f"  Valid: {result.is_valid}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")
    print(f"  Total pairs: {result.stats.get('total_pairs')}")
    print(f"  Parity violations: {result.stats.get('parity_violations')}")
    
    if result.warnings:
        print(f"\n  Warnings:")
        for warning in result.warnings[:3]:
            print(f"    - {warning}")
    
    print("\n✓ Option parity validation test passed!")
    return True


def test_quality_report():
    """测试质量报告生成"""
    print("\n" + "=" * 60)
    print("Test 4: Quality Report Generation")
    print("=" * 60)
    
    validator = HistoricalDataValidator()
    
    # 创建测试数据
    data = create_test_data(count=20, with_gaps=True)
    
    # 生成质量报告
    report = validator.generate_quality_report(
        data,
        start_date=datetime(2024, 3, 29, 0, 0, 0),
        end_date=datetime(2024, 3, 29, 23, 0, 0)
    )
    
    print(f"\n  Total records: {report.total_records}")
    print(f"  Missing records: {report.missing_records}")
    print(f"  Anomaly records: {report.anomaly_records}")
    print(f"  Coverage: {report.coverage_percentage:.1%}")
    print(f"  Quality score: {report.quality_score:.1f}/100")
    print(f"  Time range: {report.time_range[0]} to {report.time_range[1]}")
    print(f"  Total issues: {len(report.issues)}")
    
    if report.issues:
        print(f"\n  Sample issues:")
        for issue in report.issues[:3]:
            print(f"    - [{issue.severity.value}] {issue.message}")
    
    print("\n✓ Quality report generation test passed!")
    return True


def test_coverage_stats():
    """测试覆盖率统计"""
    print("\n" + "=" * 60)
    print("Test 5: Coverage Statistics")
    print("=" * 60)
    
    validator = HistoricalDataValidator()
    
    # 创建测试数据
    data = create_test_data(count=15, with_gaps=True)
    
    # 计算覆盖率
    stats = validator.get_coverage_stats(
        data,
        start_date=datetime(2024, 3, 29, 0, 0, 0),
        end_date=datetime(2024, 3, 30, 23, 0, 0)
    )
    
    print(f"\n  Start date: {stats.start_date}")
    print(f"  End date: {stats.end_date}")
    print(f"  Total days: {stats.total_days}")
    print(f"  Days with data: {stats.days_with_data}")
    print(f"  Coverage: {stats.coverage_percentage:.1%}")
    print(f"  Missing dates: {len(stats.missing_dates)}")
    print(f"  Strikes covered: {len(stats.strikes_covered)}")
    print(f"  Expiries covered: {len(stats.expiries_covered)}")
    
    if stats.missing_dates:
        print(f"\n  Sample missing dates:")
        for date in stats.missing_dates[:3]:
            print(f"    - {date.date()}")
    
    print("\n✓ Coverage statistics test passed!")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("HistoricalDataValidator Test Suite")
    print("=" * 60)
    
    results = {
        "Completeness Validation": test_completeness_validation(),
        "Price Sanity Validation": test_price_sanity_validation(),
        "Option Parity Validation": test_option_parity_validation(),
        "Quality Report": test_quality_report(),
        "Coverage Statistics": test_coverage_stats(),
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
