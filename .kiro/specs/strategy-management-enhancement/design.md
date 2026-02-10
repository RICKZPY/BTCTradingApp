# 设计文档 - 策略管理页面增强

## 概述

本设计文档描述了BTC期权交易回测系统策略管理页面的全面增强方案。主要目标是提升用户体验、增强功能完整性，并实现与实时市场数据的深度集成。

设计遵循以下原则：
- **渐进式增强**: 保持现有功能的同时逐步添加新功能
- **数据驱动**: 与Deribit API深度集成，提供实时市场数据
- **用户友好**: 提供清晰的指引和智能的默认值
- **性能优化**: 使用缓存和WebSocket减少API调用

## 架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层 (React)                         │
├─────────────────────────────────────────────────────────────┤
│  StrategiesTab (主组件)                                       │
│  ├── StrategyList (策略列表)                                  │
│  │   ├── StrategyCard (策略卡片)                             │
│  │   ├── SearchBar (搜索栏)                                  │
│  │   └── FilterPanel (筛选面板)                              │
│  ├── StrategyDetailModal (详情模态框)                         │
│  ├── StrategyWizard (创建向导)                                │
│  │   ├── Step1_TemplateSelection (选择模板)                  │
│  │   ├── Step2_ParameterConfig (配置参数)                    │
│  │   │   └── StrikePicker (执行价选择器)                     │
│  │   └── Step3_Confirmation (确认创建)                       │
│  └── StrategyEditModal (编辑模态框)                           │
└─────────────────────────────────────────────────────────────┘
                              ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                        后端层 (FastAPI)                       │
