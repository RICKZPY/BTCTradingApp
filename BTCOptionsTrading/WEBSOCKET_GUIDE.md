# WebSocket实时数据推送指南

## 概述

系统现在支持WebSocket实时数据推送，可以实时接收市场数据和期权链更新，无需手动刷新页面。

## 功能特性

### ✅ 已实现功能

1. **WebSocket服务器**
   - 基于FastAPI的WebSocket端点
   - 连接管理和订阅系统
   - 自动重连机制

2. **数据频道**
   - `market_data` - 市场数据（BTC价格，每5秒更新）
   - `options_chain` - 期权链数据（每10秒更新）
   - `portfolio` - 组合数据（未来实现）

3. **前端Hook**
   - `useWebSocket` - React Hook用于WebSocket连接
   - 自动重连（最多5次）
   - 订阅管理
   - 错误处理

4. **UI组件**
   - `WebSocketIndicator` - 连接状态指示器
   - 实时状态显示（绿色=已连接，黄色=连接中，红色=断开）

## 使用方法

### 后端启动

WebSocket服务器会随后端API自动启动：

```bash
cd BTCOptionsTrading/backend
python run_api.py
```

WebSocket端点: `ws://localhost:8000/ws`

### 测试WebSocket

运行测试脚本验证功能：

```bash
cd BTCOptionsTrading/backend
python test_websocket.py
```

测试内容：
- ✅ Ping-Pong心跳
- ✅ 订阅/取消订阅
- ✅ 市场数据推送
- ✅ 期权链数据推送
- ✅ 错误处理
- ✅ 多客户端连接

### 前端使用

#### 1. 使用WebSocket Hook

```typescript
import { useWebSocket } from '../hooks/useWebSocket'

function MyComponent() {
  const { isConnected, subscribe, lastMessage } = useWebSocket({
    autoConnect: true
  })

  useEffect(() => {
    // 订阅市场数据
    subscribe('market_data')
    
    return () => {
      // 组件卸载时自动取消订阅
    }
  }, [subscribe])

  useEffect(() => {
    if (lastMessage?.type === 'market_data') {
      const price = lastMessage.data.price
      console.log('BTC价格更新:', price)
      // 更新UI
    }
  }, [lastMessage])

  return (
    <div>
      状态: {isConnected ? '已连接' : '未连接'}
    </div>
  )
}
```

#### 2. 添加连接状态指示器

```typescript
import WebSocketIndicator from '../components/WebSocketIndicator'

function Layout() {
  return (
    <div>
      <header>
        <WebSocketIndicator />
      </header>
    </div>
  )
}
```

## 消息格式

### 客户端发送

```json
{
  "action": "subscribe" | "unsubscribe" | "ping",
  "channel": "market_data" | "options_chain" | "portfolio",
  "params": {}  // 可选参数
}
```

### 服务器推送

```json
{
  "type": "market_data" | "options_chain" | "error" | "pong",
  "data": {
    // 数据内容
  },
  "timestamp": "2024-02-09T12:00:00Z"
}
```

### 示例消息

**市场数据**:
```json
{
  "type": "market_data",
  "data": {
    "symbol": "BTC",
    "price": 45234.50,
    "timestamp": "2024-02-09T12:00:00Z"
  },
  "timestamp": "2024-02-09T12:00:00Z"
}
```

**期权链数据**:
```json
{
  "type": "options_chain",
  "data": {
    "currency": "BTC",
    "options": [
      {
        "instrument_name": "BTC-29DEC23-45000-C",
        "strike": 45000,
        "mark_price": 1234.56,
        "implied_volatility": 0.65,
        "delta": 0.52
      }
    ],
    "timestamp": "2024-02-09T12:00:00Z"
  },
  "timestamp": "2024-02-09T12:00:00Z"
}
```

## 配置选项

### WebSocket Hook选项

```typescript
interface UseWebSocketOptions {
  url?: string                    // WebSocket URL (默认: ws://localhost:8000/ws)
  autoConnect?: boolean           // 自动连接 (默认: true)
  reconnectInterval?: number      // 重连间隔毫秒 (默认: 3000)
  maxReconnectAttempts?: number   // 最大重连次数 (默认: 5)
}
```

### 使用示例

