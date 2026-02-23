# CSV 数据前端调试指南 (Frontend Debugging)

## 问题诊断

### ✅ 后端 API 状态
- ✓ CSV API 端点工作正常
- ✓ 找到 1300 个合约
- ✓ 数据格式正确

### ❓ 前端问题排查

## 调试步骤

### 步骤 1: 打开浏览器开发者工具
1. 按 `F12` 打开开发者工具
2. 切换到 **Network** 标签页
3. 刷新页面

### 步骤 2: 检查 API 调用
1. 在历史数据分析页面
2. 点击 **"CSV数据分析"** 标签页
3. 在 Network 标签中查找以下请求：
   - `GET /api/csv/contracts?underlying=BTC`
   - `GET /api/csv/summary`

### 步骤 3: 检查响应
对于 `/api/csv/contracts?underlying=BTC` 请求：
- **状态码**: 应该是 `200`
- **响应体**: 应该包含 `contracts` 数组，有 1300 个合约

**正确的响应示例**:
```json
{
  "underlying": "BTC",
  "contracts": [
    {
      "instrument_name": "BTC-13MAR26-100000-C",
      "record_count": 4,
      "strike_price": 100000,
      "option_type": "call",
      "expiry_date": "2026-03-13",
      "date_range": {
        "start": "2026-02-20T01:27:34.759220",
        "end": "2026-02-23T00:00:03.263874"
      }
    },
    ...
  ],
  "data_dir": "/Users/rickzhong/BTCTradingApp/BTCOptionsTrading/backend/data/downloads"
}
```

### 步骤 4: 检查浏览器控制台
1. 切换到 **Console** 标签页
2. 查看是否有错误信息
3. 常见错误：
   - `CORS error` - 跨域问题
   - `404 Not Found` - API 端点不存在
   - `Network error` - 后端 API 未启动

## 常见问题解决

### 问题 1: 显示 "0 个可用合约"
**可能原因**:
1. 后端 API 未启动
2. 前端缓存问题
3. API 响应为空

**解决方案**:
```bash
# 1. 确保后端 API 正在运行
curl http://localhost:8000/api/csv/contracts?underlying=BTC

# 2. 清除前端缓存
# - 打开浏览器开发者工具 (F12)
# - 右键点击刷新按钮 → 清空缓存并硬性重新加载
# 或者按 Ctrl+Shift+Delete 打开清除浏览数据对话框

# 3. 重新加载页面
```

### 问题 2: 显示 "加载CSV合约列表失败"
**可能原因**:
1. API 返回错误
2. 网络连接问题
3. API 格式不匹配

**解决方案**:
```bash
# 检查 API 是否返回正确的格式
curl http://localhost:8000/api/csv/contracts?underlying=BTC | jq '.'

# 应该看到类似的结构：
# {
#   "underlying": "BTC",
#   "contracts": [...],
#   "data_dir": "..."
# }
```

### 问题 3: 网络请求显示 404
**可能原因**:
1. API 路由未正确注册
2. 后端代码未更新

**解决方案**:
```bash
# 检查 API 是否可访问
curl -v http://localhost:8000/api/csv/summary

# 应该返回 200 状态码
```

## 完整的调试流程

### 1. 启动后端 API
```bash
cd BTCOptionsTrading/backend
python -m uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

### 2. 验证 API 工作
```bash
# 测试 API 端点
curl http://localhost:8000/api/csv/summary | jq '.total_contracts'
# 应该输出: 1300
```

### 3. 清除前端缓存
- 打开浏览器开发者工具 (F12)
- 右键点击刷新按钮
- 选择 "清空缓存并硬性重新加载"

### 4. 打开历史数据分析页面
- 导航到"历史数据分析"
- 点击"CSV数据分析"标签页
- 应该看到 1300 个合约

### 5. 选择合约
- 从下拉菜单选择一个合约
- 应该看到价格曲线、波动率、成交量等图表

## 如果还是不行

### 检查清单
- [ ] 后端 API 正在运行 (`http://localhost:8000/api/csv/summary` 返回 200)
- [ ] 前端缓存已清除
- [ ] 浏览器控制台没有错误
- [ ] Network 标签显示 `/api/csv/contracts` 返回 200
- [ ] 响应包含 1300 个合约

### 获取更多信息
1. 打开浏览器开发者工具 (F12)
2. 切换到 **Console** 标签页
3. 运行以下命令：
```javascript
// 测试 API 调用
fetch('/api/csv/contracts?underlying=BTC')
  .then(r => r.json())
  .then(d => console.log('合约数:', d.contracts.length))
  .catch(e => console.error('错误:', e))
```

4. 查看输出结果

## 文件位置

- **后端 API**: `backend/src/api/routes/csv_data.py`
- **前端客户端**: `frontend/src/api/csv.ts`
- **前端组件**: `frontend/src/components/tabs/HistoricalDataTab.tsx`

---

**最后更新**: 2026年2月23日
