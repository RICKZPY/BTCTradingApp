# CSV 数据回退修复 - 测试指南

## 快速测试

### 步骤 1: 启动后端 API
```bash
cd BTCOptionsTrading/backend
python -m uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

### 步骤 2: 打开前端应用
- 在浏览器中访问 `http://localhost:3000`

### 步骤 3: 打开开发者工具
- 按 `F12` 打开浏览器开发者工具
- 切换到 **Console** 标签页

### 步骤 4: 导航到历史数据分析
- 点击菜单中的"历史数据分析"
- 查看 Console 中的日志

**预期日志**:
```
数据库中没有合约，尝试从 CSV 数据获取...
```

### 步骤 5: 点击"合约分析"标签页
- 点击第二个标签页 **"合约分析"**
- 等待数据加载

**预期结果**:
- 下拉菜单显示 1300 个合约
- 例如：`BTC-13MAR26-100000-C`

### 步骤 6: 选择一个合约
- 点击下拉菜单
- 选择任意一个合约

**预期结果**:
- 页面显示合约信息
- 显示价格曲线、波动率、成交量等图表

## 验证检查清单

- [ ] 后端 API 正在运行
- [ ] 前端应用可访问
- [ ] Console 中看到 "数据库中没有合约，尝试从 CSV 数据获取..." 日志
- [ ] "合约分析"标签页显示 1300 个合约
- [ ] 选择合约后显示数据和图表
- [ ] 没有错误信息

## 常见问题

### Q: 为什么还是显示 0 个合约？
A: 可能是以下原因：
1. 后端 API 未启动
2. 前端缓存问题
3. CSV 数据文件不存在

**解决方案**:
1. 确保后端 API 正在运行
2. 清除浏览器缓存（Ctrl+Shift+Delete）
3. 检查 `backend/data/downloads/` 目录是否有 CSV 文件

### Q: 为什么看不到图表？
A: 可能是以下原因：
1. 合约数据还在加载
2. 合约没有价格数据
3. 浏览器不支持图表库

**解决方案**:
1. 等待数据加载完成
2. 选择另一个合约
3. 使用最新版本的浏览器

### Q: Console 中看到错误信息怎么办？
A: 查看错误信息的具体内容：
- 如果是 "404 Not Found" → API 端点不存在
- 如果是 "Network error" → 后端 API 未启动
- 如果是 "CORS error" → 跨域问题

**解决方案**:
1. 检查后端 API 是否正在运行
2. 检查 API 端点是否正确
3. 检查浏览器控制台中的详细错误信息

## 调试技巧

### 查看详细日志
在 Console 中运行：
```javascript
// 测试 CSV API
fetch('/api/csv/contracts?underlying=BTC')
  .then(r => {
    console.log('状态码:', r.status)
    return r.json()
  })
  .then(d => {
    console.log('合约数:', d.contracts.length)
    console.log('第一个合约:', d.contracts[0])
  })
  .catch(e => console.error('错误:', e))
```

### 查看网络请求
1. 打开 Network 标签页
2. 刷新页面
3. 查找以下请求：
   - `GET /api/historical/instruments?underlying=BTC` - 数据库 API
   - `GET /api/csv/contracts?underlying=BTC` - CSV API

### 查看响应内容
1. 点击网络请求
2. 切换到 **Response** 标签页
3. 查看响应内容

## 性能测试

### 加载时间
- 数据库 API: 通常 < 100ms
- CSV API: 通常 < 500ms（首次加载）

### 合约数量
- 数据库: 0 个（如果数据库为空）
- CSV: 1300 个

## 文件位置

- **后端 API**: `backend/src/api/routes/csv_data.py`
- **前端组件**: `frontend/src/components/tabs/HistoricalDataTab.tsx`
- **CSV 数据**: `backend/data/downloads/`

---

**最后更新**: 2026年2月23日
