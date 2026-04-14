"""Session and engine management for SQLAlchemy (async) – Loan Service."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from loan.infrastructure.config.settings import get_settings

_settings = get_settings()

engine = create_async_engine(_settings.database_url, echo=True, future=True)
AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: provides a SQLAlchemy AsyncSession per request.

    Yields:
        AsyncSession: The active database session.
    """
    async with AsyncSessionLocal() as session:  # pragma: no cover
        yield session  # pragma: no cover

