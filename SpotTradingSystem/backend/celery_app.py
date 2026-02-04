"""
Celery application configuration for async task processing
"""
from celery import Celery
from config import settings

# Create Celery app
celery_app = Celery(
    "bitcoin_trading_system",
    broker=settings.redis.redis_url,
    backend=settings.redis.redis_url,
    include=[
        "tasks.data_collection",
        "tasks.news_analysis", 
        "tasks.technical_analysis",
        "tasks.trading_execution"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task routing
celery_app.conf.task_routes = {
    "tasks.data_collection.*": {"queue": "data_collection"},
    "tasks.news_analysis.*": {"queue": "analysis"},
    "tasks.technical_analysis.*": {"queue": "analysis"},
    "tasks.trading_execution.*": {"queue": "trading"},
}

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "collect-news-data": {
        "task": "tasks.data_collection.collect_news_data",
        "schedule": settings.app.news_collection_interval,
    },
    "collect-market-data": {
        "task": "tasks.data_collection.collect_market_data",
        "schedule": settings.app.market_data_interval,
    },
    "analyze-market-conditions": {
        "task": "tasks.technical_analysis.analyze_market_conditions",
        "schedule": 300.0,  # Every 5 minutes
    },
}