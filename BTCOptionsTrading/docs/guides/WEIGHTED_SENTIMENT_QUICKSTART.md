# 加权情绪跨式期权交易 - 快速入门指南

## 概述

这是一个轻量级的自动化交易系统，基于加权情绪新闻 API 执行跨式期权交易策略。系统设计用于资源受限的测试环境，使用 cron job 而不是常驻服务。

### 核心特性

- ✅ 轻量级设计，适合资源受限环境
- ✅ 基于 cron job，每小时执行一次
- ✅ SQLite 数据库，无需额外数据库服务
- ✅ 简单的 HTTP API 用于状态查询
- ✅ 完整的日志记录

### 工作原理

1. **每小时执行**：Cron job 每小时触发一次
2. **获取新闻**：从加权情绪 API 获取最新新闻
3. **筛选高分新闻**：识别重要性评分 ≥ 7 的新闻
4. **去重处理**：跳过已处理的新闻
5. **执行交易**：为每条新的高分新闻执行跨式期权交易
6. **记录日志**：保存交易记录和系统日志

## 系统要求

### 最低配置

- **CPU**: 1 核心
- **内存**: 512 MB
- **磁盘**: 1 GB 可用空间
- **Python**: 3.7+
- **网络**: 可访问 Deribit Test API 和加权情绪 API

### 依赖项

```bash
pip install aiohttp
```

## 快速开始

### 1. 配置环境变量

创建或编辑 `.env` 文件：

```bash
cd BTCOptionsTrading/backend

# 加权情绪交易专用凭证（独立账户）
WEIGHTED_SENTIMENT_DERIBIT_API_KEY=your_api_key_here
WEIGHTED_SENTIMENT_DERIBIT_API_SECRET=your_api_secret_here
```

**重要**：使用独立的 Deribit Test 账户，与现有的 sentiment_trading_service 分离。

### 2. 创建必要的目录

```bash
mkdir -p data logs
```

### 3. 测试运行

手动运行一次，确保一切正常：

```bash
python weighted_sentiment_cron.py
```

查看输出，确认：
- ✓ 成功连接到新闻 API
- ✓ 数据库初始化成功
- ✓ 新闻识别和筛选正常

### 4. 设置 Cron Job

运行设置脚本：

```bash
bash setup_weighted_sentiment_cron.sh
```

这将自动：
- 创建日志目录
- 添加执行权限
- 配置 cron 任务（每小时整点执行）

### 5. 启动状态查询 API（可选）

如果需要通过 HTTP 查询系统状态：

```bash
python weighted_sentiment_status_api.py
```

API 将在端口 5003 上运行。

## 使用指南

### 查看日志

**Cron 执行日志**：
```bash
tail -f logs/weighted_sentiment_cron.log
```

**系统详细日志**：
```bash
tail -f logs/weighted_sentiment.log
```

**交易记录日志**：
```bash
tail -f logs/weighted_sentiment_trades.log
```

### 查询系统状态

如果状态 API 正在运行：

**浏览器访问**：
```
http://your-server:5003/
```

**命令行查询**：
```bash
# 系统状态
curl http://localhost:5003/api/status

# 历史统计
curl http://localhost:5003/api/history

# 最近交易
curl http://localhost:5003/api/trades
```

### 管理 Cron Job

**查看当前 cron 任务**：
```bash
crontab -l
```

**删除 cron 任务**：
```bash
crontab -l | grep -v 'weighted_sentiment_cron.py' | crontab -
```

**修改执行频率**：

编辑 cron 任务：
```bash
crontab -e
```

示例配置：
```bash
# 每小时整点执行
0 * * * * cd /path/to/backend && python3 weighted_sentiment_cron.py >> logs/weighted_sentiment_cron.log 2>&1

# 每30分钟执行
*/30 * * * * cd /path/to/backend && python3 weighted_sentiment_cron.py >> logs/weighted_sentiment_cron.log 2>&1

# 每天上午9点执行
0 9 * * * cd /path/to/backend && python3 weighted_sentiment_cron.py >> logs/weighted_sentiment_cron.log 2>&1
```

## 文件结构

```
BTCOptionsTrading/backend/
├── weighted_sentiment_cron.py              # Cron job 主脚本
├── weighted_sentiment_status_api.py        # 状态查询 API
├── weighted_sentiment_api_client.py        # 新闻 API 客户端
├── weighted_sentiment_news_tracker.py      # 新闻跟踪器
├── weighted_sentiment_models.py            # 数据模型
├── setup_weighted_sentiment_cron.sh        # Cron 设置脚本
├── data/
│   └── weighted_news_history.db           # 新闻历史数据库
└── logs/
    ├── weighted_sentiment_cron.log        # Cron 执行日志
    ├── weighted_sentiment.log             # 系统详细日志
    └── weighted_sentiment_trades.log      # 交易记录日志
```

