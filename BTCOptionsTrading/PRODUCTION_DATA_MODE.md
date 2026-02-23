# 生产环境数据模式配置指南

## 概述

本文档说明如何在生产环境中禁用所有模拟数据，确保系统只使用真实数据。

## 配置方法

### 1. 后端配置

在 `.env` 文件中添加以下配置：

```bash
# 数据模式配置
ENVIRONMENT=production
USE_MOCK_DATA=false
STRICT_DATA_MODE=true  # 启用严格模式，数据获取失败时抛出错误而不是降级到模拟数据
```

### 2. 前端配置

在 `frontend/.env.production` 文件中添加：

```bash
VITE_ENVIRONMENT=production
VITE_USE_MOCK_DATA=false
VITE_STRICT_DATA_MODE=true
```

## 受影响的组件

### 后端组件

1. **回测引擎** (`src/backtest/backtest_engine.py`)
   - 默认使用历史数据
   - 如果历史数据不可用，抛出错误

2. **API路由** (`src/api/routes/`)
   - 所有数据端点在无法获取真实数据时抛出错误
   - 不再返回模拟数据作为降级

### 前端组件

1. **期权链Tab** (`frontend/src/components/tabs/OptionsChainTab.tsx`)
   - 移除模拟数据生成
   - 数据加载失败时显示错误消息

2. **策略管理Tab** (`frontend/src/components/tabs/StrategiesTab.tsx`)
   - 移除模拟期权数据生成
   - 要求用户手动输入或等待真实数据

3. **策略创建向导** (`frontend/src/components/strategy/Step2_ParameterConfig.tsx`)
   - 移除模拟数据降级
   - 显示明确的错误消息

## 实施步骤

### 步骤1: 更新后端配置类

修改 `src/config/settings.py`，添加数据模式配置：

```python
class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # 数据模式配置
    environment: str = Field(default="development", env="ENVIRONMENT")
    use_mock_data: bool = Field(default=True, env="USE_MOCK_DATA")
    strict_data_mode: bool = Field(default=False, env="STRICT_DATA_MODE")
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def should_use_mock_data(self) -> bool:
        # 生产环境永远不使用模拟数据
        if self.is_production:
            return False
        return self.use_mock_data
```

### 步骤2: 更新回测引擎

修改 `src/backtest/backtest_engine.py`：

```python
def __init__(
    self,
    options_engine: OptionsEngine = None,
    use_historical_data: bool = None,  # None表示根据配置决定
    historical_data_manager: HistoricalDataManager = None
):
    self.options_engine = options_engine or OptionsEngine()
    
    # 根据环境配置决定是否使用历史数据
    settings = Settings()
    if use_historical_data is None:
        use_historical_data = settings.is_production or not settings.should_use_mock_data
    
    self.use_historical_data = use_historical_data
    self.strict_mode = settings.strict_data_mode
    
    # 在严格模式下，必须提供历史数据管理器
    if self.use_historical_data and self.strict_mode and historical_data_manager is None:
        raise ValueError("Strict mode requires historical_data_manager")
    
    self.historical_data_manager = historical_data_manager
```

### 步骤3: 更新API路由

修改 `src/api/routes/data.py`，添加严格模式检查：

```python
from src.config.settings import Settings

settings = Settings()

@router.get("/options-chain")
async def get_options_chain(
    currency: str = "BTC",
    expired: bool = False
):
    """获取期权链数据"""
    try:
        connector = DeribitConnector()
        contracts = await connector.get_options_chain(currency)
        
        if not contracts:
            if settings.strict_data_mode:
                raise HTTPException(
                    status_code=503,
                    detail="No options data available from exchange"
                )
            # 非严格模式可以返回空列表
            return []
        
        return [contract.dict() for contract in contracts]
        
    except Exception as e:
        if settings.strict_data_mode:
            raise HTTPException(status_code=503, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))
```

### 步骤4: 更新前端组件

修改 `frontend/src/components/tabs/OptionsChainTab.tsx`：

