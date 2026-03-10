# 情绪交易系统 - Cron Job监控指南

## 概述

本指南介绍如何监控和管理基于cron job的情绪交易系统。

## 资源使用对比

### 优化前（持续运行模式）
- CPU使用：持续占用约0.5%
- 内存使用：持续占用约75MB
- 运行时间：24小时/天
- 资源效率：低（1440次时间检查，只执行1次交易）

### 优化后（Cron Job模式）
- CPU使用：仅在执行时占用（每天约2-5分钟）
- 内存使用：仅在执行时占用（约75MB，执行完成后释放）
- 运行时间：约2-5分钟/天
- 资源效率：高（按需执行，无空转）

### 资源节省
- CPU时间节省：约99.8%
- 内存占用时间节省：约99.8%
- 非常适合2核vCPU等资源受限的服务器

## 验证Cron Job安装

### 检查Cron Job状态

```bash
cd BTCOptionsTrading/backend
./setup_cron.sh status
```

输出示例：
```
ℹ Cron Job状态:

✓ 找到Python解释器: python3
✓ 找到脚本文件: /path/to/sentiment_trading_service.py
✓ 找到.env配置文件
✓ 日志目录: /path/to/logs
✓ Cron job已安装

当前配置:
# Sentiment Trading Service - Daily execution at 5:00 AM
0 5 * * * cd /path/to/backend && python3 sentiment_trading_service.py >> /path/to/logs/sentiment_trading_cron.log 2>&1

ℹ 日志文件: /path/to/logs/sentiment_trading_cron.log (1.2K, 45 行)

ℹ 下次执行时间: 明天早上 5:00 AM
```

### 手动查看Crontab

```bash
crontab -l | grep sentiment
```

应该看到类似的输出：
```
# Sentiment Trading Service - Daily execution at 5:00 AM
0 5 * * * cd /path/to/backend && python3 sentiment_trading_service.py >> /path/to/logs/sentiment_trading_cron.log 2>&1
```

## 监控执行日志

### 实时监控Cron执行日志

```bash
tail -f logs/sentiment_trading_cron.log
```

### 查看详细交易日志

```bash
tail -f logs/sentiment_trading.log
```

### 查看最近的执行记录

```bash
# 查看最后20行
tail -20 logs/sentiment_trading_cron.log

# 查看今天的日志
grep "$(date +%Y-%m-%d)" logs/sentiment_trading_cron.log
```

## 验证执行成功

### 检查日志中的关键信息

成功执行的日志应包含：

1. 服务启动：
```
情绪驱动交易服务启动（单次执行模式）
配置: 测试网用于交易下单
```

2. 认证成功：
```
Deribit测试网认证成功
```

3. 情绪分析：
```
成功获取情绪数据
情绪分析: 负面=10, 正面=5
选择策略: bearish_news
```

4. 交易执行：
```
开始执行策略: bearish_news
策略执行完成
```

5. 服务完成：
```
情绪驱动交易服务执行完成
连接已关闭，资源已释放
```

### 检查交易历史文件

```bash
# 查看最新的交易记录
cat data/sentiment_trading_history.json | python3 -m json.tool | tail -30

# 统计交易次数
cat data/sentiment_trading_history.json | python3 -c "import json, sys; print(len(json.load(sys.stdin)))"
```

### 检查持仓文件

```bash
cat data/current_positions.json | python3 -m json.tool
```

## 手动触发执行（测试）

### 立即执行一次

```bash
cd BTCOptionsTrading/backend
python3 sentiment_trading_service.py
```

观察输出，确保：
1. 服务启动成功
2. 认证成功
3. 获取情绪数据
4. 执行交易逻辑
5. 服务自动退出

### 验证进程退出

执行完成后，验证没有残留进程：

```bash
ps aux | grep sentiment_trading_service
```

应该只看到grep进程本身，没有Python进程。

## 监控系统资源

### 在执行期间监控资源

```bash
# 在另一个终端窗口运行
watch -n 1 'ps aux | grep sentiment_trading_service | grep -v grep'
```

你会看到：
- 执行时：进程出现，占用CPU和内存
- 执行完成后：进程消失，资源释放

### 监控服务器整体资源

```bash
# 查看CPU和内存使用
top

# 或使用htop（如果已安装）
htop
```

## 故障排查

### Cron Job未执行

1. 检查cron服务是否运行：
```bash
# Linux
sudo systemctl status cron

# macOS
sudo launchctl list | grep cron
```

2. 检查crontab语法：
```bash
crontab -l
```

3. 检查脚本权限：
```bash
ls -l sentiment_trading_service.py
# 应该有执行权限
```

4. 检查Python路径：
```bash
which python3
# 确保crontab中的Python路径正确
```

### 执行失败

1. 查看错误日志：
```bash
tail -50 logs/sentiment_trading_cron.log
```

2. 手动执行测试：
```bash
python3 sentiment_trading_service.py
```

3. 检查.env配置：
```bash
cat .env | grep DERIBIT
# 确保API密钥配置正确
```

4. 检查网络连接：
```bash
ping test.deribit.com
```

### 日志文件过大

定期清理旧日志：

```bash
# 备份当前日志
cp logs/sentiment_trading_cron.log logs/sentiment_trading_cron.log.backup

# 清空日志文件
> logs/sentiment_trading_cron.log

# 或使用logrotate（推荐）
```

## 最佳实践

### 1. 定期检查

建议每周检查一次：
```bash
./setup_cron.sh status
```

### 2. 监控交易历史

定期查看交易记录，确保策略正常执行：
```bash
cat data/sentiment_trading_history.json | python3 -m json.tool | less
```

### 3. 备份数据

定期备份交易历史和持仓数据：
```bash
cp data/sentiment_trading_history.json backups/history_$(date +%Y%m%d).json
cp data/current_positions.json backups/positions_$(date +%Y%m%d).json
```

### 4. 日志轮转

配置logrotate自动管理日志文件大小。

### 5. 告警设置

可以添加监控脚本，在执行失败时发送通知：

```bash
# 示例：检查最近的执行是否成功
if ! grep -q "执行完成" logs/sentiment_trading_cron.log | tail -1; then
    echo "Sentiment trading execution failed!" | mail -s "Alert" your@email.com
fi
```

## 性能指标

### 正常执行时间

- 启动和认证：5-10秒
- 获取情绪数据：2-5秒
- 策略构建：5-10秒
- 订单执行：10-30秒
- 总计：约30-60秒

如果执行时间超过5分钟，可能存在问题。

### 资源使用

- 峰值CPU：10-20%（短暂）
- 峰值内存：75-100MB
- 网络流量：< 1MB

## 修改执行时间

如需修改执行时间，编辑cron表达式：

```bash
# 卸载当前cron job
./setup_cron.sh uninstall

# 编辑setup_cron.sh，修改cron表达式
# 例如改为每天早上8点：
# 0 8 * * * ...

# 重新安装
./setup_cron.sh install
```

Cron表达式格式：
```
分 时 日 月 周
0  5  *  *  *   # 每天5:00 AM
0  8  *  *  *   # 每天8:00 AM
0  */6 *  *  *  # 每6小时
```

## 总结

Cron job模式的优势：
- ✅ 资源效率高（节省99.8%的CPU和内存占用时间）
- ✅ 适合资源受限的服务器
- ✅ 自动化调度，无需手动管理
- ✅ 所有交易逻辑保持不变
- ✅ 易于监控和故障排查

通过本指南的监控方法，你可以确保系统稳定运行并及时发现问题。
