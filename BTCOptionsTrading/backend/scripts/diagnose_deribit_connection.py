#!/usr/bin/env python3
"""
Deribit连接诊断脚本

全面检查Deribit API连接问题
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.config.settings import Settings
from src.connectors.deribit_connector import DeribitConnector
from src.config.logging_config import get_logger
import httpx

logger = get_logger(__name__)


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


async def test_configuration():
    """测试配置"""
    print_section("1. 检查配置")
    
    settings = Settings()
    
    print(f"\n📋 Deribit配置:")
    print(f"  测试模式: {settings.deribit.test_mode}")
    print(f"  Base URL: {settings.deribit.base_url}")
    print(f"  WebSocket URL: {settings.deribit.websocket_url}")
    print(f"  API Key: {settings.deribit.api_key[:10]}..." if settings.deribit.api_key else "  API Key: (未设置)")
    print(f"  API Secret: {'*' * 10}..." if settings.deribit.api_secret else "  API Secret: (未设置)")
    print(f"  速率限制: {settings.deribit.rate_limit_requests} 请求/{settings.deribit.rate_limit_window}秒")
    
    # 检查配置一致性
    issues = []
    
    if settings.deribit.test_mode:
        if "test.deribit.com" not in settings.deribit.base_url:
            issues.append("⚠️  测试模式启用，但Base URL不是测试网地址")
    else:
        if "test.deribit.com" in settings.deribit.base_url:
            issues.append("⚠️  测试模式禁用，但Base URL是测试网地址")
        if not settings.deribit.api_key or not settings.deribit.api_secret:
            issues.append("⚠️  生产模式需要有效的API Key和Secret")
    
    if issues:
        print(f"\n⚠️  配置问题:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print(f"\n✅ 配置检查通过")
        return True


async def test_network_connectivity():
    """测试网络连接"""
    print_section("2. 检查网络连接")
    
    settings = Settings()
    base_url = settings.deribit.base_url
    
    print(f"\n🌐 测试连接到: {base_url}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 测试基本连接
            response = await client.get(f"{base_url}/api/v2/public/test")
            
            if response.status_code == 200:
                print(f"  ✅ 网络连接正常")
                print(f"  ✅ 状态码: {response.status_code}")
                return True
            else:
                print(f"  ❌ 连接失败")
                print(f"  ❌ 状态码: {response.status_code}")
                print(f"  ❌ 响应: {response.text[:200]}")
                return False
                
    except httpx.ConnectError as e:
        print(f"  ❌ 无法连接到Deribit")
        print(f"  ❌ 错误: {str(e)}")
        print(f"\n💡 可能的原因:")
        print(f"  1. 网络连接问题")
        print(f"  2. 防火墙阻止")
        print(f"  3. Deribit服务不可用")
        return False
    except Exception as e:
        print(f"  ❌ 连接测试失败: {str(e)}")
        return False


async def test_public_api():
    """测试公开API"""
    print_section("3. 测试公开API（无需认证）")
    
    connector = DeribitConnector()
    
    try:
        # 测试1: 获取服务器时间
        print(f"\n📅 测试1: 获取服务器时间")
        result = await connector._request("public/get_time")
        print(f"  ✅ 服务器时间: {result}")
        
        # 测试2: 获取BTC指数价格
        print(f"\n💰 测试2: 获取BTC指数价格")
        btc_price = await connector.get_index_price("BTC")
        print(f"  ✅ BTC价格: ${btc_price:,.2f}")
        
        # 验证价格合理性
        if 10000 < btc_price < 200000:
            print(f"  ✅ 价格在合理范围内")
        else:
            print(f"  ⚠️  价格可能异常: ${btc_price:,.2f}")
        
        # 测试3: 获取ETH指数价格
        print(f"\n💰 测试3: 获取ETH指数价格")
        eth_price = await connector.get_index_price("ETH")
        print(f"  ✅ ETH价格: ${eth_price:,.2f}")
        
        # 测试4: 获取可用合约
        print(f"\n📋 测试4: 获取BTC期权合约列表")
        result = await connector._request(
            "public/get_instruments",
            {"currency": "BTC", "kind": "option", "expired": False}
        )
        
        if result and len(result) > 0:
            print(f"  ✅ 找到 {len(result)} 个BTC期权合约")
            print(f"  ✅ 示例合约: {result[0].get('instrument_name', 'N/A')}")
        else:
            print(f"  ⚠️  未找到期权合约")
        
        print(f"\n✅ 公开API测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 公开API测试失败: {str(e)}")
        print(f"\n💡 可能的原因:")
        print(f"  1. API端点变更")
        print(f"  2. 请求格式错误")
        print(f"  3. 速率限制")
        return False
    finally:
        await connector.close()


async def test_options_chain():
    """测试期权链获取"""
    print_section("4. 测试期权链数据获取")
    
    connector = DeribitConnector()
    
    try:
        print(f"\n📊 获取BTC期权链...")
        contracts = await connector.get_options_chain("BTC")
        
        if contracts and len(contracts) > 0:
            print(f"  ✅ 成功获取 {len(contracts)} 个期权合约")
            
            # 显示第一个合约的详细信息
            first_contract = contracts[0]
            print(f"\n  示例合约详情:")
            print(f"    合约名称: {first_contract.instrument_name}")
            print(f"    执行价: ${first_contract.strike_price}")
            print(f"    类型: {first_contract.option_type.value}")
            print(f"    到期日: {first_contract.expiration_date}")
            print(f"    当前价格: ${first_contract.current_price}")
            print(f"    隐含波动率: {first_contract.implied_volatility:.2%}")
            print(f"    Delta: {first_contract.delta:.4f}")
            
            return True
        else:
            print(f"  ⚠️  未获取到期权合约数据")
            return False
            
    except Exception as e:
        print(f"\n❌ 期权链获取失败: {str(e)}")
        import traceback
        print(f"\n详细错误:")
        traceback.print_exc()
        return False
    finally:
        await connector.close()


async def test_api_endpoints():
    """测试后端API端点"""
    print_section("5. 测试后端API端点")
    
    base_url = "http://localhost:8000"
    
    print(f"\n🔌 测试连接到: {base_url}")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # 测试1: 健康检查
            print(f"\n❤️  测试1: 健康检查")
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ 健康检查通过")
                print(f"  ✅ 状态: {data.get('status', 'unknown')}")
            else:
                print(f"  ❌ 健康检查失败: {response.status_code}")
            
            # 测试2: 获取BTC价格
            print(f"\n💰 测试2: 获取BTC价格")
            response = await client.get(f"{base_url}/api/data/underlying-price/BTC")
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ 价格获取成功")
                print(f"  ✅ BTC价格: ${data['price']:,.2f}")
            else:
                print(f"  ❌ 价格获取失败: {response.status_code}")
                print(f"  ❌ 响应: {response.text[:200]}")
            
            # 测试3: 获取期权链
            print(f"\n📊 测试3: 获取期权链")
            response = await client.get(f"{base_url}/api/data/options-chain?currency=BTC")
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ 期权链获取成功")
                print(f"  ✅ 合约数量: {len(data)}")
            else:
                print(f"  ❌ 期权链获取失败: {response.status_code}")
                print(f"  ❌ 响应: {response.text[:200]}")
            
            return True
            
        except httpx.ConnectError:
            print(f"\n❌ 无法连接到后端API服务器")
            print(f"\n💡 请确保API服务器正在运行:")
            print(f"  cd backend")
            print(f"  python run_api.py")
            return False
        except Exception as e:
            print(f"\n❌ API端点测试失败: {str(e)}")
            return False


async def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("  🔍 Deribit连接诊断工具")
    print("=" * 70)
    
    results = {
        "配置检查": False,
        "网络连接": False,
        "公开API": False,
        "期权链": False,
        "后端API": False
    }
    
    # 运行所有测试
    results["配置检查"] = await test_configuration()
    results["网络连接"] = await test_network_connectivity()
    results["公开API"] = await test_public_api()
    results["期权链"] = await test_options_chain()
    results["后端API"] = await test_api_endpoints()
    
    # 总结
    print_section("诊断总结")
    
    print(f"\n测试结果:")
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print(f"\n" + "=" * 70)
        print(f"  ✅ 所有测试通过！系统可以正常获取实时市场数据")
        print(f"=" * 70)
    else:
        print(f"\n" + "=" * 70)
        print(f"  ❌ 部分测试失败，请根据上述信息排查问题")
        print(f"=" * 70)
        
        print(f"\n💡 常见问题和解决方案:")
        
        if not results["配置检查"]:
            print(f"\n1. 配置问题:")
            print(f"  - 检查 .env 文件中的 DERIBIT_TEST_MODE 设置")
            print(f"  - 确保 DERIBIT_BASE_URL 与测试模式匹配")
            print(f"  - 测试网: https://test.deribit.com")
            print(f"  - 生产网: https://www.deribit.com")
        
        if not results["网络连接"]:
            print(f"\n2. 网络连接问题:")
            print(f"  - 检查网络连接")
            print(f"  - 检查防火墙设置")
            print(f"  - 尝试访问: https://test.deribit.com")
        
        if not results["公开API"]:
            print(f"\n3. API访问问题:")
            print(f"  - 检查API端点是否正确")
            print(f"  - 查看日志文件: logs/app.log")
            print(f"  - 检查是否被速率限制")
        
        if not results["期权链"]:
            print(f"\n4. 期权链获取问题:")
            print(f"  - 可能是数据解析错误")
            print(f"  - 检查Deribit API响应格式是否变更")
            print(f"  - 查看详细错误信息")
        
        if not results["后端API"]:
            print(f"\n5. 后端API问题:")
            print(f"  - 确保后端服务器正在运行")
            print(f"  - 检查端口8000是否被占用")
            print(f"  - 查看后端日志")
    
    print()


if __name__ == "__main__":
    asyncio.run(main())
