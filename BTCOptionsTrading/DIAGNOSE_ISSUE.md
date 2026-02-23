# 诊断问题 - 为什么"合约分析"还是显示 0 个合约

## 可能的原因

### 原因 1: 前端没有重新加载修改后的代码
- 前端开发服务器没有重启
- 浏览器缓存问题
- 代码修改没有被编译

### 原因 2: 前端开发服务器没有启动
- 需要运行 `npm start` 或 `yarn start`

### 原因 3: API 调用失败
- 后端 API 未启动
- API 端点不正确
- 网络连接问题

### 原因 4: 代码修改没有被保存
- 虽然看起来修改已保存，但可能有其他问题

## 诊断步骤

### 步骤 1: 检查后端 API 是否运行
```bash
curl http://localhost:8000/api/csv/contracts?underlying=BTC | jq '.contracts | length'
```

**预期结果**: `1300`

### 步骤 2: 检查前端开发服务器是否运行
- 打开浏览器访问 `http://localhost:3000`
- 应该看到应用界面

### 步骤 3: 打开浏览器开发者工具
1. 按 `F12` 打开开发者工具
2. 切换到 **Console** 标签页
3. 导航到"历史数据分析" → "合约分析"
4. 查看 Console 中的日志

**预期日志**:
```
数据库中没有合约，尝试从 CSV 数据获取...
```

### 步骤 4: 检查网络请求
1. 打开浏览器开发者工具 (F12)
2. 切换到 **Network** 标签页
3. 刷新页面
4. 查找以下请求：
   - `GET /api/historical/instruments?underlying=BTC` - 应该返回 `[]`
   - `GET /api/csv/contracts?underlying=BTC` - 应该返回 1300 个合约

### 步骤 5: 使用测试工具
1. 打开 `frontend/test_csv_api_direct.html` 文件
2. 在浏览器中打开这个 HTML 文件
3. 点击各个按钮进行测试
4. 查看测试结果

## 快速修复

### 如果前端开发服务器没有启动
```bash
cd BTCOptionsTrading/frontend
npm start
# 或者
yarn start
```

### 如果前端缓存问题
1. 按 `Ctrl+Shift+Delete` 清除浏览器缓存
2. 或者按 `Ctrl+F5` 硬性刷新页面

### 如果代码修改没有被编译
1. 停止前端开发服务器 (Ctrl+C)
2. 删除 `node_modules` 和 `.next` 目录
3. 重新安装依赖：`npm install`
4. 重新启动开发服务器：`npm start`

## 测试 API 直接调用

### 在浏览器 Console 中运行
```javascript
// 测试 CSV API
fetch('/api/csv/contracts?underlying=BTC')
  .then(r => r.json())
  .then(d => console.log('CSV 合约数:', d.contracts.length))
  .catch(e => console.error('错误:', e))

// 测试历史数据 API
fetch('/api/historical/instruments?underlying=BTC')
  .then(r => r.json())
  .then(d => console.log('历史数据合约数:', d.length))
  .catch(e => console.error('错误:', e))
```

## 如果还是不行

### 检查清单
- [ ] 后端 API 正在运行 (`http://localhost:8000/api/csv/summary` 返回 200)
- [ ] 前端开发服务器正在运行 (`http://localhost:3000` 可访问)
- [ ] 浏览器缓存已清除
- [ ] 页面已刷新
- [ ] Console 中看到 "数据库中没有合约，尝试从 CSV 数据获取..." 日志
- [ ] Network 标签显示 `/api/csv/contracts` 返回 200
- [ ] 响应包含 1300 个合约

### 获取更多信息
1. 打开浏览器开发者工具 (F12)
2. 切换到 **Console** 标签页
3. 运行测试命令
4. 记录所有错误信息
5. 检查 Network 标签中的请求和响应

## 可能的错误信息

### "Cannot read property 'map' of undefined"
- 原因: CSV API 返回的数据格式不正确
- 解决方案: 检查 CSV API 是否返回正确的格式

### "404 Not Found"
- 原因: API 端点不存在
- 解决方案: 检查后端 API 是否正确注册

### "Network error"
- 原因: 后端 API 未启动
- 解决方案: 启动后端 API

### "CORS error"
- 原因: 跨域问题
- 解决方案: 检查后端 CORS 配置

---

**最后更新**: 2026年2月23日
