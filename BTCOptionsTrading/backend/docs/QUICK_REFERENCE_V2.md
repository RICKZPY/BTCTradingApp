# 加权情绪跨式交易 V2.0 - 快速参考

## 🚀 一键命令

### 查看实时日志
```bash
ssh root@47.86.62.200 "tail -f /root/BTCOptionsTrading/backend/logs/weighted_sentiment_cron.log"
```

### 查看交易记录
```bash
ssh root@47.86.62.200 "tail -20 /root/BTCOptionsTrading/backend/logs/weighted_sentiment_trades.log"
```

### 手动执行测试
```bash
ssh root@47.86.62.200 "cd /root/BTCOptionsTrading/backend && python3 weighted_sentiment_cron.py"
```

### 检查 Cron 状态
```bash
ssh root@47.86.62.200 "crontab -l | grep weighted_sentiment"
```

---

## 📊 关键信息

| 项目 | 值 |
|------|-----|
| **服务器** | root@47.86.62.200 |
| **路径** | /root/BTCOptionsTrading/backend |
| **脚本** | weighted_sentiment_cron.py |
| **执行频率** | 每小时（整点） |
| **Deribit 环境** | Test (测试网) |
| **账户** | 0366QIa2 |
| **交易数量** | 0.1 BTC per option |
| **触发条件** | 新闻评分 >= 7 |

---

## 🔍 日志位置

| 日志文件 | 内容 |
|---------|------|
| `logs/weighted_sentiment_cron.log` | 执行过程日志 |
| `logs/weighted_sentiment_trades.log` | 交易详情记录 |
| `logs/weighted_sentiment.log` | 通用日志 |

---

## ✅ 成功交易标志

在 `weighted_sentiment_trades.log` 中看到：
```
交易成功: True
订单 ID: 12345678  ← 有真实订单 ID
```

---

## ❌ 常见错误

| 错误信息 | 原因 | 解决方法 |
|---------|------|---------|
| `Deribit 认证失败` | API 凭证错误 | 检查 .env 文件 |
| `无法获取现货价格` | 网络问题 | 检查网络连接 |
| `未找到合适的 ATM 期权` | 市场流动性不足 | 等待或调整筛选条件 |
| `看涨期权下单失败` | 余额不足或 API 权限 | 检查账户余额 |

---

## 🌐 Deribit Test 登录

- **网址**: https://test.deribit.com/
- **账户**: 0366QIa2
- **查看**: 订单历史、持仓、余额

---

## 📈 监控清单

- [ ] 每天检查日志一次
- [ ] 每周验证 Deribit 账户一次
- [ ] 监控账户余额
- [ ] 记录交易成功率
- [ ] 观察市场波动

---

## 🔧 维护命令

### 重启 Cron（如需要）
```bash
ssh root@47.86.62.200 "sudo service cron restart"
```

### 清理旧日志（可选）
```bash
ssh root@47.86.62.200 "cd /root/BTCOptionsTrading/backend/logs && rm -f *.log.old"
```

### 备份交易记录
```bash
scp root@47.86.62.200:/root/BTCOptionsTrading/backend/logs/weighted_sentiment_trades.log ./backup_$(date +%Y%m%d).log
```

---

## 📞 紧急联系

- Deribit API 状态: https://status.deribit.com/
- Deribit 支持: https://www.deribit.com/pages/support

---

*快速参考 V2.0 | 更新时间: 2026-03-12*
