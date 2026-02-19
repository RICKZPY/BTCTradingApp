# 数据采集器部署指南

## 🚀 首次部署？请先看这里！

如果这是你第一次在服务器上设置项目，请先运行一键设置脚本：

```bash
cd /root/BTCTradingApp/BTCOptionsTrading
chmod +x deploy/setup_server_first_time.sh
./deploy/setup_server_first_time.sh
```

这个脚本会自动安装所有依赖、创建目录、测试采集器。

**详细说明**: 参见 `deploy/SERVER_FIRST_TIME_SETUP.md`

---

## 快速部署到阿里云服务器

服务器信息：
- IP: 47.86.62.200
- 用户: root
- 项目目录: /root/BTCTradingApp/BTCOptionsTrading

## 方法1: 使用部署脚本（推荐）

```bash
# 在本地运行
cd BTCOptionsTrading/deploy
./quick_deploy_collector.sh
```

脚本会自动：
1. 测试SSH连接
2. 创建远程目录
3. 上传所有必需文件
4. 设置执行权限

## 方法2: 手动部署

### 步骤1: SSH登录到服务器

```bash
ssh root@47.86.62.200
```

### 步骤2: 拉取最新代码

如果服务器上已有项目：
```bash
cd /root/BTCOptionsTrading
git pull origin main
```

如果是首次部署：
```bash
cd /root
git clone https://github.com/RICKZPY/BTCTradingApp.git BTCOptionsTrading
cd BTCOptionsTrading
```

### 步骤3: 安装依赖

```bash
cd backend
pip3 install -r requirements.txt
```

### 步骤4: 创建必要的目录

```bash
mkdir -p logs
mkdir -p data/daily_snapshots
mkdir -p data/downloads
```

### 步骤5: 测试采集脚本

```bash
# 测试运行（不保存数据）
python3 daily_data_collector.py --no-csv --no-db

# 完整测试（保存数据）
python3 daily_data_collector.py --currency BTC
```

### 步骤6: 设置自动采集

```bash
# 运行配置脚本
./setup_daily_collection.sh

# 或手动添加cron job
crontab -e
# 添加以下行：
# 0 0 * * * cd /root/BTCOptionsTrading/backend && python3 daily_data_collector.py --currency BTC >> logs/daily_collection.log 2>&1
```

### 步骤7: 验证cron job

```bash
# 查看已安装的cron jobs
crontab -l

# 查看cron日志
tail -f /var/log/cron
```

## 方法3: 使用SCP直接上传

```bash
# 从本地上传文件
cd BTCOptionsTrading

# 上传采集脚本
scp backend/daily_data_collector.py root@47.86.62.200:/root/BTCOptionsTrading/backend/

# 上传配置脚本
scp backend/setup_daily_collection.sh root@47.86.62.200:/root/BTCOptionsTrading/backend/

# 上传文档
scp backend/DAILY_COLLECTION_GUIDE.md root@47.86.62.200:/root/BTCOptionsTrading/backend/

# 设置权限
ssh root@47.86.62.200 "chmod +x /root/BTCOptionsTrading/backend/*.py /root/BTCOptionsTrading/backend/*.sh"
```

## 启动和监控

### 立即运行一次采集

```bash
ssh root@47.86.62.200
cd /root/BTCOptionsTrading/backend
python3 daily_data_collector.py --currency BTC
```

### 查看实时日志

```bash
ssh root@47.86.62.200
tail -f /root/BTCOptionsTrading/backend/logs/daily_collection.log
```

### 检查采集状态

```bash
ssh root@47.86.62.200
cd /root/BTCOptionsTrading/backend

# 查看最近的采集记录
ls -lht data/daily_snapshots/ | head -10

# 查看数据库大小
ls -lh data/btc_options.db

# 统计采集次数
grep -c "Collection Summary" logs/daily_collection.log
```

## 常用命令

### 查看服务器状态

```bash
# 磁盘空间
df -h

# 内存使用
free -h

# CPU使用
top

# 进程列表
ps aux | grep python
```

### 管理cron job

```bash
# 查看cron jobs
crontab -l

# 编辑cron jobs
crontab -e

# 删除所有cron jobs
crontab -r

# 查看cron日志
tail -f /var/log/cron
```

### 数据管理