```typescript
const { isConnected, subscribe } = useWebSocket({
  url: 'ws://localhost:8000/ws',
  autoConnect: true,
  reconnectInterval: 5000,  // 5秒重连间隔
  maxReconnectAttempts: 10  // 最多重连10次
})
```

## 数据更新频率

- **市场数据**: 每5秒更新一次
- **期权链数据**: 每10秒更新一次
- **组合数据**: 按需更新（未来实现）

可以在 `src/api/routes/websocket.py` 中调整更新频率。

## 性能优化

### 1. 按需订阅

只订阅需要的数据频道：

```typescript
// 只在需要时订阅
useEffect(() => {
  if (isTabActive) {
    subscribe('market_data')
  }
}, [isTabActive, subscribe])
```

### 2. 数据节流

对于高频更新，使用节流：

```typescript
import { useThrottle } from '../hooks/useThrottle'

const throttledPrice = useThrottle(lastMessage?.data?.price, 1000)
```

### 3. 条件渲染

避免不必要的重渲染：

```typescript
const MemoizedComponent = React.memo(({ price }) => {
  return <div>{price}</div>
}, (prev, next) => prev.price === next.price)
```

## 错误处理

### 连接失败

```typescript
const { error, isConnected } = useWebSocket()

if (error) {
  console.error('WebSocket错误:', error)
  // 显示错误提示
}
```

### 自动重连

Hook会自动尝试重连（最多5次），无需手动处理。

### 手动重连

```typescript
const { disconnect, connect } = useWebSocket({ autoConnect: false })

// 手动连接
connect()

// 手动断开
disconnect()
```

## 安全考虑

### 1. 生产环境配置

在生产环境中，应该：
- 使用WSS（加密WebSocket）
- 添加认证机制
- 限制连接数量
- 添加速率限制

### 2. 数据验证

始终验证接收到的数据：

```typescript
if (lastMessage?.type === 'market_data') {
  const price = lastMessage.data?.price
  if (typeof price === 'number' && price > 0) {
    // 使用数据
  }
}
```

## 调试

### 1. 浏览器开发者工具

在Chrome DevTools的Network标签中查看WebSocket连接：
- 查看消息历史
- 检查连接状态
- 监控数据流量

### 2. 后端日志

查看后端日志：

```bash
tail -f BTCOptionsTrading/backend/logs/app.log
```

### 3. 测试脚本

使用测试脚本验证功能：

```bash
python test_websocket.py
```

## 未来改进

### 短期（1周内）

1. **组合实时更新**
   - 实时组合价值
   - 实时希腊字母
   - 实时盈亏

2. **认证机制**
   - JWT token验证
   - 用户权限控制

3. **数据压缩**
   - 使用消息压缩减少带宽
   - 增量更新而非全量推送

### 中期（1个月内）

1. **高级订阅**
   - 订阅特定期权合约
   - 自定义更新频率
   - 数据过滤

2. **历史回放**
   - 回放历史数据流
   - 用于回测验证

3. **性能监控**
   - 延迟监控
   - 消息丢失检测
   - 连接质量指标

### 长期（3个月内）

1. **集群支持**
   - 多服务器负载均衡
   - Redis Pub/Sub
   - 水平扩展

2. **高级功能**
   - 二进制协议（更高效）
   - 自定义心跳
   - 断线重连优化

## 常见问题

### Q1: WebSocket连接失败？

**A**: 检查：
1. 后端服务是否运行
2. 端口8000是否被占用
3. 防火墙设置
4. CORS配置

### Q2: 数据不更新？

**A**: 检查：
1. 是否已订阅频道
2. API密钥是否配置
3. 后端日志是否有错误
4. 网络连接是否正常

### Q3: 如何减少数据流量？

**A**: 
1. 只订阅需要的频道
2. 增加更新间隔
3. 使用数据节流
4. 实现增量更新

### Q4: 支持多少并发连接？

**A**: 
- 开发环境：建议<100
- 生产环境：需要配置负载均衡
- 可以通过Redis扩展

## 相关文档

- [FastAPI WebSocket文档](https://fastapi.tiangolo.com/advanced/websockets/)
- [WebSocket API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [React WebSocket最佳实践](https://react.dev/)

---

**总结**: WebSocket实时数据推送功能已完全实现，支持市场数据和期权链的实时更新。前端可以通过`useWebSocket` Hook轻松集成实时数据功能。
