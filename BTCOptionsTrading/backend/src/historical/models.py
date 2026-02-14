"""
历史数据模型
定义历史期权数据相关的数据结构
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4

from src.core.models import OptionType


class DataSource(str, Enum):
    """数据源枚举"""
    CRYPTO_DATA_DOWNLOAD = "CryptoDataDownload"
    DERIBIT_API = "Deribit_API"
    TARDIS = "Tardis"
    MANUAL = "Manual"


class ImportStatus(str, Enum):
    """导入状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ValidationSeverity(str, Enum):
    """验证严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class OptionOHLCV:
    """期权 OHLCV 数据（从 CSV 解析的原始数据）"""
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    
    def __post_init__(self):
        """验证 OHLC 关系"""
        if not (self.low <= self.open <= self.high):
            raise ValueError(f"Invalid OHLC relationship: Low={self.low}, Open={self.open}, High={self.high}")
        if not (self.low <= self.close <= self.high):
            raise ValueError(f"Invalid OHLC relationship: Low={self.low}, Close={self.close}, High={self.high}")
        if self.low < 0 or self.high < 0:
            raise ValueError("Prices cannot be negative")


@dataclass
class OptionInfo:
    """期权信息（从文件名提取）"""
    symbol: str  # BTC, ETH
    expiry_date: datetime
    strike_price: Decimal
    option_type: OptionType
    
    def to_instrument_name(self) -> str:
        """转换为标准期权合约名称"""
        # 格式: BTC-29MAR24-50000-C
        date_str = self.expiry_date.strftime("%d%b%y").upper()
        type_str = "C" if self.option_type == OptionType.CALL else "P"
        return f"{self.symbol}-{date_str}-{int(self.strike_price)}-{type_str}"


@dataclass
class HistoricalOptionData:
    """历史期权数据（系统内部格式）"""
    instrument_name: str
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
    data_source: DataSource = DataSource.CRYPTO_DATA_DOWNLOAD
    id: UUID = field(default_factory=uuid4)
    
    @property
    def mid_price(self) -> Decimal:
        """中间价（使用收盘价作为近似）"""
        return self.close_price
    
    @property
    def price_range(self) -> Decimal:
        """价格范围"""
        return self.high_price - self.low_price


@dataclass
class DataFileInfo:
    """可下载的数据文件信息"""
    expiry_date: datetime
    url: str
    filename: str
    estimated_size: int  # bytes
    last_modified: Optional[datetime] = None
    is_downloaded: bool = False
    local_path: Optional[str] = None


@dataclass
class DataIssue:
    """数据问题"""
    severity: ValidationSeverity
    message: str
    timestamp: Optional[datetime] = None
    record_index: Optional[int] = None
    field_name: Optional[str] = None


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    issues: List[DataIssue] = field(default_factory=list)
    
    @property
    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0 or any(
            issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL] 
            for issue in self.issues
        )
    
    @property
    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0 or any(
            issue.severity == ValidationSeverity.WARNING 
            for issue in self.issues
        )


@dataclass
class DataQualityReport:
    """数据质量报告"""
    total_records: int
    missing_records: int
    anomaly_records: int
    coverage_percentage: float
    time_range: Tuple[datetime, datetime]
    issues: List[DataIssue] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def quality_score(self) -> float:
        """质量评分（0-100）"""
        if self.total_records == 0:
            return 0.0
        
        # 基础分数基于覆盖率
        base_score = self.coverage_percentage * 100
        
        # 根据问题严重程度扣分
        critical_issues = sum(1 for issue in self.issues if issue.severity == ValidationSeverity.CRITICAL)
        error_issues = sum(1 for issue in self.issues if issue.severity == ValidationSeverity.ERROR)
        warning_issues = sum(1 for issue in self.issues if issue.severity == ValidationSeverity.WARNING)
        
        penalty = (critical_issues * 10) + (error_issues * 5) + (warning_issues * 1)
        
        return max(0.0, base_score - penalty)


@dataclass
class CoverageStats:
    """数据覆盖率统计"""
    start_date: datetime
    end_date: datetime
    total_days: int
    days_with_data: int
    coverage_percentage: float
    missing_dates: List[datetime] = field(default_factory=list)
    strikes_covered: List[Decimal] = field(default_factory=list)
    expiries_covered: List[datetime] = field(default_factory=list)


@dataclass
class ImportResult:
    """导入结果"""
    success_count: int
    failure_count: int
    total_count: int
    quality_report: Optional[DataQualityReport] = None
    failed_files: List[str] = field(default_factory=list)
    import_duration_seconds: float = 0.0
    records_imported: int = 0
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_count == 0:
            return 0.0
        return self.success_count / self.total_count


@dataclass
class UpdateResult:
    """更新结果"""
    new_files_found: int
    files_downloaded: int
    files_imported: int
    errors: List[str] = field(default_factory=list)


@dataclass
class BacktestDataSet:
    """回测数据集"""
    start_date: datetime
    end_date: datetime
    options_data: Dict[str, List[HistoricalOptionData]]  # instrument_name -> data list
    underlying_data: List['UnderlyingPriceData'] = field(default_factory=list)
    coverage_stats: Optional[CoverageStats] = None
    
    def get_option_data(self, instrument_name: str) -> List[HistoricalOptionData]:
        """获取指定期权的数据"""
        return self.options_data.get(instrument_name, [])
    
    def get_all_instruments(self) -> List[str]:
        """获取所有期权合约名称"""
        return list(self.options_data.keys())


@dataclass
class UnderlyingPriceData:
    """标的资产价格数据"""
    symbol: str
    timestamp: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int
    
    @property
    def mid_price(self) -> Decimal:
        """中间价"""
        return (self.high_price + self.low_price) / 2


@dataclass
class ExportConfig:
    """导出配置"""
    format: str  # "csv", "json", "parquet"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    instruments: Optional[List[str]] = None
    compress: bool = True
    batch_size: int = 10000


@dataclass
class ExportResult:
    """导出结果"""
    file_path: str
    records_exported: int
    file_size_bytes: int
    export_duration_seconds: float
    format: str
