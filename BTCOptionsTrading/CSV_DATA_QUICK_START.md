# CSV数据集成 - 快速开始 (Quick Start)

## 5分钟快速上手

### 第1步: 启动后端API
```bash
cd BTCOptionsTrading/backend
python -m uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

### 第2步: 打开前端应用
- 访问 `http://localhost:3000`
- 导航到"历史数据分析"页面

### 第3步: 查看CSV数据
1. 点击"CSV数据分析"标签页
2. 从下拉菜单选择一个合约
3. 查看价格曲线、波动率、成交量等图表

## 主要功能

### 📊 价格曲线
- 显示标记价格、买价、卖价
- 支持交互式缩放和平移
- 自动格式化时间轴

### 📈 隐含波动率
- 显示期权隐含波动率变化
- 帮助分析市场情绪

### 📉 成交量
- 显示每个时间点的成交量
- 识别流动性变化

## API端点速查

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/csv/summary` | GET | 获取数据摘要 |
| `/api/csv/contracts` | GET | 获取合约列表 |
| `/api/csv/contract/{name}` | GET | 获取合约数据 |
| `/api/csv/sync` | POST | 同步数据到缓存 |

## 常见问题

**Q: 为什么看不到CSV数据?**
A: 检查服务器路径 `/root/BTCTradingApp/BTCOptionsTrading/backend/data/daily_snapshots/` 是否有CSV文件

**Q: 数据加载很慢?**
A: 调用 `POST /api/csv/sync` 预加载数据到缓存

**Q: 如何导出数据?**
A: 目前支持通过浏览器开发者工具导出，后续版本将添加导出功能

## 文件位置

- 后端API: `backend/src/api/routes/csv_data.py`
- 前端客户端: `frontend/src/api/csv.ts`
- UI组件: `frontend/src/components/tabs/HistoricalDataTab.tsx`
- CSV数据源: `/root/BTCTradingApp/BTCOptionsTrading/backend/data/daily_snapshots/`

## 下一步

- 查看完整文档: [CSV_DATA_INTEGRATION.md](./CSV_DATA_INTEGRATION.md)
- 了解数据收集: [DAILY_COLLECTION_GUIDE.md](./backend/DAILY_COLLECTION_GUIDE.md)
- 查看API文档: [HISTORICAL_DATA_API.md](./backend/HISTORICAL_DATA_API.md)
