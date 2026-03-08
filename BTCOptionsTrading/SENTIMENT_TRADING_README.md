# 情绪驱动自动交易系统

## 功能概述

这是一个基于市场情绪数据的自动交易系统，具有以下功能：

1. **自动监听情绪API** - 每天早上5点自动获取情绪数据
2. **智能策略选择** - 根据情绪数据自动选择交易策略：
   - 负面消息 > 正面消息 → 执行"负面消息策略"（买入ATM看跌期权）
   - 正面消息 > 负面消息 → 执行"利好消息策略"（买入ATM看涨期权）
   - 正面 = 负面 → 执行"消息混杂策略"（卖出窄宽跨式）
3. **自动下单** - 在Deribit测试网自动执行交易
4. **状态监控API** - 提供持仓、订单、交易历史的查询接口

## 文件说明

- `sentiment_trading_service.py` - 主交易服务，监听情绪API并执行交易
- `sentiment_api.py` - 状态查询API服务
- `start_sentiment_trading.sh` - 启动脚本
- `stop_sentiment_trading.sh` - 停止脚本
- `test_sentiment_trading.py` - 测试脚本
- `sentiment_trading.service` - systemd服务配置（用于服务器部署）
- `sentiment_api.service` - API服务的systemd配置

## 快速开始

### 1. 配置环境

确保`.env`文件中配置了Deribit API密钥：

```bash
DERIBIT_API_KEY=your_api_key
DERIBIT_API_SECRET=your_api_secret
```

### 2. 安装依赖

```bash
cd BTCOptionsTrading/backend
pip install -r requirements.txt
pip install aiohttp fastapi uvicorn
```

### 3. 测试服务

运行测试脚本验证配置：

```bash
python3 test_sentiment_trading.py
```

### 4. 启动服务

```bash
chmod +x start_sentiment_trading.sh stop_sentiment_trading.sh
./start_sentiment_trading.sh
```

服务将在后台运行，每天早上5点自动检查情绪数据并执行交易。

### 5. 查看状态

访问API查看当前状态：

```bash
# 完整状态（持仓+订单+历史）
curl http://localhost:5002/api/status

# 仅持仓
curl http://localhost:5002/api/positions

# 仅订单
curl http://localhost:5002/api/orders

# 交易历史
curl http://localhost:5002/api/history

# 实时持仓（直接从Deribit获取）
curl http://localhost:5002/api/live/positions

# 实时订单（直接从Deribit获取）
curl http://localhost:5002/api/live/orders
```

### 6. 停止服务

```bash
./stop_sentiment_trading.sh
```

## 服务器部署（使用systemd）

### 1. 编辑服务文件

修改`sentiment_trading.service`和`sentiment_api.service`中的路径和用户名：

```bash
# 替换YOUR_USERNAME为你的用户名
# 替换/path/to/为实际路径
sed -i 's/YOUR_USERNAME/your_username/g' sentiment_trading.service
sed -i 's|/path/to/|/home/your_username/|g' sentiment_trading.service

sed -i 's/YOUR_USERNAME/your_username/g' sentiment_api.service
sed -i 's|/path/to/|/home/your_username/|g' sentiment_api.service
```

### 2. 安装服务

```bash
# 复制服务文件
sudo cp sentiment_trading.service /etc/systemd/system/
sudo cp sentiment_api.service /etc/systemd/system/

# 重载systemd
sudo systemctl daemon-reload

# 启用服务（开机自启）
sudo systemctl enable sentiment_trading.service
sudo systemctl enable sentiment_api.service

# 启动服务
sudo systemctl start sentiment_trading.service
sudo systemctl start sentiment_api.service
```

### 3. 管理服务

```bash
# 查看状态
sudo systemctl status sentiment_trading.service
sudo systemctl status sentiment_api.service

# 查看日志
sudo journalctl -u sentiment_trading.service -f
sudo journalctl -u sentiment_api.service -f

# 重启服务
sudo systemctl restart sentiment_trading.service
sudo systemctl restart sentiment_api.service

# 停止服务
sudo systemctl stop sentiment_trading.service
sudo systemctl stop sentiment_api.service
```

## API接口文档

### 基础信息

- **基础URL**: `http://localhost:5002`
- **返回格式**: JSON

### 接口列表

#### 1. 获取完整状态

```
GET /api/status
```

返回持仓、订单和交易历史的完整信息。

**响应示例**:
```json
{
  "status": "success",
  "timestamp": "2026-03-02T10:30:00",
  "data": {
    "positions": {
      "items": [...],
      "count": 2,
      "last_update": "2026-03-02T05:05:00"
    },
    "orders": {
      "items": [...],
      "count": 1,
      "last_update": "2026-03-02T05:05:00"
    },
    "history": {
      "recent_trades": [...],
      "total_count": 10
    },
    "errors": null
  }
}
```

#### 2. 获取持仓信息

```
GET /api/positions
```

