# BTC期权交易系统 REST API 文档

## 概述

本API提供BTC期权交易回测系统的完整后端接口，支持策略管理、回测执行、数据分析等功能。

## 技术栈

- **框架**: FastAPI 0.103.2
- **数据库**: PostgreSQL (SQLAlchemy ORM)
- **数据验证**: Pydantic
- **服务器**: Uvicorn
- **文档**: 自动生成OpenAPI (Swagger/ReDoc)

## 快速开始

### 1. 安装依赖

```bash
cd BTCOptionsTrading/backend
pip install -r requirements.txt
```

### 2. 配置环境变量

复制`.env.example`到`.env`并配置数据库连接:

```bash
cp .env.example .env
```

编辑`.env`文件:

```env
# 数据库配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=btc_options
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Deribit API配置
DERIBIT_API_KEY=your_api_key
DERIBIT_API_SECRET=your_api_secret
DERIBIT_TEST_MODE=true
```

### 3. 初始化数据库

```bash
python src/storage/init_db.py init
```

### 4. 启动API服务器

```bash
python run_api.py
```

服务器将在 `http://localhost:8000` 启动

### 5. 访问API文档

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API接口

### 健康检查

#### GET /health
基础健康检查

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-07T10:00:00",
  "service": "BTC Options Trading System"
}
```

#### GET /status
系统状态和数据库统计

**响应示例**:
```json
{
  "status": "operational",
  "timestamp": "2026-02-07T10:00:00",
  "database": {
    "connected": true,
    "stats": {
      "option_contracts": 150,
      "strategies": 25,
      "backtest_results": 10
    }
  }
}
```

### 策略管理 (/api/strategies)

#### POST /api/strategies/
创建新策略

**请求体**:
```json
{
  "name": "买入看涨期权",
  "description": "看涨BTC，买入执行价45000的看涨期权",
  "strategy_type": "single_leg",
  "legs": [
    {
      "option_contract": {
        "instrument_name": "BTC-30DEC23-45000-C",
        "underlying": "BTC",
        "option_type": "call",
        "strike_price": 45000.0,
        "expiration_date": "2023-12-30T08:00:00"
      },
      "action": "buy",
      "quantity": 1
    }
  ]
}
```

**响应示例**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "买入看涨期权",
  "description": "看涨BTC，买入执行价45000的看涨期权",
  "strategy_type": "single_leg",
  "max_profit": null,
  "max_loss": null,
  "created_at": "2026-02-07T10:00:00"
}
```

#### GET /api/strategies/
获取策略列表

**查询参数**:
- `skip`: 跳过记录数 (默认: 0)
- `limit`: 返回记录数 (默认: 100)

#### GET /api/strategies/{strategy_id}
获取策略详情

#### DELETE /api/strategies/{strategy_id}
删除策略

#### GET /api/strategies/templates/list
获取策略模板列表

**响应示例**:
```json
{
  "templates": [
    {
      "type": "single_leg",
      "name": "单腿期权",
      "description": "买入或卖出单个期权合约"
    },
    {
      "type": "straddle",
      "name": "跨式策略",
      "description": "同时买入/卖出相同执行价的看涨和看跌期权"
    }
  ]
}
```

### 回测 (/api/backtest)

#### POST /api/backtest/run
运行回测

**请求体**:
```json
{
  "strategy_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_date": "2023-11-01T00:00:00",
  "end_date": "2023-12-01T00:00:00",
  "initial_capital": 100000.0,
  "underlying_symbol": "BTC"
}
```

