# 每日期权数据采集指南

## 概述

`daily_data_collector.py` 是一个自动化脚本，用于每天从Deribit API获取期权数据并保存到本地。

## 功能特点

- ✅ 从Deribit API实时获取期权数据
- ✅ 支持BTC和ETH期权
- ✅ 自动保存为CSV文件
- ✅ 自动保存到SQLite数据库
- ✅ 详细的日志记录
- ✅ 支持cron job自动运行
- ✅ 错误处理和重试机制

## 快速开始

### 1. 手动运行

```bash
# 基本用法（BTC期权，保存到CSV和数据库）
python3 daily_data_collector.py

# 指定货币
python3 daily_data_collector.py --currency BTC
python3 daily_data_collector.py --currency ETH

# 只保存到CSV
python3 daily_data_collector.py --no-db

# 只保存到数据库
python3 daily_data_collector.py --no-csv

# 自定义输出目录
python3 daily_data_collector.py --csv-dir /path/to/csv --db-path /path/to/db.sqlite
```

### 2. 设置自动采集（Cron Job）

```bash
# 运行设置脚本
chmod +x setup_daily_collection.sh
./setup_daily_collection.sh
```

这将设置一个cron job，每天午夜（00:00）自动运行数据采集。

### 3. 查看日志

```bash
# 查看最新日志
tail -f logs/daily_collection.log

# 查看完整日志
cat logs/daily_collection.log
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--currency` | 标的资产（BTC或ETH） | BTC |
| `--csv` | 保存到CSV文件 | True |
| `--no-csv` | 不保存到CSV文件 | - |
| `--db` | 保存到数据库 | True |
| `--no-db` | 不保存到数据库 | - |
| `--csv-dir` | CSV输出目录 | data/daily_snapshots |
| `--db-path` | 数据库路径 | data/btc_options.db |

## 输出格式

### CSV文件

文件名格式：`YYYYMMDD_HHMMSS_BTC_options.csv`

示例：`20240220_000000_BTC_options.csv`

CSV字段：
- `timestamp` - 采集时间
- `instrument_name` - 合约名称
- `underlying_symbol` - 标的资产
- `strike_price` - 执行价
- `expiry_date` - 到期日
- `option_type` - 期权类型（call/put）
- `mark_price` - 标记价格
- `bid_price` - 买价
- `ask_price` - 卖价
- `last_price` - 最新价
- `volume` - 成交量
- `open_interest` - 持仓量
- `implied_volatility` - 隐含波动率
- `delta` - Delta
- `gamma` - Gamma
- `theta` - Theta
- `vega` - Vega
- `rho` - Rho

### 数据库

数据保存在SQLite数据库中，可以通过历史数据API或CLI工具访问。

## Cron Job配置

### 默认配置

```cron
# 每天午夜运行
0 0 * * * cd /path/to/backend && python3 daily_data_collector.py --currency BTC >> logs/daily_collection.log 2>&1
```

### 自定义时间

编辑crontab：
```bash
crontab -e
```

常用时间表达式：
- `0 0 * * *` - 每天午夜
- `0 */6 * * *` - 每6小时
- `0 9,15,21 * * *` - 每天9点、15点、21点
- `*/30 * * * *` - 每30分钟

### 查看当前cron jobs

```bash
crontab -l
```

### 删除cron job

```bash
crontab -e
# 删除包含 'daily_data_collector.py' 的行
```

## 数据管理

### 查看采集的数据

```bash
# 使用CLI工具查看统计
python3 historical_cli.py stats

# 查看可用合约
python3 historical_cli.py stats --instruments

# 查看可用日期
python3 historical_cli.py stats --dates
```

### 导出数据

```bash
# 导出为CSV
python3 historical_cli.py export -s 2024-01-01 -e 2024-12-31 -f csv

# 导出为JSON
python3 historical_cli.py export -s 2024-01-01 -e 2024-12-31 -f json
```

### 清理旧数据

```bash
# 清理缓存
python3 historical_cli.py clear --cache

# 清理所有数据（需要确认）
python3 historical_cli.py clear --all
```

