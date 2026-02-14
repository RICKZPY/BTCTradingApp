# 历史期权数据集成设计文档

## 概述

本设计文档描述了如何将 CryptoDataDownload 的免费 Deribit 期权历史数据集成到现有的 BTC 期权交易回测系统中。系统将支持下载、解析、存储和查询历史期权 OHLCV 数据，使回测引擎能够使用真实的历史数据而不仅仅依赖模拟数据。

## 架构

### 系统组件

```
┌─────────────────────────────────────────────────────────────┐
│                    用户界面 / API                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Historical Data Manager                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Downloader │  │   Converter  │  │   Validator  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Cache Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  File Cache  │  │  DB Cache    │  │  Index       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backtest Engine                           │
│  (使用历史数据或实时API数据)                                  │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

1. **下载阶段**: Downloader 从 CryptoDataDownload 下载 ZIP 文件
2. **解析阶段**: Converter 解析 CSV 文件并提取期权数据
3. **验证阶段**: Validator 验证数据质量和完整性
4. **存储阶段**: 数据存储到文件缓存和数据库
5. **查询阶段**: Backtest Engine 从缓存查询历史数据

## 组件和接口

### 1. CryptoDataDownloader

负责从 CryptoDataDownload 网站下载历史数据。

```python
class CryptoDataDownloader:
    """CryptoDataDownload 数据下载器"""
    
    def __init__(self, cache_dir: str = "data/historical"):
        """初始化下载器"""
        pass
    
    async def list_available_data(
        self,
        symbol: str = "BTC"
    ) -> List[DataFileInfo]:
        """
        列出可用的历史数据文件
        
        Returns:
            数据文件信息列表（包含到期日、URL、大小等）
        """
        pass
    
    async def download_data(
        self,
        expiry_date: datetime,
        force_redownload: bool = False
    ) -> Path:
        """
        下载指定到期日的期权数据
        
        Args:
            expiry_date: 期权到期日
            force_redownload: 是否强制重新下载
            
        Returns:
            下载文件的本地路径
        """
        pass
    
    async def batch_download(
        self,
        expiry_dates: List[datetime],
        max_concurrent: int = 3
    ) -> Dict[datetime, Path]:
        """
        批量下载多个到期日的数据
        
        Args:
            expiry_dates: 到期日列表
            max_concurrent: 最大并发下载数
            
        Returns:
            到期日到文件路径的映射
        """
        pass
```

### 2. HistoricalDataConverter

负责将 CSV 格式数据转换为系统内部格式。

```python
class HistoricalDataConverter:
    """历史数据转换器"""
    
    def parse_csv_file(
        self,
        csv_path: Path
    ) -> List[OptionOHLCV]:
        """
        解析 CSV 文件
        
        Args:
            csv_path: CSV 文件路径
            
        Returns:
            期权 OHLCV 数据列表
        """
        pass
    
    def extract_option_info(
        self,
        filename: str
    ) -> OptionInfo:
        """
        从文件名提取期权信息
        
        文件名格式: Deribit_BTCUSD_20240329_50000_C.csv
        
        Returns:
            期权信息（到期日、执行价、类型）
        """
        pass
    
    def convert_to_internal_format(
        self,
        ohlcv_data: List[OptionOHLCV],
        option_info: OptionInfo
    ) -> List[HistoricalOptionData]:
        """
        转换为系统内部格式
        
        Returns:
            系统内部格式的历史数据
        """
        pass
```

### 3. HistoricalDataValidator

负责验证历史数据的质量和完整性。

```python
class HistoricalDataValidator:
    """历史数据验证器"""
    
    def validate_data_completeness(
        self,
        data: List[HistoricalOptionData]
    ) -> ValidationResult:
        """
        验证数据完整性
        
        检查:
        - 时间序列连续性
        - 缺失值
        - 数据点数量
        """
        pass
    
    def validate_price_sanity(
        self,
        data: List[HistoricalOptionData]
    ) -> ValidationResult:
        """
        验证价格合理性
        
        检查:
        - 负价格
        - 异常波动
        - OHLC 关系 (Open <= High, Low <= Close)
        """
        pass
    
    def validate_option_parity(
        self,
        call_data: List[HistoricalOptionData],
        put_data: List[HistoricalOptionData],
        underlying_price: Decimal
    ) -> ValidationResult:
        """
        验证看涨看跌平价关系
        
        C - P ≈ S - K * e^(-rT)
        """
        pass
    
    def generate_quality_report(
        self,
        data: List[HistoricalOptionData]
    ) -> DataQualityReport:
        """
        生成数据质量报告
        
        Returns:
            包含覆盖率、缺失率、异常点等信息的报告
        """
        pass
