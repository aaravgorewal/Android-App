"""
database.py — Async SQLAlchemy engine + session factory + Base declaration.

Design decisions:
- asyncpg driver for non-blocking PostgreSQL queries
- Connection pooling configured for moderate scale (10 + 20 overflow)
- pool_pre_ping=True ensures stale connections are recycled automatically
- Base defined here (not in models) to avoid circular imports
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, declared_attr

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_ENV == "development",  # SQL logging only in dev
    pool_pre_ping=True,       # Recycle dead connections silently
    pool_size=10,             # Steady-state pool size
    max_overflow=20,          # Burst capacity
    pool_recycle=1800,        # Recycle connections every 30 min (avoids idle timeouts)
    pool_timeout=30,          # Wait max 30s for a connection before raising
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,   # Avoids lazy-load errors after commit in async context
)


class Base(DeclarativeBase):
    """
    Shared declarative base.
    All models inherit from this — gives us a central place to add
    future cross-model features (e.g., soft-delete mixin, audit fields).
    """

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Auto-generates snake_case table names from class names."""
        import re
        return re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()


async def get_db() -> AsyncSession:
    """
    FastAPI dependency that yields a scoped async DB session.
    Rolls back on error, always closes on exit.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
