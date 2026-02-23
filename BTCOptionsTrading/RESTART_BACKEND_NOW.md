# 重启后端 API - 立即执行

## 问题
后端 API 服务器还在运行旧的代码，所以仍然返回 404。

## 解决方案 - 重启后端 API

### 步骤 1: 停止后端 API 服务器
在运行后端 API 的终端中，按 `Ctrl+C` 停止服务器。

**你应该看到类似的输出**:
```
^C
Shutting down BTC Options Trading System API
```

### 步骤 2: 重新启动后端 API 服务器
```bash
cd BTCOptionsTrading/backend
python -m uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

**你应该看到类似的输出**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 步骤 3: 验证后端 API 是否工作
在另一个终端运行：
```bash
curl 'http://localhost:8000/api/csv/contracts?underlying=BTC' | jq '.contracts | length'
```

**预期结果**: `1300`

### 步骤 4: 清除浏览器缓存
- 按 `Ctrl+Shift+Delete` 打开清除浏览数据对话框
- 或者按 `Ctrl+F5` 硬性刷新页面

### 步骤 5: 打开历史数据分析
- 点击菜单中的"历史数据分析"
- 点击"合约分析"标签页
- 下拉菜单应该显示 1300 个合约

## 验证

打开浏览器开发者工具 (F12)，切换到 Network 标签页，应该看到：
- `GET /api/csv/contracts?underlying=BTC` - 返回 200 ✓
- 响应包含 1300 个合约 ✓

## 如果还是不行

1. 确保后端 API 服务器已经完全停止
2. 等待 5 秒钟
3. 重新启动后端 API 服务器
4. 清除浏览器缓存
5. 刷新页面

---

**最后更新**: 2026年2月23日
