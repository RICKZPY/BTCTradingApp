# 情绪交易系统 - 快速开始指南

## 🎯 系统功能

这个系统会：
1. ⏰ 每天早上5点自动检查情绪API（通过cron job调度）
2. 🧠 根据情绪数据智能选择策略
3. 💰 在Deribit测试网自动下单
4. 📊 记录交易历史和持仓信息
5. 💾 执行完成后自动退出，释放服务器资源

## ✨ 新特性：资源优化

相比之前的持续运行模式，新版本采用cron job调度：
- ✅ 资源占用从24小时降低到每天约2-5分钟
- ✅ 非常适合资源受限的服务器（如2核vCPU）
- ✅ 自动化调度，无需手动管理进程
- ✅ 所有交易逻辑保持完全不变

## 🚀 部署方式

### 方式A：服务器自动部署（推荐）

如果你要部署到远程服务器，使用自动化部署脚本：

```bash
# 在本地机器上运行
cd BTCOptionsTrading/backend
./deploy_to_server.sh user@your_server_ip
```

脚本会自动完成：
- ✅ 上传代码到服务器
- ✅ 安装Python依赖
- ✅ 配置环境变量
- ✅ 安装Cron Job
- ✅ 配置时区

详细说明请查看：[服务器部署指南](SERVER_DEPLOYMENT_GUIDE.md)

### 方式B：本地/手动部署

如果在本地测试或手动部署，按以下步骤：

#### 第1步：配置API密钥

编辑 `backend/.env` 文件：

```bash
DERIBIT_API_KEY=你的API密钥
DERIBIT_API_SECRET=你的API密钥密码
```

#### 第2步：测试系统

手动运行一次，确保配置正确：

```bash
cd BTCOptionsTrading/backend
python3 sentiment_trading_service.py
```

如果一切正常，你会看到服务执行交易后自动退出。

#### 第3步：安装Cron Job

使用自动化脚本安装cron job：

```bash
./setup_cron.sh install
```

完成！系统现在会在每天早上5点自动运行。

## 📱 查看状态

### 方法1：查看Cron Job状态

```bash
./setup_cron.sh status
```

这会显示：
- Cron job是否已安装
- 最近的执行日志
- 下次执行时间

### 方法2：查看日志文件

```bash
# 查看cron执行日志
tail -f logs/sentiment_trading_cron.log

# 查看详细交易日志
tail -f logs/sentiment_trading.log
```

### 方法3：查看数据文件

```bash
# 查看交易历史
cat data/sentiment_trading_history.json | python3 -m json.tool

# 查看当前持仓
cat data/current_positions.json | python3 -m json.tool
```

## 🎮 策略说明

系统会根据情绪数据自动选择策略：

| 情况 | 策略 | 操作 |
|------|------|------|
| 负面 > 正面 | 负面消息策略 | 买入ATM看跌期权 |
| 正面 > 负面 | 利好消息策略 | 买入ATM看涨期权 |
| 正面 = 负面 | 消息混杂策略 | 卖出窄宽跨式 |

每次交易使用 1000 USD，期权7天后到期。

## 🛑 管理Cron Job

### 查看状态
```bash
./setup_cron.sh status
```

### 卸载Cron Job
```bash
./setup_cron.sh uninstall
```

### 重新安装
```bash
./setup_cron.sh uninstall
./setup_cron.sh install
```

### 手动触发执行（测试用）
```bash
python3 sentiment_trading_service.py
```

## 📂 重要文件

- `sentiment_trading_service.py` - 主交易服务（单次执行模式）
- `setup_cron.sh` - Cron job安装/管理脚本
- `data/sentiment_trading_history.json` - 交易历史
- `data/current_positions.json` - 当前持仓快照
- `logs/sentiment_trading.log` - 详细交易日志
- `logs/sentiment_trading_cron.log` - Cron执行日志

## 🔧 常见问题

### Q: 如何修改执行时间？
A: 编辑 `setup_cron.sh`，修改cron表达式中的时间（默认是 `0 5 * * *` 表示每天5:00 AM）

### Q: 如何修改交易金额？
A: 编辑 `sentiment_trading_service.py`，在 `execute_sentiment_strategy` 方法中修改 `capital=Decimal("1000")`

### Q: 如何验证cron job是否正常工作？
A: 运行 `./setup_cron.sh status` 查看状态，或查看 `logs/sentiment_trading_cron.log`

### Q: 服务执行需要多长时间？
A: 通常2-5分钟，取决于网络状况和市场条件

### Q: 相比之前的持续运行模式有什么优势？
A: 
- 资源占用从24小时降低到每天几分钟
- 非常适合2核vCPU等资源受限的服务器
- 自动化调度，无需手动管理进程
- 所有交易逻辑完全不变

### Q: 如何手动测试？
A: 直接运行 `python3 sentiment_trading_service.py`，服务会执行一次后自动退出

### Q: 情绪API什么时候有数据？
A: 每天早上5点会有新数据，其他时间可能返回之前的数据

## 📞 获取帮助

1. 查看cron设置帮助：`./setup_cron.sh help`
2. 查看执行日志：`tail -f logs/sentiment_trading_cron.log`
3. 手动测试：`python3 sentiment_trading_service.py`

## ⚠️ 重要提示

- ✅ 默认使用Deribit测试网，不会使用真实资金
- ✅ 服务采用单次执行模式，执行完成后自动退出释放资源
- ✅ Cron job会自动在每天5点触发执行
- ✅ 交易历史会自动保存到JSON文件
- ✅ 非常适合资源受限的服务器环境（如2核vCPU）

## 🎉 就这么简单！

系统现在会通过cron job自动在每天早上5点执行交易，完成后自动退出。你可以通过日志文件随时查看执行状态和交易结果。
