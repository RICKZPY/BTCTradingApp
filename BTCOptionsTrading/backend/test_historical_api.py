"""
测试历史数据 API
完整的集成测试套件，测试所有API端点和错误处理
"""

import csv
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from fastapi.testclient import TestClient
from src.api.app import create_app


def create_test_csv_files(temp_dir: Path, count: int = 2):
    """创建测试 CSV 文件"""
    files = []
    
    filenames = [
        "Deribit_BTCUSD_20240329_50000_C.csv",
        "Deribit_BTCUSD_20240329_51000_C.csv",
    ]
    
    for i, filename in enumerate(filenames[:count]):
        filepath = temp_dir / filename
        
        # 创建测试数据
        test_data = []
        for j in range(5):
            timestamp = 1711670400 + (j * 3600)
            test_data.append({
                'unix': str(timestamp),
                'open': f'{0.05 + i * 0.001 + j * 0.0001:.6f}',
                'high': f'{0.055 + i * 0.001 + j * 0.0001:.6f}',
                'low': f'{0.047 + i * 0.001 + j * 0.0001:.6f}',
                'close': f'{0.052 + i * 0.001 + j * 0.0001:.6f}',
                'volume': f'{100 + j * 10}'
            })
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['unix', 'open', 'high', 'low', 'close', 'volume'])
            writer.writeheader()
            writer.writerows(test_data)
        
        files.append(filepath)
    
    return files


def create_invalid_csv_file(temp_dir: Path):
    """创建无效的 CSV 文件用于错误测试"""
    filepath = temp_dir / "Deribit_BTCUSD_20240329_52000_C.csv"
    
    # 创建格式错误的数据
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['unix', 'open', 'high', 'low', 'close', 'volume'])
        writer.writerow(['invalid_timestamp', 'not_a_number', '0.05', '0.04', '0.045', '100'])
    
    return filepath


def test_api_endpoints():
    """测试所有API端点"""
    print("\n" + "=" * 60)
    print("Historical Data API Test Suite")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    download_dir = Path(temp_dir) / "downloads"
    download_dir.mkdir()
    db_path = Path(temp_dir) / "test.db"
    
    try:
        # 创建测试文件
        print("\n1. Setting up test data...")
        create_test_csv_files(download_dir, count=2)
        print("  ✓ Created test CSV files")
        
        # 创建测试客户端
        app = create_app()
        client = TestClient(app)
        
        # 修改管理器配置以使用临时目录
        from src.api.routes import historical_data
        historical_data._manager = None  # 重置单例
        
        # 手动创建管理器
        from src.historical.manager import HistoricalDataManager
        historical_data._manager = HistoricalDataManager(
            download_dir=str(download_dir),
            db_path=str(db_path),
            cache_size_mb=10
        )
        
        # 测试健康检查
        print("\n2. Testing health check...")
        response = client.get("/api/historical-data/health")
        assert response.status_code == 200
        data = response.json()
        print(f"  Status: {data['status']}")
        print("  ✓ Health check passed")
        
        # 测试导入数据
        print("\n3. Testing data import...")
        response = client.post(
            "/api/historical-data/import",
            json={"validate": True, "generate_report": True}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"  Success: {data['success_count']}/{data['total_count']} files")
        print(f"  Records imported: {data['records_imported']}")
        print(f"  Quality score: {data['quality_score']:.1f}")
        print("  ✓ Import test passed")
        
        # 测试获取可用合约
        print("\n4. Testing available instruments...")
        response = client.get("/api/historical-data/available/instruments?underlying_symbol=BTC")
        assert response.status_code == 200
        instruments = response.json()
        print(f"  Found {len(instruments)} instruments:")
        for inst in instruments:
            print(f"    - {inst}")
        print("  ✓ Available instruments test passed")
        
        # 测试获取可用日期
        print("\n5. Testing available dates...")
        response = client.get("/api/historical-data/available/dates?underlying_symbol=BTC")
        assert response.status_code == 200
        dates = response.json()
        print(f"  Found {len(dates)} dates")
        print("  ✓ Available dates test passed")
        
        # 测试覆盖率统计
        print("\n6. Testing coverage stats...")
        response = client.get(
            "/api/historical-data/coverage",
            params={
                "start_date": "2024-03-29T00:00:00",
                "end_date": "2024-03-29T23:00:00",
                "underlying_symbol": "BTC"
            }
        )
        assert response.status_code == 200
        stats = response.json()
        print(f"  Coverage: {stats['coverage_percentage']:.1%}")
        print(f"  Days with data: {stats['days_with_data']}/{stats['total_days']}")
        print("  ✓ Coverage stats test passed")
        
        # 测试质量报告
        print("\n7. Testing quality report...")
        response = client.get(
            "/api/historical-data/quality",
            params={
                "start_date": "2024-03-29T00:00:00",
                "end_date": "2024-03-29T23:00:00"
            }
        )
        assert response.status_code == 200
        report = response.json()
        print(f"  Quality score: {report['quality_score']:.1f}/100")
        print(f"  Total records: {report['total_records']}")
        print("  ✓ Quality report test passed")
        
        # 测试统计信息
        print("\n8. Testing stats...")
        response = client.get("/api/historical-data/stats")
        assert response.status_code == 200
        stats = response.json()
        print(f"  Database records: {stats['database_records']}")
        print(f"  CSV files: {stats['csv_files']}")
        print("  ✓ Stats test passed")
        
        # 测试清理缓存
        print("\n9. Testing cache clear...")
        response = client.delete("/api/historical-data/cache?clear_database=false")
        assert response.status_code == 200
        data = response.json()
        print(f"  Message: {data['message']}")
        print("  ✓ Cache clear test passed")
        
        print("\n" + "=" * 60)
        print("✅ All API tests passed!")
        print("=" * 60)
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        shutil.rmtree(temp_dir)


