"""
API使用示例
演示如何使用REST API接口
"""

import requests
import json
from datetime import datetime, timedelta


# API基础URL
BASE_URL = "http://localhost:8000"


def test_health_check():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2)}")


def test_system_status():
    """测试系统状态"""
    print("\n=== 测试系统状态 ===")
    response = requests.get(f"{BASE_URL}/status")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2)}")


def test_create_strategy():
    """测试创建策略"""
    print("\n=== 测试创建策略 ===")
    
    expiry = (datetime.now() + timedelta(days=30)).isoformat()
    strategy_data = {
        "name": "买入看涨期权",
        "description": "看涨BTC，买入执行价45000的看涨期权",
        "strategy_type": "single_leg",
        "legs": [
            {
                "option_contract": {
                    "instrument_name": "BTC-30DEC23-45000-C",
                    "underlying": "BTC",
                    "option_type": "call",
                    "strike_price": 45000.0,
                    "expiration_date": expiry
                },
                "action": "buy",
                "quantity": 1
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/api/strategies/", json=strategy_data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        return response.json()["id"]
    return None


def test_list_strategies():
    """测试获取策略列表"""
    print("\n=== 测试获取策略列表 ===")
    response = requests.get(f"{BASE_URL}/api/strategies/")
    print(f"状态码: {response.status_code}")
    strategies = response.json()
    print(f"策略数量: {len(strategies)}")
    for strategy in strategies:
        print(f"  - {strategy['name']} ({strategy['strategy_type']})")


def test_get_strategy(strategy_id):
    """测试获取策略详情"""
    print(f"\n=== 测试获取策略详情 (ID: {strategy_id}) ===")
    response = requests.get(f"{BASE_URL}/api/strategies/{strategy_id}")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_strategy_templates():
    """测试获取策略模板"""
    print("\n=== 测试获取策略模板 ===")
    response = requests.get(f"{BASE_URL}/api/strategies/templates/list")
    print(f"状态码: {response.status_code}")
    templates = response.json()["templates"]
    print(f"模板数量: {len(templates)}")
    for template in templates:
        print(f"  - {template['name']}: {template['description']}")


def test_calculate_greeks():
    """测试计算希腊字母"""
    print("\n=== 测试计算希腊字母 ===")
    
    greeks_request = {
        "spot_price": 40000.0,
        "strike_price": 42000.0,
        "time_to_expiry": 0.25,  # 3个月
        "volatility": 0.8,  # 80%波动率
        "risk_free_rate": 0.05,
        "option_type": "call"
    }
    
    response = requests.post(f"{BASE_URL}/api/data/calculate-greeks", json=greeks_request)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"期权价格: ${data['price']:.2f}")
        print(f"Delta: {data['delta']:.4f}")
        print(f"Gamma: {data['gamma']:.6f}")
        print(f"Theta: {data['theta']:.4f}")
        print(f"Vega: {data['vega']:.4f}")
        print(f"Rho: {data['rho']:.4f}")


def test_run_backtest(strategy_id):
    """测试运行回测"""
    print(f"\n=== 测试运行回测 (策略ID: {strategy_id}) ===")
    
    backtest_request = {
        "strategy_id": strategy_id,
        "start_date": (datetime.now() - timedelta(days=60)).isoformat(),
        "end_date": (datetime.now() - timedelta(days=30)).isoformat(),
        "initial_capital": 100000.0,
        "underlying_symbol": "BTC"
    }
    
    response = requests.post(f"{BASE_URL}/api/backtest/run", json=backtest_request)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"回测ID: {result['id']}")
        print(f"初始资金: ${result['initial_capital']:.2f}")
        print(f"最终资金: ${result['final_capital']:.2f}")
        print(f"总收益率: {result['total_return']:.2%}")
        if result['sharpe_ratio']:
            print(f"夏普比率: {result['sharpe_ratio']:.4f}")
        if result['max_drawdown']:
            print(f"最大回撤: {result['max_drawdown']:.2%}")
        if result['win_rate']:
            print(f"胜率: {result['win_rate']:.2%}")
        print(f"总交易数: {result['total_trades']}")
        return result['id']
    return None


def test_list_backtest_results():
    """测试获取回测结果列表"""
    print("\n=== 测试获取回测结果列表 ===")
    response = requests.get(f"{BASE_URL}/api/backtest/results")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        results = response.json()
        print(f"回测结果数量: {len(results)}")
        for result in results:
            print(f"  - 回测ID: {result['id'][:8]}... | 收益率: {result['total_return']:.2%}")


def test_delete_strategy(strategy_id):
    """测试删除策略"""
    print(f"\n=== 测试删除策略 (ID: {strategy_id}) ===")
    response = requests.delete(f"{BASE_URL}/api/strategies/{strategy_id}")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def main():
    """主函数"""
    print("=" * 60)
    print("BTC期权交易系统 API 使用示例")
    print("=" * 60)
    
    try:
        # 1. 健康检查
        test_health_check()
        test_system_status()
        
        # 2. 策略管理
        test_strategy_templates()
        strategy_id = test_create_strategy()
        test_list_strategies()
        
        if strategy_id:
            test_get_strategy(strategy_id)
            
            # 3. 回测
            backtest_id = test_run_backtest(strategy_id)
            test_list_backtest_results()
            
            # 4. 数据分析
            test_calculate_greeks()
            
            # 5. 清理
            test_delete_strategy(strategy_id)
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n错误: 无法连接到API服务器")
        print("请确保API服务器正在运行: python run_api.py")
    except Exception as e:
        print(f"\n错误: {str(e)}")


if __name__ == "__main__":
    main()
