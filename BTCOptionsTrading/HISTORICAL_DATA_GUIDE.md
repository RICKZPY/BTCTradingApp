# 历史数据集成系统使用指南

## 概述

历史数据集成系统提供了完整的历史期权数据管理功能，包括数据下载、转换、验证、存储和查询。系统支持从 CryptoDataDownload 导入 Deribit 期权历史数据。

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                  历史数据管理器                          │
│              (HistoricalDataManager)                    │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   下载器      │  │   转换器      │  │   验证器      │
│ Downloader   │  │  Converter   │  │  Validator   │
└──────────────┘  └──────────────┘  └──────────────┘
                          │
                          ▼
                  ┌──────────────┐
                  │   缓存层      │
                  │    Cache     │
                  │ (LRU+SQLite) │
                  └──────────────┘
```

## 快速开始

### 1. 准备数据文件

将 CryptoDataDownload 的 CSV 文件放入 `data/downloads` 目录：

```bash
mkdir -p data/downloads
# 将 CSV 文件复制到此目录
# 文件名格式: Deribit_BTCUSD_20240329_50000_C.csv
```

### 2. 使用 Python API

```python
from src.historical.manager import HistoricalDataManager

# 初始化管理器
manager = HistoricalDataManager(
    download_dir="data/downloads",
    db_path="data/historical_options.db",
    cache_size_mb=100
)

# 导入数据
result = manager.import_historical_data(
    validate=True,
    generate_report=True
)

print(f"导入完成: {result.success_count}/{result.total_count} 文件")
print(f"记录数: {result.records_imported}")
print(f"质量评分: {result.quality_report.quality_score:.1f}/100")

# 获取回测数据
from datetime import datetime

dataset = manager.get_data_for_backtest(
    start_date=datetime(2024, 3, 29),
    end_date=datetime(2024, 3, 30),
    underlying_symbol="BTC"
)

print(f"合约数量: {len(dataset.options_data)}")
print(f"数据覆盖率: {dataset.coverage_stats.coverage_percentage:.1%}")
```

### 3. 使用 REST API

启动 API 服务器：

```bash
cd BTCOptionsTrading/backend
python run_api.py
```

#### 导入数据

```bash
curl -X POST "http://localhost:8000/api/historical-data/import" \
  -H "Content-Type: application/json" \
  -d '{"validate": true, "generate_report": true}'
```

#### 查询可用合约

```bash
curl "http://localhost:8000/api/historical-data/available/instruments?underlying_symbol=BTC"
```

#### 获取覆盖率统计

```bash
curl "http://localhost:8000/api/historical-data/coverage?start_date=2024-03-29T00:00:00&end_date=2024-03-30T00:00:00&underlying_symbol=BTC"
```

#### 导出数据

```bash
curl -X POST "http://localhost:8000/api/historical-data/export" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "csv",
    "start_date": "2024-03-29T00:00:00",
    "end_date": "2024-03-30T00:00:00"
  }'
```

## 核心功能

### 1. 数据导入

系统支持批量导入 CSV 文件，自动完成以下流程：

1. **文件扫描** - 扫描下载目录中的所有 CSV 文件
2. **数据解析** - 解析 CSV 文件和文件名中的期权信息
3. **数据转换** - 转换为系统内部格式
4. **数据验证** - 验证数据完整性和质量
5. **数据存储** - 存储到 SQLite 数据库

```python
# 导入所有文件
result = manager.import_historical_data()

# 导入指定文件
from pathlib import Path
files = [Path("data/downloads/file1.csv"), Path("data/downloads/file2.csv")]
result = manager.import_historical_data(file_paths=files)
```

### 2. 数据验证

系统提供多层次的数据验证：

#### 完整性验证
- 时间序列连续性检查
- 缺失值检测
- 重复数据检测

#### 价格合理性验证
- OHLC 关系验证
- 负价格检测
- 异常波动检测

#### 期权平价关系验证
- 看涨看跌平价关系检查

```python
# 验证数据质量
report = manager.validate_data_quality(
    start_date=datetime(2024, 3, 29),
    end_date=datetime(2024, 3, 30)
)

print(f"质量评分: {report.quality_score:.1f}/100")
print(f"总记录数: {report.total_records}")
print(f"异常记录: {report.anomaly_records}")
print(f"问题数量: {len(report.issues)}")
```

### 3. 数据查询

#### 查询可用合约

```python
# 查询所有 BTC 合约
instruments = manager.get_available_instruments(underlying_symbol="BTC")

