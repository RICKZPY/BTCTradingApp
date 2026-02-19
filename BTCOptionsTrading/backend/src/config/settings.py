"""
系统配置设置
使用Pydantic进行配置验证和管理
"""

from typing import Optional, Dict, Any
try:
    # Pydantic v2
    from pydantic_settings import BaseSettings
    from pydantic import Field, field_validator
    PYDANTIC_V2 = True
except ImportError:
    # Pydantic v1
    from pydantic import BaseSettings, Field, validator
    PYDANTIC_V2 = False
from decimal import Decimal


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    # 数据库类型选择
    db_type: str = Field(default="sqlite", env="DB_TYPE")  # sqlite 或 postgresql
    
    # SQLite配置
    sqlite_path: str = Field(default="./data/btc_options.db", env="SQLITE_PATH")
    
    # PostgreSQL配置
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="btc_options", env="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", env="POSTGRES_USER")
    postgres_password: str = Field(default="", env="POSTGRES_PASSWORD")
    
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    influxdb_host: str = Field(default="localhost", env="INFLUXDB_HOST")
    influxdb_port: int = Field(default=8086, env="INFLUXDB_PORT")
    influxdb_token: str = Field(default="", env="INFLUXDB_TOKEN")
    influxdb_org: str = Field(default="btc-options", env="INFLUXDB_ORG")
    influxdb_bucket: str = Field(default="market-data", env="INFLUXDB_BUCKET")
    
    @property
    def postgres_url(self) -> str:
        """PostgreSQL连接URL"""
        if self.db_type == "sqlite":
            return f"sqlite:///{self.sqlite_path}"
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


class DeribitSettings(BaseSettings):
    """Deribit API配置"""
    api_key: str = Field(default="", env="DERIBIT_API_KEY")
    api_secret: str = Field(default="", env="DERIBIT_API_SECRET")
    test_mode: bool = Field(default=True, env="DERIBIT_TEST_MODE")
    base_url: str = Field(default="https://test.deribit.com", env="DERIBIT_BASE_URL")
    websocket_url: str = Field(default="wss://test.deribit.com/ws/api/v2", env="DERIBIT_WS_URL")
    
    # API限制设置
    rate_limit_requests: int = Field(default=20, env="DERIBIT_RATE_LIMIT")
    rate_limit_window: int = Field(default=1, env="DERIBIT_RATE_WINDOW")  # seconds
    max_retries: int = Field(default=3, env="DERIBIT_MAX_RETRIES")
    retry_delay: float = Field(default=1.0, env="DERIBIT_RETRY_DELAY")  # seconds
    
    if PYDANTIC_V2:
        @field_validator('base_url', 'websocket_url')
        @classmethod
        def validate_urls(cls, v, info):
            """验证URL格式"""
            # In v2, we need to check test_mode from the model being validated
            return v
    else:
        @validator('base_url', 'websocket_url')
        def validate_urls(cls, v, values):
            """验证URL格式"""
            if values.get('test_mode', True):
                if 'test.deribit.com' not in v:
                    raise ValueError("Test mode requires test.deribit.com URLs")
            return v


class TradingSettings(BaseSettings):
    """交易配置"""
    default_currency: str = Field(default="BTC", env="DEFAULT_CURRENCY")
    risk_free_rate: float = Field(default=0.05, env="RISK_FREE_RATE")
    
    # 风险管理参数
    max_portfolio_delta: float = Field(default=100.0, env="MAX_PORTFOLIO_DELTA")
    max_portfolio_gamma: float = Field(default=50.0, env="MAX_PORTFOLIO_GAMMA")
    max_portfolio_vega: float = Field(default=1000.0, env="MAX_PORTFOLIO_VEGA")
    max_portfolio_value: float = Field(default=1000000.0, env="MAX_PORTFOLIO_VALUE")
    max_single_position: float = Field(default=100000.0, env="MAX_SINGLE_POSITION")
    
    # 回测参数
    default_initial_capital: float = Field(default=100000.0, env="DEFAULT_INITIAL_CAPITAL")
    commission_rate: float = Field(default=0.001, env="COMMISSION_RATE")
    
    if PYDANTIC_V2:
        @field_validator('risk_free_rate')
        @classmethod
        def validate_risk_free_rate(cls, v):
            """验证无风险利率范围"""
            if not 0 <= v <= 1:
                raise ValueError("Risk free rate must be between 0 and 1")
            return v
    else:
        @validator('risk_free_rate')
        def validate_risk_free_rate(cls, v):
            """验证无风险利率范围"""
            if not 0 <= v <= 1:
                raise ValueError("Risk free rate must be between 0 and 1")
            return v


class APISettings(BaseSettings):
    """API服务配置"""
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="API_DEBUG")
    
    # CORS设置
    cors_origins: str = Field(default="http://localhost:3000", env="CORS_ORIGINS")
    cors_methods: str = Field(default="GET,POST,PUT,DELETE", env="CORS_METHODS")
    
    # JWT设置
    jwt_secret_key: str = Field(default="your-secret-key", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=30, env="JWT_EXPIRE_MINUTES")
    
    @property
    def cors_origins_list(self):
        """CORS origins as list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def cors_methods_list(self):
        """CORS methods as list"""
        return [method.strip() for method in self.cors_methods.split(",")]


class LoggingSettings(BaseSettings):
    """日志配置"""
    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT")
    file_path: str = Field(default="logs/app.log", env="LOG_FILE_PATH")
    max_file_size: int = Field(default=10485760, env="LOG_MAX_FILE_SIZE")  # 10MB
    backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    if PYDANTIC_V2:
        @field_validator('level')
        @classmethod
        def validate_log_level(cls, v):
            """验证日志级别"""
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if v.upper() not in valid_levels:
                raise ValueError(f"Log level must be one of {valid_levels}")
            return v.upper()
    else:
        @validator('level')
        def validate_log_level(cls, v):
            """验证日志级别"""
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if v.upper() not in valid_levels:
                raise ValueError(f"Log level must be one of {valid_levels}")
            return v.upper()


class Settings(BaseSettings):
    """主配置类"""
    app_name: str = Field(default="BTC Options Trading System", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # 子配置
    database: DatabaseSettings = DatabaseSettings()
    deribit: DeribitSettings = DeribitSettings()
    trading: TradingSettings = TradingSettings()
    api: APISettings = APISettings()
    logging: LoggingSettings = LoggingSettings()
    
    if PYDANTIC_V2:
        model_config = {
            "env_file": ".env",
            "env_file_encoding": "utf-8",
            "case_sensitive": False
        }
        
        @field_validator('environment')
        @classmethod
        def validate_environment(cls, v):
            """验证环境设置"""
            valid_envs = ['development', 'testing', 'staging', 'production']
            if v.lower() not in valid_envs:
                raise ValueError(f"Environment must be one of {valid_envs}")
            return v.lower()
    else:
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False
        
        @validator('environment')
        def validate_environment(cls, v):
            """验证环境设置"""
            valid_envs = ['development', 'testing', 'staging', 'production']
            if v.lower() not in valid_envs:
                raise ValueError(f"Environment must be one of {valid_envs}")
            return v.lower()


# 全局设置实例
settings = Settings()