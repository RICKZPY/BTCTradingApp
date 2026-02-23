#!/usr/bin/env python3
"""
测试标的资产价格API

检查underlying-price端点是否正常工作
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.connectors.deribit_connector import DeribitConnector
from src.config.logging_config import get_logger

logger = get_logger(__name__)


async def test_index_price():
    """测试获取指数价格"""
    print("=" * 60)
    print("测试标的资产价格获取")
    print("=" * 60)
    print()
    
    connector = DeribitConnector()
    
    try:
        # 测试BTC价格
        print("1. 获取BTC指数价格...")
        btc_price = await connector.get_index_price("BTC")
        print(f"   ✅ BTC价格: ${btc_price:,.2f}")
        print()
        
        # 测试ETH价格
        print("2. 获取ETH指数价格...")
        eth_price = await connector.get_index_price("ETH")
        print(f"   ✅ ETH价格: ${eth_price:,.2f}")
        print()
        
        # 验证价格合理性
        print("3. 验证价格合理性...")
        if btc_price > 0 and btc_price < 1000000:
            print(f"   ✅ BTC价格在合理范围内")
        else:
            print(f"   ⚠️  BTC价格异常: ${btc_price}")
        
        if eth_price > 0 and eth_price < 100000:
            print(f"   ✅ ETH价格在合理范围内")
        else:
            print(f"   ⚠️  ETH价格异常: ${eth_price}")
        
        print()
        print("=" * 60)
        print("✅ 测试完成！价格获取正常")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ 测试失败: {str(e)}")
        print("=" * 60)
        print()
        print("可能的原因:")
        print("  1. 网络连接问题")
        print("  2. Deribit API不可用")
        print("  3. API配置错误")
        print()
        print("解决方法:")
        print("  1. 检查网络连接")
        print("  2. 检查.env文件中的Deribit配置")
        print("  3. 确认Deribit API服务正常")
        print()
        sys.exit(1)
    
    finally:
        await connector.close()


async def test_api_endpoint():
    """测试API端点"""
    import httpx
    
    print()
    print("=" * 60)
    print("测试API端点")
    print("=" * 60)
    print()
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        try:
            # 测试BTC价格端点
            print("1. 测试 /api/data/underlying-price/BTC ...")
            response = await client.get(f"{base_url}/api/data/underlying-price/BTC")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 状态码: {response.status_code}")
                print(f"   ✅ 响应数据: {data}")
                print(f"   ✅ BTC价格: ${data['price']:,.2f}")
            else:
                print(f"   ❌ 状态码: {response.status_code}")
                print(f"   ❌ 响应: {response.text}")
            
            print()
            
            # 测试ETH价格端点
            print("2. 测试 /api/data/underlying-price/ETH ...")
            response = await client.get(f"{base_url}/api/data/underlying-price/ETH")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 状态码: {response.status_code}")
                print(f"   ✅ 响应数据: {data}")
                print(f"   ✅ ETH价格: ${data['price']:,.2f}")
            else:
                print(f"   ❌ 状态码: {response.status_code}")
                print(f"   ❌ 响应: {response.text}")
            
            print()
            print("=" * 60)
            print("✅ API端点测试完成！")
            print("=" * 60)
            
        except httpx.ConnectError:
            print()
            print("=" * 60)
            print("❌ 无法连接到API服务器")
            print("=" * 60)
            print()
            print("请确保API服务器正在运行:")
            print("  cd backend")
            print("  python run_api.py")
            print()
        except Exception as e:
            print()
            print("=" * 60)
            print(f"❌ API测试失败: {str(e)}")
            print("=" * 60)


async def main():
    """主函数"""
    print()
    print("🔍 BTC Options Trading System - 价格API测试")
    print()
    
    # 测试1: 直接调用连接器
    await test_index_price()
    
    # 测试2: 测试API端点
    await test_api_endpoint()
    
    print()
    print("如果所有测试都通过，但前端仍然显示$0，请检查:")
    print("  1. 浏览器控制台是否有错误")
    print("  2. 前端是否正确连接到后端API")
    print("  3. CORS配置是否正确")
    print()


if __name__ == "__main__":
    asyncio.run(main())
