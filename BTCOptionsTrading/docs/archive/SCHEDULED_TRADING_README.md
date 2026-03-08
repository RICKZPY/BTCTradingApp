# 定时交易功能

## 功能特性

✅ 已实现的功能：

1. **Deribit交易集成**
   - 支持测试网和生产环境
   - API认证和令牌管理
   - 买入/卖出期权
   - 查询账户和持仓
   - 订单管理（查询、取消）

2. **策略执行**
   - 自动执行多腿策略
   - 支持限价单和市价单
   - 执行日志记录
   - 自动平仓功能

3. **定时调度**
   - 基于cron的定时任务
   - 支持任意时区
   - 每天自动执行
   - 可配置开仓和平仓时间

4. **管理功能**
   - 添加/移除定时策略
   - 启用/禁用策略
   - 查看执行日志
   - 监控账户和持仓

## 快速开始

### 1. 获取Deribit测试API

访问 https://test.deribit.com/ 注册并获取API密钥

### 2. 测试功能

```bash
cd BTCOptionsTrading/backend
python scripts/test_scheduled_trading.py
```

### 3. 使用API

```python
# 初始化
POST /api/scheduled-trading/initialize
{
  "api_key": "your_key",
  "api_secret": "your_secret",
  "testnet": true
}

# 添加定时策略
POST /api/scheduled-trading/add-strategy
{
  "strategy_id": "strategy-uuid",
  "schedule_time": "05:00",
  "timezone": "Asia/Shanghai",
  "use_market_order": false,
  "auto_close": true,
  "close_time": "16:00"
}
```

## 使用场景

### 每天早上5点自动交易

1. 在策略管理中创建策略
2. 配置定时交易：
   - 执行时间：05:00（北京时间）
   - 使用限价单
3. 启用策略
4. 系统每天自动执行

### 日内交易（自动开平仓）

1. 创建策略
2. 配置：
   - 开仓：09:00
   - 平仓：15:00
   - 启用自动平仓
3. 系统自动管理整个交易周期

## 配置文件

配置保存在 `backend/data/scheduled_trades.json`

```json
{
  "scheduled_trades": [
    {
      "strategy_id": "abc-123",
      "strategy_name": "看涨策略",
      "enabled": true,
      "schedule_time": "05:00",
      "timezone": "Asia/Shanghai",
      "use_market_order": false,
      "auto_close": true,
      "close_time": "16:00"
    }
  ]
}
```

## 架构

```
定时交易系统
├── DeribitTrader          # Deribit API客户端
│   ├── 认证管理
│   ├── 订单执行
│   └── 账户查询
├── StrategyExecutor       # 策略执行器
│   ├── 执行多腿策略
│   ├── 订单管理
│   └── 执行日志
└── ScheduledTradingManager # 定时管理器
    ├── 任务调度
    ├── 配置管理
    └── 自动平仓
```

## 安全建议

⚠️ **重要提示**：

1. **始终先在测试网测试**
2. **不要硬编码API密钥**
3. **使用环境变量存储凭证**
4. **设置合理的仓位大小**
5. **定期检查执行日志**

## 文档

详细文档：`backend/docs/SCHEDULED_TRADING_GUIDE.md`

## 下一步

可以扩展的功能：
- [ ] 前端界面集成
- [ ] 邮件/短信通知
- [ ] 更复杂的触发条件
- [ ] 风险限额检查
- [ ] 多账户管理
- [ ] 执行报告生成
