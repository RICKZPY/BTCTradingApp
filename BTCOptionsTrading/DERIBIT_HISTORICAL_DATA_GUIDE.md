# Deribit 历史期权数据获取指南

## 概述

根据对 Deribit API 的研究，以下是获取历史BTC期权成交数据用于回测的几种方案。

## 方案对比

### 方案 1: Deribit 官方 API（限制较多）⚠️

**可用性**: ❌ **不适合长期历史数据**

**限制**:
- **用户交易数据**: 只能获取你自己账户的历史交易记录（需要认证）
- **公开市场数据**: `public/get_last_trades_by_instrument` 只提供最近的交易数据
- **时间范围**: 
  - 最近订单: 30分钟内
  - 最近交易: 24小时内
  - 历史记录: 需要使用 `historical=true` 参数，但仅限于**你自己的交易**

**支持的端点**（仅限私有数据）:
```
private/get_user_trades_by_instrument
private/get_user_trades_by_instrument_and_time
private/get_user_trades_by_currency
private/get_user_trades_by_currency_and_time
```

**结论**: Deribit 官方 API **不提供**公开的历史市场成交数据用于回测。

---

### 方案 2: Tardis.dev（推荐）✅

**可用性**: ✅ **最佳选择**

**优势**:
- ✅ 提供 Deribit 所有期权合约的历史数据
- ✅ 数据从 **2019年3月30日** 开始
- ✅ 包含完整的 tick-by-tick 交易数据
- ✅ 提供订单簿快照（order book snapshots）
- ✅ 支持 Python 和 Node.js 客户端
- ✅ 可下载 CSV 格式数据

**数据类型**:
- `trades` - 逐笔成交数据
- `incremental_book_L2` - 订单簿增量更新
- `quotes` - 报价数据
- `book_snapshot_25` - 订单簿快照（25档）

**定价**: 
- 需要付费订阅（提供免费试用）
- 官网: https://tardis.dev

**使用示例**:
```python
from tardis_dev import datasets

# 下载BTC期权历史数据
datasets.download(
    exchange='deribit',
    data_types=['trades', 'incremental_book_L2'],
    from_date='2023-01-01',
    to_date='2025-01-01',
    symbols=['BTC-*'],  # 所有BTC期权
    api_key='YOUR_API_KEY',
    download_dir='./historical_data'
)
```

**官方文档**: https://docs.tardis.dev/historical-data-details/deribit

---

### 方案 3: CryptoDataDownload.com（部分免费）📊

**可用性**: ⚠️ **有限的免费数据**

**优势**:
- ✅ 提供部分免费的 Deribit 数据
- ✅ CSV 格式，易于使用
- ✅ 包含 DVOL（Deribit 波动率指数）数据

**限制**:
- ⚠️ 数据更新频率不确定
- ⚠️ 可能不包含所有期权合约
- ⚠️ 历史深度有限

**官网**: https://www.cryptodatadownload.com/data/deribit/

---

### 方案 4: Laevitas.ch API（专业级）💼

**可用性**: ✅ **专业数据服务**

**优势**:
- ✅ 专门提供期权历史数据
- ✅ 包含 Deribit 和其他交易所
- ✅ 提供 REST API 访问
- ✅ 数据质量高

**数据类型**:
- 期权链历史快照
- 隐含波动率数据
- 希腊字母历史数据
- 成交量和持仓量

**定价**: 需要付费订阅

**官方文档**: https://docs.laevitas.ch/options/historical

---

### 方案 5: 自建数据收集系统（开源工具）🛠️

**可用性**: ✅ **免费但需要自己维护**

**GitHub 项目**:

1. **deribit_data_collector**
   - 仓库: https://github.com/schepal/deribit_data_collector
   - 功能: 下载完整的 BTC 和 ETH 期权链数据
   - 语言: Python
   - 限制: 只能收集当前和未来的数据，无法获取历史数据