def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("Error Handling Test Suite")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    download_dir = Path(temp_dir) / "downloads"
    download_dir.mkdir()
    db_path = Path(temp_dir) / "test.db"
    
    try:
        # 创建测试客户端
        app = create_app()
        client = TestClient(app)
        
        # 修改管理器配置
        from src.api.routes import historical_data
        historical_data._manager = None
        
        from src.historical.manager import HistoricalDataManager
        historical_data._manager = HistoricalDataManager(
            download_dir=str(download_dir),
            db_path=str(db_path),
            cache_size_mb=10
        )
        
        # 测试1: 导入空目录（无数据）
        print("\n1. Testing import with no data...")
        response = client.post(
            "/api/historical-data/import",
            json={"validate": True, "generate_report": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['total_count'] == 0
        print("  ✓ Empty import handled correctly")
        
        # 测试2: 导入包含无效文件
        print("\n2. Testing import with invalid data...")
        create_test_csv_files(download_dir, count=1)
        create_invalid_csv_file(download_dir)
        
        response = client.post(
            "/api/historical-data/import",
            json={"validate": True, "generate_report": True}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"  Success: {data['success_count']}, Failed: {data['failure_count']}")
        assert data['failure_count'] > 0  # 应该有失败的文件
        print("  ✓ Invalid data handled correctly")
        
        # 测试3: 查询不存在的数据
        print("\n3. Testing query for non-existent data...")
        response = client.get(
            "/api/historical-data/available/instruments?underlying_symbol=ETH"
        )
        assert response.status_code == 200
        instruments = response.json()
        assert len(instruments) == 0
        print("  ✓ Non-existent data query handled correctly")
        
        # 测试4: 无效的日期范围
        print("\n4. Testing invalid date range...")
        response = client.get(
            "/api/historical-data/coverage",
            params={
                "start_date": "2024-12-31T00:00:00",
                "end_date": "2024-01-01T00:00:00"  # 结束日期早于开始日期
            }
        )
        # 应该返回错误或空结果
        assert response.status_code in [200, 400, 422]
        print("  ✓ Invalid date range handled")
        
        # 测试5: 导出不存在的数据
        print("\n5. Testing export with no data...")
        response = client.post(
            "/api/historical-data/export",
            json={
                "format": "csv",
                "start_date": "2025-01-01T00:00:00",
                "end_date": "2025-01-02T00:00:00"
            }
        )
        assert response.status_code == 404  # 应该返回404
        print("  ✓ Export with no data handled correctly")
        
        # 测试6: 不支持的导出格式
        print("\n6. Testing unsupported export format...")
        # 先导入一些数据
        historical_data._manager.import_historical_data(validate=False, generate_report=False)
        
        response = client.post(
            "/api/historical-data/export",
            json={
                "format": "xml",  # 不支持的格式
                "start_date": "2024-03-29T00:00:00",
                "end_date": "2024-03-29T23:00:00"
            }
        )
        assert response.status_code == 400  # 应该返回400
        print("  ✓ Unsupported format handled correctly")
        
        # 测试7: 缺少必需参数
        print("\n7. Testing missing required parameters...")
        response = client.get("/api/historical-data/coverage")
        assert response.status_code == 422  # FastAPI 验证错误
        print("  ✓ Missing parameters handled correctly")
        
        print("\n" + "=" * 60)
        print("✅ All error handling tests passed!")
        print("=" * 60)
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        shutil.rmtree(temp_dir)


def test_export_functionality():
    """测试导出功能"""
    print("\n" + "=" * 60)
    print("Export Functionality Test Suite")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    download_dir = Path(temp_dir) / "downloads"
    download_dir.mkdir()
    db_path = Path(temp_dir) / "test.db"
    
    try:
        # 创建测试数据
        print("\n1. Setting up test data...")
        create_test_csv_files(download_dir, count=2)
        
        # 创建测试客户端
        app = create_app()
        client = TestClient(app)
        
        # 配置管理器
        from src.api.routes import historical_data
        historical_data._manager = None
        
        from src.historical.manager import HistoricalDataManager
        historical_data._manager = HistoricalDataManager(
            download_dir=str(download_dir),
            db_path=str(db_path),
            cache_size_mb=10
        )
        
        # 导入数据
        print("\n2. Importing data...")
        response = client.post(
            "/api/historical-data/import",
            json={"validate": False, "generate_report": False}
        )
        assert response.status_code == 200
        print("  ✓ Data imported")
        
        # 测试CSV导出
        print("\n3. Testing CSV export...")
        response = client.post(
            "/api/historical-data/export",
            json={
                "format": "csv",
                "start_date": "2024-03-29T00:00:00",
                "end_date": "2024-03-29T23:00:00",
                "compress": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data['format'] == 'csv'
        assert data['records_exported'] > 0
        assert Path(data['file_path']).exists()
        print(f"  Exported {data['records_exported']} records to {data['file_path']}")
        print("  ✓ CSV export passed")
        
        # 测试JSON导出
        print("\n4. Testing JSON export...")
        response = client.post(
            "/api/historical-data/export",
            json={
                "format": "json",
                "start_date": "2024-03-29T00:00:00",
                "end_date": "2024-03-29T23:00:00"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data['format'] == 'json'
        assert data['records_exported'] > 0
        
        # 验证JSON文件内容
        with open(data['file_path'], 'r') as f:
            json_data = json.load(f)
            assert isinstance(json_data, list)
            assert len(json_data) > 0
            assert 'instrument_name' in json_data[0]
        
        print(f"  Exported {data['records_exported']} records")
        print("  ✓ JSON export passed")
        
        # 测试带筛选的导出
        print("\n5. Testing export with filters...")
        instruments = client.get("/api/historical-data/available/instruments").json()
        if instruments:
            response = client.post(
                "/api/historical-data/export",
                json={
                    "format": "csv",
                    "instruments": [instruments[0]],
                    "start_date": "2024-03-29T00:00:00",
                    "end_date": "2024-03-29T23:00:00"
                }
            )
            assert response.status_code == 200
            data = response.json()
            print(f"  Filtered export: {data['records_exported']} records")
            print("  ✓ Filtered export passed")
        
        print("\n" + "=" * 60)
        print("✅ All export tests passed!")
        print("=" * 60)
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        shutil.rmtree(temp_dir)


def test_cache_operations():
    """测试缓存操作"""
    print("\n" + "=" * 60)
    print("Cache Operations Test Suite")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    download_dir = Path(temp_dir) / "downloads"
    download_dir.mkdir()
    db_path = Path(temp_dir) / "test.db"
    
    try:
        # 创建测试数据
        print("\n1. Setting up test data...")
        create_test_csv_files(download_dir, count=2)
        
        # 创建测试客户端
        app = create_app()
        client = TestClient(app)
        
        # 配置管理器
        from src.api.routes import historical_data
        historical_data._manager = None
        
        from src.historical.manager import HistoricalDataManager
        historical_data._manager = HistoricalDataManager(
            download_dir=str(download_dir),
            db_path=str(db_path),
            cache_size_mb=10
        )
        
        # 导入数据
        print("\n2. Importing data...")
        response = client.post(
            "/api/historical-data/import",
            json={"validate": False, "generate_report": False}
        )
        assert response.status_code == 200
        
        # 检查统计信息
        print("\n3. Checking stats before cache clear...")
        response = client.get("/api/historical-data/stats")
        assert response.status_code == 200
        stats_before = response.json()
        print(f"  Database records: {stats_before['database_records']}")
        print(f"  Memory cache entries: {stats_before['memory_cache_entries']}")
        
        # 清理内存缓存
        print("\n4. Clearing memory cache...")
        response = client.delete("/api/historical-data/cache?clear_database=false")
        assert response.status_code == 200
        
        # 检查统计信息
        print("\n5. Checking stats after cache clear...")
        response = client.get("/api/historical-data/stats")
        assert response.status_code == 200
        stats_after = response.json()
        print(f"  Database records: {stats_after['database_records']}")
        print(f"  Memory cache entries: {stats_after['memory_cache_entries']}")
        
        # 数据库记录应该保持不变
        assert stats_after['database_records'] == stats_before['database_records']
        print("  ✓ Memory cache cleared, database intact")
        
        # 清理数据库
        print("\n6. Clearing database...")
        response = client.delete("/api/historical-data/cache?clear_database=true")
        assert response.status_code == 200
        
        # 检查统计信息
        print("\n7. Checking stats after database clear...")
        response = client.get("/api/historical-data/stats")
        assert response.status_code == 200
        stats_final = response.json()
        print(f"  Database records: {stats_final['database_records']}")
        assert stats_final['database_records'] == 0
        print("  ✓ Database cleared")
        
        print("\n" + "=" * 60)
        print("✅ All cache operation tests passed!")
        print("=" * 60)
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    all_passed = True
    
    # 运行所有测试套件
    all_passed &= test_api_endpoints()
    all_passed &= test_error_handling()
    all_passed &= test_export_functionality()
    all_passed &= test_cache_operations()
    
    if all_passed:
        print("\n" + "=" * 60)
        print("🎉 ALL TEST SUITES PASSED!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
    
    exit(0 if all_passed else 1)
