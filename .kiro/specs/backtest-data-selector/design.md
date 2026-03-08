# Design Document: Backtest Data Selector

## Overview

回测数据选择器是一个全栈功能，旨在改进用户在配置回测时的体验。该功能通过提供直观的界面展示可用的历史数据信息、数据质量指标，并简化数据选择流程，确保用户始终使用真实的历史数据进行回测。

核心设计理念：
- 数据驱动：所有可选项基于实际可用的历史数据
- 即时反馈：实时显示数据质量和覆盖率信息
- 简化流程：通过智能默认值和预设选项减少用户操作
- 性能优先：使用缓存和防抖技术优化响应速度

## Architecture

系统采用三层架构：

```
┌─────────────────────────────────────────┐
│         Frontend (React)                │
│  ┌───────────────────────────────────┐  │
│  │  BacktestDataSelector Component  │  │
│  │  - DateRangeSelector             │  │
│  │  - InstrumentSelector            │  │
│  │  - DataQualityDisplay            │  │
│  │  - ConfigurationManager          │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
                    │
                    │ HTTP/REST
                    ▼
┌─────────────────────────────────────────┐
│         Backend API Layer               │
│  ┌───────────────────────────────────┐  │
│  │  Backtest Routes                  │  │
│  │  - /api/backtest/available-dates  │  │
│  │  - /api/backtest/available-       │  │
│  │    instruments                    │  │
│  │  - /api/backtest/coverage-stats   │  │
│  │  - /api/backtest/prepare-data     │  │
│  │  - /api/backtest/preview-data     │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         Service Layer                   │
│  ┌───────────────────────────────────┐  │
│  │  HistoricalDataManager (existing) │  │
│  │  - get_available_dates()          │  │
│  │  - get_available_instruments()    │  │
│  │  - get_coverage_stats()           │  │
│  │  - get_data_for_backtest()        │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## Components and Interfaces

### Frontend Components

#### 1. BacktestDataSelector (主组件)

```typescript
interface BacktestDataSelectorProps {
  onStartBacktest: (config: BacktestConfig) => void;
  onCancel?: () => void;
}

interface BacktestConfig {
  dateRange: DateRange;
  instruments: string[];
  configName?: string;
}

interface DateRange {
  startDate: string; // ISO 8601 format
  endDate: string;   // ISO 8601 format
}
```

主要职责：
- 协调子组件
- 管理整体状态
- 处理配置保存/加载
- 触发回测启动

#### 2. DateRangeSelector (日期范围选择器)

```typescript
interface DateRangeSelectorProps {
  availableDates: string[];
  selectedRange: DateRange | null;
  onRangeChange: (range: DateRange) => void;
  presets: DateRangePreset[];
}

interface DateRangePreset {
  label: string;
  days: number;
}
```

功能：
- 显示日历视图，高亮有数据的日期
- 提供预设选项（7天、30天、90天）
- 验证选择的日期范围
- 自动调整到最近的有数据日期

#### 3. InstrumentSelector (合约选择器)

```typescript
interface InstrumentSelectorProps {
  instruments: Instrument[];
  selectedInstruments: string[];
  onSelectionChange: (instruments: string[]) => void;
  dateRange: DateRange | null;
}

interface Instrument {
  symbol: string;
  expiryDate: string;
  type: 'call' | 'put';
  strike: number;
  availableDateRange: DateRange;
}
```

功能：
- 显示可用合约列表
- 支持搜索和过滤
- 多选功能
- 根据日期范围过滤合约

#### 4. DataQualityDisplay (数据质量展示)

```typescript
interface DataQualityDisplayProps {
  coverageStats: CoverageStats | null;
  loading: boolean;
}

interface CoverageStats {
  coveragePercentage: number;
  totalDataPoints: number;
  missingDataPoints: number;
  dateRange: DateRange;
  instrumentCount: number;
}
```

功能：
- 显示数据覆盖率百分比
- 显示缺失数据点数量
- 低覆盖率警告
- 加载状态指示

#### 5. DataPreviewModal (数据预览模态框)

```typescript
interface DataPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  config: BacktestConfig;
}

