# CSV数据集成指南 (CSV Data Integration Guide)

## 功能概述 (Overview)
本功能将服务器上收集的历史数据CSV文件集成到前端的历史数据分析页面，提供价格曲线图、波动率曲线、成交量等多维度的数据可视化。

## 系统架构 (System Architecture)

### 后端 (Backend)
- **CSV数据源**: `/root/BTCTradingApp/BTCOptionsTrading/backend/data/daily_snapshots/`
- **新增API路由**: `src/api/routes/csv_data.py`
- **API前缀**: `/api/csv`

### 前端 (Frontend)
- **API客户端**: `src/api/csv.ts`
- **UI组件**: `src/components/tabs/HistoricalDataTab.tsx` (新增CSV数据分析视图)

## 后端API端点 (Backend API Endpoints)

### 1. 获取CSV数据摘要
```
GET /api/csv/summary
```
返回CSV文件的统计信息，包括文件数、记录数、合约数等。

**响应示例**:
```json
{
  "total_files": 45,
  "total_records": 125000,
  "total_contracts": 250,
  "contracts": {
    "BTC-25FEB26-60000-C": {
      "record_count": 500,
      "date_range": {
        "start": "2026-02-01T00:00:00",
        "end": "2026-02-22T23:59:59"
      }
    }
  },
  "last_updated": "2026-02-22T20:30:00"
}
```

### 2. 获取合约列表
```
GET /api/csv/contracts?underlying=BTC
```
获取指定标的资产的所有合约列表。

**参数**:
- `underlying` (string): 标的资产，默认为 "BTC"

**响应示例**:
```json
{
  "underlying": "BTC",
  "contracts": [
    {
      "instrument_name": "BTC-25FEB26-60000-C",
      "record_count": 500,
      "strike_price": 60000,
      "option_type": "call",
      "expiry_date": "2026-02-25",
      "date_range": {
        "start": "2026-02-01T00:00:00",
        "end": "2026-02-22T23:59:59"
      }
    }
  ]
}
```

### 3. 获取合约详细数据
```
GET /api/csv/contract/{instrument_name}
```
获取特定合约的完整价格历史数据。

**参数**:
- `instrument_name` (string): 合约名称，如 "BTC-25FEB26-60000-C"

**响应示例**:
```json
{
  "instrument_name": "BTC-25FEB26-60000-C",
  "underlying": "BTC",
  "strike_price": 60000,
  "option_type": "call",
  "expiry_date": "2026-02-25",
  "data_points": 500,
  "avg_price": 0.0234,
  "price_history": [
    {
      "timestamp": "2026-02-01T08:00:00",
      "mark_price": 0.0230,
      "bid_price": 0.0228,
      "ask_price": 0.0232,
      "volume": 1500,
      "open_interest": 5000,
      "implied_volatility": 0.65
    }
  ],
  "date_range": {
    "start": "2026-02-01T00:00:00",
    "end": "2026-02-22T23:59:59"
  }
}
```

### 4. 同步CSV数据
```
POST /api/csv/sync
```
将CSV文件数据同步到本地缓存，加快后续查询速度。

**响应示例**:
```json
{
  "status": "success",
  "files_processed": 45,
  "contracts_found": 250,
  "total_records": 125000,
  "cache_file": "./csv_data_cache/contracts_cache.json"
}
```

## 前端API客户端 (Frontend API Client)

### 使用示例
```typescript
import { csvApi } from '@/api/csv'

// 获取摘要
const summary = await csvApi.getSummary()

// 获取合约列表
const contracts = await csvApi.getContracts('BTC')

// 获取合约数据
const data = await csvApi.getContractData('BTC-25FEB26-60000-C')

// 同步数据
const result = await csvApi.syncData()
```

## 前端UI功能 (Frontend UI Features)

### CSV数据分析视图
在历史数据分析页面新增"CSV数据分析"标签页，包含以下功能：

#### 1. 合约选择器
- 显示所有可用的CSV合约
- 支持按执行价过滤
- 实时加载合约数据

