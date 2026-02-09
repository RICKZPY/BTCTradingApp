# Deribit连接器使用示例

本目录包含Deribit API连接器的使用示例。

## 测试连接

运行以下命令测试Deribit API连接：

```bash
cd BTCOptionsTrading/backend
python examples/test_deribit_connection.py
```

**注意**: 此示例使用Deribit测试环境（test.deribit.com），不需要API密钥即可访问公开数据。

## 功能演示

示例脚本演示了以下功能：

1. **获取期权链数据** - 获取所有可用的BTC期权合约
2. **获取实时市场数据** - 获取特定合约的实时价格和交易量
3. **获取历史数据** - 获取合约的历史价格数据
4. **构建波动率曲面** - 从期权数据构建隐含波动率曲面

## 配置

连接器配置在 `.env` 文件中设置：

```env
# Deribit API配置
DERIBIT_TEST_MODE=true
DERIBIT_BASE_URL=https://test.deribit.com
DERIBIT_WS_URL=wss://test.deribit.com/ws/api/v2
DERIBIT_API_KEY=
DERIBIT_API_SECRET=

# API限制
DERIBIT_RATE_LIMIT=20
DERIBIT_RATE_WINDOW=1
DERIBIT_MAX_RETRIES=3
DERIBIT_RETRY_DELAY=1.0
```

## 生产环境

要在生产环境中使用：

1. 在Deribit官网注册账户并获取API密钥
2. 设置环境变量：
   ```env
   DERIBIT_TEST_MODE=false
   DERIBIT_BASE_URL=https://www.deribit.com
   DERIBIT_WS_URL=wss://www.deribit.com/ws/api/v2
   DERIBIT_API_KEY=your_api_key
   DERIBIT_API_SECRET=your_api_secret
   ```
3. 使用认证方法：
   ```python
   connector = DeribitConnector()
   await connector.authenticate(api_key, api_secret)
   ```

## API限流

连接器内置了限流机制，默认配置为每秒最多20个请求。如果超过限制，请求会自动排队等待。

## 错误处理

连接器实现了自动重试机制：
- 网络错误：最多重试3次，使用指数退避策略
- API错误：记录错误并抛出APIConnectionError异常
- 数据解析错误：记录警告并跳过无效数据
