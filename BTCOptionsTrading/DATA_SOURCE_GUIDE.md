# 数据来源和回测指南

## 当前数据来源状态

### ✅ 已实现 - 真实数据接口

系统已经实现了从Deribit获取真实数据的接口：

1. **期权链数据** (`/api/data/options-chain`)
   - 从Deribit API获取真实期权合约
   - 包含实时价格、隐含波动率、希腊字母
   - 支持BTC和ETH期权

2. **标的资产价格** (`/api/data/underlying-price/{symbol}`)
   - 获取BTC/ETH实时指数价格
   - 直接从Deribit获取

3. **波动率曲面** (`/api/data/volatility-surface/{currency}`)
   - 获取完整的隐含波动率曲面
   - 用于波动率分析

4. **历史数据** (`get_historical_data`)
   - Deribit连接器支持获取历史K线数据
   - 可用于回测

### ⚠️ 当前限制 - 模拟数据

由于以下原因，系统目前使用模拟数据：

1. **API配置未完成**
   - 需要配置有效的Deribit API密钥
   - 测试网或主网API密钥都可以

2. **回测引擎使用模拟价格**
   - 回测引擎中的价格更新使用简化模型
   - 未集成真实历史数据

3. **前端Fallback机制**
   - 当API调用失败时，前端使用模拟数据
   - 模拟数据使用Black-Scholes模型计算

## 如何启用真实数据

### 步骤1: 配置Deribit API

1. 打开前端界面: http://localhost:3000
2. 进入"设置"Tab
3. 配置Deribit API:
   ```
   API Key: 你的Deribit API Key
   API Secret: 你的Deribit API Secret
   网络模式: 测试网络（推荐）
   ```
4. 点击"保存配置"

### 步骤2: 重启后端服务

```bash
cd BTCOptionsTrading/backend
# 停止当前服务 (Ctrl+C)
python run_api.py
```

### 步骤3: 验证真实数据

1. 打开"期权链"Tab
2. 选择BTC或ETH
3. 选择到期日
4. 点击"刷新数据"
5. 如果配置正确，将显示真实的Deribit期权数据

## 当前模拟数据说明

### 期权链模拟数据

**改进后的计算方法**（已修复）：

```typescript
// 使用Black-Scholes模型计算期权价格
- Call价格 = S * N(d1) - K * e^(-rT) * N(d2)
- Put价格 = K * e^(-rT) * N(-d2) - S * N(-d1)

// 希腊字母计算
- Delta: Call = N(d1), Put = N(d1) - 1
- Gamma: 基于正态分布密度函数
- Theta: 时间价值衰减
- Vega: 波动率敏感度

// 波动率微笑
- ATM期权: 基础IV = 80%
- OTM期权: IV增加（反映市场特征）
```

**参数设置**：
- 基础价格: BTC $45,000 / ETH $2,500
- 无风险利率: 5%
- 基础隐含波动率: 80%
- 执行价间隔: BTC $1,000 / ETH $50

### 回测模拟数据

**当前实现**：
```python
# 标的价格: 固定在50,000（简化）
underlying_price = 50000.0

# 期权定价: 使用Black-Scholes模型
new_price = options_engine.black_scholes_price(
    S=underlying_price,
    K=strike_price,
    T=time_to_expiry,
    r=0.05,
    sigma=implied_volatility,
    option_type=option_type
)
```

**限制**：
- 标的价格不变化（无真实价格走势）
- 无法反映真实市场波动
- 回测结果仅供参考

## 如何使用真实历史数据进行回测

### 方案1: 集成Deribit历史数据（推荐）

需要修改回测引擎以使用真实历史数据：

```python
# 在回测引擎中添加历史数据加载
async def load_historical_prices(
    self,
    symbol: str,
    start_date: datetime,
    end_date: datetime
) -> Dict[datetime, Decimal]:
    """从Deribit加载历史价格"""
    connector = DeribitConnector()
    historical_data = await connector.get_historical_data(
        instrument=f"{symbol}-PERPETUAL",
        start_timestamp=int(start_date.timestamp() * 1000),
        end_timestamp=int(end_date.timestamp() * 1000),
        resolution="1D"
    )
    
    prices = {}
    for data in historical_data:
        prices[data.timestamp] = data.close_price
    
    return prices
```

### 方案2: 导入CSV历史数据

如果你有其他来源的历史数据：

```python
import pandas as pd

def load_prices_from_csv(file_path: str) -> Dict[datetime, Decimal]:
    """从CSV文件加载历史价格"""
    df = pd.read_csv(file_path)
    prices = {}
    for _, row in df.iterrows():
        date = datetime.fromisoformat(row['date'])
        price = Decimal(str(row['close']))
        prices[date] = price
    return prices
```

## 回测使用方法

### 通过Web界面

1. **创建策略**
   - 进入"策略管理"Tab
   - 选择策略类型（Long Call, Straddle等）
   - 设置执行价、到期日、数量
   - 保存策略

2. **运行回测**
   - 进入"回测分析"Tab
   - 选择已创建的策略
   - 设置回测参数：
     - 开始日期
     - 结束日期
     - 初始资金
   - 点击"运行回测"