# 查询特定时间范围的合约
instruments = manager.get_available_instruments(
    start_date=datetime(2024, 3, 29),
    end_date=datetime(2024, 3, 30),
    underlying_symbol="BTC"
)
```

#### 查询可用日期

```python
# 查询所有日期
dates = manager.get_available_dates(underlying_symbol="BTC")

# 查询特定合约的日期
dates = manager.get_available_dates(instrument_name="BTC-29MAR24-50000-C")
```

#### 获取覆盖率统计

```python
stats = manager.get_coverage_stats(
    start_date=datetime(2024, 3, 29),
    end_date=datetime(2024, 3, 30),
    underlying_symbol="BTC"
)

print(f"总天数: {stats.total_days}")
print(f"有数据天数: {stats.days_with_data}")
print(f"覆盖率: {stats.coverage_percentage:.1%}")
print(f"缺失日期: {len(stats.missing_dates)}")
print(f"覆盖的执行价: {stats.strikes_covered}")
```

### 4. 回测数据获取

为回测引擎提供数据集：

```python
dataset = manager.get_data_for_backtest(
    start_date=datetime(2024, 3, 29),
    end_date=datetime(2024, 3, 30),
    instruments=["BTC-29MAR24-50000-C", "BTC-29MAR24-51000-C"],  # 可选
    underlying_symbol="BTC",
    check_completeness=True
)

# 访问数据
for instrument_name, data_list in dataset.options_data.items():
    print(f"{instrument_name}: {len(data_list)} 条记录")

# 检查覆盖率
if dataset.coverage_stats.coverage_percentage < 0.9:
    print("警告: 数据覆盖率低于 90%")
```

#### 与回测引擎集成

系统支持在回测引擎中使用历史数据：

```python
from src.backtest.backtest_engine import BacktestEngine
from src.historical.manager import HistoricalDataManager

# 初始化历史数据管理器
historical_manager = HistoricalDataManager(
    download_dir="data/downloads",
    db_path="data/historical_options.db"
)

# 创建使用历史数据的回测引擎
backtest_engine = BacktestEngine(
    use_historical_data=True,
    historical_data_manager=historical_manager
)

# 运行回测（自动使用历史数据）
result = await backtest_engine.run_backtest(
    strategy=my_strategy,
    start_date=datetime(2024, 3, 1),
    end_date=datetime(2024, 3, 31),
    initial_capital=Decimal("10000"),
    underlying_symbol="BTC"
)

print(f"回测收益率: {result.total_return:.2%}")
print(f"夏普比率: {result.sharpe_ratio:.2f}")
print(f"最大回撤: {result.max_drawdown:.2%}")
```

#### 数据源切换

回测引擎支持在历史数据和模拟数据之间切换：

```python
# 使用历史数据
engine_historical = BacktestEngine(
    use_historical_data=True,
    historical_data_manager=historical_manager
)

# 使用模拟数据（Black-Scholes定价）
engine_simulated = BacktestEngine(
    use_historical_data=False
)

# 两种引擎可以独立运行回测
result_historical = await engine_historical.run_backtest(...)
result_simulated = await engine_simulated.run_backtest(...)

# 比较结果
print(f"历史数据回测收益: {result_historical.total_return:.2%}")
print(f"模拟数据回测收益: {result_simulated.total_return:.2%}")
```

**数据源行为说明：**

- 当 `use_historical_data=True` 时：
  - 优先使用历史数据中的实际期权价格
  - 如果某个时间点没有历史数据，回退到 Black-Scholes 定价
  - 自动检查数据覆盖率并记录警告
  
- 当 `use_historical_data=False` 时：
  - 完全使用 Black-Scholes 模型定价
  - 适用于测试策略逻辑或没有历史数据的情况

### 5. 数据导出

支持导出为 CSV 或 JSON 格式：

```python
# 通过 API 导出
import requests

response = requests.post(
    "http://localhost:8000/api/historical-data/export",
    json={
        "format": "csv",
        "start_date": "2024-03-29T00:00:00",
        "end_date": "2024-03-30T00:00:00",
        "instruments": ["BTC-29MAR24-50000-C"],
        "compress": True
    }
)

