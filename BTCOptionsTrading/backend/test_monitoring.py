"""
监控系统测试脚本
测试性能监控、健康检查和统计功能
"""

import sys
import time
import requests
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:8000"


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_health_check():
    """测试健康检查接口"""
    print_section("测试 1: 健康检查")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 服务状态: {data['status']}")
            print(f"✓ 时间戳: {data['timestamp']}")
            print(f"✓ 服务名称: {data['service']}")
            
            if 'checks' in data:
                print("\n健康检查项:")
                for check, passed in data['checks'].items():
                    status = "✓" if passed else "✗"
                    print(f"  {status} {check}: {'通过' if passed else '失败'}")
            
            if 'issues' in data and data['issues']:
                print("\n发现的问题:")
                for issue in data['issues']:
                    print(f"  ⚠ {issue}")
            
            return True
        else:
            print(f"✗ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ 错误: {str(e)}")
        return False


def test_system_status():
    """测试系统状态接口"""
    print_section("测试 2: 系统状态")
    
    try:
        response = requests.get(f"{BASE_URL}/status")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 系统状态: {data['status']}")
            
            if 'uptime' in data:
                uptime = data['uptime']
                print(f"\n运行时间:")
                print(f"  启动时间: {uptime['start_time']}")
                print(f"  运行时长: {uptime['uptime_formatted']}")
            
            if 'performance' in data:
                perf = data['performance']
                print(f"\n性能指标:")
                print(f"  CPU使用率: {perf['cpu_percent']:.1f}%")
                print(f"  内存使用率: {perf['memory_percent']:.1f}%")
                print(f"  内存使用量: {perf['memory_used_mb']:.1f} MB")
                print(f"  磁盘使用率: {perf['disk_usage_percent']:.1f}%")
                print(f"  活动连接数: {perf['active_connections']}")
            
            if 'requests' in data:
                req = data['requests']
                print(f"\n请求统计:")
                print(f"  总请求数: {req['total']}")
                print(f"  错误数: {req['errors']}")
                print(f"  错误率: {req['error_rate']:.2%}")
                print(f"  平均响应时间: {req['avg_response_time_ms']:.2f} ms")
            
            if 'database' in data:
                db = data['database']
                print(f"\n数据库状态:")
                print(f"  连接状态: {'已连接' if db['connected'] else '未连接'}")
                if 'stats' in db:
                    stats = db['stats']
                    print(f"  策略数: {stats.get('strategies', 0)}")
                    print(f"  回测数: {stats.get('backtests', 0)}")
                    print(f"  持仓数: {stats.get('positions', 0)}")
            
            return True
        else:
            print(f"✗ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ 错误: {str(e)}")
        return False


def test_metrics():
    """测试性能指标接口"""
    print_section("测试 3: 性能指标")
    
    try:
        response = requests.get(f"{BASE_URL}/metrics")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 时间戳: {data['timestamp']}")
            print(f"\n当前指标:")
            print(f"  CPU: {data['cpu_percent']:.1f}%")
            print(f"  内存: {data['memory_percent']:.1f}% ({data['memory_used_mb']:.1f} MB)")
            print(f"  可用内存: {data['memory_available_mb']:.1f} MB")
            print(f"  磁盘: {data['disk_usage_percent']:.1f}%")
            print(f"  连接数: {data['active_connections']}")
            print(f"  请求数: {data['request_count']}")
            print(f"  错误数: {data['error_count']}")
            print(f"  平均响应时间: {data['avg_response_time_ms']:.2f} ms")
            
            return True
        else:
            print(f"✗ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ 错误: {str(e)}")
        return False


