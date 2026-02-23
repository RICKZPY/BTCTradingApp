# 期权链页面价格显示问题排查指南

## 问题描述

期权链页面没有显示当前价格（显示为$0或不显示）。

## 可能的原因

1. **后端API未启动或无法访问**
2. **Deribit API连接失败**
3. **前端API调用失败**
4. **CORS配置问题**
5. **网络连接问题**

## 排查步骤

### 步骤1: 检查后端API是否运行

```bash
# 检查API进程
ps aux | grep run_api

# 或者尝试访问健康检查端点
curl http://localhost:8000/health
```

**预期结果**: 应该返回健康状态JSON

如果API未运行，启动它：
```bash
cd BTCOptionsTrading/backend
python run_api.py
```

### 步骤2: 测试价格API端点

运行测试脚本：
```bash
cd BTCOptionsTrading/backend
python test_underlying_price.py
```

**预期结果**: 
- ✅ 成功获取BTC和ETH价格
- ✅ 价格在合理范围内
- ✅ API端点返回200状态码

**如果失败**:
- 检查网络连接
- 检查Deribit API配置（.env文件）
- 查看日志文件 `logs/app.log`

### 步骤3: 检查前端配置

1. **检查API基础URL**

编辑 `frontend/src/api/client.ts`，确认baseURL正确：
```typescript
const apiClient = axios.create({
  baseURL: 'http://localhost:8000',  // 应该指向后端API
  timeout: 10000,
})
```

2. **检查浏览器控制台**

打开浏览器开发者工具（F12），查看：
- Console标签：是否有JavaScript错误
- Network标签：API请求是否成功
  - 查找 `/api/data/underlying-price/BTC` 请求
  - 检查状态码（应该是200）
  - 检查响应内容

### 步骤4: 检查CORS配置

如果看到CORS错误，检查后端配置：

编辑 `backend/.env`:
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

或者在 `backend/src/api/app.py` 中检查CORS中间件配置。

### 步骤5: 手动测试API

使用curl或浏览器直接访问：

```bash
# 测试BTC价格
curl http://localhost:8000/api/data/underlying-price/BTC

# 预期响应:
# {
#   "symbol": "BTC",
#   "price": 45000.0,
#   "timestamp": "2026-02-22T..."
# }
```

### 步骤6: 检查前端代码

查看 `frontend/src/components/tabs/OptionsChainTab.tsx` 第377-384行：

```typescript
<span className="text-text-secondary">当前价格:</span>
<span className="text-2xl font-bold text-text-primary ml-3 font-mono">
  ${(underlyingPrice || 0).toLocaleString()}
</span>
```

在浏览器控制台中检查 `underlyingPrice` 的值：
```javascript
// 在控制台中运行
console.log('Underlying Price:', underlyingPrice)
```

## 常见问题和解决方案

### 问题1: API返回404

**原因**: 路由配置错误或API未正确注册

**解决方案**:
1. 检查 `backend/src/api/app.py` 是否包含data路由
2. 确认路由前缀正确：`app.include_router(data.router, prefix="/api/data")`

### 问题2: API返回500错误

**原因**: Deribit连接失败或内部错误

**解决方案**:
1. 查看后端日志：`tail -f backend/logs/app.log`
2. 检查Deribit API配置
3. 确认网络可以访问Deribit

### 问题3: 前端显示$0

**原因**: API调用失败但错误被捕获

**解决方案**:
1. 检查浏览器控制台的错误消息
2. 确认API端点可访问
3. 检查前端的错误处理逻辑

### 问题4: CORS错误

**错误消息**: "Access to XMLHttpRequest has been blocked by CORS policy"

**解决方案**:
```python
# 在 backend/src/api/app.py 中
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 问题5: 价格显示为NaN

**原因**: 数据类型转换问题

**解决方案**:
检查API响应的price字段是否为数字类型：
```typescript
// 在前端添加类型检查
const data = await dataApi.getUnderlyingPrice(currency)
console.log('Price type:', typeof data.price, 'Value:', data.price)
setUnderlyingPrice(Number(data.price) || 0)
```

## 调试技巧

### 1. 添加详细日志

在前端 `OptionsChainTab.tsx` 的 `loadUnderlyingPrice` 函数中添加日志：

```typescript
const loadUnderlyingPrice = async () => {
  console.log('🔍 Loading underlying price for:', currency)
  try {
    const data = await dataApi.getUnderlyingPrice(currency)
    console.log('✅ Received price data:', data)
    setUnderlyingPrice(data.price)
    console.log('✅ Set underlying price to:', data.price)
  } catch (error) {
    console.error('❌ Failed to load price:', error)
    const fallbackPrice = currency === 'BTC' ? 45000 : 2500
    console.log('⚠️  Using fallback price:', fallbackPrice)
    setUnderlyingPrice(fallbackPrice)
  }
}
```

### 2. 使用React DevTools

安装React DevTools浏览器扩展，检查组件状态：
- 找到 `OptionsChainTab` 组件
- 查看 `underlyingPrice` state的值
- 确认值是否正确更新

### 3. 网络请求监控

在浏览器Network标签中：
1. 刷新页面
2. 查找 `underlying-price` 请求
3. 检查：
   - 请求URL是否正确
   - 状态码
   - 响应内容
   - 响应时间

## 快速修复

如果需要临时修复，可以在前端使用模拟数据：

```typescript
// 在 OptionsChainTab.tsx 中
const loadUnderlyingPrice = async () => {
  try {
    const data = await dataApi.getUnderlyingPrice(currency)
    setUnderlyingPrice(data.price)
  } catch (error) {
    console.error('加载标的价格失败:', error)
    // 临时使用固定价格
    setUnderlyingPrice(currency === 'BTC' ? 45000 : 2500)
  }
}
```

## 验证修复

修复后，验证以下内容：

1. ✅ 页面显示当前价格（不是$0）
2. ✅ 价格在合理范围内
3. ✅ 切换BTC/ETH时价格更新
4. ✅ 刷新按钮可以更新价格
5. ✅ 浏览器控制台无错误

## 需要帮助？

如果以上步骤都无法解决问题，请提供以下信息：

1. 后端日志（`logs/app.log`）
2. 浏览器控制台错误
3. Network标签的API请求详情
4. `test_underlying_price.py` 的输出

## 相关文件

- 前端组件: `frontend/src/components/tabs/OptionsChainTab.tsx`
- API客户端: `frontend/src/api/data.ts`
- 后端路由: `backend/src/api/routes/data.py`
- Deribit连接器: `backend/src/connectors/deribit_connector.py`
- 测试脚本: `backend/test_underlying_price.py`
