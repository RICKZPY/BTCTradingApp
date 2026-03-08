# API访问指南

## 服务器信息
- **服务器IP**: 47.86.62.200
- **API端口**: 5002
- **基础URL**: http://47.86.62.200:5002

## 从本地访问API

### 方法1：使用浏览器

直接在浏览器中打开以下URL：

```
http://47.86.62.200:5002/api/health
http://47.86.62.200:5002/api/status
http://47.86.62.200:5002/api/positions
http://47.86.62.200:5002/api/orders
http://47.86.62.200:5002/api/history
```

### 方法2：使用curl命令

在终端中执行：

```bash
# 健康检查
curl http://47.86.62.200:5002/api/health

# 完整状态
curl http://47.86.62.200:5002/api/status

# 持仓信息
curl http://47.86.62.200:5002/api/positions

# 订单信息
curl http://47.86.62.200:5002/api/orders

# 交易历史
curl http://47.86.62.200:5002/api/history

# 实时持仓（直接从Deribit获取）
curl http://47.86.62.200:5002/api/live/positions

# 实时订单（直接从Deribit获取）
curl http://47.86.62.200:5002/api/live/orders
```

### 方法3：使用监控面板

1. 编辑本地的 `sentiment_dashboard.html` 文件
2. 找到这一行：
   ```javascript
   const API_BASE = 'http://localhost:5002';
   ```
3. 修改为：
   ```javascript
   const API_BASE = 'http://47.86.62.200:5002';
   ```
4. 在浏览器中打开 `sentiment_dashboard.html`

### 方法4：使用Python脚本

创建一个简单的Python脚本：

```python
import requests
import json

BASE_URL = "http://47.86.62.200:5002"

# 健康检查
response = requests.get(f"{BASE_URL}/api/health")
print("健康状态:", json.dumps(response.json(), indent=2, ensure_ascii=False))

# 完整状态
response = requests.get(f"{BASE_URL}/api/status")
print("\n完整状态:", json.dumps(response.json(), indent=2, ensure_ascii=False))
```

## 可用的API端点

### 1. 健康检查
```
GET /api/health
```
返回服务健康状态

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-08T15:30:00",
  "trader_initialized": true
}
```

### 2. 完整状态
```
GET /api/status
```
返回持仓、订单和交易历史的完整信息

**响应示例**:
```json
{
  "status": "success",
  "timestamp": "2026-03-08T15:30:00",
  "data": {
    "positions": {
      "items": [...],
      "count": 2
    },
    "orders": {
      "items": [...],
      "count": 1
    },
    "history": {
      "recent_trades": [...],
      "total_count": 10
    }
  }
}
```

### 3. 持仓信息
```
GET /api/positions
```
返回当前持仓（从缓存）

### 4. 订单信息
```
GET /api/orders
```
返回未完成订单（从缓存）

### 5. 交易历史
```
GET /api/history?limit=10
```
返回最近的交易历史

**参数**:
- `limit`: 返回记录数量（默认10）

### 6. 实时持仓
```
GET /api/live/positions
```
直接从Deribit获取最新持仓

### 7. 实时订单
```
GET /api/live/orders
```
直接从Deribit获取最新订单

## 故障排查

### 问题1: 无法访问API

**检查1**: 确认API服务正在运行
```bash
ssh root@47.86.62.200
ps aux | grep sentiment_api
```

**检查2**: 确认端口5002已开放
```bash
# 在服务器上
netstat -tlnp | grep 5002

# 检查防火墙
ufw status
```

**检查3**: 测试本地连接
```bash
# 从本地测试
curl -v http://47.86.62.200:5002/api/health
```

### 问题2: 连接超时

可能原因：
1. 防火墙未开放5002端口
2. 云服务器安全组未配置

**解决方案**:

在服务器上开放端口：
```bash
# Ubuntu/Debian
sudo ufw allow 5002/tcp
sudo ufw reload

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=5002/tcp
sudo firewall-cmd --reload
```

在云服务商控制台添加安全组规则：
- 协议：TCP
- 端口：5002
- 来源：0.0.0.0/0（或你的本地IP）

### 问题3: 返回502/503错误

API服务可能未启动，重启服务：
```bash
ssh root@47.86.62.200
cd /root/BTCTradingApp/BTCOptionsTrading/backend
./start_sentiment_trading.sh
```

## 快速测试脚本

保存为 `test_api.sh`:

```bash
#!/bin/bash

SERVER="http://47.86.62.200:5002"

echo "测试情绪交易API"
echo "=================="
echo ""

echo "1. 健康检查..."
curl -s $SERVER/api/health | python3 -m json.tool
echo ""

echo "2. 完整状态..."
curl -s $SERVER/api/status | python3 -m json.tool
echo ""

echo "3. 持仓信息..."
curl -s $SERVER/api/positions | python3 -m json.tool
echo ""

echo "4. 交易历史..."
curl -s $SERVER/api/history | python3 -m json.tool
echo ""

echo "测试完成！"
```

使用方法：
```bash
chmod +x test_api.sh
./test_api.sh
```

## 监控建议

### 1. 定期健康检查

创建一个cron任务定期检查：
```bash
# 每5分钟检查一次
*/5 * * * * curl -s http://47.86.62.200:5002/api/health || echo "API服务异常" | mail -s "告警" your@email.com
```

### 2. 使用监控工具

推荐使用：
- **Uptime Robot**: 免费的网站监控服务
- **Grafana**: 可视化监控面板
- **Prometheus**: 指标收集和告警

### 3. 日志监控

定期检查日志：
```bash
ssh root@47.86.62.200 "tail -f /root/BTCTradingApp/BTCOptionsTrading/backend/logs/sentiment_api.log"
```

## 安全建议

### 1. 限制访问IP

如果只需要从特定IP访问，配置防火墙：
```bash
# 只允许你的IP访问
sudo ufw allow from YOUR_IP to any port 5002
```

### 2. 添加API认证

考虑添加API密钥认证（未来改进）

### 3. 使用HTTPS

配置Nginx反向代理和SSL证书（未来改进）

## 快速命令参考

```bash
# 查看服务状态
curl http://47.86.62.200:5002/api/health

# 查看最近交易
curl http://47.86.62.200:5002/api/history?limit=5

# 查看实时持仓
curl http://47.86.62.200:5002/api/live/positions

# 美化JSON输出
curl -s http://47.86.62.200:5002/api/status | python3 -m json.tool

# 保存到文件
curl http://47.86.62.200:5002/api/status > status.json
```

## 获取帮助

如果遇到问题：
1. 检查服务器日志
2. 确认防火墙配置
3. 测试网络连接
4. 查看API服务状态

---

**服务器**: 47.86.62.200  
**端口**: 5002  
**基础URL**: http://47.86.62.200:5002