```

### 4. HistoricalDataCache

负责缓存和快速查询历史数据。

```python
class HistoricalDataCache:
    """历史数据缓存"""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        file_cache_dir: str = "data/cache"
    ):
        """初始化缓存"""
        pass
    
    def store_historical_data(
        self,
        data: List[HistoricalOptionData]
    ) -> None:
        """
        存储历史数据到缓存
        
        同时存储到:
        1. 数据库（用于查询）
        2. Parquet 文件（用于快速批量读取）
        """
        pass
    
    def query_option_data(
        self,
        instrument_name: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[HistoricalOptionData]:
        """
        查询期权历史数据
        
        优先从缓存读取，缓存未命中则从数据库读取
        """
        pass
    
    def get_available_dates(
        self,
        symbol: str = "BTC"
    ) -> List[datetime]:
        """
        获取可用的历史数据日期
        
        Returns:
            已缓存数据的日期列表
        """
        pass
    
    def get_coverage_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> CoverageStats:
        """
        获取数据覆盖率统计
        
        Returns:
            时间范围内的数据覆盖情况
        """
        pass
    
    def clear_cache(
        self,
        before_date: Optional[datetime] = None
    ) -> int:
        """
        清理缓存
        
        Args:
            before_date: 清理此日期之前的数据（None表示清理全部）
            
        Returns:
            清理的记录数
        """
        pass
```

### 5. HistoricalDataManager

协调所有历史数据相关操作的主管理器。

```python
class HistoricalDataManager:
    """历史数据管理器"""
    
    def __init__(
        self,
        downloader: CryptoDataDownloader,
        converter: HistoricalDataConverter,
        validator: HistoricalDataValidator,
        cache: HistoricalDataCache
    ):
        """初始化管理器"""
        pass
    
    async def import_historical_data(
        self,
        expiry_dates: List[datetime],
        validate: bool = True
    ) -> ImportResult:
        """
        导入历史数据的完整流程
        
        1. 下载数据
        2. 解析转换
        3. 验证质量
        4. 存储缓存
        
        Returns:
            导入结果（成功/失败数量、质量报告等）
        """
        pass
    
    async def update_historical_data(
        self
    ) -> UpdateResult:
        """
        检查并更新历史数据
        
        检查 CryptoDataDownload 是否有新数据可用
        """
        pass
    
    def get_data_for_backtest(
        self,
        start_date: datetime,
        end_date: datetime,
        strikes: Optional[List[Decimal]] = None
    ) -> BacktestDataSet:
        """
        获取回测所需的历史数据
        
        Args:
            start_date: 回测开始日期
            end_date: 回测结束日期
            strikes: 执行价列表（None表示所有执行价）
            
        Returns:
            回测数据集
        """
        pass
```

## 数据模型

### OptionOHLCV

从 CSV 文件解析的原始 OHLCV 数据。

```python
@dataclass
class OptionOHLCV:
    """期权 OHLCV 数据"""
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
```

### OptionInfo

从文件名提取的期权信息。

```python
@dataclass
class OptionInfo:
    """期权信息"""
    symbol: str  # BTC, ETH
    expiry_date: datetime
    strike_price: Decimal
    option_type: OptionType  # CALL or PUT
```

### HistoricalOptionData

系统内部使用的历史期权数据格式。

```python
@dataclass
class HistoricalOptionData:
    """历史期权数据"""
    instrument_name: str  # BTC-29MAR24-50000-C
    timestamp: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal
    strike_price: Decimal
    expiry_date: datetime
    option_type: OptionType
    underlying_symbol: str
```

### DataFileInfo

可下载的数据文件信息。

```python
@dataclass
class DataFileInfo:
    """数据文件信息"""
    expiry_date: datetime
    url: str
    filename: str
    estimated_size: int  # bytes
    last_modified: datetime
```

### ValidationResult

数据验证结果。

```python
@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    stats: Dict[str, Any]
```

### DataQualityReport

数据质量报告。

```python
@dataclass
class DataQualityReport:
    """数据质量报告"""
    total_records: int
    missing_records: int
    anomaly_records: int
    coverage_percentage: float
    time_range: Tuple[datetime, datetime]
    issues: List[DataIssue]
```

### BacktestDataSet

回测数据集。

```python
@dataclass
class BacktestDataSet:
    """回测数据集"""
    start_date: datetime
    end_date: datetime
    options_data: Dict[str, List[HistoricalOptionData]]  # instrument_name -> data
    underlying_data: List[UnderlyingPriceData]
    coverage_stats: CoverageStats
```

## 数据库模式

### historical_option_data 表

存储历史期权数据。

```sql
CREATE TABLE historical_option_data (
    id UUID PRIMARY KEY,
    instrument_name VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open_price DECIMAL(20, 8) NOT NULL,
    high_price DECIMAL(20, 8) NOT NULL,
    low_price DECIMAL(20, 8) NOT NULL,
    close_price DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(20, 8) NOT NULL,
    strike_price DECIMAL(20, 8) NOT NULL,
    expiry_date TIMESTAMP NOT NULL,
    option_type VARCHAR(10) NOT NULL,
    underlying_symbol VARCHAR(10) NOT NULL,
    data_source VARCHAR(50) DEFAULT 'CryptoDataDownload',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(instrument_name, timestamp)
);

CREATE INDEX idx_historical_instrument_time 
ON historical_option_data(instrument_name, timestamp);

CREATE INDEX idx_historical_expiry 
ON historical_option_data(expiry_date);

CREATE INDEX idx_historical_timestamp 
ON historical_option_data(timestamp);
```

### data_import_log 表

记录数据导入历史。

```sql
CREATE TABLE data_import_log (
    id UUID PRIMARY KEY,
    expiry_date TIMESTAMP NOT NULL,
    import_date TIMESTAMP NOT NULL,
    records_imported INT NOT NULL,
    records_failed INT NOT NULL,
    file_source VARCHAR(255),
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 正确性属性

*属性是关于系统应该满足的特征或行为的形式化陈述，这些陈述在所有有效执行中都应该成立。属性是人类可读规范和机器可验证正确性保证之间的桥梁。*

### 属性 1: 数据下载幂等性

*对于任何*到期日和下载参数，多次下载相同数据应该产生相同的结果，不会创建重复记录，且已存在的数据应该被跳过。

**验证: 需求 1.5**

### 属性 2: 文件列表排序一致性

*对于任何*可用数据文件列表，返回的文件应该按到期日严格递增排序。

**验证: 需求 1.2**

### 属性 3: ZIP 文件完整性

*对于任何*下载的数据文件，文件应该是有效的 ZIP 格式且能成功解压，解压后应该包含至少一个 CSV 文件。

**验证: 需求 1.3**

### 属性 4: 网络错误重试机制

*对于任何*网络错误，系统应该记录错误信息并实施指数退避重试，重试次数不超过配置的最大值。

**验证: 需求 1.4, 10.1**

### 属性 5: CSV 解析往返一致性

*对于任何*有效的 CSV 文件，解析后保存到数据库再读取出来的数据应该与原始 CSV 数据一致（在精度范围内）。

**验证: 需求 2.1, 2.5**

### 属性 6: 期权信息提取一致性

*对于任何*符合命名规范的文件名，从文件名解析的期权信息（到期日、执行价、类型）应该与文件内容中的期权信息一致。

**验证: 需求 2.2**

### 属性 7: 时间戳转换往返性

*对于任何*时间戳，转换为 UTC 格式后再转换回原格式应该得到相同的时间点。

**验证: 需求 2.3**

### 属性 8: 数据验证完整性

*对于任何*数据集，验证过程应该识别所有缺失值和异常值，且验证报告中的问题数量应该等于实际问题数量。

**验证: 需求 2.4**

### 属性 9: 缓存读写一致性

*对于任何*数据，首次加载后存储到缓存，再从缓存读取应该得到完全相同的数据。

**验证: 需求 3.1, 3.2**

### 属性 10: 缓存 LRU 淘汰正确性

*对于任何*缓存满的情况，淘汰的数据应该是最久未使用的数据，且淘汰后缓存大小应该在限制范围内。

**验证: 需求 3.3**

### 属性 11: 缓存清理安全性

*对于任何*缓存清理操作，清理后的数据应该只包含指定日期之后的记录，指定日期之前的记录应该全部被删除。

**验证: 需求 3.5**

### 属性 12: 回测数据加载完整性

*对于任何*回测时间范围，从缓存加载的数据应该包含该范围内所有可用的期权数据，不应遗漏任何记录。

**验证: 需求 4.2**

### 属性 13: 数据缺失检测准确性

*对于任何*回测时间范围，如果历史数据不足，系统应该准确识别缺失的时间段，且缺失段的并集应该等于请求范围减去可用范围。

**验证: 需求 4.3**

### 属性 14: 数据源切换一致性

*对于任何*数据查询，无论使用历史数据源还是实时数据源，返回的数据格式和字段应该完全一致。

**验证: 需求 4.5**

### 属性 15: 时间序列单调性

*对于任何*按时间排序的数据序列，时间戳必须严格递增，不应存在重复或乱序的时间戳。

**验证: 需求 5.1**

### 属性 16: OHLC 关系不变性

*对于任何*历史期权数据记录，必须满足：Low <= Open <= High 且 Low <= Close <= High，且所有价格必须非负。

**验证: 需求 5.2**

### 属性 17: 期权平价关系合理性

*对于任何*相同执行价和到期日的看涨看跌期权对，应该在合理误差范围内满足平价关系：C - P ≈ S - K * e^(-rT)。

**验证: 需求 5.3**

### 属性 18: 数据质量报告完整性

*对于任何*验证结果，生成的质量报告应该包含所有发现的问题，且报告中的问题数量应该等于实际检测到的问题数量。

**验证: 需求 5.4**

### 属性 19: 数据覆盖率准确性

*对于任何*时间范围，报告的数据覆盖率应该等于实际存在数据的时间点数量除以总时间点数量，且覆盖率应该在 0 到 1 之间。

**验证: 需求 5.5**

### 属性 20: 批量下载完整性

*对于任何*到期日列表，批量下载成功的文件数量加上失败的文件数量应该等于请求的总数量。

**验证: 需求 7.1, 7.4**

### 属性 21: 并行处理结果一致性

*对于任何*文件列表，并行处理的结果应该与串行处理的结果完全相同（顺序可能不同但内容相同）。

**验证: 需求 7.2**

### 属性 22: 批量操作摘要准确性

*对于任何*批量操作，生成的摘要报告中的成功数、失败数和总数应该满足：成功数 + 失败数 = 总数。

**验证: 需求 7.5**

### 属性 23: 数据更新检测准确性

*对于任何*更新检查，识别的新数据应该是远程存在但本地不存在的数据，不应包含已存在的数据。

**验证: 需求 8.1**

### 属性 24: 数据版本保留完整性

*对于任何*数据更新操作，更新后旧版本的数据应该仍然可访问，且版本标记应该正确区分新旧数据。

**验证: 需求 8.4**

### 属性 25: 数据导出往返一致性

*对于任何*数据和导出格式（CSV、JSON、Parquet），导出后重新导入应该得到与原始数据一致的数据。

**验证: 需求 9.1**

### 属性 26: 导出筛选准确性

*对于任何*筛选条件，导出的数据应该只包含满足筛选条件的记录，不应包含不满足条件的记录。

**验证: 需求 9.2**

### 属性 27: 分批导出一致性

*对于任何*大数据集，分批导出的结果合并后应该与一次性导出的结果完全相同。

**验证: 需求 9.3**

### 属性 28: 解析错误恢复性

*对于任何*包含部分无效数据的文件，解析失败不应该中断整个处理流程，有效数据应该被正常处理。

**验证: 需求 10.2**

### 属性 29: 日志格式结构化

*对于任何*日志记录，日志应该是有效的结构化格式（JSON），且包含必需的字段（时间戳、级别、消息）。

**验证: 需求 10.4**

## 错误处理

### 网络错误

- 实施指数退避重试机制（最多 3 次）
- 记录详细的错误日志
- 提供用户友好的错误消息

### 数据解析错误

- 跳过无法解析的行，继续处理其他数据
- 记录失败的行号和原因
- 在导入结果中报告失败统计

### 存储错误

- 使用事务确保数据一致性
- 失败时回滚所有更改
- 提前检查磁盘空间

### 验证错误

- 标记但不拒绝有警告的数据
- 拒绝有严重错误的数据
- 生成详细的质量报告

## 测试策略

### 单元测试

- 测试 CSV 解析逻辑
- 测试数据转换函数
- 测试验证规则
- 测试缓存读写操作

### 属性测试

- 使用 Hypothesis 库生成随机测试数据
- 验证所有正确性属性
- 每个属性测试至少运行 100 次迭代
- 测试标签格式: `Feature: historical-data-integration, Property {N}: {property_text}`

### 集成测试

- 测试完整的数据导入流程
- 测试与回测引擎的集成
- 测试批量操作
- 使用真实的 CSV 样本文件

### 性能测试

- 测试大文件解析性能
- 测试批量导入性能
- 测试查询性能
- 目标: 处理 1GB 数据 < 5 分钟

## 性能优化

### 并行处理

- 使用 asyncio 并行下载多个文件
- 使用多进程并行解析 CSV 文件
- 批量插入数据库以提高写入性能

### 缓存策略

- 使用 Parquet 格式存储常用数据（比 CSV 快 10-100 倍）
- 实施 LRU 缓存策略
- 预加载常用时间范围的数据

### 数据库优化

- 创建适当的索引
- 使用批量插入而不是逐条插入
- 定期执行 VACUUM 清理

### 内存管理

- 流式处理大文件而不是一次性加载
- 及时释放不再使用的数据
- 限制并发操作数量以控制内存使用

## 配置

### 环境变量

```bash
# 历史数据配置
HISTORICAL_DATA_DIR=data/historical
HISTORICAL_CACHE_DIR=data/cache
MAX_CONCURRENT_DOWNLOADS=3
DOWNLOAD_TIMEOUT=300  # seconds
CACHE_SIZE_LIMIT=10GB

# CryptoDataDownload 配置
CRYPTODATADOWNLOAD_BASE_URL=https://www.cryptodatadownload.com/data/deribit/
```

### 配置文件

```python
# config/historical_data_config.py

HISTORICAL_DATA_CONFIG = {
    "downloader": {
        "base_url": "https://www.cryptodatadownload.com/data/deribit/",
        "timeout": 300,
        "max_retries": 3,
        "retry_delay": 5,
    },
    "converter": {
        "date_format": "%Y-%m-%d %H:%M:%S",
        "decimal_precision": 8,
    },
    "validator": {
        "max_price_change_pct": 50.0,  # 50% 单日最大价格变化
        "min_volume": 0.0,
    },
    "cache": {
        "file_format": "parquet",
        "compression": "snappy",
        "max_size_gb": 10,
    }
}
```

## 部署考虑

### 初始数据导入

1. 确定需要的历史数据范围
2. 批量下载所有需要的数据文件
3. 验证数据质量
4. 导入到数据库和缓存
5. 生成数据覆盖率报告

### 定期更新

1. 设置定时任务（如每周检查一次）
2. 检查是否有新的免费数据可用
3. 自动下载和导入新数据
4. 发送通知给管理员

### 监控

- 监控磁盘空间使用
- 监控数据导入成功率
- 监控查询性能
- 设置告警阈值

## 未来扩展

### 支持更多数据源

- Tardis.dev（付费数据）
- Deribit 官方历史数据 API
- 其他交易所数据

### 数据增强

- 计算隐含波动率
- 构建波动率曲面
- 插值缺失数据

### 高级功能

- 数据版本控制
- 数据质量评分
- 自动异常检测和修复
