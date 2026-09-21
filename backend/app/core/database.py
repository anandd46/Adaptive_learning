"""
SQLAlchemy database engine and session management.
Uses async-compatible session with connection pooling.
"""
from typing import AsyncGenerator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

# ─── Engine ──────────────────────────────────────────────────────────────────
engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before use
    echo=settings.debug,  # Log SQL in development
)

# ─── Session Factory ─────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ─── Base Model ──────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Declarative base for all SQLAlchemy ORM models."""
    pass


# ─── Dependency ──────────────────────────────────────────────────────────────
def get_db() -> Session:
    """
    FastAPI dependency that provides a database session.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Verify database connectivity. Used in health check."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Database connection check failed", extra={"error": str(exc)})
        return False