interface PreviewData {
  totalRecords: number;
  sampleRecords: DataRecord[];
}

interface DataRecord {
  timestamp: string;
  instrument: string;
  price: number;
  volume: number;
}
```

功能：
- 显示数据样本（前10条）
- 显示总记录数
- 提供关闭功能

#### 6. ConfigurationManager (配置管理器)

```typescript
interface SavedConfiguration {
  id: string;
  name: string;
  config: BacktestConfig;
  createdAt: string;
}
```

功能：
- 保存配置到 localStorage
- 加载已保存的配置
- 删除配置
- 显示配置列表

### Backend API Endpoints

#### 1. GET /api/backtest/available-dates

```python
@router.get("/available-dates")
async def get_available_dates() -> AvailableDatesResponse:
    """
    获取所有可用的历史数据日期
    
    Returns:
        AvailableDatesResponse: {
            "dates": ["2024-01-01", "2024-01-02", ...],
            "earliest": "2024-01-01",
            "latest": "2024-12-31"
        }
    """
```

#### 2. GET /api/backtest/available-instruments

```python
@router.get("/available-instruments")
async def get_available_instruments(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> AvailableInstrumentsResponse:
    """
    获取可用的合约列表，可选按日期范围过滤
    
    Args:
        start_date: 开始日期 (ISO 8601)
        end_date: 结束日期 (ISO 8601)
    
    Returns:
        AvailableInstrumentsResponse: {
            "instruments": [
                {
                    "symbol": "BTC-31MAR24-50000-C",
                    "expiry_date": "2024-03-31",
                    "type": "call",
                    "strike": 50000,
                    "available_date_range": {
                        "start": "2024-01-01",
                        "end": "2024-03-31"
                    }
                },
                ...
            ],
            "total_count": 150
        }
    """
```

#### 3. GET /api/backtest/coverage-stats

```python
@router.get("/coverage-stats")
async def get_coverage_stats(
    start_date: str,
    end_date: str,
    instruments: Optional[List[str]] = None
) -> CoverageStatsResponse:
    """
    获取指定日期范围和合约的数据覆盖率统计
    
    Args:
        start_date: 开始日期 (ISO 8601)
        end_date: 结束日期 (ISO 8601)
        instruments: 合约列表（可选）
    
    Returns:
        CoverageStatsResponse: {
            "coverage_percentage": 95.5,
            "total_data_points": 10000,
            "missing_data_points": 450,
            "date_range": {
                "start": "2024-01-01",
                "end": "2024-01-31"
            },
            "instrument_count": 10
        }
    """
```

#### 4. POST /api/backtest/prepare-data

```python
@router.post("/prepare-data")
async def prepare_backtest_data(
    request: PrepareDataRequest
) -> PrepareDataResponse:
    """
    准备回测数据集
    
    Args:
        request: {
            "date_range": {
                "start_date": "2024-01-01",
                "end_date": "2024-01-31"
            },
            "instruments": ["BTC-31MAR24-50000-C", ...]
        }
    
    Returns:
        PrepareDataResponse: {
            "dataset_id": "uuid-string",
            "total_records": 10000,
            "status": "ready"
        }
    """
```

#### 5. GET /api/backtest/preview-data

```python
@router.get("/preview-data")
async def preview_backtest_data(
    start_date: str,
    end_date: str,
    instruments: List[str],
    limit: int = 10
) -> PreviewDataResponse:
    """
    预览回测数据样本
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        instruments: 合约列表
        limit: 返回记录数（默认10）
    
    Returns:
        PreviewDataResponse: {
            "total_records": 10000,
            "sample_records": [
                {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "instrument": "BTC-31MAR24-50000-C",
                    "price": 2500.0,
                    "volume": 100
                },
                ...
            ]
        }
    """
```

### Backend Service Integration

现有的 `HistoricalDataManager` 类已提供所需方法，API 层将直接调用这些方法：

```python
class HistoricalDataManager:
    def get_available_dates(self) -> List[str]:
        """返回所有有数据的日期列表"""
        
    def get_available_instruments(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """返回可用合约列表，可选按日期过滤"""
        
    def get_coverage_stats(
        self,
        start_date: str,
        end_date: str,
        instruments: Optional[List[str]] = None
    ) -> Dict:
        """返回数据覆盖率统计"""
        
    def get_data_for_backtest(
        self,
        start_date: str,
        end_date: str,
        instruments: List[str]
    ) -> pd.DataFrame:
        """返回回测数据集"""
```

## Data Models

### Frontend State Management

```typescript
interface BacktestDataState {
  // 可用数据
  availableDates: string[];
  availableInstruments: Instrument[];
  
  // 用户选择
  selectedDateRange: DateRange | null;
  selectedInstruments: string[];
  
  // 数据质量
  coverageStats: CoverageStats | null;
  
  // UI 状态
  loading: {
    dates: boolean;
    instruments: boolean;
    coverage: boolean;
    preview: boolean;
  };
  
  errors: {
    dates: string | null;
    instruments: string | null;
    coverage: string | null;
    preview: string | null;
  };
  
  // 预览
  previewData: PreviewData | null;
  showPreview: boolean;
  
  // 配置管理
  savedConfigurations: SavedConfiguration[];
  currentConfigName: string;
}
```

### Backend Data Models

```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class DateRange(BaseModel):
    start_date: str
    end_date: str

class Instrument(BaseModel):
    symbol: str
    expiry_date: str
    type: str  # 'call' or 'put'
    strike: float
    available_date_range: DateRange

class AvailableDatesResponse(BaseModel):
    dates: List[str]
    earliest: str
    latest: str

class AvailableInstrumentsResponse(BaseModel):
    instruments: List[Instrument]
    total_count: int

class CoverageStatsResponse(BaseModel):
    coverage_percentage: float
    total_data_points: int
    missing_data_points: int
    date_range: DateRange
    instrument_count: int

class PrepareDataRequest(BaseModel):
    date_range: DateRange
    instruments: List[str]

class PrepareDataResponse(BaseModel):
    dataset_id: str
    total_records: int
    status: str

class DataRecord(BaseModel):
    timestamp: str
    instrument: str
    price: float
    volume: int

class PreviewDataResponse(BaseModel):
    total_records: int
    sample_records: List[DataRecord]
```

## Correctness Properties

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的正式陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*


### Property Reflection

在编写具体属性之前，让我审查 prework 中识别的所有属性，消除冗余：

**识别的冗余：**
- 属性 1.3（显示最早和最晚日期）和 1.4（显示合约数量）都是关于正确显示数据的，但它们测试不同的数据类型，保留两者
- 属性 2.2（显示覆盖率百分比）和 2.3（显示缺失数据点）都是关于显示统计数据，可以合并为一个综合属性
- 属性 4.1（显示合约信息）和 6.3（显示预览数据字段）都是关于显示必需字段，但应用于不同的上下文，保留两者
- 属性 7.2（保存配置）和 7.4（加载配置）是往返属性的两部分，应该合并为一个往返属性
- 属性 10.1、10.2、10.3 都是性能测试，但测试不同的操作，保留所有

**合并决策：**
1. 合并 2.2 和 2.3 为"覆盖率统计完整显示"属性
2. 合并 7.2 和 7.4 为"配置保存加载往返"属性

### Core Properties

**Property 1: 日期范围显示正确性**
*For any* 返回的可用日期列表，组件显示的最早日期应该等于列表中的最小日期，最晚日期应该等于列表中的最大日期
**Validates: Requirements 1.3**

**Property 2: 合约数量显示一致性**
*For any* 返回的合约列表，组件显示的合约数量应该等于列表的实际长度
**Validates: Requirements 1.4**

**Property 3: 日期范围变更触发覆盖率查询**
*For any* 有效的日期范围选择，组件应该调用覆盖率统计 API 并传递正确的日期参数
**Validates: Requirements 2.1**

**Property 4: 覆盖率统计完整显示**
*For any* 返回的覆盖率统计数据，组件应该显示所有关键指标（覆盖率百分比、总数据点、缺失数据点）
**Validates: Requirements 2.2, 2.3**

**Property 5: 日历高亮正确性**
*For any* 可用日期列表，日历视图中高亮的日期集合应该与可用日期列表完全匹配
**Validates: Requirements 3.1**

**Property 6: 结束日期范围限制**
*For any* 选择的开始日期，可选的结束日期应该只包含开始日期之后且在可用日期列表中的日期
**Validates: Requirements 3.2**

**Property 7: 无效日期范围自动调整**
*For any* 包含无数据日期的选择范围，系统调整后的范围应该只包含可用日期列表中的日期
**Validates: Requirements 3.3**

**Property 8: 预设日期范围计算正确性**
*For any* 预设选项（如"最近 N 天"），选择后填充的日期范围应该正确计算为从最晚可用日期往前 N 天
**Validates: Requirements 3.5**

**Property 9: 合约信息完整性**
*For any* 显示的合约，渲染的内容应该包含所有必需字段（合约名称、到期日、类型）
**Validates: Requirements 4.1**

**Property 10: 选择数量一致性**
*For any* 选择的合约集合，显示的选择数量应该等于集合的实际大小
**Validates: Requirements 4.3**

**Property 11: 日期范围过滤合约**
*For any* 日期范围变更，过滤后的合约列表应该只包含在该日期范围内有数据的合约
**Validates: Requirements 4.4**

**Property 12: 按钮启用条件**
*For any* 配置状态，"开始回测"按钮应该在且仅在日期范围有效且至少选择一个合约时启用
**Validates: Requirements 5.1**

**Property 13: 回测参数传递正确性**
*For any* 有效配置，点击"开始回测"按钮时调用的 API 应该接收到与用户选择完全匹配的参数（日期范围和合约列表）
**Validates: Requirements 5.2**

**Property 14: 预览数据字段完整性**
*For any* 预览数据记录，显示的内容应该包含所有必需字段（时间戳、合约、价格、成交量）
**Validates: Requirements 6.3**

**Property 15: 预览总数显示正确性**
*For any* 预览响应，显示的总记录数应该等于响应中的 total_records 字段值
**Validates: Requirements 6.5**

**Property 16: 配置保存加载往返**
*For any* 有效的回测配置，保存到 localStorage 后再加载应该得到完全相同的配置（日期范围、合约列表、配置名称）
**Validates: Requirements 7.2, 7.4**

**Property 17: 配置删除一致性**
*For any* 已保存的配置，删除后该配置不应该出现在配置列表中，且不应该存在于 localStorage 中
**Validates: Requirements 7.5**

**Property 18: 触摸目标尺寸要求**
*For any* 交互元素（按钮、输入框、选择器），在小屏幕视口下的尺寸应该至少为 44x44 像素
**Validates: Requirements 9.3**

**Property 19: 布局调整状态保持**
*For any* 用户输入状态（选择的日期、选择的合约），调整窗口大小后所有状态值应该保持不变
**Validates: Requirements 9.4**

**Property 20: 初始加载性能**
*For any* 组件挂载，从开始加载到显示可用数据的时间应该不超过 2000 毫秒
**Validates: Requirements 10.1**

**Property 21: 覆盖率查询性能**
*For any* 日期范围变更，从触发变更到显示更新的覆盖率统计的时间应该不超过 500 毫秒
**Validates: Requirements 10.2**

**Property 22: 搜索响应性能**
*For any* 搜索输入，从输入到显示搜索结果的时间应该不超过 200 毫秒
**Validates: Requirements 10.3**

**Property 23: 防抖效果验证**
*For any* 在短时间内（如 300ms）的连续输入序列，实际触发的 API 调用次数应该显著少于输入次数（理想情况下只有 1 次）
**Validates: Requirements 10.4**

**Property 24: 缓存效果验证**
*For any* 相同的请求参数，第二次请求应该从缓存返回而不触发新的网络调用
**Validates: Requirements 10.5**

## Error Handling

### Frontend Error Handling

1. **API 调用失败**
   - 捕获所有 API 调用的错误
   - 显示用户友好的错误消息
   - 提供重试选项
   - 记录错误到控制台以便调试

2. **数据验证错误**
   - 验证用户输入的日期范围有效性
   - 验证至少选择一个合约
   - 在提交前进行客户端验证
   - 显示具体的验证错误消息

3. **网络超时**
   - 设置合理的请求超时时间（30秒）
   - 超时后显示友好提示
   - 允许用户取消长时间运行的请求

4. **数据不一致**
   - 处理后端返回的空数据情况
   - 处理日期格式不匹配
   - 处理合约信息缺失字段

5. **LocalStorage 错误**
   - 捕获 localStorage 配额超限错误
   - 捕获 localStorage 访问被禁用的情况
   - 提供降级方案（仅会话内保存）

### Backend Error Handling

1. **数据库查询错误**
   - 捕获数据库连接失败
   - 捕获查询超时
   - 返回 500 错误和错误描述

2. **参数验证错误**
   - 验证日期格式（ISO 8601）
   - 验证日期范围逻辑（开始日期 <= 结束日期）
   - 验证合约列表非空
   - 返回 400 错误和具体验证消息

3. **数据不存在错误**
   - 处理请求的日期范围没有数据的情况
   - 处理请求的合约不存在的情况
   - 返回 404 错误和描述性消息

4. **资源限制错误**
   - 限制单次请求的合约数量（如最多 100 个）
   - 限制日期范围跨度（如最多 1 年）
   - 返回 400 错误和限制说明

5. **服务依赖错误**
   - 处理 HistoricalDataManager 不可用
   - 处理数据存储服务不可用
   - 返回 503 错误和重试建议

### Error Response Format

所有 API 错误响应使用统一格式：

```python
class ErrorResponse(BaseModel):
    error: str  # 错误类型
    message: str  # 用户友好的错误消息
    details: Optional[Dict]  # 额外的错误详情
    timestamp: str  # 错误发生时间
```

示例：
```json
{
  "error": "INVALID_DATE_RANGE",
  "message": "开始日期必须早于或等于结束日期",
  "details": {
    "start_date": "2024-02-01",
    "end_date": "2024-01-01"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Testing Strategy

本功能采用双重测试策略，结合单元测试和基于属性的测试，以确保全面的代码覆盖和正确性验证。

### Testing Approach

**单元测试（Unit Tests）**：
- 验证特定示例和边界情况
- 测试组件的初始化行为
- 测试错误处理路径
- 测试 UI 交互的具体场景
- 使用 Jest + React Testing Library（前端）
- 使用 pytest（后端）

**基于属性的测试（Property-Based Tests）**：
- 验证跨所有输入的通用属性
- 通过随机化实现全面的输入覆盖
- 每个测试至少运行 100 次迭代
- 使用 fast-check（前端 TypeScript）
- 使用 Hypothesis（后端 Python）

### Frontend Testing

#### Unit Tests

1. **组件初始化测试**
   - 测试组件挂载时调用正确的 API
   - 测试加载状态的显示
   - 测试错误状态的显示

2. **用户交互测试**
   - 测试日期选择交互
   - 测试合约选择交互
   - 测试预设选项点击
   - 测试配置保存/加载/删除

3. **边界情况测试**
   - 测试空数据列表的处理
   - 测试低覆盖率警告显示
   - 测试无数据日期范围的阻止

4. **API 集成测试**
   - 使用 Mock Service Worker 模拟 API
   - 测试成功响应的处理
   - 测试错误响应的处理
   - 测试超时情况

#### Property-Based Tests

每个属性测试配置为运行至少 100 次迭代，使用 fast-check 库生成随机测试数据。

```typescript
// 示例：Property 1 - 日期范围显示正确性
// Feature: backtest-data-selector, Property 1: 日期范围显示正确性
fc.assert(
  fc.property(
    fc.array(fc.date(), { minLength: 1 }),
    (dates) => {
      const sortedDates = dates.sort((a, b) => a.getTime() - b.getTime());
      const earliest = sortedDates[0];
      const latest = sortedDates[sortedDates.length - 1];
      
      const { getByTestId } = render(
        <BacktestDataSelector availableDates={dates} />
      );
      
      expect(getByTestId('earliest-date')).toHaveTextContent(
        earliest.toISOString()
      );
      expect(getByTestId('latest-date')).toHaveTextContent(
        latest.toISOString()
      );
    }
  ),
  { numRuns: 100 }
);
```

**测试的属性：**
- Property 1: 日期范围显示正确性
- Property 2: 合约数量显示一致性
- Property 3: 日期范围变更触发覆盖率查询
- Property 4: 覆盖率统计完整显示
- Property 5: 日历高亮正确性
- Property 6: 结束日期范围限制
- Property 7: 无效日期范围自动调整
- Property 8: 预设日期范围计算正确性
- Property 9: 合约信息完整性
- Property 10: 选择数量一致性
- Property 11: 日期范围过滤合约
- Property 12: 按钮启用条件
- Property 13: 回测参数传递正确性
- Property 14: 预览数据字段完整性
- Property 15: 预览总数显示正确性
- Property 16: 配置保存加载往返
- Property 17: 配置删除一致性
- Property 18: 触摸目标尺寸要求
- Property 19: 布局调整状态保持
- Property 23: 防抖效果验证
- Property 24: 缓存效果验证

### Backend Testing

#### Unit Tests

1. **API 端点测试**
   - 测试每个端点的基本功能
   - 测试参数验证
   - 测试错误响应格式
   - 测试认证和授权（如需要）

2. **数据模型测试**
   - 测试 Pydantic 模型验证
   - 测试序列化/反序列化
   - 测试默认值

3. **服务集成测试**
   - 测试与 HistoricalDataManager 的集成
   - 测试数据转换逻辑
   - 测试错误传播

#### Property-Based Tests

使用 Hypothesis 库生成随机测试数据，每个测试至少运行 100 次。

```python
# 示例：API 参数验证属性
# Feature: backtest-data-selector, Property: API 参数验证
@given(
    start_date=st.dates(),
    end_date=st.dates()
)
@settings(max_examples=100)
def test_date_range_validation(start_date, end_date):
    """验证日期范围参数的正确验证"""
    response = client.get(
        "/api/backtest/coverage-stats",
        params={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    )
    
    if start_date <= end_date:
        assert response.status_code in [200, 404]  # 成功或无数据
    else:
        assert response.status_code == 400  # 无效范围
        assert "start_date" in response.json()["message"].lower()
```

**测试的属性：**
- API 参数验证的一致性
- 日期范围逻辑验证
- 数据过滤的正确性
- 响应格式的一致性
- 错误处理的完整性

### Performance Testing

性能测试验证以下属性：
- Property 20: 初始加载性能（< 2000ms）
- Property 21: 覆盖率查询性能（< 500ms）
- Property 22: 搜索响应性能（< 200ms）

使用工具：
- Frontend: React DevTools Profiler, Lighthouse
- Backend: pytest-benchmark, locust（负载测试）

### Integration Testing

端到端测试验证完整的用户流程：
1. 打开回测配置界面
2. 查看可用数据信息
3. 选择日期范围
4. 选择合约
5. 查看数据质量指标
6. 预览数据
7. 保存配置
8. 开始回测

使用工具：Playwright 或 Cypress

### Test Coverage Goals

- 前端代码覆盖率：> 80%
- 后端代码覆盖率：> 90%
- 关键路径覆盖率：100%
- 属性测试覆盖所有已识别的正确性属性

### Continuous Integration

所有测试在 CI/CD 管道中自动运行：
- 每次提交运行单元测试和属性测试
- 每次 PR 运行完整测试套件
- 每日运行性能测试和负载测试
- 测试失败阻止合并和部署
