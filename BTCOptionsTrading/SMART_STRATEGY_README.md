# 智能策略构建器

## 功能亮点

✨ 使用相对参数创建灵活的策略模板，无需硬编码具体日期和价格！

### 相对到期日
不再需要选择具体日期，使用相对时间：
- **T+1** - 明天
- **T+7** - 一周后
- **T+30** - 一个月后

### 相对行权价
不再需要猜测具体价格，使用相对位置：
- **ATM** - 平值（最接近当前价格）
- **ITM+1** - 实值第1档
- **OTM+1** - 虚值第1档

## 使用示例

### 创建一个简单的看涨策略

```json
POST /api/smart-strategy/build

{
  "name": "周度看涨",
  "description": "每周买入ATM看涨期权",
  "strategy_type": "single_leg",
  "legs": [
    {
      "option_type": "call",
      "action": "buy",
      "quantity": 1,
      "relative_expiry": "T+7",
      "relative_strike": "ATM"
    }
  ]
}
```

系统会自动：
1. 获取当前BTC价格（例如 $95,000）
2. 找到7天后到期的合约
3. 选择最接近$95,000的行权价
4. 返回完整的策略对象

### 创建跨式策略

```json
{
  "name": "OTM跨式",
  "strategy_type": "strangle",
  "legs": [
    {
      "option_type": "call",
      "action": "buy",
      "quantity": 1,
      "relative_expiry": "T+7",
      "relative_strike": "OTM+1"
    },
    {
      "option_type": "put",
      "action": "buy",
      "quantity": 1,
      "relative_expiry": "T+7",
      "relative_strike": "OTM+1"
    }
  ]
}
```

## API端点

### 获取选项
```bash
GET /api/smart-strategy/relative-expiries  # 获取所有到期日选项
GET /api/smart-strategy/relative-strikes   # 获取所有行权价选项
GET /api/smart-strategy/templates          # 获取预定义模板
```

### 构建策略
```bash
POST /api/smart-strategy/build                        # 自定义构建
POST /api/smart-strategy/build-from-template/{id}     # 从模板构建
GET  /api/smart-strategy/preview                      # 预览合约
```

## 预定义模板

系统提供3个预定义模板：

1. **ATM看涨周策略** (`atm_call_weekly`)
   - 买入ATM看涨期权，一周到期
   
2. **OTM跨式策略** (`otm_straddle`)
   - 买入OTM看涨和看跌期权
   
3. **牛市看涨价差** (`bull_call_spread`)
   - 买入ATM看涨，卖出OTM看涨

## 与定时交易结合

智能策略与定时交易完美配合：

```python
# 1. 创建智能策略模板
template = {
  "name": "每日ATM看涨",
  "legs": [{
    "option_type": "call",
    "action": "buy",
    "quantity": 1,
    "relative_expiry": "T+7",
    "relative_strike": "ATM"
  }]
}

# 2. 配置定时交易
scheduled_config = {
  "schedule_time": "05:00",
  "timezone": "Asia/Shanghai"
}

# 3. 每天早上5点，系统会：
#    - 获取当前BTC价格
#    - 找到最合适的ATM看涨期权
#    - 自动执行交易
```

## 优势

### 1. 灵活性
策略模板可以在任何时间、任何价格使用，无需修改。

### 2. 自动化
系统自动找到最匹配的合约，无需手动查找。

### 3. 可重用
一次创建，多次使用，适合定时交易。

### 4. 简单易用
不需要了解具体的合约名称和到期日格式。

## 前端UI建议

### 策略创建表单

```
策略名称: [___________________]

策略腿 #1:
  期权类型: [看涨 ▼]
  操作:     [买入 ▼]
  数量:     [1___]
  到期日:   [一周(T+7) ▼]
  行权价:   [平值(ATM) ▼]
  
  实时预览: BTC-28FEB26-95000-C
  当前价格: 0.05 BTC

[+ 添加策略腿]

[保存模板] [立即构建] [配置定时交易]
```

### 下拉选项示例

**到期日选择：**
- 明天 (T+1)
- 后天 (T+2)
- 一周 (T+7) ⭐
- 两周 (T+14)
- 一个月 (T+30)
- 两个月 (T+60)
- 三个月 (T+90)

**行权价选择：**
- 实值第3档 (ITM+3)
- 实值第2档 (ITM+2)
- 实值第1档 (ITM+1)
- 平值 (ATM) ⭐
- 虚值第1档 (OTM+1)
- 虚值第2档 (OTM+2)
- 虚值第3档 (OTM+3)

## 工作原理

```
用户输入相对参数
    ↓
获取当前BTC价格
    ↓
查询可用期权合约
    ↓
计算目标到期日
    ↓
找到最接近的行权价
    ↓
返回实际策略对象
```

## 完整示例

### Python代码

```python
from src.strategy.smart_strategy_builder import (
    SmartStrategyBuilder,
    SmartStrategyTemplate,
    SmartStrategyLeg,
    RelativeExpiry,
    RelativeStrike
)

# 创建模板
template = SmartStrategyTemplate(
    name="我的策略",
    description="买入ATM看涨",
    strategy_type=StrategyType.SINGLE_LEG,
    legs=[
        SmartStrategyLeg(
            option_type=OptionType.CALL,
            action=ActionType.BUY,
            quantity=1,
            relative_expiry=RelativeExpiry.T_PLUS_7,
            relative_strike=RelativeStrike.ATM
        )
    ]
)

# 构建策略
builder = SmartStrategyBuilder(connector)
strategy = await builder.build_strategy(template)

print(f"策略名称: {strategy.name}")
print(f"策略腿数: {len(strategy.legs)}")
for leg in strategy.legs:
    print(f"  合约: {leg.option_contract.instrument_name}")
    print(f"  价格: {leg.option_contract.current_price}")
```

## 文档

详细文档：`backend/docs/SMART_STRATEGY_GUIDE.md`

## 下一步

可以扩展的功能：
- [ ] 前端UI组件
- [ ] 更多预定义模板
- [ ] 波动率筛选
- [ ] 流动性检查
- [ ] 策略回测集成
- [ ] 保存和管理模板库
