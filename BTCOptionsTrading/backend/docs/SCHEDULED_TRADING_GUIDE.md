# 定时交易功能使用指南

## 功能概述

定时交易功能允许你：
- 配置策略在指定时间自动执行
- 使用Deribit测试API进行真实交易测试
- 设置自动平仓时间
- 监控交易执行状态和持仓

## 快速开始

### 1. 获取Deribit测试API密钥

1. 访问 [Deribit测试网](https://test.deribit.com/)
2. 注册并登录账户
3. 进入 Account → API → Create new key
4. 保存API Key和API Secret

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 测试定时交易

```bash
python scripts/test_scheduled_trading.py
```

按提示输入API密钥，脚本会：
- 连接到Deribit测试网
- 创建一个测试策略
- 设置1分钟后执行
- 显示执行结果

## API使用

### 初始化管理器

```bash
POST /api/scheduled-trading/initialize
```

请求体：
```json
{
  "api_key": "your_api_key",
  "api_secret": "your_api_secret",
  "testnet": true
}
```

### 添加定时策略

```bash
POST /api/scheduled-trading/add-strategy
```

请求体：
```json
{
  "strategy_id": "strategy-uuid",
  "schedule_time": "05:00",
  "timezone": "Asia/Shanghai",
  "use_market_order": false,
  "auto_close": true,
  "close_time": "16:00"
}
```

参数说明：
- `strategy_id`: 策略ID（从策略管理获取）
- `schedule_time`: 执行时间（HH:MM格式）
- `timezone`: 时区（默认Asia/Shanghai）
- `use_market_order`: 是否使用市价单（false=限价单）
- `auto_close`: 是否自动平仓
- `close_time`: 平仓时间

### 查看定时策略

```bash
GET /api/scheduled-trading/strategies
```

返回所有已配置的定时策略列表。

### 启用/禁用策略

```bash
POST /api/scheduled-trading/enable/{strategy_id}
POST /api/scheduled-trading/disable/{strategy_id}
```

### 移除策略

```bash
DELETE /api/scheduled-trading/{strategy_id}
```

### 查看执行日志

```bash
GET /api/scheduled-trading/execution-log
```

返回所有策略的执行历史。

### 查看账户信息

```bash
GET /api/scheduled-trading/account-summary
GET /api/scheduled-trading/positions
```

## 配置文件

定时策略配置保存在 `backend/data/scheduled_trades.json`

示例：
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

## 使用场景

### 场景1：每天早上5点买入看涨期权

1. 在策略管理中创建看涨策略
2. 添加定时交易，设置时间为 05:00
3. 启用策略
4. 系统会在每天早上5点自动执行

### 场景2：日内交易（早上开仓，下午平仓）

1. 创建策略
2. 添加定时交易：
   - 开仓时间：09:00
   - 启用自动平仓
   - 平仓时间：15:00
3. 系统会自动开仓和平仓

### 场景3：测试策略

1. 使用测试网API
2. 设置小额交易
3. 观察执行日志
4. 验证策略逻辑

## 注意事项

### 安全性
- ⚠️ 始终先在测试网测试
- ⚠️ 不要在代码中硬编码API密钥
- ⚠️ 使用环境变量或配置文件存储凭证

### 风险管理
- 设置合理的仓位大小
- 使用限价单避免滑点
- 启用自动平仓控制风险
- 定期检查执行日志

### 监控
- 每天检查执行日志
- 监控账户余额和持仓
- 设置告警通知（可扩展）

## 故障排除

### 认证失败
- 检查API密钥是否正确
- 确认使用的是测试网密钥（testnet=true）
- 检查网络连接

### 订单失败
- 检查账户余额是否充足
- 验证合约名称是否正确
- 查看Deribit API状态

### 定时任务未执行
- 检查策略是否启用
- 确认时区设置正确
- 查看系统日志

## 扩展功能

可以添加的功能：
- 邮件/短信通知
- 更复杂的执行条件（价格触发等）
- 多账户管理
- 风险限额检查
- 执行报告生成

## 相关文档

- [Deribit API文档](https://docs.deribit.com/)
- [策略管理指南](./STRATEGY_MANAGEMENT.md)
- [风险管理指南](./RISK_MANAGEMENT.md)
