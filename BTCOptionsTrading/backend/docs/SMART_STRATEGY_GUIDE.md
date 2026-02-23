# 智能策略构建器使用指南

## 功能概述

智能策略构建器允许你使用相对参数创建策略，而不是硬编码具体的到期日和行权价。这使得策略更加灵活和可重用。

## 核心概念

### 1. 相对到期日

使用相对时间而不是具体日期：

| 代码 | 说明 | 实际天数 |
|------|------|----------|
| T+1 | 明天 | 1天 |
| T+2 | 后天 | 2天 |
| T+7 | 一周 | 7天 |
| T+14 | 两周 | 14天 |
| T+30 | 一个月 | 30天 |
| T+60 | 两个月 | 60天 |
| T+90 | 三个月 | 90天 |

### 2. 相对行权价

使用相对价格而不是具体金额：

| 代码 | 说明 | 对于看涨期权 | 对于看跌期权 |
|------|------|--------------|--------------|
| ITM+3 | 实值第3档 | 当前价-3档 | 当前价+3档 |
| ITM+2 | 实值第2档 | 当前价-2档 | 当前价+2档 |
| ITM+1 | 实值第1档 | 当前价-1档 | 当前价+1档 |
| ATM | 平值 | 最接近当前价 | 最接近当前价 |
| OTM+1 | 虚值第1档 | 当前价+1档 | 当前价-1档 |
| OTM+2 | 虚值第2档 | 当前价+2档 | 当前价-2档 |
| OTM+3 | 虚值第3档 | 当前价+3档 | 当前价-3档 |

## API使用

### 1. 获取可用选项

```bash
# 获取相对到期日选项
GET /api/smart-strategy/relative-expiries

# 获取相对行权价选项
GET /api/smart-strategy/relative-strikes
```

### 2. 获取预定义模板

```bash
GET /api/smart-strategy/templates
```

返回示例：
```json
{
  "templates": [
    {
      "id": "atm_call_weekly",
      "name": "ATM看涨周策略",
      "description": "买入ATM看涨期权，一周到期",
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
  ]
}
```

### 3. 构建智能策略

```bash
POST /api/smart-strategy/build
```

请求体：
```json
{
  "name": "我的看涨策略",
  "description": "买入ATM看涨期权",
  "strategy_type": "single_leg",
  "underlying": "BTC",
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

返回实际的策略对象，包含具体的合约信息。

### 4. 从模板构建

```bash
POST /api/smart-strategy/build-from-template/atm_call_weekly?underlying=BTC
```

### 5. 预览合约

```bash
GET /api/smart-strategy/preview?option_type=call&relative_expiry=T+7&relative_strike=ATM&underlying=BTC
```

实时显示匹配的合约信息。

## 使用示例

### 示例1：简单看涨策略

```json
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

### 示例2：跨式策略

```json
{
  "name": "OTM跨式",
  "description": "买入OTM看涨和看跌",
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

### 示例3：牛市价差

```json
{
  "name": "牛市看涨价差",
  "description": "买入ATM，卖出OTM",
  "strategy_type": "custom",
  "legs": [
    {
      "option_type": "call",
      "action": "buy",
      "quantity": 1,
      "relative_expiry": "T+14",
      "relative_strike": "ATM"
    },
    {
      "option_type": "call",
      "action": "sell",
      "quantity": 1,
      "relative_expiry": "T+14",
      "relative_strike": "OTM+2"
    }
  ]
}
```

## 优势

### 1. 可重用性
策略模板可以在任何时间、任何价格水平使用，无需修改。

### 2. 自动适应
系统自动找到最接近的合约，适应市场变化。

### 3. 简化配置
不需要手动查找合约名称和到期日。

### 4. 定时交易友好
与定时交易完美配合，每天自动选择合适的合约。

## 工作流程

1. **创建模板**
   - 使用相对参数定义策略
   - 保存为可重用模板

2. **构建策略**
   - 系统获取当前BTC价格
   - 查找匹配的期权合约
   - 计算实际行权价
   - 返回完整策略

3. **执行交易**
   - 可以立即执行
   - 或配置为定时交易

## 前端集成建议

### 策略创建界面

```
┌─────────────────────────────────┐
│ 创建智能策略                     │
├─────────────────────────────────┤
│ 策略名称: [___________________] │
│ 策略类型: [单腿 ▼]              │
│                                 │
│ 策略腿配置:                     │
│ ┌─────────────────────────────┐ │
│ │ 期权类型: [看涨 ▼]          │ │
│ │ 操作:     [买入 ▼]          │ │
│ │ 数量:     [1___]            │ │
│ │ 到期日:   [一周(T+7) ▼]    │ │
│ │ 行权价:   [平值(ATM) ▼]    │ │
│ │                             │ │
│ │ 预览: BTC-28FEB26-95000-C   │ │
│ │ 当前价: 0.05 BTC            │ │
│ └─────────────────────────────┘ │
│                                 │
│ [+ 添加策略腿]                  │
│                                 │
│ [预览策略] [保存模板] [立即构建]│
└─────────────────────────────────┘
```

### 下拉选项

到期日选择：
- 明天 (T+1)
- 后天 (T+2)
- 一周 (T+7) ⭐ 推荐
- 两周 (T+14)
- 一个月 (T+30)

行权价选择：
- 实值第2档 (ITM+2)
- 实值第1档 (ITM+1)
- 平值 (ATM) ⭐ 推荐
- 虚值第1档 (OTM+1)
- 虚值第2档 (OTM+2)

## 注意事项

1. **合约可用性**
   - 并非所有相对参数组合都有对应合约
   - 系统会选择最接近的可用合约

2. **价格变化**
   - 相对行权价基于构建时的BTC价格
   - 价格波动可能影响实际选择的合约

3. **到期日匹配**
   - 系统允许±3天的到期日偏差
   - 确保有足够的流动性

## 预定义模板

系统提供以下预定义模板：

1. **ATM看涨周策略** (`atm_call_weekly`)
   - 买入ATM看涨，一周到期
   - 适合看涨行情

2. **OTM跨式策略** (`otm_straddle`)
   - 买入OTM看涨和看跌
   - 适合高波动预期

3. **牛市看涨价差** (`bull_call_spread`)
   - 买入ATM，卖出OTM
   - 有限风险的看涨策略

## 扩展功能

可以添加的功能：
- 更多预定义模板
- 自定义行权价间隔
- 波动率筛选
- 流动性检查
- 历史回测