├─────────────────────────────────────────────────────────────┤
│  API路由层                                                    │
│  ├── /api/strategies/* (策略CRUD)                            │
│  ├── /api/data/options-chain (期权链)                        │
│  ├── /api/data/underlying-price (标的价格)                   │
│  └── /ws (WebSocket实时推送)                                 │
├─────────────────────────────────────────────────────────────┤
│  业务逻辑层                                                   │
│  ├── StrategyManager (策略管理器)                            │
│  ├── StrategyValidator (策略验证器)                          │
│  ├── RiskCalculator (风险计算器)                             │
│  └── MarketDataCache (市场数据缓存)                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    外部服务 (Deribit API)                     │
│  ├── 期权链数据                                               │
│  ├── 实时价格                                                 │
│  └── 希腊字母                                                 │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

1. **策略创建流程**:
   ```
   用户选择模板 → 加载期权链 → 选择执行价 → 验证参数 → 计算风险 → 保存策略
   ```

2. **实时数据更新流程**:
   ```
   WebSocket连接 → 接收价格更新 → 更新策略市场价值 → 刷新UI
   ```

3. **策略编辑流程**:
   ```
   加载策略详情 → 预填充表单 → 用户修改 → 验证更改 → 更新数据库
   ```

## 组件和接口

### 前端组件

#### 1. StrategyWizard (策略创建向导)

**职责**: 引导用户分步创建策略

**Props**:
```typescript
interface StrategyWizardProps {
  isOpen: boolean
  onClose: () => void
  onComplete: (strategy: Strategy) => void
  initialTemplate?: string
}
```

**State**:
```typescript
interface WizardState {
  currentStep: 1 | 2 | 3
  selectedTemplate: string
  formData: StrategyFormData
  optionsChain: OptionChainData[]
  underlyingPrice: number
  isLoadingMarketData: boolean
  validationErrors: Record<string, string>
}
```

**关键方法**:
- `loadOptionsChain(expiryDate: string)`: 加载期权链数据
- `validateStep(step: number)`: 验证当前步骤
- `calculateRisk()`: 计算策略风险指标
- `submitStrategy()`: 提交创建策略

#### 2. StrikePicker (执行价选择器)

**职责**: 从期权链中选择执行价

**Props**:
```typescript
interface StrikePickerProps {
  optionsChain: OptionChainData[]
  underlyingPrice: number
  optionType: 'call' | 'put'
  value: number
  onChange: (strike: number, optionData: OptionData) => void
}
```

**功能**:
- 显示所有可用执行价
- 高亮ATM期权
- 显示每个执行价的价格和IV
- 支持键盘导航

#### 3. StrategyDetailModal (策略详情模态框)

**职责**: 显示策略完整信息

**Props**:
```typescript
interface StrategyDetailModalProps {
  strategy: Strategy
  isOpen: boolean
  onClose: () => void
  onEdit: () => void
  onDelete: () => void
  onDuplicate: () => void
}
```

**显示内容**:
- 策略基本信息（名称、类型、创建时间）
- 所有策略腿的详细配置
- 风险指标（最大收益、最大损失、盈亏平衡点）
- 当前市场价值和未实现盈亏
- 希腊字母汇总

#### 4. StrategyCard (策略卡片)

**职责**: 在列表中展示策略摘要

**Props**:
```typescript
interface StrategyCardProps {
  strategy: Strategy
  marketValue?: number
  unrealizedPnL?: number
  onClick: () => void
  onDelete: () => void
  isSelected?: boolean
  onSelect?: (selected: boolean) => void
}
```

**显示内容**:
- 策略名称和类型
- 创建时间
- 最大收益/损失
- 当前市场价值（如果可用）
- 未实现盈亏（如果可用）

### 后端API接口

#### 1. 策略更新接口

```python
@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: UUID,
    request: StrategyUpdateRequest,
    db: Session = Depends(get_db)
):
    """更新策略"""
```

**请求模型**:
```python
class StrategyUpdateRequest(BaseModel):
    name: Optional[str]
    description: Optional[str]
    legs: Optional[List[StrategyLegRequest]]
```

#### 2. 策略验证接口

```python
@router.post("/validate", response_model=ValidationResponse)
async def validate_strategy(
    request: StrategyCreateRequest
):
    """验证策略配置"""
```

**响应模型**:
```python
class ValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    risk_metrics: RiskMetrics
```

#### 3. 期权链增强接口

```python
@router.get("/options-chain-enhanced")
async def get_options_chain_enhanced(
    currency: str = "BTC",
    expiry_date: Optional[str] = None
):
    """获取增强的期权链数据（按到期日分组）"""
```

**响应格式**:
```json
{
  "underlying_price": 45000,
  "expiry_dates": [
    {
      "date": "2024-03-29",
      "days_to_expiry": 7,
      "options": [
        {
          "strike": 44000,
          "call": {
            "price": 1200,
            "iv": 0.75,
            "delta": 0.65,
            "volume": 150
          },
          "put": {
            "price": 180,
            "iv": 0.72,
            "delta": -0.35,
            "volume": 200
          }
        }
      ]
    }
  ]
}
```

#### 4. 策略风险计算接口

```python
@router.post("/calculate-risk", response_model=RiskMetricsResponse)
async def calculate_strategy_risk(
    request: StrategyRiskRequest
):
    """计算策略风险指标"""
```

**响应模型**:
```python
class RiskMetricsResponse(BaseModel):
    max_profit: float
    max_loss: float
    breakeven_points: List[float]
    total_delta: float
    total_gamma: float
    total_theta: float
    total_vega: float
    initial_cost: float
    risk_reward_ratio: float
```

#### 5. 批量操作接口

```python
@router.post("/batch-delete")
async def batch_delete_strategies(
    strategy_ids: List[UUID],
    db: Session = Depends(get_db)
):
    """批量删除策略"""

@router.post("/batch-export")
async def batch_export_strategies(
    strategy_ids: List[UUID],
    db: Session = Depends(get_db)
):
    """批量导出策略"""
```

### 数据模型

#### 策略表单数据

```typescript
interface StrategyFormData {
  name: string
  description: string
  strategy_type: string
  expiry_date: string
  quantity: number
  
  // 单腿策略
  strike?: number
  option_type?: 'call' | 'put'
  action?: 'buy' | 'sell'
  
  // 跨式策略
  straddle_strike?: number
  
  // 宽跨式策略
  call_strike?: number
  put_strike?: number
  
  // 铁鹰策略
  iron_condor_strikes?: [number, number, number, number]
  
  // 蝶式策略
  butterfly_center?: number
  butterfly_wing_width?: number
}
```

#### 期权链数据

```typescript
interface OptionChainData {
  strike: number
  call: OptionData
  put: OptionData
}

interface OptionData {
  price: number
  bid: number
  ask: number
  iv: number
  delta: number
  gamma: number
  theta: number
  vega: number
  volume: number
  open_interest: number
  instrument_name: string
}
```

#### 策略详情

```typescript
interface StrategyDetail extends Strategy {
  legs: StrategyLegDetail[]
  risk_metrics: RiskMetrics
  market_value?: number
  unrealized_pnl?: number
}

interface StrategyLegDetail {
  option_contract: OptionContract
  action: 'buy' | 'sell'
  quantity: number
  entry_price: number
  current_price?: number
  pnl?: number
}

interface RiskMetrics {
  max_profit: number
  max_loss: number
  breakeven_points: number[]
  total_delta: number
  total_gamma: number
  total_theta: number
  total_vega: number
  initial_cost: number
  risk_reward_ratio: number
}
```

## 数据模型

### 数据库模式更新

需要在策略表中添加以下字段：

```sql
ALTER TABLE strategies ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE strategies ADD COLUMN market_value DECIMAL(20, 8);
ALTER TABLE strategies ADD COLUMN unrealized_pnl DECIMAL(20, 8);
ALTER TABLE strategies ADD COLUMN last_price_update TIMESTAMP;
```

### 缓存策略

使用Redis缓存期权链数据：

```python
# 缓存键格式
options_chain:{currency}:{expiry_date}

# 缓存时间
TTL = 300  # 5分钟
```

## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的正式陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### 属性 1: 策略更新保持一致性

*对于任何*有效的策略和更新请求，更新操作后从数据库检索的策略应该反映所有请求的更改，并且未更新的字段应该保持不变。

**验证: 需求 1.3**

### 属性 2: 策略详情显示完整性

*对于任何*策略，详情视图应该显示所有必需的信息，包括基本信息（名称、描述、类型、创建时间）、所有策略腿的配置、以及完整的风险指标（最大收益、最大损失、盈亏平衡点、希腊字母汇总、初始成本）。

**验证: 需求 2.2, 2.3, 2.4, 14.1, 14.2, 14.3, 14.4, 14.5**

### 属性 3: 期权链数据完整性

*对于任何*给定的到期日和货币，从API获取的期权链应该包含该到期日所有可用的执行价，并且每个执行价都应该同时包含看涨和看跌期权的完整市场数据（价格、隐含波动率、希腊字母）。

**验证: 需求 3.1, 4.2, 4.5**

### 属性 4: 风险计算准确性

*对于任何*策略配置，计算的最大收益、最大损失和盈亏平衡点应该与基于Black-Scholes模型的理论值一致，误差不超过0.01%。

**验证: 需求 7.4, 14.3**

### 属性 5: 实时价格更新及时性

*对于任何*通过WebSocket接收的价格更新，策略的市场价值和未实现盈亏应该在1秒内更新，并且更新后的值应该基于最新的市场价格准确计算。

**验证: 需求 12.3, 12.1, 12.2**

### 属性 6: 批量操作原子性

*对于任何*批量删除操作，要么所有选中的策略都被成功删除，要么在发生错误时没有任何策略被删除（全部成功或全部失败）。

**验证: 需求 10.4**

### 属性 7: 策略导入导出往返一致性

*对于任何*策略，导出为JSON然后重新导入应该产生一个等价的策略，所有业务字段（名称、描述、类型、腿配置）应该完全相同（除了系统生成的ID和时间戳字段）。

**验证: 需求 11.1, 11.3**

### 属性 8: 搜索结果完整性和准确性

*对于任何*搜索关键词，返回的策略列表应该包含且仅包含名称或描述中包含该关键词的所有策略（不区分大小写）。

**验证: 需求 9.2**

### 属性 9: 策略复制完整性

*对于任何*策略，复制操作应该创建一个新策略，该策略包含原策略的所有腿配置和参数，名称添加"(副本)"后缀，并且修改复制的策略不应该影响原策略。

**验证: 需求 8.2, 8.3, 8.5**

### 属性 10: 参数验证完整性

*对于任何*不合理的策略配置（如宽跨式的看涨执行价低于看跌执行价、铁鹰策略的执行价顺序错误、负数数量等），验证器应该检测到错误并返回清晰的错误消息，阻止策略创建。

**验证: 需求 7.1, 7.3**

### 属性 11: ATM识别准确性

*对于任何*期权链和标的价格，标记为ATM的期权应该是执行价与标的价格差距最小的期权（对于BTC阈值为1000，对于ETH阈值为50）。

**验证: 需求 4.3, 13.2**

### 属性 12: 排序功能正确性

*对于任何*排序选项（创建时间、最大收益、最大损失），排序后的策略列表应该按照指定字段的升序或降序正确排列。

**验证: 需求 9.4, 9.5**

### 属性 13: 名称冲突处理

*对于任何*导入的策略，如果其名称与现有策略冲突，系统应该自动添加数字后缀（如"策略名(1)"、"策略名(2)"），确保所有策略名称唯一。

**验证: 需求 11.4**

## 错误处理

### 错误类型

1. **网络错误**
   - Deribit API不可用
   - WebSocket连接断开
   - 超时错误

2. **数据验证错误**
   - 无效的执行价
   - 不合理的策略配置
   - 缺少必填字段

3. **业务逻辑错误**
   - 策略不存在
   - 权限不足
   - 并发冲突

### 错误处理策略

```typescript
// 前端错误处理
class StrategyError extends Error {
  constructor(
    message: string,
    public code: string,
    public recoverable: boolean = true
  ) {
    super(message)
  }
}

// 错误恢复策略
const errorRecoveryStrategies = {
  NETWORK_ERROR: {
    retry: true,
    maxRetries: 3,
    fallback: 'use_cached_data'
  },
  VALIDATION_ERROR: {
    retry: false,
    showUserMessage: true
  },
  API_ERROR: {
    retry: true,
    maxRetries: 2,
    fallback: 'use_mock_data'
  }
}
```

### 降级策略

当Deribit API不可用时：

1. **期权链数据**: 使用缓存数据（如果可用）或生成模拟数据
2. **实时价格**: 显示"数据不可用"提示，禁用依赖实时数据的功能
3. **策略创建**: 允许手动输入价格，但显示警告

## 测试策略

### 单元测试

**前端组件测试**:
- StrategyWizard: 测试步骤导航、表单验证、数据提交
- StrikePicker: 测试选项渲染、ATM高亮、选择回调
- StrategyCard: 测试数据显示、点击事件、选择状态

**后端API测试**:
- 策略CRUD操作
- 风险计算准确性
- 批量操作事务性
- 导入导出往返一致性

### 集成测试

1. **端到端策略创建流程**
   - 选择模板 → 加载期权链 → 选择执行价 → 提交创建
   
2. **实时数据更新流程**
   - 建立WebSocket连接 → 接收价格更新 → 验证UI更新

3. **策略编辑流程**
   - 加载策略 → 修改参数 → 保存更改 → 验证更新

### 属性测试

使用属性测试验证正确性属性：

```python
# 示例：测试属性1 - 策略更新保持一致性
@given(
    strategy_id=st.uuids(),
    update_data=st.builds(StrategyUpdateRequest)
)
async def test_strategy_update_consistency(strategy_id, update_data):
    # 创建初始策略
    original = await create_test_strategy()
    
    # 更新策略
    await update_strategy(original.id, update_data)
    
    # 验证更新
    updated = await get_strategy(original.id)
    
    # 检查更新的字段
    if update_data.name:
        assert updated.name == update_data.name
    
    # 检查未更新的字段保持不变
    assert updated.id == original.id
    assert updated.created_at == original.created_at
```

### 性能测试

1. **加载时间测试**
   - 策略列表加载（100个策略）< 2秒
   - 期权链加载 < 3秒
   - 搜索响应 < 500ms

2. **并发测试**
   - 10个并发用户同时创建策略
   - 验证数据一致性和响应时间

3. **WebSocket性能**
   - 测试1000次价格更新的延迟
   - 验证UI更新不阻塞主线程

## 实现计划

### 阶段 1: 核心功能增强（优先级：高）

1. 策略编辑功能
2. 策略详情查看
3. 实时市场数据集成
4. 智能执行价选择器

### 阶段 2: 用户体验优化（优先级：中）

5. 策略创建向导
6. 策略模板增强
7. 策略验证和风险提示
8. 策略复制功能

### 阶段 3: 高级功能（优先级：中）

9. 策略搜索和筛选
10. 批量操作
11. 策略导入导出
12. 实时价格更新

### 阶段 4: 扩展功能（优先级：低）

13. 快速创建常用策略
14. 策略性能指标
15. 移动端响应式设计

## 技术栈

### 前端

- **React 18**: UI框架
- **TypeScript**: 类型安全
- **TailwindCSS**: 样式
- **React Hook Form**: 表单管理
- **Zod**: 表单验证
- **SWR**: 数据获取和缓存
- **WebSocket**: 实时数据

### 后端

- **FastAPI**: Web框架
- **SQLAlchemy**: ORM
- **Pydantic**: 数据验证
- **Redis**: 缓存
- **WebSocket**: 实时推送
- **httpx**: HTTP客户端

### 测试

- **前端**: Jest, React Testing Library, Cypress
- **后端**: pytest, pytest-asyncio, Hypothesis
- **E2E**: Playwright

## 安全考虑

1. **输入验证**: 所有用户输入必须经过验证
2. **SQL注入防护**: 使用参数化查询
3. **XSS防护**: 对用户输入进行转义
4. **CSRF防护**: 使用CSRF令牌
5. **API限流**: 防止滥用
6. **敏感数据**: 不在前端存储API密钥

## 可访问性

1. **键盘导航**: 所有交互元素支持键盘操作
2. **屏幕阅读器**: 提供ARIA标签
3. **颜色对比**: 符合WCAG 2.1 AA标准
4. **焦点指示**: 清晰的焦点状态
5. **错误提示**: 可访问的错误消息

## 国际化

虽然当前版本使用中文，但设计应支持未来的国际化：

1. 使用i18n库（如react-i18next）
2. 将所有文本提取到语言文件
3. 支持日期和数字格式化
4. 支持RTL布局（未来）
