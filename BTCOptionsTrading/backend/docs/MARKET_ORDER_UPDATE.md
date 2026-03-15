# Market Order 更新说明

## 修改日期
2026-03-12

## 问题描述
weighted_sentiment 情绪交易服务下单时使用的是 limit order（限价单），导致订单无法快速成交。

## 解决方案
将所有交易订单类型从 limit order 改为 market order（市价单），以确保快速成交。

## 修改文件

### 1. `src/trading/deribit_trader.py`
- 修改 `buy()` 方法：将默认 `order_type` 从 `"limit"` 改为 `"market"`
- 修改 `sell()` 方法：将默认 `order_type` 从 `"limit"` 改为 `"market"`
- 增强日志输出：在日志中显示订单类型

### 2. `src/trading/strategy_executor.py`
- `_execute_leg()` 方法已经使用 `order_type = "market"`（无需修改）
- 该方法会调用 `trader.buy()` 和 `trader.sell()`，现在会使用 market order

## 影响范围
- weighted_sentiment 情绪交易服务
- 所有使用 `DeribitTrader` 的交易策略
- 默认行为变更：所有未明确指定 order_type 的交易都将使用 market order

## 注意事项
1. Market order 会立即以市场最优价格成交，可能存在滑点
2. 如果需要使用 limit order，需要在调用时明确指定 `order_type="limit"` 和 `price` 参数
3. 建议在流动性较好的合约上使用 market order

## 测试建议
1. 在测试网环境测试 market order 是否能正常成交
2. 检查成交价格是否合理
3. 监控滑点情况
4. 验证日志输出是否正确显示订单类型
