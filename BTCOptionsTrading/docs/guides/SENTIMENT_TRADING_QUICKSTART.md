# 情绪交易系统 - 快速开始指南

## 🎯 系统功能

这个系统会：
1. ⏰ 每天早上5点自动检查情绪API
2. 🧠 根据情绪数据智能选择策略
3. 💰 在Deribit测试网自动下单
4. 📊 提供API查询持仓、订单和历史

## 🚀 三步启动

### 第1步：配置API密钥

编辑 `backend/.env` 文件：

```bash
DERIBIT_API_KEY=你的API密钥
DERIBIT_API_SECRET=你的API密钥密码
```

### 第2步：测试系统

```bash
cd BTCOptionsTrading/backend
./quick_test_sentiment.sh
```

### 第3步：启动服务

```bash
./start_sentiment_trading.sh
```

完成！系统现在在后台运行。

## 📱 查看状态

### 方法1：使用浏览器

打开 `backend/sentiment_dashboard.html` 文件，可以看到漂亮的监控面板。

### 方法2：使用命令行

```bash
# 查看完整状态
curl http://localhost:5002/api/status | python3 -m json.tool

# 查看持仓
curl http://localhost:5002/api/positions | python3 -m json.tool

# 查看订单
curl http://localhost:5002/api/orders | python3 -m json.tool

# 查看交易历史
curl http://localhost:5002/api/history | python3 -m json.tool
```

### 方法3：查看日志

```bash
# 交易服务日志
tail -f logs/sentiment_trading.log

# API服务日志
tail -f logs/sentiment_api.log
```

## 🎮 策略说明

系统会根据情绪数据自动选择策略：

| 情况 | 策略 | 操作 |
|------|------|------|
| 负面 > 正面 | 负面消息策略 | 买入ATM看跌期权 |
| 正面 > 负面 | 利好消息策略 | 买入ATM看涨期权 |
| 正面 = 负面 | 消息混杂策略 | 卖出窄宽跨式 |

每次交易使用 1000 USD，期权7天后到期。

## 🛑 停止服务

```bash
./stop_sentiment_trading.sh
```

## 📂 重要文件

- `sentiment_trading_service.py` - 主交易服务
- `sentiment_api.py` - 状态查询API
- `sentiment_dashboard.html` - 监控面板
- `data/sentiment_trading_history.json` - 交易历史
- `data/current_positions.json` - 当前持仓快照
- `logs/sentiment_trading.log` - 交易日志

## 🔧 常见问题

### Q: 如何修改检查时间？
A: 编辑 `sentiment_trading_service.py`，修改 `CHECK_TIME = time(5, 0)` 这一行。

### Q: 如何修改交易金额？
A: 编辑 `sentiment_trading_service.py`，在 `execute_sentiment_strategy` 方法中修改 `capital=Decimal("1000")`。

### Q: 如何在服务器上持续运行？
A: 使用systemd服务，详见 `SENTIMENT_TRADING_README.md` 的"服务器部署"章节。

### Q: 如何查看是否正常运行？
A: 运行 `ps aux | grep sentiment` 查看进程，或访问 http://localhost:5002/api/health

### Q: 情绪API什么时候有数据？
A: 每天早上5点会有新数据，其他时间可能返回之前的数据。

## 📞 获取帮助

1. 查看完整文档：`SENTIMENT_TRADING_README.md`
2. 运行测试：`python3 test_sentiment_trading.py`
3. 查看日志：`tail -f logs/sentiment_trading.log`

## ⚠️ 重要提示

- ✅ 默认使用Deribit测试网，不会使用真实资金
- ✅ 确保服务器时间正确（影响定时执行）
- ✅ 定期检查日志，确保服务正常运行
- ✅ 交易历史会自动保存到JSON文件

## 🎉 就这么简单！

系统现在会自动监听情绪数据并执行交易。你可以通过API或监控面板随时查看状态。
