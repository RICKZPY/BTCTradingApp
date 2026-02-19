# 服务器首次部署指南

## 快速开始

### 方法 1: 自动化脚本（推荐）

1. **SSH 连接到服务器**
```bash
ssh root@47.86.62.200
```

2. **下载并运行设置脚本**
```bash
# 下载脚本
curl -o setup.sh https://raw.githubusercontent.com/RICKZPY/BTCTradingApp/main/BTCOptionsTrading/deploy/setup_server_first_time.sh

# 或者使用 wget
wget https://raw.githubusercontent.com/RICKZPY/BTCTradingApp/main/BTCOptionsTrading/deploy/setup_server_first_time.sh -O setup.sh

# 设置执行权限
chmod +x setup.sh

# 运行脚本
./setup.sh
```

脚本会自动完成：
- ✓ 检查并安装 Git 和 Python 3
- ✓ 克隆项目代码
- ✓ 安装 Python 依赖
- ✓ 创建必要的目录
- ✓ 测试数据采集器
- ✓ 设置定时任务

---

### 方法 2: 手动部署

如果自动脚本失败，可以手动执行以下步骤：

#### 步骤 1: 克隆项目
```bash
cd /root
git clone https://github.com/RICKZPY/BTCTradingApp.git
```

#### 步骤 2: 进入后端目录
```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend
```

#### 步骤 3: 安装依赖
```bash
pip3 install -r requirements.txt
```

#### 步骤 4: 创建目录
```bash
mkdir -p logs data/daily_snapshots data/downloads data/exports
```

#### 步骤 5: 设置权限
```bash
chmod +x daily_data_collector.py
chmod +x setup_daily_collection.sh
```

#### 步骤 6: 测试运行
```bash
python3 daily_data_collector.py --currency BTC --test
```

#### 步骤 7: 设置定时任务
```bash
./setup_daily_collection.sh
```

---

## 验证部署

### 检查定时任务
```bash
crontab -l
```

应该看到类似这样的输出：
```
0 2 * * * cd /root/BTCTradingApp/BTCOptionsTrading/backend && /usr/bin/python3 daily_data_collector.py --currency BTC >> logs/daily_collector.log 2>&1
```

### 查看日志
```bash
# 实时查看日志
tail -f /root/BTCTradingApp/BTCOptionsTrading/backend/logs/daily_collector.log

# 查看最近的日志
tail -n 50 /root/BTCTradingApp/BTCOptionsTrading/backend/logs/daily_collector.log
```

### 手动运行测试
```bash
cd /root/BTCTradingApp/BTCOptionsTrading/backend
python3 daily_data_collector.py --currency BTC
```

### 检查数据文件
```bash
# 查看 CSV 文件
ls -lh /root/BTCTradingApp/BTCOptionsTrading/backend/data/daily_snapshots/

# 查看数据库
sqlite3 /root/BTCTradingApp/BTCOptionsTrading/backend/data/historical_options.db "SELECT COUNT(*) FROM options_data;"
```

---

## 常见问题

### Q: 如果项目已经存在怎么办？
```bash
cd /root/BTCTradingApp
git pull origin main
```

### Q: 如何更新代码？
```bash
cd /root/BTCTradingApp
git pull
cd BTCOptionsTrading/backend
pip3 install -r requirements.txt
```

### Q: 如何停止定时任务？
```bash
crontab -e
# 在编辑器中注释掉或删除相关行
```

### Q: 如何修改采集时间？
```bash
crontab -e
# 修改时间设置，例如：
# 0 2 * * *  表示每天凌晨 2:00
# 0 */6 * * * 表示每 6 小时一次
```

### Q: Python 依赖安装失败？
```bash
# 升级 pip
pip3 install --upgrade pip

# 重新安装依赖
pip3 install -r requirements.txt --force-reinstall
```

---

## 项目结构

```
/root/BTCTradingApp/
└── BTCOptionsTrading/
    └── backend/
        ├── daily_data_collector.py      # 数据采集脚本
        ├── setup_daily_collection.sh    # 定时任务设置脚本
        ├── requirements.txt             # Python 依赖
        ├── logs/
        │   └── daily_collector.log      # 采集日志
        └── data/
            ├── daily_snapshots/         # CSV 数据文件
            ├── historical_options.db    # SQLite 数据库
            └── exports/                 # 导出文件
```

---

## 下一步

部署完成后，系统会：
1. 每天自动采集 BTC 期权数据
2. 保存到 CSV 文件和数据库
3. 记录详细日志

你可以：
- 通过前端界面查看历史数据
- 使用 API 访问数据
- 运行回测分析

详细使用说明请参考：
- `DAILY_COLLECTION_GUIDE.md` - 采集器使用指南
- `HISTORICAL_DATA_API.md` - API 文档
- `BACKTEST_GUIDE.md` - 回测指南
