# Deribit 环境配置说明

## 测试网 vs 生产网

Deribit 提供两个环境：

### 测试网（Testnet）
- URL: `https://test.deribit.com`
- 用途：开发和测试
- 数据：模拟数据，不是真实市场
- API Key：测试网专用，免费获取
- 特点：
  - 可以免费获取测试币
  - 可以模拟交易
  - 数据可能不完整或不准确
  - 适合开发和测试策略

### 生产网（Production）
- URL: `https://www.deribit.com`
- 用途：真实交易和数据采集
- 数据：真实市场数据
- API Key：需要注册真实账户
- 特点：
  - 真实的市场数据
  - 真实的交易（需要资金）
  - 完整准确的历史数据
  - 适合生产环境

## 配置切换

### 方法 1：修改 .env 文件

编辑 `backend/.env` 文件：

**使用生产网（推荐用于数据采集）：**
```bash
DERIBIT_TEST_MODE=false
DERIBIT_BASE_URL="https://www.deribit.com"
DERIBIT_WS_URL="wss://www.deribit.com/ws/api/v2"
DERIBIT_API_KEY=""  # 只读数据不需要 API Key
DERIBIT_API_SECRET=""
```

**使用测试网（用于开发测试）：**
```bash
DERIBIT_TEST_MODE=true
DERIBIT_BASE_URL="https://test.deribit.com"
DERIBIT_WS_URL="wss://test.deribit.com/ws/api/v2"
DERIBIT_API_KEY="your_test_api_key"
DERIBIT_API_SECRET="your_test_api_secret"
```

### 方法 2：使用环境变量

在运行脚本时临时覆盖：

```bash
# 使用生产网
DERIBIT_TEST_MODE=false DERIBIT_BASE_URL="https://www.deribit.com" python3 daily_data_collector.py --currency BTC

# 使用测试网
DERIBIT_TEST_MODE=true DERIBIT_BASE_URL="https://test.deribit.com" python3 daily_data_collector.py --currency BTC
```

## API Key 说明

### 公开 API（只读）
- 不需要 API Key
- 可以获取市场数据
- 不能进行交易
- 适合数据采集

### 私有 API（需要认证）
- 需要 API Key 和 Secret
- 可以进行交易
- 可以查看账户信息
- 需要在 Deribit 网站注册并创建 API Key

## 数据采集建议

### 历史数据采集
- **推荐使用生产网**
- 数据更完整准确
- 反映真实市场情况

### 策略开发测试
- **推荐使用测试网**
- 可以安全测试策略
- 不会影响真实资金

### 实盘交易
- **必须使用生产网**
- 需要真实 API Key
- 需要账户资金

## 当前配置检查

运行以下命令检查当前配置：

```bash
cd backend
python3 -c "from src.config.settings import settings; print(f'Test Mode: {settings.deribit.test_mode}'); print(f'Base URL: {settings.deribit.base_url}')"
```

## 切换到生产网步骤

1. 备份当前 .env 文件：
```bash
cp backend/.env backend/.env.backup
```

2. 修改 .env 文件：
```bash
cd backend
nano .env  # 或使用其他编辑器
```

3. 修改以下行：
```
DERIBIT_TEST_MODE=false
DERIBIT_BASE_URL="https://www.deribit.com"
DERIBIT_WS_URL="wss://www.deribit.com/ws/api/v2"
```

4. 保存并测试：
```bash
python3 daily_data_collector.py --currency BTC
```

5. 检查日志确认使用正确的 URL：
```bash
tail -f logs/daily_collection.log
```

## 注意事项

1. **数据采集不需要 API Key**
   - 公开市场数据可以直接访问
   - API Key 留空即可

2. **测试网数据不可靠**
   - 仅用于开发测试
   - 不要用于生产数据分析

3. **生产网有速率限制**
   - 默认 20 请求/秒
   - 超过限制会被暂时封禁
   - 代码已实现自动限流

4. **服务器配置**
   - 确保服务器上的 .env 也已更新
   - 重启相关服务使配置生效
