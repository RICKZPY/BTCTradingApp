"""
测试策略风险计算API
"""

import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/strategies"


def test_single_leg_call_risk():
    """测试单腿看涨期权风险计算"""
    print("\n=== 测试单腿看涨期权风险计算 ===")
    
    expiry = (datetime.now() + timedelta(days=30)).isoformat()
    
    payload = {
        "legs": [
            {
                "option_contract": {
                    "instrument_name": "BTC-30000-C",
                    "underlying": "BTC",
                    "option_type": "call",
                    "strike_price": 30000.0,
                    "expiration_date": expiry
                },
                "action": "buy",
                "quantity": 1
            }
        ],
        "spot_price": 29000.0,
        "risk_free_rate": 0.05,
        "volatility": 0.8
    }
    
    response = requests.post(f"{BASE_URL}/calculate-risk", json=payload)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Greeks: {result['greeks']}")
        print(f"初始成本: ${result['initial_cost']:.2f}")
        print(f"最大收益: ${result['max_profit']:.2f}")
        print(f"最大损失: ${result['max_loss']:.2f}")
        print(f"盈亏平衡点: {result['breakeven_points']}")
        print(f"风险收益比: {result['risk_reward_ratio']:.2f}")
        print(f"盈利概率: {result['probability_of_profit']:.1f}%")
        
        # 验证单腿看涨期权的特性
        assert result['greeks']['delta'] > 0, "看涨期权Delta应该为正"
        assert result['max_loss'] < 0, "买入期权最大损失应该为负（成本）"
        assert result['max_profit'] > 0, "看涨期权最大收益应该为正"
        print("✓ 测试通过")
    else:
        print(f"错误: {response.json()}")


def test_straddle_risk():
    """测试跨式策略风险计算"""
    print("\n=== 测试跨式策略风险计算 ===")
    
    expiry = (datetime.now() + timedelta(days=30)).isoformat()
    spot_price = 29000.0
    
    payload = {
        "legs": [
            {
                "option_contract": {
                    "instrument_name": "BTC-29000-C",
                    "underlying": "BTC",
                    "option_type": "call",
                    "strike_price": 29000.0,
                    "expiration_date": expiry
                },
                "action": "buy",
                "quantity": 1
            },
            {
                "option_contract": {
                    "instrument_name": "BTC-29000-P",
                    "underlying": "BTC",
                    "option_type": "put",
                    "strike_price": 29000.0,
                    "expiration_date": expiry
                },
                "action": "buy",
                "quantity": 1
            }
        ],
        "spot_price": spot_price,
        "risk_free_rate": 0.05,
        "volatility": 0.8
    }
    
    response = requests.post(f"{BASE_URL}/calculate-risk", json=payload)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Greeks: {result['greeks']}")
        print(f"初始成本: ${result['initial_cost']:.2f}")
        print(f"最大收益: ${result['max_profit']:.2f}")
        print(f"最大损失: ${result['max_loss']:.2f}")
        print(f"盈亏平衡点: {result['breakeven_points']}")
        print(f"风险收益比: {result['risk_reward_ratio']:.2f}")
        
        # 验证跨式策略的特性
        assert abs(result['greeks']['delta']) < 0.2, "ATM跨式策略Delta应该接近0"
        assert result['greeks']['gamma'] > 0, "买入跨式策略Gamma应该为正"
        assert result['greeks']['vega'] > 0, "买入跨式策略Vega应该为正"
        assert len(result['breakeven_points']) == 2, "跨式策略应该有2个盈亏平衡点"
        print("✓ 测试通过")
    else:
        print(f"错误: {response.json()}")


