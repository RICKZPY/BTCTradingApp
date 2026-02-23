"""
测试WebSocket实时数据推送功能
"""

import asyncio
import websockets
import json
from datetime import datetime


async def test_websocket_connection():
    """测试WebSocket连接和订阅"""
    uri = "ws://localhost:8000/ws"
    
    print("=" * 60)
    print("测试WebSocket实时数据推送")
    print("=" * 60)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("\n✓ WebSocket连接成功")
            
            # 测试1: Ping-Pong
            print("\n1. 测试Ping-Pong...")
            await websocket.send(json.dumps({
                "action": "ping"
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"   收到响应: {data['type']}")
            assert data['type'] == 'pong', "Ping-Pong测试失败"
            print("   ✓ Ping-Pong测试通过")
            
            # 测试2: 订阅市场数据
            print("\n2. 订阅市场数据频道...")
            await websocket.send(json.dumps({
                "action": "subscribe",
                "channel": "market_data"
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"   收到响应: {data['type']}")
            assert data['type'] == 'subscription_confirmed', "订阅确认失败"
            print("   ✓ 订阅确认成功")
            
            # 测试3: 接收市场数据推送
            print("\n3. 等待市场数据推送（最多15秒）...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                data = json.loads(response)
                print(f"   收到数据类型: {data['type']}")
                if data['type'] == 'market_data':
                    print(f"   BTC价格: ${data['data']['price']:,.2f}")
                    print(f"   时间戳: {data['timestamp']}")
                    print("   ✓ 市场数据推送成功")
                else:
                    print(f"   收到其他类型数据: {data}")
            except asyncio.TimeoutError:
                print("   ⚠ 超时未收到数据（可能API未配置）")
            
            # 测试4: 订阅期权链数据
            print("\n4. 订阅期权链频道...")
            await websocket.send(json.dumps({
                "action": "subscribe",
                "channel": "options_chain"
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"   收到响应: {data['type']}")
            assert data['type'] == 'subscription_confirmed', "订阅确认失败"
            print("   ✓ 订阅确认成功")
            
            # 测试5: 接收期权链数据推送
            print("\n5. 等待期权链数据推送（最多15秒）...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                data = json.loads(response)
                print(f"   收到数据类型: {data['type']}")
                if data['type'] == 'options_chain':
                    options_count = len(data['data'].get('options', []))
                    print(f"   期权合约数量: {options_count}")
                    print(f"   时间戳: {data['timestamp']}")
                    print("   ✓ 期权链数据推送成功")
                else:
                    print(f"   收到其他类型数据: {data}")
            except asyncio.TimeoutError:
                print("   ⚠ 超时未收到数据（可能API未配置）")
            
            # 测试6: 取消订阅
            print("\n6. 取消订阅市场数据...")
            await websocket.send(json.dumps({
                "action": "unsubscribe",
                "channel": "market_data"
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"   收到响应: {data['type']}")
            assert data['type'] == 'subscription_cancelled', "取消订阅失败"
            print("   ✓ 取消订阅成功")
            
            # 测试7: 错误处理
            print("\n7. 测试错误处理...")
            await websocket.send(json.dumps({
                "action": "invalid_action"
            }))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"   收到响应: {data['type']}")
            assert data['type'] == 'error', "错误处理测试失败"
            print("   ✓ 错误处理正常")
            
            print("\n" + "=" * 60)
            print("✓ WebSocket测试完成！")
            print("=" * 60)
            
    except websockets.exceptions.WebSocketException as e:
        print(f"\n✗ WebSocket连接错误: {str(e)}")
        print("\n请确保后端服务正在运行:")
        print("  cd BTCOptionsTrading/backend")
        print("  python run_api.py")
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_multiple_clients():
    """测试多个客户端同时连接"""
    uri = "ws://localhost:8000/ws"
    
    print("\n" + "=" * 60)
    print("测试多客户端连接")
    print("=" * 60)
    
    async def client_task(client_id: int):
        """单个客户端任务"""
        try:
            async with websockets.connect(uri) as websocket:
                print(f"\n客户端 {client_id}: 已连接")
                
                # 订阅市场数据
                await websocket.send(json.dumps({
                    "action": "subscribe",
                    "channel": "market_data"
                }))
                response = await websocket.recv()
                print(f"客户端 {client_id}: 订阅确认")
                
                # 接收3条消息
                for i in range(3):
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                        data = json.loads(response)
                        if data['type'] == 'market_data':
                            print(f"客户端 {client_id}: 收到市场数据 #{i+1}")
                    except asyncio.TimeoutError:
                        print(f"客户端 {client_id}: 超时")
                        break
                
                print(f"客户端 {client_id}: 断开连接")
                
        except Exception as e:
            print(f"客户端 {client_id}: 错误 - {str(e)}")
    
    try:
        # 创建3个并发客户端
        tasks = [client_task(i) for i in range(1, 4)]
        await asyncio.gather(*tasks)
        
        print("\n✓ 多客户端测试完成")
        
    except Exception as e:
        print(f"\n✗ 多客户端测试失败: {str(e)}")


if __name__ == "__main__":
    print("\n开始WebSocket测试...")
    print("确保后端服务正在运行: python run_api.py\n")
    
    # 运行基础测试
    asyncio.run(test_websocket_connection())
    
    # 运行多客户端测试
    print("\n按Enter键继续多客户端测试，或Ctrl+C退出...")
    try:
        input()
        asyncio.run(test_multiple_clients())
    except KeyboardInterrupt:
        print("\n测试已取消")
