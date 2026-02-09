#!/usr/bin/env python3
"""
测试真实数据获取
验证Deribit API连接和数据获取功能
"""

import asyncio
from src.connectors.deribit_connector import DeribitConnector
from src.config.settings import settings

async def test_real_data():
    """测试真实数据获取"""
    print("=" * 60)
    print("测试Deribit真实数据获取")
    print("=" * 60)
    
    # 检查API配置
    print("\n1. 检查API配置...")
    print(f"   Base URL: {settings.deribit.base_url}")
    print(f"   Test Mode: {settings.deribit.test_mode}")
    print(f"   API Key: {settings.deribit.api_key[:10]}..." if settings.deribit.api_key else "   API Key: 未配置")
    
    if not settings.deribit.api_key or not settings.deribit.api_secret:
        print("\n⚠️  警告: API密钥未配置")
        print("   请在前端设置页面配置Deribit API密钥")
        print("   或直接编辑 .env 文件")
        return False
    
    # 创建连接器
    print("\n2. 创建Deribit连接器...")
    connector = DeribitConnector()
    print("   ✓ 连接器创建成功")
    
    # 测试获取BTC指数价格
    print("\n3. 获取BTC指数价格...")
    try:
        btc_price = await connector.get_index_price("BTC")
        print(f"   ✓ BTC价格: ${btc_price:,.2f}")
    except Exception as e:
        print(f"   ✗ 获取失败: {str(e)}")
        return False
    
    # 测试获取期权链
    print("\n4. 获取BTC期权链...")
    try:
        options = await connector.get_options_chain("BTC", "option")
        print(f"   ✓ 获取到 {len(options)} 个期权合约")
        
        if options:
            # 显示第一个期权的详细信息
            first_option = options[0]
            print(f"\n   示例期权合约:")
            print(f"   - 合约名称: {first_option.get('instrument_name', 'N/A')}")
            print(f"   - 执行价: ${first_option.get('strike', 0):,.0f}")
            print(f"   - 类型: {first_option.get('option_type', 'N/A')}")
            print(f"   - 标记价格: ${first_option.get('mark_price', 0):,.4f}")
            print(f"   - 隐含波动率: {first_option.get('mark_iv', 0) * 100:.1f}%")
            
            greeks = first_option.get('greeks', {})
            if greeks:
                print(f"   - Delta: {greeks.get('delta', 0):.4f}")
                print(f"   - Gamma: {greeks.get('gamma', 0):.4f}")
                print(f"   - Vega: {greeks.get('vega', 0):.4f}")
    except Exception as e:
        print(f"   ✗ 获取失败: {str(e)}")
        return False
    
    # 测试获取波动率曲面
    print("\n5. 获取波动率曲面...")
    try:
        surface = await connector.get_volatility_surface("BTC")
        print(f"   ✓ 波动率曲面数据获取成功")
        if surface:
            print(f"   - 数据点数量: {len(surface)}")
    except Exception as e:
        print(f"   ✗ 获取失败: {str(e)}")
        # 波动率曲面可能不是所有账户都能访问
        print("   ℹ️  注意: 波动率曲面可能需要特定权限")
    
    print("\n" + "=" * 60)
    print("✓ 真实数据测试完成！")
    print("=" * 60)
    print("\n提示:")
    print("- 如果所有测试通过，说明API配置正确")
    print("- 前端期权链页面将显示真实数据")
    print("- 可以开始使用真实数据进行分析")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_real_data())
        if not success:
            print("\n建议:")
            print("1. 访问 http://localhost:3000")
            print("2. 进入'设置'Tab")
            print("3. 配置Deribit API密钥")
            print("4. 重启后端服务")
            print("5. 重新运行此测试")
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
