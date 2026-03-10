# 从持续运行模式迁移到Cron Job模式

## 概述

本指南帮助你从旧的持续运行模式（24小时运行的Python进程）迁移到新的Cron Job模式（按需执行）。

## 为什么要迁移？

### 旧模式的问题
- ❌ 24小时持续占用CPU和内存
- ❌ 每分钟检查时间，但每天只执行1次交易
- ❌ 在2核vCPU服务器上浪费资源
- ❌ 需要手动管理进程（启动、停止、重启）

### 新模式的优势
- ✅ 资源占用降低99.8%（每天只运行2-5分钟）
- ✅ 自动化调度，无需手动管理
- ✅ 所有交易逻辑完全不变
- ✅ 非常适合资源受限的服务器

## 迁移步骤

### 步骤1：停止旧服务

#### 方法1：使用停止脚本（推荐）

在服务器上运行：

```bash
cd ~/BTCOptionsTrading/backend
./stop_old_service.sh
```

脚本会：
- 查找所有sentiment_trading_service.py进程
- 显示进程信息
- 优雅地停止进程（SIGTERM）
- 如果需要，强制停止（SIGKILL）

#### 方法2：手动停止

**查找进程：**
```bash
ps aux | grep sentiment_trading_service.py
```

**停止进程：**
```bash
# 使用进程ID停止（替换PID为实际的进程ID）
kill PID

# 或者一次性停止所有
pkill -f sentiment_trading_service.py

# 如果上面的命令不起作用，使用强制停止
kill -9 PID
# 或
pkill -9 -f sentiment_trading_service.py
```

**验证进程已停止：**
```bash
ps aux | grep sentiment_trading_service.py
# 应该只看到grep进程本身
```

#### 方法3：停止systemd服务（如果使用）

如果你之前配置了systemd服务：

```bash
# 停止服务
sudo systemctl stop sentiment_trading

# 禁用开机自启
sudo systemctl disable sentiment_trading

# 删除服务文件（可选）
sudo rm /etc/systemd/system/sentiment_trading.service
sudo systemctl daemon-reload
```

### 步骤2：备份数据（重要！）

在停止服务后，立即备份数据：

```bash
cd ~/BTCOptionsTrading/backend

# 创建备份目录
mkdir -p ~/trading_backup_$(date +%Y%m%d)

# 备份数据文件
cp -r data/ ~/trading_backup_$(date +%Y%m%d)/
cp .env ~/trading_backup_$(date +%Y%m%d)/

# 创建压缩包
tar -czf ~/trading_backup_$(date +%Y%m%d).tar.gz ~/trading_backup_$(date +%Y%m%d)/

echo "备份已保存到: ~/trading_backup_$(date +%Y%m%d).tar.gz"
```

### 步骤3：更新代码

#### 方法A：使用Git（推荐）

```bash
cd ~/BTCOptionsTrading
git pull origin main
```

#### 方法B：从本地上传

在本地机器上：

```bash
cd /path/to/BTCOptionsTrading
rsync -avz --exclude='data/' --exclude='logs/' --exclude='.env' \
  BTCOptionsTrading/ user@server_ip:~/BTCOptionsTrading/
```

### 步骤4：更新Python依赖

```bash
cd ~/BTCOptionsTrading/backend

# 如果使用虚拟环境
source venv/bin/activate

# 更新依赖
pip install -r requirements.txt --upgrade
```

### 步骤5：验证配置文件

确保.env文件配置正确：

```bash
cat ~/BTCOptionsTrading/backend/.env
```

应该包含：
```bash
DERIBIT_TESTNET_API_KEY=your_key
DERIBIT_TESTNET_API_SECRET=your_secret
```

### 步骤6：测试新版本

手动运行一次，确保新版本工作正常：

```bash
cd ~/BTCOptionsTrading/backend
source venv/bin/activate  # 如果使用虚拟环境
python3 sentiment_trading_service.py
```

检查输出：
- ✅ 服务启动（单次执行模式）
- ✅ 认证成功
- ✅ 获取情绪数据
- ✅ 执行交易
- ✅ 服务自动退出
- ✅ 连接已关闭，资源已释放

### 步骤7：安装Cron Job

