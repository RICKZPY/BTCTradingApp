"""
Configuration management for Bitcoin Trading System
"""
import os
from typing import Optional
from pydantic import BaseSettings, Field


class DatabaseSettings(BaseSettings):
    """Database configuration"""
    # PostgreSQL settings
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="bitcoin_trading", env="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", env="POSTGRES_USER")
    postgres_password: str = Field(default="password", env="POSTGRES_PASSWORD")
    
    # InfluxDB settings
    influxdb_url: str = Field(default="http://localhost:8086", env="INFLUXDB_URL")
    influxdb_token: str = Field(default="", env="INFLUXDB_TOKEN")
    influxdb_org: str = Field(default="trading-org", env="INFLUXDB_ORG")
    influxdb_bucket: str = Field(default="market-data", env="INFLUXDB_BUCKET")
    
    @property
    def postgres_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


class RedisSettings(BaseSettings):
    """Redis configuration"""
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


class APISettings(BaseSettings):
    """External API configuration"""
    # OpenAI
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    
    # Binance
    binance_api_key: str = Field(default="", env="BINANCE_API_KEY")
    binance_secret_key: str = Field(default="", env="BINANCE_SECRET_KEY")
    binance_testnet: bool = Field(default=True, env="BINANCE_TESTNET")
    
    # Twitter/X
    twitter_bearer_token: str = Field(default="", env="TWITTER_BEARER_TOKEN")
    
    # News APIs
    newsapi_key: str = Field(default="", env="NEWSAPI_KEY")


class TradingSettings(BaseSettings):
    """Trading configuration"""
    # Risk management
    max_position_size: float = Field(default=0.1, env="MAX_POSITION_SIZE")  # 10% of portfolio
    max_daily_loss: float = Field(default=0.05, env="MAX_DAILY_LOSS")  # 5% daily loss limit
    stop_loss_percentage: float = Field(default=0.02, env="STOP_LOSS_PERCENTAGE")  # 2% stop loss
    
    # Trading parameters
    min_confidence_threshold: float = Field(default=0.7, env="MIN_CONFIDENCE_THRESHOLD")
    sentiment_weight: float = Field(default=0.4, env="SENTIMENT_WEIGHT")
    technical_weight: float = Field(default=0.6, env="TECHNICAL_WEIGHT")


class AppSettings(BaseSettings):
    """Application configuration"""
    app_name: str = "Bitcoin Trading System"
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    
    # Data collection intervals (in seconds)
    news_collection_interval: int = Field(default=300, env="NEWS_COLLECTION_INTERVAL")  # 5 minutes
    market_data_interval: int = Field(default=60, env="MARKET_DATA_INTERVAL")  # 1 minute
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class Settings(BaseSettings):
    """Main settings class combining all configurations"""
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    api: APISettings = APISettings()
    trading: TradingSettings = TradingSettings()
    app: AppSettings = AppSettings()


# Global settings instance
settings = Settings()