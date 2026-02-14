# 回测引擎历史数据集成总结

## 概述

成功将历史数据系统集成到回测引擎中，使回测引擎能够使用真实的历史期权数据进行回测，而不仅仅依赖于 Black-Scholes 模型的理论定价。

## 实现内容

### 1. BacktestEngine 增强

修改了 `src/backtest/backtest_engine.py`，添加以下功能：

#### 初始化参数
- `use_historical_data`: 布尔值，控制是否使用历史数据
- `historical_data_manager`: HistoricalDataManager 实例引用

#### 数据加载
- 在 `run_backtest()` 开始时自动加载历史数据集
- 使用 `get_data_for_backtest()` 获取指定时间范围的数据
- 自动检查数据覆盖率并记录警告

#### 价格更新策略
- `_get_option_price_from_data()`: 从历史数据中获取期权价格
- `_get_underlying_price_from_data()`: 从历史数据中估算标的价格
- `_update_option_prices()`: 优先使用历史价格，缺失时回退到 Black-Scholes 定价

### 2. 集成测试

创建了 `test_backtest_integration.py`，包含 9 个测试用例：

1. ✅ `test_backtest_engine_initialization_with_historical_data` - 测试引擎初始化（历史数据模式）
2. ✅ `test_backtest_engine_initialization_without_historical_data` - 测试引擎初始化（模拟数据模式）
3. ✅ `test_backtest_with_simulated_data` - 测试使用模拟数据的回测
4. ✅ `test_backtest_with_historical_data_no_data` - 测试使用历史数据但数据库为空的情况
5. ✅ `test_data_source_switching` - 测试数据源切换
6. ✅ `test_get_underlying_price_from_data_no_data` - 测试获取标的价格（无数据）
7. ✅ `test_get_option_price_from_data_no_data` - 测试获取期权价格（无数据）
8. ✅ `test_backtest_performance_metrics` - 测试性能指标计算
9. ✅ `test_historical_data_manager_integration` - 测试历史数据管理器集成

**测试结果**: 9/9 通过 (100%)

### 3. 文档更新

更新了 `HISTORICAL_DATA_GUIDE.md`，添加：

- 回测引擎集成使用说明
- 数据源切换示例
- 完整的集成使用示例
- 数据源对比示例

## 核心特性

### 1. 数据源选择

```python
# 使用历史数据
engine = BacktestEngine(
    use_historical_data=True,
    historical_data_manager=manager
)

# 使用模拟数据
engine = BacktestEngine(use_historical_data=False)
```

### 2. 自动数据加载

回测引擎在运行时自动：
- 加载指定时间范围的历史数据
- 检查数据覆盖率
- 记录数据质量警告

### 3. 智能价格获取

价格更新策略：
1. 优先从历史数据中获取实际期权价格
2. 如果历史数据不存在，使用 Black-Scholes 模型定价
3. 始终使用 Black-Scholes 计算希腊字母（即使有历史价格）

### 4. 数据覆盖率监控

```python
# 自动检查覆盖率
result = await engine.run_backtest(...)

# 如果覆盖率 < 80%，记录警告
# 2024-03-01 10:00:00 [warning] Low data coverage (75.5%). Missing 7 dates
```

### 5. 无缝切换

可以在同一个系统中同时运行：
- 历史数据回测（真实市场数据）
- 模拟数据回测（理论定价）
- 对比两种结果

## 使用场景

### 场景 1: 策略验证

使用历史数据验证策略在真实市场中的表现：

```python
engine = BacktestEngine(
    use_historical_data=True,
    historical_data_manager=manager
)

result = await engine.run_backtest(
    strategy=my_strategy,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 3, 31),
    initial_capital=Decimal("10000")
)

print(f"真实市场收益率: {result.total_return:.2%}")
```

### 场景 2: 策略开发

在没有历史数据时，使用模拟数据快速测试策略逻辑：

```python
engine = BacktestEngine(use_historical_data=False)

result = await engine.run_backtest(
    strategy=new_strategy,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    initial_capital=Decimal("10000")
)

print(f"理论收益率: {result.total_return:.2%}")
```

### 场景 3: 对比分析

对比历史数据和理论模型的差异：

```python
# 历史数据回测
result_historical = await engine_historical.run_backtest(...)

# 模拟数据回测
result_simulated = await engine_simulated.run_backtest(...)

# 分析差异
return_diff = result_historical.total_return - result_simulated.total_return
print(f"收益率差异: {return_diff:.2%}")
```