def test_metrics_history():
    """测试历史指标接口"""
    print_section("测试 4: 历史指标")
    
    try:
        # 获取最近5分钟的数据
        response = requests.get(f"{BASE_URL}/metrics/history?minutes=5")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 时间范围: 最近 {data['period_minutes']} 分钟")
            print(f"✓ 数据点数: {data['data_points']}")
            
            if data['data_points'] > 0:
                history = data['history']
                print(f"\n最新数据点:")
                latest = history[-1]
                print(f"  时间: {latest['timestamp']}")
                print(f"  CPU: {latest['cpu_percent']:.1f}%")
                print(f"  内存: {latest['memory_percent']:.1f}%")
                print(f"  请求数: {latest['request_count']}")
            
            return True
        else:
            print(f"✗ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ 错误: {str(e)}")
        return False


def test_statistics():
    """测试统计信息接口"""
    print_section("测试 5: 统计信息")
    
    try:
        response = requests.get(f"{BASE_URL}/statistics")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'uptime' in data:
                uptime = data['uptime']
                print(f"✓ 运行时长: {uptime['uptime_formatted']}")
            
            if 'requests' in data:
                req = data['requests']
                print(f"\n请求统计:")
                print(f"  总请求数: {req['total_requests']}")
                print(f"  总错误数: {req['total_errors']}")
                print(f"  错误率: {req['error_rate']:.2%}")
                print(f"  成功率: {req['success_rate']:.2%}")
                print(f"  平均响应时间: {req['avg_response_time_ms']:.2f} ms")
                print(f"  最小响应时间: {req['min_response_time_ms']:.2f} ms")
                print(f"  最大响应时间: {req['max_response_time_ms']:.2f} ms")
            
            return True
        else:
            print(f"✗ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ 错误: {str(e)}")
        return False


def test_load_simulation():
    """测试负载模拟"""
    print_section("测试 6: 负载模拟")
    
    print("发送10个并发请求...")
    
    try:
        start_time = time.time()
        
        # 发送多个请求
        for i in range(10):
            response = requests.get(f"{BASE_URL}/health")
            print(f"  请求 {i+1}: {response.status_code} - {response.headers.get('X-Response-Time', 'N/A')}")
        
        elapsed = time.time() - start_time
        print(f"\n✓ 完成10个请求，耗时: {elapsed:.2f}秒")
        
        # 检查统计信息
        time.sleep(1)
        response = requests.get(f"{BASE_URL}/statistics")
        if response.status_code == 200:
            data = response.json()
            req = data['requests']
            print(f"\n更新后的统计:")
            print(f"  总请求数: {req['total_requests']}")
            print(f"  平均响应时间: {req['avg_response_time_ms']:.2f} ms")
        
        return True
        
    except Exception as e:
        print(f"✗ 错误: {str(e)}")
        return False


def test_response_time_header():
    """测试响应时间头"""
    print_section("测试 7: 响应时间头")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        
        response_time = response.headers.get('X-Response-Time')
        if response_time:
            print(f"✓ 响应时间头: {response_time}")
            return True
        else:
            print("✗ 未找到响应时间头")
            return False
            
    except Exception as e:
        print(f"✗ 错误: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("  BTC Options Trading System - 监控系统测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API地址: {BASE_URL}")
    
    # 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print("✓ API服务正在运行")
    except Exception as e:
        print(f"\n✗ 无法连接到API服务: {str(e)}")
        print("\n请确保后端服务正在运行:")
        print("  cd BTCOptionsTrading/backend")
        print("  python run_api.py")
        sys.exit(1)
    
    # 运行测试
    results = []
    
    results.append(("健康检查", test_health_check()))
    results.append(("系统状态", test_system_status()))
    results.append(("性能指标", test_metrics()))
    results.append(("历史指标", test_metrics_history()))
    results.append(("统计信息", test_statistics()))
    results.append(("负载模拟", test_load_simulation()))
    results.append(("响应时间头", test_response_time_header()))
    
    # 打印测试结果
    print_section("测试结果汇总")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status}: {test_name}")
    
    print(f"\n总计: {passed}/{total} 测试通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！监控系统工作正常。")
        return 0
    else:
        print(f"\n⚠ {total - passed} 个测试失败，请检查日志。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