result = response.json()
print(f"导出文件: {result['file_path']}")
print(f"记录数: {result['records_exported']}")
```

### 6. 缓存管理

系统使用两层缓存：

1. **内存缓存 (LRU)** - 快速访问最近使用的数据
2. **SQLite 数据库** - 持久化存储

```python
# 获取缓存统计
stats = manager.get_stats()
print(f"数据库记录: {stats['cache']['database']['record_count']}")
print(f"内存缓存: {stats['cache']['memory_cache']['entries']} 条目")
print(f"缓存大小: {stats['cache']['memory_cache']['size_mb']:.2f} MB")

# 清理内存缓存
manager.clear_cache(clear_database=False)

# 清理所有数据（包括数据库）
manager.clear_cache(clear_database=True)
```

## API 端点参考

### 数据管理

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/historical-data/import` | POST | 导入历史数据 |
| `/api/historical-data/available/instruments` | GET | 获取可用合约列表 |
| `/api/historical-data/available/dates` | GET | 获取可用日期列表 |
| `/api/historical-data/coverage` | GET | 获取覆盖率统计 |
| `/api/historical-data/quality` | GET | 获取质量报告 |
| `/api/historical-data/stats` | GET | 获取统计信息 |
| `/api/historical-data/cache` | DELETE | 清理缓存 |
| `/api/historical-data/export` | POST | 导出数据 |
| `/api/historical-data/health` | GET | 健康检查 |

## 数据格式

### CSV 文件格式

文件名格式：`Deribit_BTCUSD_20240329_50000_C.csv`

- `BTCUSD` - 标的资产
- `20240329` - 到期日期 (YYYYMMDD)
- `50000` - 执行价
- `C` - 期权类型 (C=看涨, P=看跌)

CSV 内容格式：

```csv
unix,open,high,low,close,volume
1711670400,0.0500,0.0550,0.0450,0.0525,100.5
1711674000,0.0525,0.0575,0.0500,0.0550,150.25
```

### 内部数据格式

```python
{
    "instrument_name": "BTC-29MAR24-50000-C",
    "timestamp": "2024-03-29T08:00:00",
    "open_price": 0.0500,
    "high_price": 0.0550,
    "low_price": 0.0450,
    "close_price": 0.0525,
    "volume": 100.5,
    "strike_price": 50000,
    "expiry_date": "2024-03-29T00:00:00",
    "option_type": "call",
    "underlying_symbol": "BTC",
    "data_source": "CryptoDataDownload"
}
```

## 性能优化

### 1. 批量导入

使用批量导入可以显著提高性能：

```python
# 批量导入（推荐）
result = manager.import_historical_data()  # 自动批量处理

# 单个文件导入（较慢）
for file in files:
    result = manager.import_historical_data(file_paths=[file])
```

### 2. 缓存配置

根据可用内存调整缓存大小：

```python
# 小内存环境
manager = HistoricalDataManager(cache_size_mb=50)

# 大内存环境
manager = HistoricalDataManager(cache_size_mb=500)
```

### 3. 并行处理

转换器自动使用多进程并行处理：

```python
# 自动使用 CPU 核心数
converter = HistoricalDataConverter()
data = converter.process_files_parallel(files)

# 手动指定工作进程数
data = converter.process_files_parallel(files, max_workers=4)
```

## 故障排除

### 问题 1: 导入失败

**症状**: 导入时出现错误

**解决方案**:
1. 检查 CSV 文件格式是否正确
2. 确认文件名符合命名规范
3. 查看日志文件获取详细错误信息

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 问题 2: 数据质量低

**症状**: 质量评分低于预期

**解决方案**:
1. 检查质量报告中的具体问题
2. 验证源数据的完整性
3. 检查时间范围是否正确

```python
report = manager.validate_data_quality()
for issue in report.issues:
    print(f"[{issue.severity}] {issue.message}")
```

### 问题 3: 查询性能慢

**症状**: 数据查询响应时间长

**解决方案**:
1. 增加缓存大小
2. 使用更具体的查询条件
3. 定期清理不需要的数据

```python
# 使用具体的查询条件
data = manager.cache.query_option_data(
    instrument_name="BTC-29MAR24-50000-C",  # 指定合约
    start_date=start,
    end_date=end
)
```

## 最佳实践

1. **定期验证数据质量** - 在导入后立即验证
2. **监控覆盖率** - 确保数据完整性
3. **合理使用缓存** - 根据内存情况调整缓存大小
4. **批量操作** - 尽可能使用批量导入和查询
5. **定期备份** - 备份 SQLite 数据库文件