#### 2. 合约信息卡片
显示选中合约的基本信息：
- 合约名称
- 标的资产
- 执行价
- 期权类型
- 到期日
- 数据点数
- 平均价格
- 数据时间范围

#### 3. 价格曲线图
- 显示标记价格、买价、卖价的时间序列
- 支持交互式缩放和平移
- 自动格式化时间轴

#### 4. 隐含波动率曲线
- 显示隐含波动率随时间的变化
- 帮助分析期权市场情绪

#### 5. 成交量柱状图
- 显示每个时间点的成交量
- 帮助识别流动性变化

## 数据流程 (Data Flow)

```
CSV文件 (/root/BTCTradingApp/...)
    ↓
后端API (csv_data.py)
    ├─ 读取CSV文件
    ├─ 解析数据
    └─ 按合约组织
    ↓
前端API客户端 (csv.ts)
    ├─ 获取摘要
    ├─ 获取合约列表
    └─ 获取合约数据
    ↓
前端UI (HistoricalDataTab.tsx)
    ├─ 合约选择器
    ├─ 信息卡片
    ├─ 价格曲线图
    ├─ 波动率曲线
    └─ 成交量柱状图
```

## 使用步骤 (Usage Steps)

### 1. 启动API服务器
```bash
cd BTCOptionsTrading/backend
python -m uvicorn src.api.app:app --reload
```

### 2. 打开历史数据分析页面
- 在前端应用中导航到"历史数据分析"
- 点击"CSV数据分析"标签页

### 3. 选择合约
- 从下拉菜单中选择要分析的合约
- 系统自动加载该合约的数据

### 4. 查看图表
- 查看价格曲线、波动率、成交量等多维度数据
- 使用图表的交互功能进行缩放和平移

## 性能优化 (Performance Optimization)

### 缓存策略
- 首次加载时读取CSV文件并缓存
- 后续请求直接从缓存读取
- 支持手动同步更新缓存

### 数据限制
- 单个合约最多返回所有历史数据
- 前端图表自动处理大数据集的渲染

### 查询优化
- 按合约名称快速查询
- 支持批量获取合约列表

## 故障排除 (Troubleshooting)

### 问题1: CSV文件未找到
**症状**: API返回 "No CSV files found"
**解决方案**:
1. 检查服务器路径: `/root/BTCTradingApp/BTCOptionsTrading/backend/data/daily_snapshots/`
2. 确保CSV文件存在且可读
3. 检查文件权限

### 问题2: 数据加载缓慢
**症状**: 合约数据加载时间长
**解决方案**:
1. 调用 `/api/csv/sync` 端点预加载数据
2. 检查服务器磁盘I/O性能
3. 考虑分批加载数据

### 问题3: 图表显示不完整
**症状**: 某些数据点未显示
**解决方案**:
1. 检查CSV文件中的数据完整性
2. 验证数据格式是否正确
3. 查看浏览器控制台错误信息

## 文件结构 (File Structure)

```
BTCOptionsTrading/
├── backend/
│   ├── src/api/routes/
│   │   └── csv_data.py              # CSV数据API
│   ├── data/daily_snapshots/        # CSV数据源
│   └── csv_data_cache/              # 缓存目录
├── frontend/
│   ├── src/api/
│   │   └── csv.ts                   # CSV API客户端
│   └── src/components/tabs/
│       └── HistoricalDataTab.tsx    # 历史数据分析UI
└── CSV_DATA_INTEGRATION.md          # 本文档
```

## 扩展功能 (Future Enhancements)

1. **数据导出**
   - 支持导出选中合约的数据为CSV/Excel
   - 支持导出图表为图片

2. **高级分析**
   - 添加技术指标（MA、MACD等）
   - 支持自定义指标计算

3. **对比分析**
   - 支持多个合约同时显示
   - 支持不同时间段对比

4. **实时更新**
   - 支持实时数据推送
   - 自动刷新图表

## 相关文档 (Related Documentation)

- [历史数据指南](./HISTORICAL_DATA_GUIDE.md)
- [API文档](./backend/HISTORICAL_DATA_API.md)
- [数据收集指南](./backend/DAILY_COLLECTION_GUIDE.md)