**响应示例**:
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "strategy_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_date": "2023-11-01T00:00:00",
  "end_date": "2023-12-01T00:00:00",
  "initial_capital": 100000.0,
  "final_capital": 105000.0,
  "total_return": 0.05,
  "sharpe_ratio": 1.25,
  "max_drawdown": -0.03,
  "win_rate": 0.65,
  "total_trades": 20,
  "created_at": "2026-02-07T10:00:00"
}
```

#### GET /api/backtest/results
获取回测结果列表

**查询参数**:
- `strategy_id`: 策略ID (可选)
- `limit`: 返回记录数 (默认: 10)

#### GET /api/backtest/results/{result_id}
获取回测结果详情

#### GET /api/backtest/results/{result_id}/trades
获取交易记录

#### GET /api/backtest/results/{result_id}/daily-pnl
获取每日盈亏

#### DELETE /api/backtest/results/{result_id}
删除回测结果

### 数据和分析 (/api/data)

#### GET /api/data/options-chain
获取期权链数据

**查询参数**:
- `currency`: 货币类型 (默认: "BTC")
- `kind`: 合约类型 (默认: "option")

#### POST /api/data/calculate-greeks
计算期权希腊字母

**请求体**:
```json
{
  "spot_price": 40000.0,
  "strike_price": 42000.0,
  "time_to_expiry": 0.25,
  "volatility": 0.8,
  "risk_free_rate": 0.05,
  "option_type": "call"
}
```

**响应示例**:
```json
{
  "delta": 0.4523,
  "gamma": 0.000012,
  "theta": -15.23,
  "vega": 125.45,
  "rho": 45.67,
  "price": 2345.67
}
```

#### GET /api/data/underlying-price/{symbol}
获取标的资产当前价格

#### GET /api/data/volatility-surface/{currency}
获取波动率曲面数据

## 使用示例

### Python示例

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. 创建策略
strategy_data = {
    "name": "买入看涨期权",
    "strategy_type": "single_leg",
    "legs": [...]
}
response = requests.post(f"{BASE_URL}/api/strategies/", json=strategy_data)
strategy = response.json()

# 2. 运行回测
backtest_data = {
    "strategy_id": strategy["id"],
    "start_date": "2023-11-01T00:00:00",
    "end_date": "2023-12-01T00:00:00",
    "initial_capital": 100000.0
}
response = requests.post(f"{BASE_URL}/api/backtest/run", json=backtest_data)
result = response.json()

# 3. 获取回测结果
response = requests.get(f"{BASE_URL}/api/backtest/results/{result['id']}")
print(response.json())
```

完整示例请参考: `examples/test_api_usage.py`

### cURL示例

```bash
# 健康检查
curl http://localhost:8000/health

# 获取策略模板
curl http://localhost:8000/api/strategies/templates/list

# 计算希腊字母
curl -X POST http://localhost:8000/api/data/calculate-greeks \
  -H "Content-Type: application/json" \
  -d '{
    "spot_price": 40000.0,
    "strike_price": 42000.0,
    "time_to_expiry": 0.25,
    "volatility": 0.8,
    "option_type": "call"
  }'
```

## 错误处理

API使用标准HTTP状态码:

- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

错误响应格式:
```json
{
  "detail": "错误描述信息"
}
```

## 性能优化

- 使用连接池管理数据库连接
- 支持异步请求处理
- 实现请求限流和重试机制
- 数据库查询优化和索引

## 安全性

- CORS配置（生产环境需限制域名）
- 输入数据验证（Pydantic）
- SQL注入防护（ORM参数化查询）
- 错误信息脱敏

## 开发和调试

### 开发模式

```bash
# 启用自动重载
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

### 查看日志

日志文件位置: `logs/app.log`

### 数据库管理

```bash
# 初始化数据库
python src/storage/init_db.py init

# 重置数据库
python src/storage/init_db.py reset

# 删除所有表
python src/storage/init_db.py drop
```

## 部署

### Docker部署

```bash
# 构建镜像
docker build -t btc-options-api .

# 运行容器
docker run -p 8000:8000 \
  -e POSTGRES_HOST=db \
  -e POSTGRES_PASSWORD=password \
  btc-options-api
```

### 生产环境配置

1. 使用环境变量配置敏感信息
2. 启用HTTPS
3. 配置反向代理（Nginx）
4. 设置日志轮转
5. 配置监控和告警

## 支持

如有问题，请参考:
- 项目README: `BTCOptionsTrading/README.md`
- 设计文档: `.kiro/specs/btc-options-trading-system/design.md`
- 进度文档: `BTCOptionsTrading/PROGRESS.md`
