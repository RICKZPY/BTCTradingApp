# 服务器部署检查清单

## 部署前检查

- [ ] 服务器已准备好（Linux系统）
- [ ] 有SSH访问权限
- [ ] 服务器已安装Python 3.8+
- [ ] 已获取Deribit API密钥（测试网）
- [ ] 已确认服务器时区设置

## 自动部署步骤

### 使用deploy_to_server.sh脚本

```bash
cd BTCOptionsTrading/backend
./deploy_to_server.sh user@server_ip
```

脚本会引导你完成：

- [ ] SSH连接测试
- [ ] 服务器环境检查
- [ ] 文件上传
- [ ] 配置API密钥
- [ ] 安装Python依赖
- [ ] 测试运行
- [ ] 安装Cron Job
- [ ] 配置时区

## 部署后验证

### 1. 验证Cron Job安装

```bash
ssh user@server_ip
cd ~/BTCOptionsTrading/backend
./setup_cron.sh status
```

应该看到：
- [ ] ✓ Cron job已安装
- [ ] ✓ 显示下次执行时间
- [ ] ✓ 日志目录存在

### 2. 手动测试执行

```bash
cd ~/BTCOptionsTrading/backend
source venv/bin/activate
python3 sentiment_trading_service.py
```

检查输出：
- [ ] ✓ 服务启动成功
- [ ] ✓ Deribit认证成功
- [ ] ✓ 获取情绪数据
- [ ] ✓ 执行交易逻辑
- [ ] ✓ 服务自动退出
- [ ] ✓ 连接已关闭

### 3. 检查文件权限

```bash
ls -la ~/BTCOptionsTrading/backend/.env
```

应该显示：
- [ ] `-rw-------` (600权限)

### 4. 验证时区设置

```bash
timedatectl
```

确认：
- [ ] 时区正确（例如：Asia/Shanghai）
- [ ] 系统时间正确

### 5. 查看日志文件

```bash
ls -la ~/BTCOptionsTrading/backend/logs/
```

应该存在：
- [ ] `sentiment_trading.log`
- [ ] `sentiment_trading_cron.log`

## 监控设置

### 1. 设置日志查看别名（可选）

```bash
echo "alias trading-logs='tail -f ~/BTCOptionsTrading/backend/logs/sentiment_trading_cron.log'" >> ~/.bashrc
source ~/.bashrc
```

现在可以使用：
```bash
trading-logs
```

### 2. 创建状态检查脚本（可选）

```bash
cat > ~/check_trading.sh << 'EOF'
#!/bin/bash
cd ~/BTCOptionsTrading/backend
echo "=== Cron Job Status ==="
./setup_cron.sh status
echo ""
echo "=== Recent Logs (last 20 lines) ==="
tail -20 logs/sentiment_trading_cron.log
echo ""
echo "=== Trading History Count ==="
if [ -f data/sentiment_trading_history.json ]; then
    python3 -c "import json; print(f'{len(json.load(open(\"data/sentiment_trading_history.json\")))} trades recorded')"
else
    echo "No trading history yet"
fi
EOF

chmod +x ~/check_trading.sh
```

使用：
```bash
~/check_trading.sh
```

### 3. 设置备份（可选）

```bash
cat > ~/backup_trading.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=~/trading_backups
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf $BACKUP_DIR/trading_$DATE.tar.gz \
    ~/BTCOptionsTrading/backend/data/ \
    ~/BTCOptionsTrading/backend/.env
find $BACKUP_DIR -name "trading_*.tar.gz" -mtime +30 -delete
echo "Backup created: $BACKUP_DIR/trading_$DATE.tar.gz"
EOF

chmod +x ~/backup_trading.sh
```

添加到crontab（每天6点备份）：
```bash
crontab -e
```

添加：
```
0 6 * * * ~/backup_trading.sh
```

## 第一次执行前

### 等待第一次自动执行

Cron job会在第二天早上5点首次执行。

或者，手动触发一次测试：
```bash
cd ~/BTCOptionsTrading/backend
source venv/bin/activate
python3 sentiment_trading_service.py
```

### 第一次执行后检查

- [ ] 查看日志：`tail -50 logs/sentiment_trading_cron.log`
- [ ] 检查交易历史：`cat data/sentiment_trading_history.json | python3 -m json.tool`
- [ ] 验证持仓数据：`cat data/current_positions.json | python3 -m json.tool`

## 常见问题快速检查

### Cron Job未执行？

```bash
# 检查cron服务
sudo systemctl status cron

# 查看crontab
crontab -l | grep sentiment

# 查看系统日志
sudo tail -f /var/log/syslog | grep CRON
```

### Python错误？

```bash
# 检查虚拟环境
cd ~/BTCOptionsTrading/backend
source venv/bin/activate
python3 --version
pip list | grep -E "aiohttp|websockets|pydantic"

# 重新安装依赖
pip install -r requirements.txt --upgrade
```

### 网络问题？

```bash
# 测试Deribit连接
ping test.deribit.com

# 测试情绪API
curl http://43.106.51.106:5001/api/sentiment

# 检查防火墙
sudo ufw status
```

### API认证失败？

```bash
# 检查.env文件
cat ~/BTCOptionsTrading/backend/.env

# 验证API密钥格式
# 应该是类似: DERIBIT_TESTNET_API_KEY=xxxxxxxx
```

## 维护计划

### 每周检查

- [ ] 运行`./setup_cron.sh status`
- [ ] 查看最近的日志
- [ ] 检查交易历史数量

### 每月检查

- [ ] 清理旧日志（如果太大）
- [ ] 备份交易数据
- [ ] 更新代码（如果有新版本）

### 更新代码

```bash
cd ~/BTCOptionsTrading
git pull origin main
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

## 紧急情况

### 立即停止Cron Job

```bash
cd ~/BTCOptionsTrading/backend
./setup_cron.sh uninstall
```

### 重新启动

```bash
./setup_cron.sh install
```

## 完成！

- [ ] 所有检查项都已完成
- [ ] Cron Job正常运行
- [ ] 监控已设置
- [ ] 备份已配置（可选）

系统现在会在每天早上5点自动执行交易！

## 快速参考命令

```bash
# 查看状态
cd ~/BTCOptionsTrading/backend && ./setup_cron.sh status

# 查看日志
tail -f ~/BTCOptionsTrading/backend/logs/sentiment_trading_cron.log

# 手动测试
cd ~/BTCOptionsTrading/backend && source venv/bin/activate && python3 sentiment_trading_service.py

# 查看交易历史
cat ~/BTCOptionsTrading/backend/data/sentiment_trading_history.json | python3 -m json.tool | less

# 重启cron服务
sudo systemctl restart cron
```

祝交易顺利！🚀