## 监控和维护

### 日常监控

1. **检查 cron 执行**：
   ```bash
   tail -20 logs/weighted_sentiment_cron.log
   ```

2. **查看最近交易**：
   ```bash
   tail -50 logs/weighted_sentiment_trades.log
   ```

3. **检查错误**：
   ```bash
   grep -i error logs/weighted_sentiment.log | tail -20
   ```

### 数据库维护

**查看新闻历史数量**：
```bash
sqlite3 data/weighted_news_history.db "SELECT COUNT(*) FROM news_history;"
```

**查看最近处理的新闻**：
```bash
sqlite3 data/weighted_news_history.db "SELECT * FROM news_history ORDER BY processed_at DESC LIMIT 10;"
```

**清理旧数据**（可选）：
```bash
# 删除30天前的记录
sqlite3 data/weighted_news_history.db "DELETE FROM news_history WHERE processed_at < datetime('now', '-30 days');"
```

### 日志轮转

为避免日志文件过大，建议配置日志轮转：

创建 `/etc/logrotate.d/weighted-sentiment`：
```
/path/to/BTCOptionsTrading/backend/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

## 故障排查

### 问题：Cron job 没有执行

**检查步骤**：
1. 确认 cron 任务已添加：`crontab -l`
2. 检查 cron 服务状态：`systemctl status cron` 或 `service cron status`
3. 查看系统日志：`grep CRON /var/log/syslog`

### 问题：无法连接到新闻 API

**检查步骤**：
1. 测试网络连接：`curl http://43.106.51.106:5002/api/weighted-sentiment/news`
2. 检查防火墙设置
3. 查看详细错误日志

### 问题：Deribit 凭证错误

**检查步骤**：
1. 确认环境变量已设置：`echo $WEIGHTED_SENTIMENT_DERIBIT_API_KEY`
2. 验证凭证有效性
3. 确保使用的是 Test 环境凭证

### 问题：数据库锁定

**解决方法**：
```bash
# 检查是否有进程正在使用数据库
lsof data/weighted_news_history.db

# 如果需要，强制关闭
kill -9 <PID>
```

## 性能优化

### 资源使用

- **内存**：通常 < 50 MB
- **CPU**：执行时短暂峰值，平均 < 5%
- **磁盘 I/O**：最小化，仅在执行时读写

### 优化建议

1. **调整执行频率**：如果资源紧张，可以降低执行频率（如每2小时）
2. **限制日志大小**：配置日志轮转
3. **定期清理数据库**：删除旧的历史记录

## 安全注意事项

1. **保护凭证**：
   - 不要将 `.env` 文件提交到版本控制
   - 设置适当的文件权限：`chmod 600 .env`

2. **限制 API 访问**：
   - 如果运行状态 API，考虑使用防火墙限制访问
   - 仅在必要时运行状态 API

3. **监控异常活动**：
   - 定期检查日志中的错误和警告
   - 设置告警通知（如有需要）

## 升级和扩展

### 添加实际交易功能

当前实现是简化版本，不执行实际交易。要添加实际交易功能：

1. 实现完整的 `StraddleExecutor` 类
2. 集成 Deribit API 调用
3. 添加风险管理逻辑
4. 实现交易数据库存储

### 添加通知功能

可以添加邮件或消息通知：

```python
# 在 weighted_sentiment_cron.py 中添加
import smtplib
from email.mime.text import MIMEText

def send_notification(subject, message):
    # 实现邮件发送逻辑
    pass
```

## 支持和反馈

如有问题或建议，请查看：
- 系统日志：`logs/weighted_sentiment.log`
- 项目文档：`BTCOptionsTrading/DOCUMENTATION_INDEX.md`

## 附录

### Cron 时间格式说明

```
* * * * * command
│ │ │ │ │
│ │ │ │ └─ 星期几 (0-7, 0和7都表示周日)
│ │ │ └─── 月份 (1-12)
│ │ └───── 日期 (1-31)
│ └─────── 小时 (0-23)
└───────── 分钟 (0-59)
```

示例：
- `0 * * * *` - 每小时整点
- `*/30 * * * *` - 每30分钟
- `0 9,17 * * *` - 每天9点和17点
- `0 9 * * 1-5` - 工作日每天9点

### 环境变量完整列表

```bash
# 必需
WEIGHTED_SENTIMENT_DERIBIT_API_KEY=your_key
WEIGHTED_SENTIMENT_DERIBIT_API_SECRET=your_secret

# 可选（使用默认值）
WEIGHTED_SENTIMENT_API_URL=http://43.106.51.106:5002/api/weighted-sentiment/news
WEIGHTED_SENTIMENT_DB_PATH=data/weighted_news_history.db
```