```typescript
const loadOptionsChain = async () => {
  setIsLoading(true)
  setError(null)
  
  try {
    const response = await fetch(`/api/data/options-chain?currency=${currency}`)
    
    if (!response.ok) {
      if (response.status === 503) {
        throw new Error('交易所数据暂时不可用，请稍后重试')
      }
      throw new Error('加载期权链失败')
    }
    
    const data = await response.json()
    
    if (!data || data.length === 0) {
      throw new Error('没有可用的期权数据')
    }
    
    // 处理真实数据
    processOptionsData(data)
    
  } catch (error) {
    console.error('加载期权链失败:', error)
    setError(error.message)
    
    // 生产环境不使用模拟数据
    if (import.meta.env.VITE_ENVIRONMENT === 'production') {
      // 显示错误，不降级到模拟数据
      setOptionsData([])
    } else {
      // 开发环境可以使用模拟数据
      if (import.meta.env.VITE_USE_MOCK_DATA !== 'false') {
        generateMockData()
      }
    }
  } finally {
    setIsLoading(false)
  }
}
```

## 错误处理

### 生产环境错误消息

当数据不可用时，系统会显示清晰的错误消息：

**后端错误响应**:
```json
{
  "detail": "No options data available from exchange",
  "status_code": 503,
  "error_type": "ServiceUnavailable"
}
```

**前端错误显示**:
```
⚠️ 数据暂时不可用
交易所数据暂时不可用，请稍后重试。
如果问题持续存在，请联系技术支持。
```

## 监控和告警

### 建议的监控指标

1. **数据获取失败率**
   - 监控API调用失败的频率
   - 设置告警阈值（如 > 5%）

2. **数据延迟**
   - 监控数据更新的延迟
   - 设置告警阈值（如 > 30秒）

3. **数据完整性**
   - 监控返回的数据是否完整
   - 检查必需字段是否存在

### 日志记录

在生产环境中，所有数据获取失败都会被记录：

```python
logger.error(
    "Failed to fetch options data",
    extra={
        "currency": currency,
        "error": str(e),
        "timestamp": datetime.now().isoformat(),
        "environment": "production"
    }
)
```

## 测试

### 测试生产模式

1. **设置环境变量**:
```bash
export ENVIRONMENT=production
export STRICT_DATA_MODE=true
```

2. **运行测试**:
```bash
# 测试应该在没有真实数据时失败
python -m pytest tests/ -k "not mock"
```

3. **验证行为**:
   - 确认没有模拟数据被使用
   - 确认错误被正确抛出
   - 确认错误消息清晰明确

## 迁移清单

- [ ] 更新 `.env` 文件，添加生产环境配置
- [ ] 更新 `Settings` 类，添加数据模式配置
- [ ] 更新回测引擎，支持严格模式
- [ ] 更新所有API路由，移除模拟数据降级
- [ ] 更新前端组件，移除模拟数据生成
- [ ] 添加错误处理和用户友好的错误消息
- [ ] 配置监控和告警
- [ ] 测试生产模式行为
- [ ] 更新文档和部署指南

## 回滚计划

如果需要临时启用模拟数据（如紧急情况）：

```bash
# 临时启用模拟数据
export USE_MOCK_DATA=true
export STRICT_DATA_MODE=false

# 重启服务
systemctl restart btc-options-api
```

## 常见问题

### Q: 如何在开发环境中测试生产模式？

A: 设置环境变量：
```bash
ENVIRONMENT=production STRICT_DATA_MODE=true npm run dev
```

### Q: 数据获取失败时用户会看到什么？

A: 用户会看到清晰的错误消息，说明数据暂时不可用，并建议稍后重试。

### Q: 如何确保不会意外使用模拟数据？

A: 在生产环境中，`is_production` 检查会强制禁用所有模拟数据，即使配置错误。

## 相关文档

- [API配置指南](API_CONFIGURATION_GUIDE.md)
- [部署指南](deploy/DEPLOYMENT_GUIDE.md)
- [监控指南](MONITORING_GUIDE.md)
