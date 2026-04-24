"""
Integration test for the DB adapter of the Catalog Service.

Tests the SQLAlchemy repository against a real PostgreSQL instance via Testcontainers.
"""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from catalog.domain.isbn import Isbn
from catalog.domain.book import Book
from catalog.infrastructure.db.models import Base
from catalog.infrastructure.db.sqlalchemy_book_repository import SqlAlchemyBookRepository


@pytest.mark.asyncio
async def test_catalog_db_adapter_integration(postgres_url: str) -> None:
    """Book repository saves and retrieves a book from real PostgreSQL."""
    engine = create_async_engine(postgres_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        repo = SqlAlchemyBookRepository(session)
        isbn = Isbn("978-0-596-51774-8")
        book = Book(isbn=isbn, title="Test Book", author="Author", genre="Fiction", description="Desc")
        await repo.save(book)
        found = await repo.find_by_isbn(isbn)

    await engine.dispose()

    assert found is not None
    assert found.title == "Test Book"
    assert found.author == "Author"
