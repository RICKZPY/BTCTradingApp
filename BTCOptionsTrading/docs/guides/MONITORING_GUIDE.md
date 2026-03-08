# 监控指南

## 快速访问

### 浏览器访问
直接在浏览器打开：
- 健康检查: http://47.86.62.200:5002/api/health
- 完整状态: http://47.86.62.200:5002/api/status
- 持仓信息: http://47.86.62.200:5002/api/positions
- 交易历史: http://47.86.62.200:5002/api/history

### 命令行快速查看

```bash
# 查看完整状态
curl -s http://47.86.62.200:5002/api/status | python3 -m json.tool

# 查看持仓
curl -s http://47.86.62.200:5002/api/positions | python3 -m json.tool

# 查看实时持仓（直接从Deribit获取）
curl -s http://47.86.62.200:5002/api/live/positions | python3 -m json.tool
```

## 监控工具

### 1. Python监控脚本（推荐）

持续监控，每30秒自动刷新：
```bash
python3 BTCOptionsTrading/monitor_api.py
```

只检查一次：
```bash
python3 BTCOptionsTrading/monitor_api.py --once
```

自定义刷新间隔：
```bash
python3 BTCOptionsTrading/monitor_api.py --interval 10
```

### 2. 测试所有端点

```bash
./BTCOptionsTrading/test_all_endpoints.sh
```

### 3. 快速测试脚本

```bash
./BTCOptionsTrading/test_remote_api.sh
```

## API端点说明

### 基础端点

| 端点 | 说明 | 数据来源 |
|------|------|----------|
| `/api/health` | 健康检查 | 本地 |
| `/api/status` | 完整状态（持仓+订单+历史） | 缓存文件 |
| `/api/positions` | 当前持仓 | 缓存文件 |
| `/api/orders` | 未完成订单 | 缓存文件 |
| `/api/history` | 交易历史 | 本地文件 |

### 实时端点

| 端点 | 说明 | 数据来源 |
|------|------|----------|
| `/api/live/positions` | 实时持仓 | Deribit API |
| `/api/live/orders` | 实时订单 | Deribit API |

## 监控面板

### 使用HTML面板

1. 打开 `BTCOptionsTrading/backend/sentiment_dashboard.html`
2. 修改API地址：
   ```javascript
   const API_BASE = 'http://47.86.62.200:5002';
   ```
3. 在浏览器中打开该文件

## 服务管理

### 检查服务状态

在服务器上：
```bash
# 检查进程
ps aux | grep sentiment_api

# 检查端口
netstat -tlnp | grep 5002
```

### 查看日志

```bash
# 在服务器上
tail -f /root/BTCTradingApp/BTCOptionsTrading/backend/logs/sentiment_api.log
```

### 重启服务

```bash
# 在服务器上
cd /root/BTCTradingApp/BTCOptionsTrading/backend
pkill -f sentiment_api.py
./start_api_service.sh
```

## 自动化监控

### 设置定时检查

创建cron任务，每5分钟检查一次：
```bash
crontab -e
```

添加：
```
*/5 * * * * curl -s http://47.86.62.200:5002/api/health || echo "API异常" | mail -s "告警" your@email.com
```

### 使用监控服务

推荐使用：
- **Uptime Robot**: https://uptimerobot.com (免费)
- **Pingdom**: https://www.pingdom.com
- **StatusCake**: https://www.statuscake.com

配置监控URL: `http://47.86.62.200:5002/api/health`

## 理解返回数据

### 持仓信息字段

```json
{
  "instrument_name": "BTC-13MAR26-64000-C",  // 合约名称
  "size": 2.0,                                // 持仓数量
  "direction": "buy",                         // 方向（买入/卖出）
  "average_price": 0.041,                     // 平均价格（BTC）
  "mark_price": 0.06366135,                   // 标记价格
  "total_profit_loss": 0.045322707,           // 总盈亏（BTC）
  "floating_profit_loss_usd": 3400.23,        // 浮动盈亏（USD）
  "delta": 1.46613,                           // Delta值
  "gamma": 0.00011,                           // Gamma值
  "vega": 50.17371,                           // Vega值
  "theta": -408.42229                         // Theta值
}
```

### 健康检查返回

```json
{
  "status": "healthy",                        // 服务状态
  "timestamp": "2026-03-08T23:43:39",        // 时间戳
  "trader_initialized": true,                 // 交易器是否初始化
  "config": {
    "has_testnet_config": true,              // 是否有测试网配置
    "has_legacy_config": false,              // 是否有旧配置
    "using_config": "testnet"                // 使用的配置类型
  }
}
```

## 故障排查

如果API无法访问，按顺序检查：

1. **服务器上运行诊断**：
   ```bash
   cd /root/BTCTradingApp/BTCOptionsTrading/backend
   ./diagnose_api.sh
   ```

2. **检查配置**：
   ```bash
   ./check_env_config.sh
   ```

3. **查看详细故障排查指南**：
   参考 `SERVER_TROUBLESHOOTING.md`

## 常用命令速查

```bash
# 本地 - 查看完整状态
curl -s http://47.86.62.200:5002/api/status | python3 -m json.tool

# 本地 - 持续监控
python3 BTCOptionsTrading/monitor_api.py

# 服务器 - 查看日志
ssh root@47.86.62.200 "tail -f /root/BTCTradingApp/BTCOptionsTrading/backend/logs/sentiment_api.log"

# 服务器 - 重启服务
ssh root@47.86.62.200 "cd /root/BTCTradingApp/BTCOptionsTrading/backend && pkill -f sentiment_api.py && ./start_api_service.sh"

# 服务器 - 运行诊断
ssh root@47.86.62.200 "cd /root/BTCTradingApp/BTCOptionsTrading/backend && ./diagnose_api.sh"
```

---

**服务器**: 47.86.62.200  
**端口**: 5002  
**状态**: ✓ 正常运行  
**交易器**: ✓ 已初始化