## 监控和维护

### 检查采集状态

```bash
# 查看最近的日志
tail -n 100 logs/daily_collection.log

# 搜索错误
grep -i error logs/daily_collection.log

# 统计成功次数
grep -c "Collection Summary" logs/daily_collection.log
```

### 磁盘空间管理

CSV文件会随时间累积，建议定期清理：

```bash
# 查看CSV目录大小
du -sh data/daily_snapshots

# 删除30天前的CSV文件
find data/daily_snapshots -name "*.csv" -mtime +30 -delete

# 压缩旧文件
find data/daily_snapshots -name "*.csv" -mtime +7 -exec gzip {} \;
```

### 数据库维护

```bash
# 查看数据库大小
ls -lh data/btc_options.db

# 优化数据库
sqlite3 data/btc_options.db "VACUUM;"

# 备份数据库
cp data/btc_options.db data/backups/btc_options_$(date +%Y%m%d).db
```

## 故障排除

### 问题：采集失败

**可能原因**：
1. 网络连接问题
2. Deribit API限流
3. 权限问题

**解决方案**：
```bash
# 检查网络连接
curl -I https://test.deribit.com

# 手动运行查看详细错误
python3 daily_data_collector.py --currency BTC

# 检查日志
tail -f logs/daily_collection.log
```

### 问题：Cron job不运行

**可能原因**：
1. Cron服务未启动
2. 路径配置错误
3. 权限问题

**解决方案**：
```bash
# 检查cron服务
sudo service cron status  # Linux
# 或
launchctl list | grep cron  # macOS

# 检查cron日志
grep CRON /var/log/syslog  # Linux
# 或
log show --predicate 'process == "cron"' --last 1h  # macOS

# 测试脚本路径
which python3
ls -l /path/to/daily_data_collector.py
```

### 问题：数据库锁定

**可能原因**：
多个进程同时访问数据库

**解决方案**：
```bash
# 检查是否有其他进程在使用数据库
lsof data/btc_options.db

# 等待其他进程完成或终止它们
kill -9 <PID>
```

## 最佳实践

1. **定期备份**
   - 每周备份数据库
   - 保留至少3个月的备份

2. **监控磁盘空间**
   - 设置磁盘空间告警
   - 定期清理旧的CSV文件

3. **日志轮转**
   - 使用logrotate管理日志文件
   - 保留最近30天的日志

4. **数据验证**
   - 定期运行数据质量检查
   - 监控采集成功率

5. **错误通知**
   - 配置邮件通知
   - 集成到监控系统

## 示例：完整的自动化流程

```bash
#!/bin/bash
# daily_collection_with_cleanup.sh

# 1. 运行数据采集
python3 daily_data_collector.py --currency BTC

# 2. 检查采集结果
if [ $? -eq 0 ]; then
    echo "Data collection successful"
    
    # 3. 清理30天前的CSV文件
    find data/daily_snapshots -name "*.csv" -mtime +30 -delete
    
    # 4. 备份数据库（每周日）
    if [ $(date +%u) -eq 7 ]; then
        cp data/btc_options.db data/backups/btc_options_$(date +%Y%m%d).db
    fi
    
    # 5. 发送成功通知（可选）
    # echo "Data collection completed" | mail -s "Daily Collection Success" admin@example.com
else
    echo "Data collection failed"
    # 发送失败通知
    # echo "Check logs at logs/daily_collection.log" | mail -s "Daily Collection Failed" admin@example.com
fi
```

## 相关文档

- [历史数据CLI指南](HISTORICAL_CLI_GUIDE.md)
- [历史数据API文档](HISTORICAL_DATA_API.md)
- [故障排除指南](HISTORICAL_DATA_TROUBLESHOOTING.md)

## 支持

如有问题，请查看：
1. 日志文件：`logs/daily_collection.log`
2. 系统日志：`/var/log/syslog` 或 `/var/log/cron`
3. 项目文档：`HISTORICAL_DATA_GUIDE.md`
