# 快速修复指南 (Quick Fix Guide)

## 问题: ModuleNotFoundError: No module named 'httpx'

### 解决方案（3个选项，任选其一）

---

### 选项 1: 一键设置脚本 ⭐ 推荐

```bash
cd /root/BTCTradingApp/BTCOptionsTrading
git pull origin main
chmod +x deploy/setup_server_first_time.sh
./deploy/setup_server_first_time.sh
```

这会自动安装所有依赖并测试系统。

---

### 选项 2: 只安装依赖（快速）

```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend
pip3 install -r requirements.txt
```

然后测试：
```bash
python3 daily_data_collector.py --currency BTC --test
```

---

### 选项 3: 只安装缺失的包（最快）

```bash
pip3 install httpx==0.24.1
```

然后测试：
```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend
python3 daily_data_collector.py --currency BTC --test
```

---

## 完整的服务器设置流程

```bash
# 1. 进入项目目录
cd /root/BTCTradingApp/BTCOptionsTrading

# 2. 拉取最新代码
git pull origin main

# 3. 运行一键设置
chmod +x deploy/setup_server_first_time.sh
./deploy/setup_server_first_time.sh

# 4. 测试数据采集
cd backend
python3 daily_data_collector.py --currency BTC --test

# 5. 运行一次完整采集
python3 daily_data_collector.py --currency BTC

# 6. 查看结果
ls -lh data/
cat logs/app.log
```

---

## 验证安装成功

运行以下命令，如果没有错误就说明成功了：

```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend

# 检查关键包
python3 -c "import httpx; print('✓ httpx installed')"
python3 -c "import fastapi; print('✓ fastapi installed')"
python3 -c "import pandas; print('✓ pandas installed')"

# 测试采集器
python3 daily_data_collector.py --test --currency BTC
```

如果看到 "✓ Test mode: Collection successful"，就完成了！

---

## 下一步

设置定时任务，每天自动采集数据：

```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend
chmod +x setup_daily_collection.sh
./setup_daily_collection.sh
```

---

## 需要帮助？

查看详细文档：
- `deploy/SERVER_FIRST_TIME_SETUP.md` - 完整设置指南
- `backend/DAILY_COLLECTION_GUIDE.md` - 数据采集使用指南
- `deploy/COLLECTOR_DEPLOYMENT.md` - 部署指南