def test_iron_condor_risk():
    """测试铁鹰策略风险计算"""
    print("\n=== 测试铁鹰策略风险计算 ===")
    
    expiry = (datetime.now() + timedelta(days=30)).isoformat()
    
    payload = {
        "legs": [
            {
                "option_contract": {
                    "instrument_name": "BTC-27000-P",
                    "underlying": "BTC",
                    "option_type": "put",
                    "strike_price": 27000.0,
                    "expiration_date": expiry
                },
                "action": "buy",
                "quantity": 1
            },
            {
                "option_contract": {
                    "instrument_name": "BTC-28000-P",
                    "underlying": "BTC",
                    "option_type": "put",
                    "strike_price": 28000.0,
                    "expiration_date": expiry
                },
                "action": "sell",
                "quantity": 1
            },
            {
                "option_contract": {
                    "instrument_name": "BTC-30000-C",
                    "underlying": "BTC",
                    "option_type": "call",
                    "strike_price": 30000.0,
                    "expiration_date": expiry
                },
                "action": "sell",
                "quantity": 1
            },
            {
                "option_contract": {
                    "instrument_name": "BTC-31000-C",
                    "underlying": "BTC",
                    "option_type": "call",
                    "strike_price": 31000.0,
                    "expiration_date": expiry
                },
                "action": "buy",
                "quantity": 1
            }
        ],
        "spot_price": 29000.0,
        "risk_free_rate": 0.05,
        "volatility": 0.8
    }
    
    response = requests.post(f"{BASE_URL}/calculate-risk", json=payload)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Greeks: {result['greeks']}")
        print(f"初始成本: ${result['initial_cost']:.2f}")
        print(f"最大收益: ${result['max_profit']:.2f}")
        print(f"最大损失: ${result['max_loss']:.2f}")
        print(f"盈亏平衡点: {result['breakeven_points']}")
        print(f"风险收益比: {result['risk_reward_ratio']:.2f}")
        
        # 验证铁鹰策略的特性
        assert result['initial_cost'] < 0, "铁鹰策略应该收取权利金（负成本）"
        assert result['max_profit'] > 0, "铁鹰策略最大收益应该为正"
        assert result['max_loss'] < 0, "铁鹰策略最大损失应该为负"
        print("✓ 测试通过")
    else:
        print(f"错误: {response.json()}")


def test_strangle_risk():
    """测试宽跨式策略风险计算"""
    print("\n=== 测试宽跨式策略风险计算 ===")
    
    expiry = (datetime.now() + timedelta(days=30)).isoformat()
    
    payload = {
        "legs": [
            {
                "option_contract": {
                    "instrument_name": "BTC-30000-C",
                    "underlying": "BTC",
                    "option_type": "call",
                    "strike_price": 30000.0,
                    "expiration_date": expiry
                },
                "action": "buy",
                "quantity": 1
            },
            {
                "option_contract": {
                    "instrument_name": "BTC-28000-P",
                    "underlying": "BTC",
                    "option_type": "put",
                    "strike_price": 28000.0,
                    "expiration_date": expiry
                },
                "action": "buy",
                "quantity": 1
            }
        ],
        "spot_price": 29000.0,
        "risk_free_rate": 0.05,
        "volatility": 0.8
    }
    
    response = requests.post(f"{BASE_URL}/calculate-risk", json=payload)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Greeks: {result['greeks']}")
        print(f"初始成本: ${result['initial_cost']:.2f}")
        print(f"最大收益: ${result['max_profit']:.2f}")
        print(f"最大损失: ${result['max_loss']:.2f}")
        print(f"盈亏平衡点: {result['breakeven_points']}")
        print(f"风险收益比: {result['risk_reward_ratio']:.2f}")
        
        # 验证宽跨式策略的特性
        assert result['max_loss'] < 0, "买入宽跨式最大损失应该为负"
        assert len(result['breakeven_points']) == 2, "宽跨式策略应该有2个盈亏平衡点"
        print("✓ 测试通过")
    else:
        print(f"错误: {response.json()}")


if __name__ == "__main__":
    print("开始测试策略风险计算API...")
    print("确保后端服务正在运行: http://localhost:8000")
    
    try:
        test_single_leg_call_risk()
        test_straddle_risk()
        test_iron_condor_risk()
        test_strangle_risk()
        
        print("\n" + "="*50)
        print("所有测试通过！✓")
        print("="*50)
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
    except requests.exceptions.ConnectionError:
        print("\n✗ 无法连接到后端服务，请确保服务正在运行")
    except Exception as e:
        print(f"\n✗ 测试出错: {e}")
        import traceback
        traceback.print_exc()
