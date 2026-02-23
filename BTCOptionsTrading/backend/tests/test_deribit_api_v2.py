"""
测试Deribit API连接 - 使用不同的方法
"""
import asyncio
import httpx

async def test_deribit_api_simple():
    """使用简单的GET请求测试Deribit API"""
    
    base_url = "https://test.deribit.com"
    client = httpx.AsyncClient(base_url=base_url, timeout=30.0)
    
    print("=" * 60)
    print("测试 Deribit 测试环境 API (简化版)")
    print("=" * 60)
    
    # 测试1: 使用GET请求获取服务器时间
    print("\n1. 测试 GET /api/v2/public/get_time")
    try:
        response = await client.get("/api/v2/public/get_time")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 成功: {data}")
        else:
            print(f"   ❌ 失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 错误: {str(e)}")
    
    # 测试2: 获取BTC指数价格
    print("\n2. 测试 GET /api/v2/public/get_index_price?index_name=btc_usd")
    try:
        response = await client.get("/api/v2/public/get_index_price?index_name=btc_usd")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 成功: {data}")
        else:
            print(f"   ❌ 失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 错误: {str(e)}")
    
    # 测试3: 获取期权合约
    print("\n3. 测试 GET /api/v2/public/get_instruments?currency=BTC&kind=option")
    try:
        response = await client.get("/api/v2/public/get_instruments?currency=BTC&kind=option&expired=false")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'result' in data:
                print(f"   ✅ 成功: 找到 {len(data['result'])} 个合约")
                if data['result']:
                    print(f"   示例: {data['result'][0]['instrument_name']}")
            else:
                print(f"   数据: {data}")
        else:
            print(f"   ❌ 失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 错误: {str(e)}")
    
    # 测试4: 测试主网API
    print("\n4. 测试主网 API (https://www.deribit.com)")
    try:
        prod_client = httpx.AsyncClient(base_url="https://www.deribit.com", timeout=30.0)
        response = await prod_client.get("/api/v2/public/get_index_price?index_name=btc_usd")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 主网API可用: {data}")
        else:
            print(f"   ❌ 失败: {response.text}")
        await prod_client.aclose()
    except Exception as e:
        print(f"   ❌ 错误: {str(e)}")
    
    await client.aclose()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_deribit_api_simple())
