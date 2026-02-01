"""
Configuration management for Bitcoin Trading System
"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration"""
    # PostgreSQL settings
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "bitcoin_trading"
    postgres_user: str = "postgres"
    postgres_password: str = "password"
    
    # InfluxDB settings
    influxdb_url: str = "http://localhost:8086"
    influxdb_token: str = ""
    influxdb_org: str = "trading-org"
    influxdb_bucket: str = "market-data"
    
    @property
    def postgres_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


class RedisSettings(BaseSettings):
    """Redis configuration"""
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


class APISettings(BaseSettings):
    """External API configuration"""
    # OpenAI
    openai_api_key: str = ""
    
    # Binance
    binance_api_key: str = ""
    binance_secret_key: str = ""
    binance_testnet: bool = True
    
    # Twitter/X
    twitter_bearer_token: str = ""
    
    # News APIs
    newsapi_key: str = ""


class TradingSettings(BaseSettings):
    """Trading configuration"""
    # Risk management
    max_position_size: float = 0.1  # 10% of portfolio
    max_daily_loss: float = 0.05  # 5% daily loss limit
    stop_loss_percentage: float = 0.02  # 2% stop loss
    
    # Trading parameters
    min_confidence_threshold: float = 0.7
    sentiment_weight: float = 0.4
    technical_weight: float = 0.6


class AppSettings(BaseSettings):
    """Application configuration"""
    app_name: str = "Bitcoin Trading System"
    debug: bool = False
    log_level: str = "INFO"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    
    # Data collection intervals (in seconds)
    news_collection_interval: int = 300  # 5 minutes
    market_data_interval: int = 60  # 1 minute


class Settings:
    """Main settings class combining all configurations"""
    def __init__(self):
        self.database = DatabaseSettings()
        self.redis = RedisSettings()
        self.api = APISettings()
        self.trading = TradingSettings()
        self.app = AppSettings()


# Global settings instance
settings = Settings()