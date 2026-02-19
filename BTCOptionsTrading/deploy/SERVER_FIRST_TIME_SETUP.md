# 服务器首次设置指南 (Server First-Time Setup Guide)

## 快速开始 (Quick Start)

如果你刚刚把项目克隆到服务器上，按照以下步骤操作：

### 1. 进入项目目录
```bash
cd /root/BTCTradingApp/BTCOptionsTrading
```

### 2. 运行一键设置脚本
```bash
chmod +x deploy/setup_server_first_time.sh
./deploy/setup_server_first_time.sh
```

这个脚本会自动：
- ✓ 检查 Python 版本
- ✓ 安装所有 Python 依赖
- ✓ 创建必要的目录
- ✓ 设置环境文件
- ✓ 测试数据采集器
- ✓ 可选：设置定时任务

---

## 手动设置步骤 (Manual Setup Steps)

如果你想手动设置，或者自动脚本失败了：

### 步骤 1: 安装 Python 依赖

```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend
pip3 install -r requirements.txt
```

这会安装所有需要的包，包括：
- httpx (HTTP 客户端)
- fastapi (API 框架)
- pandas (数据处理)
- numpy, scipy (数学计算)
- sqlalchemy (数据库)
- 等等...

### 步骤 2: 创建必要的目录

```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend
mkdir -p data/downloads data/exports logs config backups
```

### 步骤 3: 设置环境变量

```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend
cp .env.example .env
# 编辑 .env 文件（如果需要）
nano .env
```

### 步骤 4: 测试数据采集器

```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend
python3 daily_data_collector.py --currency BTC --test
```

如果看到 "✓ Test mode: Collection successful"，说明设置成功！

### 步骤 5: 运行一次完整采集

```bash
python3 daily_data_collector.py --currency BTC
```

### 步骤 6: 设置定时任务（可选）

```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend
chmod +x setup_daily_collection.sh
./setup_daily_collection.sh
```

---

## 常见问题 (Troubleshooting)

### 问题 1: ModuleNotFoundError: No module named 'httpx'

**原因**: Python 依赖没有安装

**解决方案**:
```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend
pip3 install -r requirements.txt
```

或者只安装缺失的包：
```bash
pip3 install httpx==0.24.1
```

### 问题 2: pip3 命令不存在

**解决方案**: 安装 pip
```bash
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
rm get-pip.py
```

### 问题 3: 权限错误

**解决方案**: 使用 sudo 或切换到 root 用户
```bash
sudo pip3 install -r requirements.txt
# 或
su root
```

### 问题 4: 数据库文件不存在

**解决方案**: 数据库会自动创建，确保 data 目录存在
```bash
mkdir -p /root/BTCTradingApp/BTCOptionsTrading/backend/data
```

---

## 验证安装 (Verify Installation)

运行以下命令检查所有依赖是否正确安装：

```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend

# 检查 Python 版本
python3 --version

# 检查关键包
python3 -c "import httpx; print('httpx:', httpx.__version__)"
python3 -c "import fastapi; print('fastapi:', fastapi.__version__)"
python3 -c "import pandas; print('pandas:', pandas.__version__)"
python3 -c "import sqlalchemy; print('sqlalchemy:', sqlalchemy.__version__)"

# 测试数据采集器
python3 daily_data_collector.py --test --currency BTC
```

如果所有命令都成功运行，说明安装完成！

---

## 下一步 (Next Steps)

1. **查看采集的数据**:
   ```bash
   ls -lh /root/BTCTradingApp/BTCOptionsTrading/backend/data/
   ```

2. **查看日志**:
   ```bash
   tail -f /root/BTCTradingApp/BTCOptionsTrading/backend/logs/app.log
   ```

3. **启动后端 API**:
   ```bash
   cd /root/BTCTradingApp/BTCOptionsTrading/backend
   python3 run_api.py
   ```

4. **查看定时任务**:
   ```bash
   crontab -l
   ```

---

## 相关文档 (Related Documentation)

- **数据采集使用指南**: `backend/DAILY_COLLECTION_GUIDE.md`
- **部署指南**: `deploy/COLLECTOR_DEPLOYMENT.md`
- **完整部署文档**: `deploy/DEPLOYMENT_GUIDE.md`

---

## 快速命令参考 (Quick Command Reference)

```bash
# 进入项目目录
cd /root/BTCTradingApp/BTCOptionsTrading

# 一键设置（推荐）
./deploy/setup_server_first_time.sh

# 手动安装依赖
cd backend && pip3 install -r requirements.txt

# 测试采集器
cd backend && python3 daily_data_collector.py --test --currency BTC

# 运行采集器
cd backend && python3 daily_data_collector.py --currency BTC

# 设置定时任务
cd backend && ./setup_daily_collection.sh

# 查看日志
tail -f backend/logs/app.log

# 查看数据
ls -lh backend/data/
```

---

## 支持 (Support)

如果遇到问题：
1. 检查日志文件: `backend/logs/app.log`
2. 查看错误信息并参考上面的常见问题
3. 确保 Python 版本 >= 3.7
4. 确保网络连接正常（需要访问 Deribit API）
