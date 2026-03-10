# 情绪交易系统 - 服务器部署指南

## 概述

本指南介绍如何在远程服务器上部署情绪交易系统的cron job。

## 前提条件

- 一台Linux服务器（Ubuntu/Debian/CentOS等）
- SSH访问权限
- Python 3.8+
- 至少1GB可用磁盘空间

## 部署步骤

### 1. 连接到服务器

```bash
ssh your_username@your_server_ip
```

### 2. 安装必要的系统依赖

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
```

#### CentOS/RHEL

```bash
sudo yum install -y python3 python3-pip git
```

### 3. 上传代码到服务器

#### 方法1：使用Git（推荐）

```bash
# 在服务器上
cd ~
git clone <your_repository_url> BTCTradingApp
cd BTCTradingApp/BTCOptionsTrading/backend
```

#### 方法2：使用SCP上传

```bash
# 在本地机器上
cd /path/to/BTCTradingApp
tar -czf btc_trading.tar.gz BTCOptionsTrading/
scp btc_trading.tar.gz your_username@your_server_ip:~/

# 在服务器上
cd ~
tar -xzf btc_trading.tar.gz
cd BTCOptionsTrading/backend
```

#### 方法3：使用rsync（推荐用于更新）

```bash
# 在本地机器上
rsync -avz --exclude='*.pyc' --exclude='__pycache__' \
  --exclude='.git' --exclude='data/' --exclude='logs/' \
  BTCOptionsTrading/ your_username@your_server_ip:~/BTCOptionsTrading/
```

### 4. 配置Python虚拟环境（推荐）

```bash
cd ~/BTCOptionsTrading/backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置文件
nano .env
```

在`.env`文件中配置：

```bash
# Deribit API配置
DERIBIT_TESTNET_API_KEY=your_testnet_api_key
DERIBIT_TESTNET_API_SECRET=your_testnet_api_secret

# 可选：主网配置（用于获取真实市场数据）
DERIBIT_MAINNET_API_KEY=your_mainnet_api_key
DERIBIT_MAINNET_API_SECRET=your_mainnet_api_secret
```

保存并退出（Ctrl+X, Y, Enter）

### 6. 测试运行

```bash
# 确保在虚拟环境中
source venv/bin/activate

# 手动运行一次测试
python3 sentiment_trading_service.py
```

检查输出，确保：
- ✅ 认证成功
- ✅ 获取情绪数据
- ✅ 执行交易逻辑
- ✅ 服务自动退出

### 7. 修改setup_cron.sh以使用虚拟环境

编辑`setup_cron.sh`，找到`generate_cron_entry()`函数，修改为：

```bash
nano setup_cron.sh
```

找到这一行：
```bash
echo "0 5 * * * cd ${SCRIPT_DIR} && ${PYTHON_CMD} ${SCRIPT_PATH} >> ${LOG_FILE} 2>&1"
```

修改为（使用虚拟环境）：
```bash
echo "0 5 * * * cd ${SCRIPT_DIR} && source venv/bin/activate && python3 ${SCRIPT_PATH} >> ${LOG_FILE} 2>&1"
```

或者，如果不使用虚拟环境，使用绝对路径：
```bash
echo "0 5 * * * cd ${SCRIPT_DIR} && /usr/bin/python3 ${SCRIPT_PATH} >> ${LOG_FILE} 2>&1"
```

### 8. 安装Cron Job

```bash
# 确保脚本可执行
chmod +x setup_cron.sh

# 安装cron job
./setup_cron.sh install
```

输出应该显示：
```
✓ Cron job安装成功！

配置详情:
  执行时间: 每天早上 5:00 AM
  脚本路径: /home/username/BTCOptionsTrading/backend/sentiment_trading_service.py
  日志文件: /home/username/BTCOptionsTrading/backend/logs/sentiment_trading_cron.log
```

### 9. 验证Cron Job安装

```bash
# 查看crontab
crontab -l

# 查看状态
./setup_cron.sh status
```

### 10. 配置时区（重要！）

确保服务器时区正确，因为cron job按服务器时间执行：

```bash
# 查看当前时区
timedatectl

# 设置时区（例如：上海时间）
sudo timedatectl set-timezone Asia/Shanghai

# 或者其他时区
# sudo timedatectl set-timezone America/New_York
# sudo timedatectl set-timezone Europe/London
```

## 监控和维护

### 查看日志

```bash
# 实时查看cron执行日志
tail -f ~/BTCOptionsTrading/backend/logs/sentiment_trading_cron.log

# 查看详细交易日志
tail -f ~/BTCOptionsTrading/backend/logs/sentiment_trading.log

# 查看最近的执行
tail -50 ~/BTCOptionsTrading/backend/logs/sentiment_trading_cron.log
```

### 查看交易历史

```bash
cd ~/BTCOptionsTrading/backend
cat data/sentiment_trading_history.json | python3 -m json.tool | less
```

### 手动触发执行（测试）

```bash
cd ~/BTCOptionsTrading/backend
source venv/bin/activate  # 如果使用虚拟环境
python3 sentiment_trading_service.py
```

### 检查Cron Job状态

```bash
cd ~/BTCOptionsTrading/backend
./setup_cron.sh status
```

## 更新代码

当需要更新代码时：

### 方法1：使用Git

```bash
cd ~/BTCOptionsTrading
git pull origin main

