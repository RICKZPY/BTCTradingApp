# 简单Orderbook收集器

## 功能
每天北京时间早上5点自动收集BTC期权orderbook数据：
- ATM附近4个价位的期权
- 到期日在一个月内
- 包括call和put
- 收集3组数据，每组间隔30秒
- 每组收集最优2档bid/ask价格和订单大小
- 保存为CSV格式，文件名包含BTC价格

## 快速开始

### 1. 安装依赖
```bash
pip install aiohttp pytz
```

### 2. 手动测试运行
```bash
cd BTCOptionsTrading/backend
python3 simple_orderbook_collector.py
```

### 3. 设置定时任务（每天自动运行）
```bash
cd BTCOptionsTrading/backend
./setup_daily_orderbook.sh
```

### 4. 查看收集的数据
数据保存在：`BTCOptionsTrading/backend/data/orderbook/`

文件格式：`orderbook_YYYYMMDD_HHMMSS_BTC{price}.csv`

例如：`orderbook_20260223_050000_BTC95234.csv`

## CSV数据格式

| 列名 | 说明 |
|------|------|
| timestamp | 收集时间（北京时间） |
| instrument | 合约名称 |
| strike | 行权价 |
| option_type | 期权类型（call/put） |
| expiry | 到期日 |
| side | bid或ask |
| price | 价格 |
| amount | 订单大小 |

## 查看日志
```bash
tail -f BTCOptionsTrading/backend/logs/orderbook_collector.log
```

## 取消定时任务
```bash
crontab -e
# 删除包含 simple_orderbook_collector.py 的行
```
