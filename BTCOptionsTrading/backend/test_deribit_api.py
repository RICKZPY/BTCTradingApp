"""
测试Deribit API连接
"""
import asyncio
import httpx

async def test_deribit_api():
    """测试Deribit API"""
    
    api_key = "vXkaBDto"
    api_secret = "J54Ccsff9g5PlYK-ELRVunkvnST-cZ6puVBXbhwYrnY"
    base_url = "https://test.deribit.com"
    
    client = httpx.AsyncClient(base_url=base_url, timeout=30.0)
    
    print("=" * 60)
    print("测试 Deribit 测试环境 API")
    print("=" * 60)
    
    # 测试1: 获取服务器时间（不需要认证）
    print("\n1. 测试公共API - 获取服务器时间...")
    try:
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "public/get_time"
        }
        response = await client.post("/api/v2/public/", json=request_data)
        data = response.json()
        if "result" in data:
            print(f"   ✅ 成功! 服务器时间: {data['result']}")
        else:
            print(f"   ❌ 失败: {data}")
    except Exception as e:
        print(f"   ❌ 错误: {str(e)}")
    
    # 测试2: 获取BTC指数价格
    print("\n2. 测试获取BTC指数价格...")
    try:
        request_data = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "public/get_index_price",
            "params": {"index_name": "btc_usd"}
        }
        response = await client.post("/api/v2/public/", json=request_data)
        data = response.json()
        if "result" in data:
            print(f"   ✅ 成功! BTC指数价格: ${data['result']['index_price']:,.2f}")
        else:
            print(f"   ❌ 失败: {data}")
    except Exception as e:
        print(f"   ❌ 错误: {str(e)}")
    
    # 测试3: 获取期权合约列表
    print("\n3. 测试获取BTC期权合约...")
    try:
        request_data = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "public/get_instruments",
            "params": {
                "currency": "BTC",
                "kind": "option",
                "expired": False
            }
        }
        response = await client.post("/api/v2/public/", json=request_data)
        data = response.json()
        if "result" in data:
            instruments = data['result']
            print(f"   ✅ 成功! 找到 {len(instruments)} 个期权合约")
            if instruments:
                print(f"   示例合约: {instruments[0]['instrument_name']}")
        else:
            print(f"   ❌ 失败: {data}")
    except Exception as e:
        print(f"   ❌ 错误: {str(e)}")
    
    # 测试4: 认证测试
    print("\n4. 测试API认证...")
    try:
        request_data = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "public/auth",
            "params": {
                "grant_type": "client_credentials",
                "client_id": api_key,
                "client_secret": api_secret
            }
        }
        response = await client.post("/api/v2/public/", json=request_data)
        data = response.json()
        if "result" in data:
            print(f"   ✅ 认证成功!")
            print(f"   Access Token: {data['result']['access_token'][:20]}...")
        else:
            print(f"   ❌ 认证失败: {data}")
    except Exception as e:
        print(f"   ❌ 错误: {str(e)}")
    
    await client.aclose()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_deribit_api())