```bash
# 查看采集的数据
python3 historical_cli.py stats

# 导出数据
python3 historical_cli.py export -s 2024-01-01 -e 2024-12-31 -f csv

# 清理旧数据
find data/daily_snapshots -name "*.csv" -mtime +30 -delete
```

## 故障排除

### 问题1: 采集失败

```bash
# 查看详细错误
python3 daily_data_collector.py --currency BTC

# 检查网络连接
curl -I https://test.deribit.com

# 检查Python依赖
pip3 list | grep -E "httpx|requests|pandas"
```

### 问题2: Cron不运行

```bash
# 检查cron服务
systemctl status cron

# 启动cron服务
systemctl start cron

# 查看cron日志
grep CRON /var/log/syslog
```

### 问题3: 权限问题

```bash
# 检查文件权限
ls -l daily_data_collector.py

# 修复权限
chmod +x daily_data_collector.py
chmod +x setup_daily_collection.sh

# 检查目录权限
ls -ld data logs
```

### 问题4: 磁盘空间不足

```bash
# 检查磁盘使用
df -h

# 查看大文件
du -sh data/*

# 清理旧文件
find data/daily_snapshots -name "*.csv" -mtime +30 -delete

# 压缩旧文件
find data/daily_snapshots -name "*.csv" -mtime +7 -exec gzip {} \;
```

## 监控和告警

### 设置邮件通知

编辑cron job添加邮件通知：
```bash
crontab -e

# 添加MAILTO变量
MAILTO=your-email@example.com

# cron job会自动发送输出到邮箱
0 0 * * * cd /root/BTCOptionsTrading/backend && python3 daily_data_collector.py --currency BTC
```

### 使用监控脚本

```bash
# 创建监控脚本
cat > /root/BTCOptionsTrading/backend/check_collection.sh << 'EOF'
#!/bin/bash
LOG_FILE="/root/BTCOptionsTrading/backend/logs/daily_collection.log"
LAST_SUCCESS=$(grep -c "Collection Summary" $LOG_FILE)

if [ $LAST_SUCCESS -eq 0 ]; then
    echo "Warning: No successful collections found"
    # 发送告警
fi
EOF

chmod +x /root/BTCOptionsTrading/backend/check_collection.sh

# 添加到cron（每小时检查一次）
# 0 * * * * /root/BTCOptionsTrading/backend/check_collection.sh
```

## 性能优化

### 1. 使用数据库索引

```bash
sqlite3 data/btc_options.db << EOF
CREATE INDEX IF NOT EXISTS idx_timestamp ON historical_options(timestamp);
CREATE INDEX IF NOT EXISTS idx_instrument ON historical_options(instrument_name);
CREATE INDEX IF NOT EXISTS idx_expiry ON historical_options(expiry_date);
EOF
```

### 2. 定期优化数据库

```bash
# 添加到cron（每周日凌晨3点）
# 0 3 * * 0 sqlite3 /root/BTCOptionsTrading/backend/data/btc_options.db "VACUUM;"
```

### 3. 日志轮转

创建 `/etc/logrotate.d/btc-collector`:
```
/root/BTCOptionsTrading/backend/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
```

## 安全建议

1. **限制文件权限**
   ```bash
   chmod 700 /root/BTCOptionsTrading/backend
   chmod 600 /root/BTCOptionsTrading/backend/.env
   ```

2. **使用环境变量**
   ```bash
   # 创建.env文件
   echo "DERIBIT_API_KEY=your_key" > .env
   echo "DERIBIT_API_SECRET=your_secret" >> .env
   chmod 600 .env
   ```

3. **定期备份**
   ```bash
   # 每天备份数据库
   # 0 2 * * * cp /root/BTCOptionsTrading/backend/data/btc_options.db /root/backups/btc_options_$(date +\%Y\%m\%d).db
   ```

## 相关文档

- [每日采集使用指南](../backend/DAILY_COLLECTION_GUIDE.md)
- [部署指南](DEPLOYMENT_GUIDE.md)
- [监控指南](../MONITORING_GUIDE.md)

## 支持

如有问题，请检查：
1. 日志文件：`logs/daily_collection.log`
2. 系统日志：`/var/log/syslog`
3. Cron日志：`/var/log/cron`