## 示例代码

完整的使用示例请参考：

- `test_manager.py` - 管理器使用示例
- `test_historical_api.py` - API 使用示例
- `test_converter.py` - 转换器使用示例
- `test_validator.py` - 验证器使用示例
- `test_cache.py` - 缓存使用示例
- `test_backtest_integration.py` - 回测引擎集成示例

## 回测引擎集成

历史数据系统已完全集成到回测引擎中，支持使用真实历史数据进行回测。

### 集成特性

1. **数据源选择** - 可以选择使用历史数据或模拟数据
2. **自动数据加载** - 回测引擎自动从历史数据管理器加载数据
3. **数据覆盖率检查** - 自动检查数据完整性并记录警告
4. **价格获取策略** - 优先使用历史价格，缺失时回退到模型定价
5. **无缝切换** - 可以在历史数据和模拟数据之间轻松切换

### 使用示例

```python
from src.backtest.backtest_engine import BacktestEngine
from src.historical.manager import HistoricalDataManager
from src.core.models import Strategy, StrategyLeg, OptionContract, OptionType, ActionType
from datetime import datetime
from decimal import Decimal

# 1. 初始化历史数据管理器
historical_manager = HistoricalDataManager(
    download_dir="data/downloads",
    db_path="data/historical_options.db"
)

# 2. 导入历史数据（如果还没有）
import_result = historical_manager.import_historical_data(
    validate=True,
    generate_report=True
)
print(f"导入完成: {import_result.records_imported} 条记录")

# 3. 创建交易策略
strategy = Strategy(
    name="Bull Call Spread",
    description="看涨价差策略",
    legs=[
        StrategyLeg(
            option_contract=long_call,  # 买入低执行价看涨期权
            action=ActionType.BUY,
            quantity=1
        ),
        StrategyLeg(
            option_contract=short_call,  # 卖出高执行价看涨期权
            action=ActionType.SELL,
            quantity=1
        )
    ]
)

# 4. 创建使用历史数据的回测引擎
backtest_engine = BacktestEngine(
    use_historical_data=True,
    historical_data_manager=historical_manager
)

# 5. 运行回测
result = await backtest_engine.run_backtest(
    strategy=strategy,
    start_date=datetime(2024, 3, 1),
    end_date=datetime(2024, 3, 31),
    initial_capital=Decimal("10000"),
    underlying_symbol="BTC"
)

# 6. 查看结果
print(f"策略: {result.strategy_name}")
print(f"初始资金: {result.initial_capital}")
print(f"最终资金: {result.final_capital}")
print(f"总收益率: {result.total_return:.2%}")
print(f"夏普比率: {result.sharpe_ratio:.2f}")
print(f"最大回撤: {result.max_drawdown:.2%}")
print(f"胜率: {result.win_rate:.2%}")
print(f"总交易数: {result.total_trades}")
```

### 数据源对比

可以同时运行历史数据和模拟数据回测，对比结果：

```python
# 历史数据回测
engine_historical = BacktestEngine(
    use_historical_data=True,
    historical_data_manager=historical_manager
)
result_historical = await engine_historical.run_backtest(
    strategy=strategy,
    start_date=start_date,
    end_date=end_date,
    initial_capital=initial_capital
)

# 模拟数据回测
engine_simulated = BacktestEngine(use_historical_data=False)
result_simulated = await engine_simulated.run_backtest(
    strategy=strategy,
    start_date=start_date,
    end_date=end_date,
    initial_capital=initial_capital
)

# 对比结果
print("=" * 60)
print(f"{'指标':<20} {'历史数据':<20} {'模拟数据':<20}")
print("=" * 60)
print(f"{'总收益率':<20} {result_historical.total_return:>18.2%} {result_simulated.total_return:>18.2%}")
print(f"{'夏普比率':<20} {result_historical.sharpe_ratio:>18.2f} {result_simulated.sharpe_ratio:>18.2f}")
print(f"{'最大回撤':<20} {result_historical.max_drawdown:>18.2%} {result_simulated.max_drawdown:>18.2%}")
print(f"{'胜率':<20} {result_historical.win_rate:>18.2%} {result_simulated.win_rate:>18.2%}")
print("=" * 60)
```

## 技术支持

如有问题，请查看：

1. 系统日志文件
2. 测试文件中的示例代码
3. API 文档 (http://localhost:8000/docs)