返回当前持仓信息（从缓存）。

#### 3. 获取订单信息

```
GET /api/orders
```

返回未完成订单信息（从缓存）。

#### 4. 获取交易历史

```
GET /api/history?limit=10
```

返回最近的交易历史记录。

**参数**:
- `limit` (可选): 返回记录数量，默认10

#### 5. 实时获取持仓

```
GET /api/live/positions
```

直接从Deribit获取最新持仓信息。

#### 6. 实时获取订单

```
GET /api/live/orders
```

直接从Deribit获取最新订单信息。

#### 7. 健康检查

```
GET /api/health
```

检查服务是否正常运行。

## 数据文件

服务运行时会生成以下数据文件：

- `data/sentiment_trading_history.json` - 交易历史记录
- `data/current_positions.json` - 当前持仓和订单快照
- `data/sentiment_service.pid` - 交易服务进程ID
- `data/sentiment_api.pid` - API服务进程ID
- `logs/sentiment_trading.log` - 交易服务日志
- `logs/sentiment_api.log` - API服务日志

## 工作流程

1. **每天早上5点**，服务自动唤醒
2. 从`http://43.106.51.106:5001/api/sentiment`获取情绪数据
3. 分析情绪数据：
   - `negative_count > positive_count` → 负面消息策略
   - `negative_count < positive_count` → 利好消息策略
   - `negative_count == positive_count` → 消息混杂策略
4. 构建并执行选定的策略
5. 记录交易结果到历史文件
6. 更新持仓和订单快照
7. 等待下一个检查时间

## 策略说明

### 负面消息策略 (bearish_news)
- **类型**: 单腿策略
- **操作**: 买入ATM看跌期权
- **适用**: 负面消息居多时
- **资金**: 每次1000 USD
- **到期**: 7天后

### 利好消息策略 (bullish_news)
- **类型**: 单腿策略
- **操作**: 买入ATM看涨期权
- **适用**: 利好消息居多时
- **资金**: 每次1000 USD
- **到期**: 7天后

### 消息混杂策略 (mixed_news)
- **类型**: 跨式策略
- **操作**: 卖出窄宽跨式
- **适用**: 消息混杂、预期波动不大时
- **资金**: 每次1000 USD
- **到期**: 7天后

## 注意事项

1. **测试网环境**: 默认使用Deribit测试网，不会使用真实资金
2. **API密钥**: 确保`.env`文件中配置了正确的API密钥
3. **时区**: 检查时间设置为早上5点（服务器本地时间）
4. **网络**: 确保服务器可以访问情绪API和Deribit API
5. **日志**: 定期检查日志文件，监控服务运行状态
6. **资金管理**: 每次交易使用1000 USD，可在代码中调整

## 故障排查

### 服务无法启动

1. 检查Python环境：`python3 --version`
2. 检查依赖：`pip list | grep -E "aiohttp|fastapi|uvicorn"`
3. 检查API密钥：`cat .env | grep DERIBIT`
4. 查看日志：`tail -f logs/sentiment_trading.log`

### 无法获取情绪数据

1. 测试API连接：`curl http://43.106.51.106:5001/api/sentiment`
2. 检查网络：`ping 43.106.51.106`
3. 查看日志中的错误信息

### 交易执行失败

1. 检查Deribit连接：运行`test_sentiment_trading.py`
2. 验证API密钥权限
3. 检查账户余额
4. 查看交易历史中的错误信息

### API无法访问

1. 检查API服务状态：`ps aux | grep sentiment_api`
2. 检查端口占用：`lsof -i :5002`
3. 查看API日志：`tail -f logs/sentiment_api.log`

## 自定义配置

### 修改检查时间

编辑`sentiment_trading_service.py`中的`CHECK_TIME`：

```python
CHECK_TIME = time(5, 0)  # 早上5点
```

### 修改交易资金

编辑`sentiment_trading_service.py`中的`execute_sentiment_strategy`方法：

```python
capital=Decimal("1000"),  # 修改为你想要的金额
```

### 修改期权到期时间

```python
expiry_days=7  # 修改为你想要的天数
```

### 修改API端口

编辑`sentiment_api.py`底部：

```python
uvicorn.run(app, host="0.0.0.0", port=5002)  # 修改端口号
```

## 监控建议

1. 设置日志轮转，避免日志文件过大
2. 定期检查交易历史，确保策略执行正常
3. 监控持仓情况，及时发现异常
4. 设置告警，当服务停止或出错时通知
5. 定期备份交易历史数据

## 技术支持

如有问题，请检查：
1. 日志文件：`logs/sentiment_trading.log`和`logs/sentiment_api.log`
2. 数据文件：`data/sentiment_trading_history.json`
3. 测试脚本：运行`python3 test_sentiment_trading.py`

## 更新日志

- 2026-03-02: 初始版本发布
  - 实现情绪监听和自动交易
  - 提供状态查询API
  - 支持systemd部署
