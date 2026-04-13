"""
Session- und Engine-Management für SQLAlchemy (async).
"""
from collections.abc import AsyncGenerator
import os

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:password@localhost:5432/catalog_db",
)

engine = create_async_engine(DATABASE_URL, echo=True, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI-Dependency: liefert eine SQLAlchemy-AsyncSession pro Request.

    Yields:
        AsyncSession: Die aktive DB-Session.
    """
    async with AsyncSessionLocal() as session:
        yield session

