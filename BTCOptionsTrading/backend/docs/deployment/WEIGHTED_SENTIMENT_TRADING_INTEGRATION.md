# 加权情绪跨式交易 - Deribit 实际交易集成

## 概述

本文档说明如何将加权情绪跨式交易系统从模拟交易升级为实际 Deribit Test 交易。

## 更新内容

### 1. 核心变更

**之前（SimplifiedStraddleExecutor）：**
- 仅记录交易意图
- 不实际下单
- 返回模拟结果

**现在（StraddleExecutor）：**
- 集成 `DeribitTrader` 类
- 实际连接 Deribit Test API
- 执行真实的期权交易
- 返回实际订单 ID 和执行结果

### 2. 新增功能

#### 2.1 Deribit API 认证
```python
async def authenticate(self) -> bool:
    """认证 Deribit API"""
```
- 使用 `WEIGHTED_SENTIMENT_DERIBIT_API_KEY` 和 `WEIGHTED_SENTIMENT_DERIBIT_API_SECRET`
- 独立于现有 sentiment_trading_service 的凭证
- 自动处理令牌刷新

#### 2.2 现货价格获取
```python
async def get_spot_price(self) -> float:
    """获取 BTC 现货价格"""
```
- 从 Deribit 获取实时 BTC/USD 指数价格
- 用于确定 ATM（平值）期权

#### 2.3 ATM 期权查找
```python
async def find_atm_options(self, spot_price: float) -> tuple[Optional[str], Optional[str]]:
    """查找 ATM（平值）期权合约"""
```
- 获取所有未到期的 BTC 期权合约
- 筛选 7-30 天到期的合约（流动性较好）
- 找到最接近现货价格的执行价格
- 返回看涨和看跌期权合约名称

#### 2.4 期权价格获取
```python
async def get_option_price(self, instrument_name: str) -> float:
    """获取期权价格（使用 mark price）"""
```
- 获取期权的标记价格
- 用于计算交易成本

#### 2.5 跨式交易执行
```python
async def execute_straddle(self, news: WeightedNews) -> StraddleTradeResult:
    """执行跨式期权交易"""
```

完整流程：
1. 认证 Deribit API
2. 获取 BTC 现货价格
3. 查找 ATM 看涨和看跌期权
4. 获取期权价格
5. 下单买入看涨期权（市价单，0.1 BTC）
6. 下单买入看跌期权（市价单，0.1 BTC）
7. 构建并返回交易结果

### 3. 交易参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 交易数量 | 0.1 BTC | 每个期权的交易数量 |
| 订单类型 | market | 市价单，立即成交 |
| 期权类型 | ATM straddle | 平值跨式（看涨+看跌） |
| 到期时间 | 7-30 天 | 筛选流动性较好的合约 |
| 环境 | Deribit Test | 测试网环境 |

### 4. 交易日志增强

更新后的交易日志包含：
- 现货价格
- 看涨期权详情（合约名、执行价、权利金、订单 ID）
- 看跌期权详情（合约名、执行价、权利金、订单 ID）
- 总成本（USD）

示例：
```
================================================================================
交易时间: 2026-03-12T10:00:00.000000
新闻 ID: https://www.odaily.news/zh-CN/newsflash/471596
新闻内容: 星球早讯
情绪: negative
重要性评分: 8/10
交易成功: True
现货价格: $85234.50
看涨期权: BTC-26MAR26-85000-C
  执行价: $85000.00
  权利金: 0.0234 BTC
  订单 ID: 12345678
看跌期权: BTC-26MAR26-85000-P
  执行价: $85000.00
  权利金: 0.0198 BTC
  订单 ID: 12345679
总成本: $3682.15
================================================================================
```

## 部署步骤

### 1. 确认环境变量

确保服务器 `.env` 文件包含：
```bash
WEIGHTED_SENTIMENT_DERIBIT_API_KEY="0366QIa2"
WEIGHTED_SENTIMENT_DERIBIT_API_SECRET="UCQY8v2gThNGFAPkjONQvgwVkVsb7iaxt7bAhRshprc"
```

### 2. 执行部署脚本

```bash
./deploy_weighted_sentiment_update.sh
```

