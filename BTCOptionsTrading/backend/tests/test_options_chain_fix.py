"""
测试期权链API修复
"""
import asyncio
from src.connectors.deribit_connector import DeribitConnector
from src.api.routes.data import OptionChainResponse

async def test_options_chain():
    """测试期权链数据获取"""
    print("测试期权链数据获取...")
    
    connector = DeribitConnector()
    
    try:
        # 测试获取期权链
        print("\n1. 获取期权链数据...")
        options_data = await connector.get_options_chain("BTC")
        print(f"   成功获取 {len(options_data)} 个期权合约")
        
        if options_data:
            option = options_data[0]
            print(f"\n   第一个合约示例:")
            print(f"   - 合约名称: {option.instrument_name}")
            print(f"   - 执行价: {option.strike_price}")
            print(f"   - 期权类型: {option.option_type.value}")
            print(f"   - 到期日: {option.expiration_date}")
            print(f"   - 当前价格: {option.current_price}")
            print(f"   - 隐含波动率: {option.implied_volatility}")
            
            # 测试转换为API响应格式
            print("\n2. 测试转换为API响应格式...")
            response = OptionChainResponse(
                instrument_name=option.instrument_name,
                strike=float(option.strike_price),
                option_type=option.option_type.value,
                expiration_timestamp=int(option.expiration_date.timestamp()),
                bid_price=float(option.bid_price) if option.bid_price else None,
                ask_price=float(option.ask_price) if option.ask_price else None,
                last_price=float(option.last_price) if option.last_price else None,
                mark_price=float(option.current_price) if option.current_price else None,
                implied_volatility=option.implied_volatility,
                delta=option.delta,
                gamma=option.gamma,
                theta=option.theta,
                vega=option.vega,
                volume=option.volume,
                open_interest=option.open_interest
            )
            print(f"   ✓ 成功转换为API响应格式")
            print(f"   - strike: {response.strike}")
            print(f"   - option_type: {response.option_type}")
            print(f"   - expiration_timestamp: {response.expiration_timestamp}")
        
        # 测试获取指数价格
        print("\n3. 获取指数价格...")
        index_price = await connector.get_index_price("BTC")
        print(f"   BTC指数价格: ${index_price:,.2f}")
        
        print("\n✅ 所有测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await connector.close()

if __name__ == "__main__":
    asyncio.run(test_options_chain())