2. **deribit_historical_trades**
   - 仓库: https://github.com/BarendPotijk/deribit_historical_trades
   - 功能: 收集 Deribit 衍生品交易数据
   - 语言: Python
   - 限制: 需要长期运行以积累数据

**优势**:
- ✅ 完全免费
- ✅ 可自定义数据收集逻辑
- ✅ 开源代码可学习

**劣势**:
- ❌ 无法获取过去的历史数据
- ❌ 需要持续运行和维护
- ❌ 需要存储空间

---

## 推荐方案

### 对于回测需求（需要过去2年数据）:

**最佳选择**: **Tardis.dev** ✅

**原因**:
1. 提供从2019年开始的完整历史数据
2. 数据质量高，包含 tick-by-tick 级别
3. 易于集成，有现成的 Python 客户端
4. 支持批量下载和 API 访问

**替代方案**: **Laevitas.ch**（如果需要更多分析功能）

### 对于未来数据收集:

**推荐**: 使用 **Deribit WebSocket API** 实时收集

在你的系统中已经有 WebSocket 集成，可以：
1. 订阅期权交易流
2. 实时存储到数据库
3. 积累自己的历史数据库

---

## 实现建议

### 短期方案（立即开始回测）:

1. **购买 Tardis.dev 订阅**
   - 下载过去2年的 BTC 期权数据
   - 存储到本地数据库（PostgreSQL/InfluxDB）
   - 使用现有的回测引擎进行测试

2. **数据处理流程**:
```python
# 1. 下载历史数据
from tardis_dev import datasets

datasets.download(
    exchange='deribit',
    data_types=['trades'],
    from_date='2023-02-01',
    to_date='2025-02-01',
    symbols=['BTC-*'],
    api_key='YOUR_API_KEY',
    download_dir='./data'
)

# 2. 导入到数据库
# 3. 使用你的 BacktestEngine 进行回测
```

### 长期方案（持续数据收集）:

1. **扩展现有的 WebSocket 实现**:
   - 订阅所有 BTC 期权合约的交易流
   - 实时存储到 InfluxDB（时序数据库）
   - 定期备份数据

2. **数据存储结构**:
```python
# InfluxDB measurement
measurement = "option_trades"
tags = {
    "instrument": "BTC-28FEB25-50000-C",
    "option_type": "call",
    "strike": 50000
}
fields = {
    "price": 1250.5,
    "amount": 0.5,
    "direction": "buy",
    "iv": 0.65
}
```

---

## 成本估算

| 方案 | 初始成本 | 月度成本 | 数据范围 |
|------|---------|---------|---------|
| Tardis.dev | $0-100 | $50-500 | 2019至今 |
| Laevitas.ch | 联系销售 | 联系销售 | 完整历史 |
| CryptoDataDownload | $0 | $0 | 有限 |
| 自建系统 | $0 | $10-50（服务器） | 仅未来 |

---

## 下一步行动

1. ✅ **评估预算**: 确定是否可以购买 Tardis.dev 订阅
2. ✅ **试用 Tardis.dev**: 注册免费试用，下载样本数据
3. ✅ **设计数据库架构**: 为历史数据设计存储方案
4. ✅ **扩展 DeribitConnector**: 添加历史数据导入功能
5. ✅ **测试回测引擎**: 使用历史数据验证回测逻辑

---

## 相关资源

- [Deribit API 文档](https://docs.deribit.com/)
- [Tardis.dev 文档](https://docs.tardis.dev/)
- [Laevitas API 文档](https://docs.laevitas.ch/)
- [CryptoDataDownload](https://www.cryptodatadownload.com/data/deribit/)

---

## 总结

**Deribit 官方 API 不提供公开的历史市场数据用于回测**。你需要使用第三方数据服务（如 Tardis.dev）或自己长期收集数据。

对于你的需求（过去2年的数据用于回测），**Tardis.dev 是最佳选择**，因为它提供完整的历史数据，数据质量高，且易于集成。
