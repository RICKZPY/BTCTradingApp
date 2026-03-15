# 加权情绪跨式期权交易 - 状态查询 API 指南

## 概述

独立的状态查询 API，用于监控加权情绪跨式期权交易系统。

### 关键信息

| 项目 | 值 |
|------|-----|
| **端口** | 5004 |
| **账户** | 0366QIa2 (Deribit Test) |
| **服务名** | weighted-sentiment-straddle-trading |
| **版本** | 2.0.0 |

### 与现有服务的区别

| 服务 | 端口 | 账户 | API Key 环境变量 |
|------|------|------|-----------------|
| sentiment_api.py | 5002 | vXkaBDto | `DERIBIT_API_KEY` |
| weighted_sentiment_api.py | 5004 | 0366QIa2 | `WEIGHTED_SENTIMENT_DERIBIT_API_KEY` |

---

## 快速开始

### 本地启动

```bash
cd BTCOptionsTrading/backend
./start_weighted_sentiment_api.sh
```

访问: http://localhost:5004

### 服务器部署

```bash
cd BTCOptionsTrading/backend
./deploy_weighted_sentiment_api.sh
```

访问: http://47.86.62.200:5004

---

## API 端点

### 1. 根路径 - HTML 页面

```
GET /
```

返回一个友好的 HTML 页面，展示所有可用端点。

**示例:**
```bash
curl http://localhost:5004/
```

---

### 2. 完整状态

```
GET /api/status
```

获取系统完整状态，包括持仓、订单、交易历史和新闻统计。

**响应示例:**
```json
{
  "status": "success",
  "timestamp": "2026-03-12T10:00:00.000000",
  "account": "0366QIa2",
  "system": {
    "service": "weighted-sentiment-straddle-trading",
    "version": "2.0.0",
    "last_run": "2026-03-12T09:00:00.000000",
    "trader_connected": true
  },
  "data": {
    "positions": {
      "items": [...],
      "count": 2
    },
    "orders": {
      "items": [...],
      "count": 0
    },
    "trades": {
      "recent": [...],
      "total_count": 5
    },
    "news": {
      "total_processed": 150
    }
  }
}
```

**示例:**
```bash
curl http://localhost:5004/api/status
```

---

### 3. 持仓查询

```
GET /api/positions
```

实时从 Deribit Test 获取当前持仓。

**响应示例:**
```json
{
  "status": "success",
  "timestamp": "2026-03-12T10:00:00.000000",
  "account": "0366QIa2",
  "data": {
    "positions": [
      {
        "instrument_name": "BTC-26MAR26-85000-C",
        "size": 0.1,
        "average_price": 0.0234,
        "mark_price": 0.0245,
        "floating_profit_loss": 0.00011
      }
    ],
    "count": 1
  }
}
```

**示例:**
```bash
curl http://localhost:5004/api/positions
```

---

### 4. 订单查询

```
GET /api/orders
```

实时从 Deribit Test 获取未完成订单。

**响应示例:**
```json
{
  "status": "success",
  "timestamp": "2026-03-12T10:00:00.000000",
  "account": "0366QIa2",
  "data": {
    "orders": [],
    "count": 0
  }
}
```

**示例:**
```bash
curl http://localhost:5004/api/orders
```

---

### 5. 交易历史

```
GET /api/trades?limit=10
```

获取交易历史记录。

**参数:**
- `limit` (可选): 返回记录数量，默认 10

**响应示例:**
```json
{
  "status": "success",
  "timestamp": "2026-03-12T10:00:00.000000",
  "account": "0366QIa2",
  "data": {
    "trades": [
      {
        "交易时间": "2026-03-12T09:14:18.635725",
        "新闻 ID": "https://www.odaily.news/zh-CN/newsflash/471596",
        "新闻内容": "星球早讯",
        "情绪": "negative",
        "重要性评分": "8/10",
        "交易成功": "True",
        "现货价格": "$85234.50",
        "总成本": "$3682.15"
      }
    ],
    "total_count": 5,
    "returned_count": 5
  }
}
```

**示例:**
```bash
curl http://localhost:5004/api/trades?limit=5
```

---

### 6. 新闻统计

```
GET /api/news/history
```

获取新闻处理统计。

**响应示例:**
```json
{
  "status": "success",
  "timestamp": "2026-03-12T10:00:00.000000",
  "data": {
    "total_news_processed": 150,
    "high_score_threshold": 7
  }
}
```

**示例:**
```bash
curl http://localhost:5004/api/news/history
```

---

### 7. 账户信息

```
GET /api/account
```

获取 Deribit Test 账户摘要信息。

**响应示例:**
```json
{
  "status": "success",
  "timestamp": "2026-03-12T10:00:00.000000",
  "account": "0366QIa2",
  "data": {
    "currency": "BTC",
    "equity": 10.5,
    "balance": 10.0,
    "available_funds": 9.5,
    "margin_balance": 10.0
  }
}
```

**示例:**
```bash
curl http://localhost:5004/api/account
```

---

### 8. 健康检查

```
GET /api/health
```