## 技术实现细节

### 数据流

```
HistoricalDataManager
    ↓
get_data_for_backtest()
    ↓
BacktestDataSet
    ↓
BacktestEngine.historical_dataset
    ↓
_get_option_price_from_data()
    ↓
_update_option_prices()
    ↓
回测循环
```

### 价格获取逻辑

```python
def _update_option_prices(self, portfolio, current_date):
    # 1. 获取标的价格
    if self.use_historical_data:
        underlying_price = self._get_underlying_price_from_data(current_date)
    else:
        underlying_price = 50000.0  # 默认价格
    
    for position in portfolio.positions:
        # 2. 尝试获取历史价格
        if self.use_historical_data:
            historical_price = self._get_option_price_from_data(
                position.option_contract.instrument_name,
                current_date
            )
            
            if historical_price is not None:
                # 使用历史价格
                position.option_contract.current_price = historical_price
                continue
        
        # 3. 回退到 Black-Scholes 定价
        bs_price = self.options_engine.black_scholes_price(...)
        position.option_contract.current_price = bs_price
```

### 数据覆盖率检查

```python
if self.use_historical_data and self.historical_data_manager:
    self.historical_dataset = self.historical_data_manager.get_data_for_backtest(
        start_date=start_date,
        end_date=end_date,
        underlying_symbol=underlying_symbol,
        check_completeness=True
    )
    
    if self.historical_dataset.coverage_stats:
        coverage = self.historical_dataset.coverage_stats.coverage_percentage
        
        if coverage < 0.8:
            logger.warning(
                f"Low data coverage ({coverage:.1%}). "
                f"Missing {len(self.historical_dataset.coverage_stats.missing_dates)} dates"
            )
```

## 性能考虑

### 内存使用

- 历史数据集在回测开始时一次性加载到内存
- 使用 LRU 缓存减少重复查询
- 建议根据回测时间范围调整缓存大小

### 查询优化

- 数据按合约名称和时间戳索引
- 使用字典快速查找合约数据
- 避免在回测循环中重复查询数据库

### 建议配置

```python
# 短期回测（1-3个月）
manager = HistoricalDataManager(cache_size_mb=100)

# 中期回测（3-6个月）
manager = HistoricalDataManager(cache_size_mb=200)

# 长期回测（6-12个月）
manager = HistoricalDataManager(cache_size_mb=500)
```

## 限制和注意事项

### 1. 数据质量依赖

回测结果的准确性取决于历史数据的质量：
- 确保数据完整性（覆盖率 > 90%）
- 验证数据准确性（使用质量报告）
- 检查异常值和缺失值

### 2. 标的价格估算

当前使用简化方法从期权价格估算标的价格：
- 使用平价期权的执行价作为标的价格估算
- 未来可以改进为使用看涨看跌平价关系反推

### 3. 希腊字母计算

即使使用历史价格，希腊字母仍使用 Black-Scholes 计算：
- 需要准确的隐含波动率
- 可能与实际市场希腊字母有差异

### 4. 数据缺失处理

当历史数据缺失时：
- 自动回退到 Black-Scholes 定价
- 可能导致回测结果不完全真实
- 建议检查数据覆盖率

## 后续改进方向

### 1. 标的价格数据

添加独立的标的资产价格数据：
- 从交易所获取 BTC 现货价格
- 存储在单独的表中
- 提高标的价格的准确性

### 2. 隐含波动率曲面

构建隐含波动率曲面：
- 从历史期权价格反推隐含波动率
- 构建波动率曲面（执行价 × 到期时间）
- 用于更准确的期权定价

### 3. 市场微观结构

考虑市场微观结构因素：
- 买卖价差
- 流动性影响
- 滑点模拟

### 4. 实时数据集成

支持实时数据和历史数据混合：
- 历史数据用于回测
- 实时数据用于模拟交易
- 无缝切换

## 总结

成功完成了回测引擎与历史数据系统的集成，实现了以下目标：

✅ 回测引擎支持历史数据源
✅ 数据源可以灵活切换
✅ 自动数据加载和验证
✅ 智能价格获取策略
✅ 完整的集成测试（9/9 通过）
✅ 详细的使用文档

系统现在可以：
- 使用真实历史数据进行回测
- 在历史数据和模拟数据之间切换
- 自动处理数据缺失情况
- 监控数据质量和覆盖率

这为策略验证和性能评估提供了更可靠的基础。
