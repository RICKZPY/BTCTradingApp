"""
测试历史数据 API
"""

import csv
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


if __name__ == "__main__":
    success = test_api_endpoints()
    exit(0 if success else 1)