检查 API 服务健康状态。

**响应示例:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-12T10:00:00.000000",
  "service": "weighted-sentiment-straddle-trading",
  "version": "2.0.0",
  "account": "0366QIa2",
  "checks": {
    "trader_initialized": true,
    "news_tracker_initialized": true,
    "has_api_config": true,
    "trade_log_exists": true,
    "cron_log_exists": true
  },
  "last_run": "2026-03-12T09:00:00.000000"
}
```

**示例:**
```bash
curl http://localhost:5004/api/health
```

---

## 部署管理

### 使用 systemd（推荐）

部署时选择创建 systemd 服务，可以实现自动启动和管理。

**管理命令:**
```bash
# 启动服务
systemctl start weighted-sentiment-api

# 停止服务
systemctl stop weighted-sentiment-api

# 重启服务
systemctl restart weighted-sentiment-api

# 查看状态
systemctl status weighted-sentiment-api

# 查看日志
journalctl -u weighted-sentiment-api -f

# 开机自启
systemctl enable weighted-sentiment-api

# 禁用自启
systemctl disable weighted-sentiment-api
```

### 手动启动

```bash
ssh root@47.86.62.200
cd /root/BTCOptionsTrading/backend
./start_weighted_sentiment_api.sh
```

### 后台运行

```bash
nohup python3 weighted_sentiment_api.py > logs/weighted_sentiment_api.log 2>&1 &
```

---

## 监控和调试

### 查看日志

```bash
# API 日志（如果使用 systemd）
journalctl -u weighted-sentiment-api -f

# 或者查看文件日志
tail -f /root/BTCOptionsTrading/backend/logs/weighted_sentiment_api.log
tail -f /root/BTCOptionsTrading/backend/logs/weighted_sentiment_api_error.log
```

### 测试连接

```bash
# 健康检查
curl http://47.86.62.200:5004/api/health

# 获取状态
curl http://47.86.62.200:5004/api/status
```

### 检查端口

```bash
# 检查端口是否监听
lsof -i :5004

# 或者
netstat -tulpn | grep 5004
```

---

## 故障排查

### 问题 1: API 无法启动

**症状:** 启动脚本报错或服务无法访问

**解决方法:**
1. 检查端口是否被占用
   ```bash
   lsof -i :5004
   ```

2. 检查依赖是否安装
   ```bash
   pip3 list | grep fastapi
   pip3 list | grep uvicorn
   pip3 list | grep aiohttp
   ```

3. 检查环境变量
   ```bash
   grep WEIGHTED_SENTIMENT_DERIBIT_API_KEY .env
   ```

### 问题 2: 无法获取持仓/订单

**症状:** `/api/positions` 或 `/api/orders` 返回 503 错误

**解决方法:**
1. 检查 Deribit API 凭证
   ```bash
   curl http://localhost:5004/api/health
   ```

2. 查看 `trader_initialized` 是否为 `true`

3. 检查网络连接到 Deribit Test

### 问题 3: 交易历史为空

**症状:** `/api/trades` 返回空数组

**解决方法:**
1. 检查交易日志文件是否存在
   ```bash
   ls -la logs/weighted_sentiment_trades.log
   ```

2. 等待 cron job 执行并产生交易记录

3. 手动执行 cron 脚本测试
   ```bash
   python3 weighted_sentiment_cron.py
   ```

---

## 安全建议

1. **防火墙配置**
   ```bash
   # 只允许特定 IP 访问
   ufw allow from YOUR_IP to any port 5004
   ```

2. **反向代理**
   使用 Nginx 添加认证和 HTTPS

3. **API 密钥保护**
   确保 `.env` 文件权限正确
   ```bash
   chmod 600 .env
   ```

---

## 与其他服务集成

### 监控脚本示例

```python
import requests
import time

API_URL = "http://47.86.62.200:5004"

def check_status():
    try:
        response = requests.get(f"{API_URL}/api/health")
        data = response.json()
        
        if data["status"] == "healthy":
            print("✓ API 健康")
        else:
            print("✗ API 异常")
            
        return data
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return None

def get_positions():
    try:
        response = requests.get(f"{API_URL}/api/positions")
        data = response.json()
        
        print(f"持仓数量: {data['data']['count']}")
        return data
    except Exception as e:
        print(f"获取持仓失败: {e}")
        return None

if __name__ == "__main__":
    while True:
        print("\n" + "="*50)
        check_status()
        get_positions()
        time.sleep(60)  # 每分钟检查一次
```

---

## 相关文档

- [部署总结](DEPLOYMENT_SUMMARY_V2.md)
- [技术集成文档](WEIGHTED_SENTIMENT_TRADING_INTEGRATION.md)
- [快速参考](QUICK_REFERENCE_V2.md)
- [Cron 脚本](weighted_sentiment_cron.py)

---

## 版本历史

- **v2.0.0** (2026-03-12): 完整的 FastAPI 实现，独立账户
- **v1.0.0** (2026-03-12): 初始 aiohttp 版本

---

*最后更新: 2026-03-12*
