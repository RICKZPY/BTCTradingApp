# 情绪交易系统 - 部署说明

## 快速开始

### 🚀 自动部署到服务器（最简单）

```bash
./deploy_to_server.sh user@your_server_ip
```

这个脚本会自动完成所有部署步骤。

### 📖 详细文档

- [快速开始指南](../docs/guides/SENTIMENT_TRADING_QUICKSTART.md) - 基本使用
- [服务器部署指南](../docs/guides/SERVER_DEPLOYMENT_GUIDE.md) - 完整部署步骤
- [Cron监控指南](../docs/guides/SENTIMENT_CRON_MONITORING.md) - 监控和故障排查

## 部署方式对比

| 方式 | 适用场景 | 难度 | 资源占用 |
|------|---------|------|---------|
| **Cron Job（推荐）** | 生产环境、资源受限服务器 | 简单 | 极低（每天2-5分钟） |
| 持续运行服务 | 需要实时响应 | 中等 | 高（24小时运行） |

## Cron Job部署（推荐）

### 优势
- ✅ 资源占用极低（节省99.8%）
- ✅ 适合2核vCPU等资源受限环境
- ✅ 自动化调度，无需手动管理
- ✅ 所有交易逻辑完全不变

### 快速部署

#### 方法1：使用自动化脚本（推荐）

```bash
# 在本地机器上
cd BTCOptionsTrading/backend
./deploy_to_server.sh user@server_ip
```

#### 方法2：手动部署

```bash
# 1. 上传代码到服务器
rsync -avz BTCOptionsTrading/ user@server_ip:~/BTCOptionsTrading/

# 2. SSH到服务器
ssh user@server_ip

# 3. 安装依赖
cd ~/BTCOptionsTrading/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. 配置.env
nano .env
# 添加你的API密钥

# 5. 测试运行
python3 sentiment_trading_service.py

# 6. 安装cron job
./setup_cron.sh install
```

### 验证部署

```bash
# 查看状态
./setup_cron.sh status

# 查看日志
tail -f logs/sentiment_trading_cron.log

# 手动测试
python3 sentiment_trading_service.py
```

## 文件说明

### 核心文件
- `sentiment_trading_service.py` - 主服务脚本（单次执行模式）
- `setup_cron.sh` - Cron job管理脚本
- `deploy_to_server.sh` - 自动化部署脚本
- `.env` - 配置文件（需要手动创建）

### 配置文件
- `.env.example` - 配置文件示例
- `requirements.txt` - Python依赖

### 测试文件
- `test_bug_condition_exploration.py` - Bug条件探索测试
- `test_preservation_properties.py` - 保留性测试

### 数据目录
- `data/` - 交易历史和持仓数据
- `logs/` - 日志文件

## 配置说明

### 必需配置

在`.env`文件中配置：

```bash
# Deribit测试网（用于交易）
DERIBIT_TESTNET_API_KEY=your_testnet_key
DERIBIT_TESTNET_API_SECRET=your_testnet_secret
```

### 可选配置

```bash
# Deribit主网（用于获取真实市场数据）
DERIBIT_MAINNET_API_KEY=your_mainnet_key
DERIBIT_MAINNET_API_SECRET=your_mainnet_secret
```

## 执行时间

默认执行时间：每天早上5:00 AM（服务器时间）

修改执行时间：
1. 编辑`setup_cron.sh`
2. 修改cron表达式（默认：`0 5 * * *`）
3. 重新安装：`./setup_cron.sh uninstall && ./setup_cron.sh install`

Cron表达式示例：
```
0 5 * * *   # 每天5:00 AM
0 8 * * *   # 每天8:00 AM
0 */6 * * * # 每6小时
```

## 监控

### 查看日志

```bash
# Cron执行日志
tail -f logs/sentiment_trading_cron.log

# 详细交易日志
tail -f logs/sentiment_trading.log
```

### 查看交易历史

```bash
cat data/sentiment_trading_history.json | python3 -m json.tool
```

### 查看Cron状态

```bash
./setup_cron.sh status
```

## 故障排查

### Cron Job未执行

```bash
# 检查cron服务
sudo systemctl status cron

# 查看crontab
crontab -l

# 查看系统cron日志
sudo tail -f /var/log/syslog | grep CRON
```

### Python错误

```bash
# 重新安装依赖
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 手动测试
python3 sentiment_trading_service.py
```

### 网络问题

```bash
# 测试连接
ping test.deribit.com
curl http://43.106.51.106:5001/api/sentiment
```

## 更新代码

### 使用Git

```bash
cd ~/BTCOptionsTrading
git pull origin main
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### 使用rsync

```bash
# 在本地机器上
rsync -avz --exclude='.env' --exclude='data/' --exclude='logs/' \
  BTCOptionsTrading/ user@server_ip:~/BTCOptionsTrading/
```

## 卸载

```bash
# 卸载cron job
./setup_cron.sh uninstall

# 删除代码（可选）
cd ~
rm -rf BTCOptionsTrading
```

## 安全建议

1. **保护配置文件**
   ```bash
   chmod 600 .env
   ```

2. **使用SSH密钥**
   ```bash
   ssh-keygen -t rsa -b 4096
   ssh-copy-id user@server_ip
   ```

3. **定期备份**
   ```bash
   tar -czf backup.tar.gz data/ .env
   ```

4. **监控日志**
   定期检查日志文件，确保系统正常运行

## 资源使用

### Cron Job模式（当前）
- CPU：仅在执行时占用（每天2-5分钟）
- 内存：仅在执行时占用（约75-100MB）
- 磁盘：< 100MB（代码+日志+数据）

### 对比：持续运行模式
- CPU：24小时持续占用约0.5%
- 内存：24小时持续占用约75MB
- 资源节省：约99.8%

## 支持

遇到问题？

1. 查看[服务器部署指南](../docs/guides/SERVER_DEPLOYMENT_GUIDE.md)
2. 查看[Cron监控指南](../docs/guides/SENTIMENT_CRON_MONITORING.md)
3. 运行`./setup_cron.sh status`检查状态
4. 查看日志文件
5. 手动测试执行

## 总结

使用Cron Job模式部署情绪交易系统：
- ✅ 简单：一键自动化部署
- ✅ 高效：资源占用降低99.8%
- ✅ 可靠：自动化调度，无需手动管理
- ✅ 灵活：易于监控和故障排查

适合在资源受限的服务器（如2核vCPU）上运行！
