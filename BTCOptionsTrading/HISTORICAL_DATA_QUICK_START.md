# 历史数据系统 - 快速开始

## 5 分钟快速上手

### 1. 准备数据文件

将 CSV 文件放入下载目录：

```bash
mkdir -p BTCOptionsTrading/backend/data/downloads
# 复制 CSV 文件到此目录
# 文件格式: Deribit_BTCUSD_20240329_50000_C.csv
```

### 2. 导入数据

```python
from src.historical.manager import HistoricalDataManager

# 初始化管理器
manager = HistoricalDataManager()

# 导入所有 CSV 文件
result = manager.import_historical_data(
    validate=True,
    generate_report=True
)

print(f"✅ 导入成功: {result.records_imported} 条记录")
print(f"📊 质量评分: {result.quality_report.quality_score:.1f}/100")
```

### 3. 查询数据

```python
from datetime import datetime

# 查询可用合约
instruments = manager.get_available_instruments(underlying_symbol="BTC")
print(f"📋 可用合约: {len(instruments)} 个")

# 获取覆盖率统计
stats = manager.get_coverage_stats(
    start_date=datetime(2024, 3, 1),
    end_date=datetime(2024, 3, 31),
    underlying_symbol="BTC"
)
print(f"📈 数据覆盖率: {stats.coverage_percentage:.1%}")
```

### 4. 回测使用

```python
from src.backtest.backtest_engine import BacktestEngine
from decimal import Decimal

# 创建回测引擎（使用历史数据）
engine = BacktestEngine(
    use_historical_data=True,
    historical_data_manager=manager
)

# 运行回测
result = await engine.run_backtest(
    strategy=my_strategy,
    start_date=datetime(2024, 3, 1),
    end_date=datetime(2024, 3, 31),
    initial_capital=Decimal("10000")
)

print(f"💰 总收益率: {result.total_return:.2%}")
print(f"📊 夏普比率: {result.sharpe_ratio:.2f}")
print(f"📉 最大回撤: {result.max_drawdown:.2%}")
```

## 使用 API

### 启动 API 服务器

```bash
cd BTCOptionsTrading/backend
python run_api.py
```

### 导入数据

```bash
curl -X POST "http://localhost:8000/api/historical-data/import" \
  -H "Content-Type: application/json" \
  -d '{"validate": true, "generate_report": true}'
```

### 查询合约

```bash
curl "http://localhost:8000/api/historical-data/available/instruments?underlying_symbol=BTC"
```

### 获取统计信息

```bash
curl "http://localhost:8000/api/historical-data/stats"
```

## 常见任务

### 检查数据质量

```python
report = manager.validate_data_quality(
    start_date=datetime(2024, 3, 1),
    end_date=datetime(2024, 3, 31)
)

print(f"总记录: {report.total_records}")
print(f"异常记录: {report.anomaly_records}")
print(f"质量评分: {report.quality_score:.1f}/100")

# 查看问题详情
for issue in report.issues[:5]:  # 前 5 个问题
    print(f"[{issue.severity}] {issue.message}")
```

### 导出数据

```python
# 通过 API 导出
import requests

response = requests.post(
    "http://localhost:8000/api/historical-data/export",
    json={
        "format": "csv",
        "start_date": "2024-03-01T00:00:00",
        "end_date": "2024-03-31T23:59:59",
        "compress": True
    }
)

result = response.json()
print(f"导出文件: {result['file_path']}")
print(f"记录数: {result['records_exported']}")
```

### 清理缓存

```python
# 只清理内存缓存
manager.clear_cache(clear_database=False)

# 清理所有数据（包括数据库）
manager.clear_cache(clear_database=True)
```

## 配置选项

### 基本配置

```python
manager = HistoricalDataManager(
    download_dir="data/downloads",      # CSV 文件目录
    db_path="data/historical.db",       # 数据库路径
    cache_size_mb=100                   # 缓存大小（MB）
)
```

### 回测引擎配置

```python
# 使用历史数据
engine = BacktestEngine(
    use_historical_data=True,
    historical_data_manager=manager
)

# 使用模拟数据
engine = BacktestEngine(
    use_historical_data=False
)
```

## 故障排除

### 问题 1: 导入失败

**检查**:
- CSV 文件格式是否正确
- 文件名是否符合规范
- 查看日志获取详细错误

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 问题 2: 数据质量低

**检查**:
- 查看质量报告中的具体问题
- 验证源数据的完整性
- 检查时间范围是否正确

```python
report = manager.validate_data_quality()
for issue in report.issues:
    print(f"[{issue.severity}] {issue.message}")
```

### 问题 3: 查询慢

**优化**:
- 增加缓存大小
- 使用更具体的查询条件
- 定期清理不需要的数据

```python
# 增加缓存
manager = HistoricalDataManager(cache_size_mb=500)

# 使用具体条件
data = manager.cache.query_option_data(
    instrument_name="BTC-29MAR24-50000-C",
    start_date=start,
    end_date=end
)
```

## 测试

运行所有测试：

```bash
cd BTCOptionsTrading/backend
python -m pytest test_converter.py test_validator.py test_cache.py \
                 test_manager.py test_historical_api.py \
                 test_backtest_integration.py -v
```

预期结果: 30/30 测试通过

## 更多信息

- 📖 完整文档: `HISTORICAL_DATA_GUIDE.md`
- 🔧 API 文档: `http://localhost:8000/docs`
- 🧪 测试示例: `test_*.py` 文件
- 📝 集成说明: `BACKTEST_INTEGRATION_SUMMARY.md`

## 下一步

1. ✅ 导入历史数据
2. ✅ 验证数据质量
3. ✅ 在回测中使用
4. 📊 分析回测结果
5. 🚀 优化策略

---

**提示**: 确保数据覆盖率 > 90% 以获得最佳回测结果！