脚本会：
1. 上传更新的 `weighted_sentiment_cron.py`
2. 在服务器上测试 Python 语法
3. 测试模块导入
4. 显示部署信息

### 3. 手动测试（可选）

```bash
ssh root@47.86.62.200
cd /root/BTCOptionsTrading/backend
python3 weighted_sentiment_cron.py
```

### 4. 查看日志

```bash
# 主日志
tail -f /root/BTCOptionsTrading/backend/logs/weighted_sentiment_cron.log

# 交易日志
tail -f /root/BTCOptionsTrading/backend/logs/weighted_sentiment_trades.log
```

## 错误处理

系统会处理以下错误情况：

1. **认证失败**
   - 错误信息：`Deribit 认证失败`
   - 检查 API 凭证是否正确

2. **无法获取现货价格**
   - 错误信息：`无法获取现货价格`
   - 检查网络连接和 Deribit API 状态

3. **未找到合适的期权**
   - 错误信息：`未找到合适的 ATM 期权`
   - 可能是市场流动性不足或筛选条件过严

4. **下单失败**
   - 错误信息：`看涨期权下单失败` 或 `看跌期权下单失败`
   - 检查账户余额和 API 权限

5. **交易异常**
   - 错误信息：`交易异常: <详细错误>`
   - 查看日志获取完整堆栈跟踪

## 监控建议

### 1. 定期检查日志
```bash
# 每天检查交易日志
tail -100 /root/BTCOptionsTrading/backend/logs/weighted_sentiment_trades.log
```

### 2. 监控账户余额
```bash
# 使用 Deribit API 或 Web 界面检查账户余额
# Test 环境: https://test.deribit.com/
```

### 3. 验证订单执行
- 登录 Deribit Test 账户
- 查看订单历史
- 确认订单状态为 "filled"

## 风险提示

1. **测试环境**
   - 当前使用 Deribit Test 环境
   - 不涉及真实资金
   - 可以安全测试

2. **交易频率**
   - Cron 每小时执行一次
   - 只对评分 >= 7 的新闻交易
   - 避免过度交易

3. **资金管理**
   - 每次交易 0.1 BTC
   - 确保账户有足够余额
   - 监控总持仓

4. **市场风险**
   - 跨式策略适合高波动市场
   - 需要大幅价格波动才能盈利
   - 时间衰减会降低期权价值

## 与现有系统的隔离

| 项目 | sentiment_trading_service | weighted_sentiment_cron |
|------|---------------------------|-------------------------|
| API Key | `DERIBIT_API_KEY` | `WEIGHTED_SENTIMENT_DERIBIT_API_KEY` |
| API Secret | `DERIBIT_API_SECRET` | `WEIGHTED_SENTIMENT_DERIBIT_API_SECRET` |
| 数据源 | 情绪 API (43.106.51.106:5001) | 加权情绪 API (43.106.51.106:5002) |
| 策略 | 多种策略模板 | 固定跨式策略 |
| 执行频率 | 每天 5:00 | 每小时 |
| 日志文件 | `sentiment_trading.log` | `weighted_sentiment_cron.log` |
| 交易记录 | `sentiment_trading_history.json` | `weighted_sentiment_trades.log` |

## 下一步

1. **监控首次实际交易**
   - 等待下一个高分新闻（评分 >= 7）
   - 观察交易执行过程
   - 验证订单在 Deribit Test 上成功

2. **优化参数**（可选）
   - 调整交易数量（当前 0.1 BTC）
   - 调整到期时间筛选（当前 7-30 天）
   - 调整 ATM 选择逻辑

3. **增强功能**（可选）
   - 添加止损逻辑
   - 添加持仓管理
   - 添加盈亏统计

## 技术支持

如有问题，请查看：
1. 日志文件：`logs/weighted_sentiment_cron.log`
2. 交易日志：`logs/weighted_sentiment_trades.log`
3. Deribit API 文档：https://docs.deribit.com/
4. Deribit Test 环境：https://test.deribit.com/

## 版本历史

- **v1.0** (2026-03-12): 初始简化实现（仅模拟）
- **v2.0** (2026-03-12): 集成 Deribit 实际交易功能
