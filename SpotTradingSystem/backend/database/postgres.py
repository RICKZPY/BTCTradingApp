"""
PostgreSQL database connection and session management
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import structlog

from config import settings

logger = structlog.get_logger(__name__)

# Database engine
engine = create_engine(
    settings.database.postgres_url,
    poolclass=StaticPool,
    pool_pre_ping=True,
    echo=settings.app.debug
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Database session error", error=str(e))
        raise
    finally:
        db.close()


def init_database():
    """
    Initialize database tables
    """
    try:
        # Import all models to ensure they are registered
        import database.models  # noqa
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


def test_connection() -> bool:
    """
    Test database connection
    """
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("PostgreSQL connection successful")
        return True
    except Exception as e:
        logger.error("PostgreSQL connection failed", error=str(e))
        return False