```bash
cd ~/BTCOptionsTrading/backend

# 确保脚本可执行
chmod +x setup_cron.sh

# 安装cron job
./setup_cron.sh install
```

### 步骤8：验证Cron Job

```bash
# 查看状态
./setup_cron.sh status

# 查看crontab
crontab -l | grep sentiment

# 验证时区
timedatectl
```

### 步骤9：监控第一次执行

Cron job会在第二天早上5点首次执行。你可以：

**选项A：等待自动执行**
```bash
# 第二天早上5点后查看日志
tail -f ~/BTCOptionsTrading/backend/logs/sentiment_trading_cron.log
```

**选项B：手动触发测试**
```bash
cd ~/BTCOptionsTrading/backend
source venv/bin/activate
python3 sentiment_trading_service.py
```

## 迁移验证清单

完成迁移后，验证以下项目：

- [ ] 旧的Python进程已完全停止
- [ ] 数据已备份
- [ ] 新代码已部署
- [ ] 依赖已更新
- [ ] .env配置正确
- [ ] 手动测试执行成功
- [ ] Cron job已安装
- [ ] Cron job状态正常
- [ ] 时区设置正确
- [ ] 日志文件可访问

## 回滚计划（如果需要）

如果新版本有问题，可以回滚到旧版本：

### 1. 卸载Cron Job

```bash
cd ~/BTCOptionsTrading/backend
./setup_cron.sh uninstall
```

### 2. 恢复旧代码

```bash
cd ~/BTCOptionsTrading
git checkout <old_commit_hash>
```

### 3. 恢复数据

```bash
cd ~
tar -xzf trading_backup_YYYYMMDD.tar.gz
cp -r trading_backup_YYYYMMDD/data/* ~/BTCOptionsTrading/backend/data/
```

### 4. 重启旧服务

根据你之前的启动方式重启服务。

## 常见问题

### Q: 旧进程无法停止怎么办？

A: 尝试使用sudo权限：
```bash
sudo pkill -9 -f sentiment_trading_service.py
```

### Q: 数据会丢失吗？

A: 不会。新版本使用相同的数据文件格式，所有历史数据都会保留。

### Q: 需要重新配置API密钥吗？

A: 不需要。.env文件保持不变。

### Q: Cron job什么时候首次执行？

A: 第二天早上5点（服务器时间）。你也可以手动测试执行。

### Q: 如何确认迁移成功？

A: 运行以下命令：
```bash
# 1. 确认没有旧进程
ps aux | grep sentiment_trading_service.py

# 2. 确认cron job已安装
crontab -l | grep sentiment

# 3. 手动测试执行
cd ~/BTCOptionsTrading/backend && python3 sentiment_trading_service.py

# 4. 查看状态
./setup_cron.sh status
```

### Q: 迁移后资源占用有什么变化？

A: 
- 旧模式：24小时持续占用约75MB内存和0.5% CPU
- 新模式：每天只在执行时占用资源（约2-5分钟）
- 节省：约99.8%的资源占用时间

## 快速迁移命令总结

```bash
# 1. 停止旧服务
cd ~/BTCOptionsTrading/backend
./stop_old_service.sh

# 2. 备份数据
tar -czf ~/trading_backup_$(date +%Y%m%d).tar.gz data/ .env

# 3. 更新代码
cd ~/BTCOptionsTrading
git pull origin main

# 4. 更新依赖
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 5. 测试运行
python3 sentiment_trading_service.py

# 6. 安装cron job
./setup_cron.sh install

# 7. 验证
./setup_cron.sh status
```

## 获取帮助

如果迁移过程中遇到问题：

1. 查看日志：`tail -f logs/sentiment_trading.log`
2. 检查进程：`ps aux | grep sentiment`
3. 验证配置：`cat .env`
4. 手动测试：`python3 sentiment_trading_service.py`
5. 查看cron状态：`./setup_cron.sh status`

## 总结

迁移到Cron Job模式后：
- ✅ 资源占用大幅降低
- ✅ 自动化调度，无需手动管理
- ✅ 所有交易逻辑保持不变
- ✅ 适合资源受限的服务器环境

迁移过程简单安全，数据完全保留！