# 如果有新的依赖
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### 方法2：使用rsync

```bash
# 在本地机器上
rsync -avz --exclude='*.pyc' --exclude='__pycache__' \
  --exclude='.git' --exclude='data/' --exclude='logs/' \
  --exclude='.env' \
  BTCOptionsTrading/ your_username@your_server_ip:~/BTCOptionsTrading/
```

注意：`--exclude='.env'`确保不会覆盖服务器上的配置文件

## 故障排查

### Cron Job未执行

1. 检查cron服务状态：
```bash
sudo systemctl status cron
# 或
sudo service cron status
```

2. 如果cron服务未运行：
```bash
sudo systemctl start cron
sudo systemctl enable cron
```

3. 检查cron日志：
```bash
# Ubuntu/Debian
sudo tail -f /var/log/syslog | grep CRON

# CentOS/RHEL
sudo tail -f /var/log/cron
```

### Python依赖问题

```bash
cd ~/BTCOptionsTrading/backend
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

### 权限问题

```bash
# 确保脚本可执行
chmod +x ~/BTCOptionsTrading/backend/sentiment_trading_service.py
chmod +x ~/BTCOptionsTrading/backend/setup_cron.sh

# 确保日志目录可写
chmod 755 ~/BTCOptionsTrading/backend/logs
chmod 755 ~/BTCOptionsTrading/backend/data
```

### 网络连接问题

```bash
# 测试到Deribit的连接
ping test.deribit.com

# 测试到情绪API的连接
curl http://43.106.51.106:5001/api/sentiment
```

### 查看详细错误

```bash
# 手动运行并查看完整输出
cd ~/BTCOptionsTrading/backend
source venv/bin/activate
python3 sentiment_trading_service.py 2>&1 | tee test_run.log
```

## 安全建议

### 1. 保护.env文件

```bash
chmod 600 ~/BTCOptionsTrading/backend/.env
```

### 2. 使用SSH密钥认证

```bash
# 在本地生成SSH密钥（如果还没有）
ssh-keygen -t rsa -b 4096

# 复制公钥到服务器
ssh-copy-id your_username@your_server_ip
```

### 3. 配置防火墙

```bash
# 只允许SSH访问
sudo ufw allow ssh
sudo ufw enable
```

### 4. 定期备份

创建备份脚本：

```bash
nano ~/backup_trading_data.sh
```

内容：
```bash
#!/bin/bash
BACKUP_DIR=~/trading_backups
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)

# 备份数据和配置
tar -czf $BACKUP_DIR/trading_backup_$DATE.tar.gz \
  ~/BTCOptionsTrading/backend/data/ \
  ~/BTCOptionsTrading/backend/.env

# 保留最近30天的备份
find $BACKUP_DIR -name "trading_backup_*.tar.gz" -mtime +30 -delete
```

设置定期备份：
```bash
chmod +x ~/backup_trading_data.sh
crontab -e
```

添加：
```
0 6 * * * ~/backup_trading_data.sh
```

## 卸载

如需完全卸载：

```bash
# 1. 卸载cron job
cd ~/BTCOptionsTrading/backend
./setup_cron.sh uninstall

# 2. 删除代码（可选）
cd ~
rm -rf BTCOptionsTrading

# 3. 删除虚拟环境（如果单独创建）
rm -rf ~/venv
```

## 快速参考

### 常用命令

```bash
# 查看cron job状态
cd ~/BTCOptionsTrading/backend && ./setup_cron.sh status

# 查看最近日志
tail -50 ~/BTCOptionsTrading/backend/logs/sentiment_trading_cron.log

# 手动测试
cd ~/BTCOptionsTrading/backend && source venv/bin/activate && python3 sentiment_trading_service.py

# 重启cron服务
sudo systemctl restart cron

# 查看交易历史
cat ~/BTCOptionsTrading/backend/data/sentiment_trading_history.json | python3 -m json.tool | less
```

### 重要文件路径

```
~/BTCOptionsTrading/backend/
├── sentiment_trading_service.py    # 主服务脚本
├── setup_cron.sh                   # Cron管理脚本
├── .env                            # 配置文件（敏感）
├── venv/                           # Python虚拟环境
├── logs/
│   ├── sentiment_trading.log       # 详细日志
│   └── sentiment_trading_cron.log  # Cron执行日志
└── data/
    ├── sentiment_trading_history.json  # 交易历史
    └── current_positions.json          # 当前持仓
```

## 性能优化

### 对于2核vCPU服务器

系统已经优化为cron job模式，资源占用极低：
- 执行时间：每天约2-5分钟
- CPU峰值：10-20%（短暂）
- 内存峰值：75-100MB
- 其余时间：0资源占用

无需额外优化。

## 支持

如遇问题：
1. 查看日志文件
2. 运行`./setup_cron.sh status`
3. 手动测试执行
4. 检查网络连接
5. 验证API密钥配置

## 总结

部署完成后，系统将：
- ✅ 每天早上5点自动执行
- ✅ 获取情绪数据并分析
- ✅ 执行相应的交易策略
- ✅ 记录交易历史
- ✅ 自动退出释放资源
- ✅ 适合资源受限的服务器环境

祝交易顺利！🚀
