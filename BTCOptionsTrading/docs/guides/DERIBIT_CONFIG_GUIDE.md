# Deribit API配置指南

## 配置说明

情绪交易系统支持分离主网和测试网的API配置，实现：
- **主网API**：用于收集真实市场数据（可选）
- **测试网API**：用于执行交易下单（必需）

这样可以在使用真实市场数据的同时，在测试网上安全地进行交易测试。

## 配置方式

### 方式1：完整配置（推荐）

在 `backend/.env` 文件中配置：

```bash
# 主网配置（用于收集真实市场数据）
DERIBIT_MAINNET_API_KEY=your_mainnet_api_key
DERIBIT_MAINNET_API_SECRET=your_mainnet_api_secret

# 测试网配置（用于交易下单）
DERIBIT_TESTNET_API_KEY=your_testnet_api_key
DERIBIT_TESTNET_API_SECRET=your_testnet_api_secret
```

**效果**：
- 从主网获取真实市场数据
- 在测试网执行交易（不使用真实资金）

### 方式2：仅测试网配置

```bash
# 测试网配置（用于数据和交易）
DERIBIT_TESTNET_API_KEY=your_testnet_api_key
DERIBIT_TESTNET_API_SECRET=your_testnet_api_secret
```

**效果**：
- 从测试网获取数据
- 在测试网执行交易

### 方式3：兼容旧配置

```bash
# 使用旧的配置变量（将被视为测试网配置）
DERIBIT_API_KEY=your_api_key
DERIBIT_API_SECRET=your_api_secret
```

**效果**：
- 系统会将这个配置作为测试网配置使用
- 会显示警告提示使用新的配置方式

## 获取API密钥

### 主网API密钥

1. 访问 [Deribit主网](https://www.deribit.com/)
2. 登录账户
3. 进入 Account → API
4. 创建新的API密钥
5. 权限设置：
   - ✅ Read（读取市场数据）
   - ❌ Trade（不需要，我们不在主网交易）
   - ❌ Withdraw（不需要）

### 测试网API密钥

1. 访问 [Deribit测试网](https://test.deribit.com/)
2. 注册/登录测试账户
3. 进入 Account → API
4. 创建新的API密钥
5. 权限设置：
   - ✅ Read（读取数据）
   - ✅ Trade（执行交易）
   - ❌ Withdraw（不需要）

## 配置示例

### 完整配置示例

```bash
# backend/.env

# ========================================
# Deribit API配置
# ========================================

# 主网配置（真实市场数据）
DERIBIT_MAINNET_API_KEY=AbCdEf123456
DERIBIT_MAINNET_API_SECRET=XyZ789AbCdEf

# 测试网配置（交易下单）
DERIBIT_TESTNET_API_KEY=TestKey123456
DERIBIT_TESTNET_API_SECRET=TestSecret789

# ========================================
# 其他配置...
# ========================================
```

## 验证配置

### 测试配置是否正确

```bash
cd backend
python3 test_sentiment_trading.py
```

测试脚本会：
1. 验证测试网连接
2. 如果配置了主网，也会验证主网连接
3. 显示连接状态

### 查看日志

启动服务后查看日志：

```bash
tail -f logs/sentiment_trading.log
```

你应该看到类似的日志：

```
情绪驱动交易服务启动
配置: 测试网用于交易下单, 主网用于数据收集
Deribit测试网认证成功
Deribit主网认证成功
```

或者（如果只配置了测试网）：

```
情绪驱动交易服务启动
配置: 测试网用于交易下单, 测试网用于数据收集
未配置主网密钥，将使用测试网数据
Deribit测试网认证成功
```

## 安全建议

### 1. 保护API密钥

```bash
# 设置.env文件权限
chmod 600 backend/.env

# 确保.env不被提交到git
echo "backend/.env" >> .gitignore
```

### 2. 使用只读权限（主网）

主网API密钥只需要读取权限，不要授予交易权限。

### 3. 定期轮换密钥

建议每3-6个月更换一次API密钥。

### 4. 监控API使用

定期检查Deribit账户的API使用情况，确保没有异常活动。

## 常见问题

### Q: 必须配置主网API吗？

A: 不是必须的。如果只配置测试网API，系统会使用测试网的数据和交易。但主网数据更真实，建议配置。

### Q: 主网API会产生费用吗？

A: 读取市场数据是免费的，不会产生任何费用。只有在主网执行交易才会产生费用，但我们的系统不会在主网交易。

### Q: 测试网有资金限制吗？

A: 测试网使用虚拟资金，可以免费获取。访问测试网后台可以充值测试币。

### Q: 如何切换到主网交易？

A: 不建议这样做！如果确实需要：
1. 修改代码中的 `testnet=True` 为 `testnet=False`
2. 使用主网API密钥（需要交易权限）
3. 充分测试后再使用真实资金

### Q: 配置错误会怎样？

A: 系统会在启动时验证配置：
- 如果测试网配置错误，服务无法启动
- 如果主网配置错误，会降级使用测试网数据

## 配置检查清单

部署前检查：

- [ ] 已获取测试网API密钥
- [ ] 已获取主网API密钥（可选）
- [ ] 已在.env文件中配置密钥
- [ ] 已设置.env文件权限（chmod 600）
- [ ] 已运行测试脚本验证配置
- [ ] 已查看日志确认连接成功
- [ ] 主网API只有读取权限
- [ ] 测试网API有读取和交易权限

## 更新现有部署

如果你已经部署了旧版本，更新配置：

```bash
# 1. 拉取最新代码
cd BTCTradingApp/BTCOptionsTrading
git pull

# 2. 编辑.env文件
cd backend
nano .env

# 3. 添加新的配置项
# DERIBIT_MAINNET_API_KEY=...
# DERIBIT_MAINNET_API_SECRET=...
# DERIBIT_TESTNET_API_KEY=...
# DERIBIT_TESTNET_API_SECRET=...

# 4. 重启服务
./stop_sentiment_trading.sh
./start_sentiment_trading.sh

# 5. 查看日志确认
tail -f logs/sentiment_trading.log
```

## 技术细节

### 配置优先级

系统按以下优先级读取配置：

1. `DERIBIT_TESTNET_API_KEY` / `DERIBIT_TESTNET_API_SECRET`（测试网）
2. `DERIBIT_API_KEY` / `DERIBIT_API_SECRET`（兼容旧配置）
3. `DERIBIT_MAINNET_API_KEY` / `DERIBIT_MAINNET_API_SECRET`（主网，可选）

### 代码实现

```python
# 测试网配置（必需）
testnet_key = os.getenv('DERIBIT_TESTNET_API_KEY')
testnet_secret = os.getenv('DERIBIT_TESTNET_API_SECRET')

# 兼容旧配置
if not testnet_key:
    testnet_key = os.getenv('DERIBIT_API_KEY')
    testnet_secret = os.getenv('DERIBIT_API_SECRET')

# 主网配置（可选）
mainnet_key = os.getenv('DERIBIT_MAINNET_API_KEY')
mainnet_secret = os.getenv('DERIBIT_MAINNET_API_SECRET')

# 初始化连接
trader = DeribitTrader(testnet_key, testnet_secret, testnet=True)
if mainnet_key:
    mainnet_trader = DeribitTrader(mainnet_key, mainnet_secret, testnet=False)
```

## 获取帮助

如果配置遇到问题：

1. 查看日志：`tail -f logs/sentiment_trading.log`
2. 运行测试：`python3 test_sentiment_trading.py`
3. 检查API密钥权限
4. 确认网络连接正常