3. **查看结果**
   - 盈亏曲线图
   - 绩效指标：
     - 总收益率
     - 夏普比率
     - 最大回撤
     - 胜率
   - 交易明细

### 通过Python脚本

```python
from datetime import datetime, timedelta
from decimal import Decimal
from src.backtest.backtest_engine import BacktestEngine
from src.strategy.strategy_manager import StrategyManager
from src.pricing.options_engine import OptionsEngine

# 创建引擎
engine = BacktestEngine()
strategy_manager = StrategyManager()

# 创建策略
strategy = strategy_manager.create_long_call_strategy(
    underlying_symbol="BTC",
    strike_price=Decimal("50000"),
    expiration_date=datetime.now() + timedelta(days=30),
    quantity=1
)

# 运行回测
result = await engine.run_backtest(
    strategy=strategy,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 2, 1),
    initial_capital=Decimal("100000")
)

# 查看结果
print(f"总收益率: {result.total_return:.2%}")
print(f"夏普比率: {result.sharpe_ratio:.2f}")
print(f"最大回撤: {result.max_drawdown:.2%}")
print(f"胜率: {result.win_rate:.2%}")
```

## 数据质量说明

### 真实数据（配置API后）

**优点**：
- ✅ 真实市场价格和波动率
- ✅ 实时更新
- ✅ 包含真实的买卖价差
- ✅ 真实的成交量和持仓量

**限制**：
- ⚠️ 需要API密钥
- ⚠️ 受API速率限制
- ⚠️ 历史数据有限（Deribit保留期限）

### 模拟数据（当前默认）

**优点**：
- ✅ 无需API配置即可使用
- ✅ 基于Black-Scholes理论模型
- ✅ 符合期权定价基本规律
- ✅ 包含波动率微笑特征

**限制**：
- ⚠️ 不反映真实市场情况
- ⚠️ 标的价格固定不变
- ⚠️ 回测结果仅供学习参考
- ⚠️ 无法用于实盘决策

## 改进建议

### 短期改进（1-2天）

1. **集成真实历史价格**
   ```python
   # 修改回测引擎的_update_option_prices方法
   # 从历史数据中获取真实价格，而不是使用固定值
   ```

2. **添加价格数据缓存**
   ```python
   # 缓存历史数据到本地数据库
   # 减少API调用次数
   ```

3. **改进错误处理**
   ```python
   # 当API调用失败时，给出明确提示
   # 而不是静默切换到模拟数据
   ```

### 中期改进（1周）

1. **实现数据下载功能**
   - 批量下载历史数据
   - 存储到本地数据库
   - 支持离线回测

2. **添加数据验证**
   - 检查数据完整性
   - 识别异常数据点
   - 数据质量报告

3. **支持多数据源**
   - Deribit（主要）
   - Binance期权
   - OKX期权

### 长期改进（1个月）

1. **实时数据流**
   - WebSocket实时价格推送
   - 实时组合监控
   - 实时风险计算

2. **高级回测功能**
   - 滑点模拟
   - 流动性影响
   - 交易成本优化

3. **机器学习集成**
   - 波动率预测
   - 价格趋势预测
   - 策略优化

## 常见问题

### Q1: 为什么期权价格看起来不对？

**A**: 当前使用模拟数据。要使用真实数据：
1. 配置Deribit API密钥
2. 重启后端服务
3. 刷新期权链数据

### Q2: 回测结果可靠吗？

**A**: 当前回测使用模拟数据，结果仅供学习参考。要获得可靠结果：
1. 需要集成真实历史数据
2. 考虑交易成本和滑点
3. 使用足够长的回测周期

### Q3: 如何获取Deribit API密钥？

**A**: 
1. 访问 https://test.deribit.com （测试网）
2. 注册账号
3. 进入 Account → API
4. 创建新的API密钥
5. 设置权限（只需Read权限）

### Q4: 测试网和主网有什么区别？

**A**:
- **测试网**: 虚拟资金，用于开发和测试
- **主网**: 真实资金，用于实盘交易
- **建议**: 先在测试网充分测试

### Q5: 模拟数据的价格是如何计算的？

**A**: 使用Black-Scholes模型：
- 基于标的价格、执行价、到期时间
- 考虑无风险利率和隐含波动率
- 包含波动率微笑效应
- 符合期权定价理论

## 下一步行动

### 立即可做

1. ✅ 配置Deribit API（5分钟）
2. ✅ 查看真实期权链数据（1分钟）
3. ✅ 创建简单策略（5分钟）
4. ✅ 运行模拟回测（1分钟）

### 需要开发

1. ⏳ 集成真实历史数据到回测引擎
2. ⏳ 添加数据缓存机制
3. ⏳ 改进价格更新逻辑
4. ⏳ 添加数据质量检查

## 相关文档

- [API配置指南](./API_CONFIGURATION_GUIDE.md)
- [系统使用指南](./README.md)
- [回测引擎文档](./backend/src/backtest/README.md)
- [Deribit API文档](https://docs.deribit.com/)

---

**总结**: 系统已经具备获取真实数据的能力，但回测引擎还需要改进以使用真实历史数据。当前的模拟数据基于理论模型，可用于学习和测试，但不应用于实盘决策。
