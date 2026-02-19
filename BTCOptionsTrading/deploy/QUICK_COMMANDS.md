# 快速命令参考

## 首次部署（服务器上还没有项目）

### 方法 1: 一键自动部署（推荐）
```bash
ssh root@47.86.62.200
curl -o setup.sh https://raw.githubusercontent.com/RICKZPY/BTCTradingApp/main/BTCOptionsTrading/deploy/setup_server_first_time.sh
chmod +x setup.sh
./setup.sh
```

### 方法 2: 手动部署
```bash
ssh root@47.86.62.200
cd /root
git clone https://github.com/RICKZPY/BTCTradingApp.git
cd /root/BTCTradingApp/BTCOptionsTrading/backend
pip3 install -r requirements.txt
mkdir -p logs data/daily_snapshots data/downloads data/exports
chmod +x daily_data_collector.py setup_daily_collection.sh
python3 daily_data_collector.py --currency BTC --test
./setup_daily_collection.sh
```

---

## 更新代码（项目已存在）

```bash
ssh root@47.86.62.200
cd /root/BTCTradingApp
git pull origin main
cd BTCOptionsTrading/backend
pip3 install -r requirements.txt
```

---

## 常用操作

### 手动运行数据采集
```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend
python3 daily_data_collector.py --currency BTC
```

### 查看实时日志
```bash
tail -f /root/BTCTradingApp/BTCOptionsTrading/backend/logs/daily_collector.log
```

### 查看定时任务
```bash
crontab -l
```

### 编辑定时任务
```bash
crontab -e
```

### 查看数据文件
```bash
ls -lh /root/BTCTradingApp/BTCOptionsTrading/backend/data/daily_snapshots/
```

### 查看数据库记录数
```bash
sqlite3 /root/BTCTradingApp/BTCOptionsTrading/backend/data/historical_options.db "SELECT COUNT(*) FROM options_data;"
```

---

## 完整的 git pull 命令

如果你在服务器上，项目已经存在：

```bash
cd /root/BTCTradingApp && git pull origin main
```

如果需要强制覆盖本地修改：

```bash
cd /root/BTCTradingApp && git fetch origin && git reset --hard origin/main
```

---

## 故障排查

### 检查 Python 版本
```bash
python3 --version
```

### 检查 pip 版本
```bash
pip3 --version
```

### 重新安装依赖
```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend
pip3 install -r requirements.txt --force-reinstall
```

### 测试 Deribit API 连接
```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend
python3 -c "import requests; print(requests.get('https://www.deribit.com/api/v2/public/get_instruments?currency=BTC&kind=option').status_code)"
```

应该输出: `200`
