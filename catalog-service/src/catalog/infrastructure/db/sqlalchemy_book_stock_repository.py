"""
SQLAlchemy implementation of the BookStockRepository port.

Handles persistence for BookStock objects using SQLAlchemy (async) and
maps between ORM models and domain objects.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from catalog.domain.book_stock import BookStock
from catalog.domain.isbn import Isbn
from catalog.domain.ports.book_stock_repository import BookStockRepository

from .models import BookStockModel


class SqlAlchemyBookStockRepository(BookStockRepository):
    """SQLAlchemy adapter for the BookStockRepository port.

    Args:
        session: Active SQLAlchemy AsyncSession.
    """

    def __init__(self, session: AsyncSession) -> None:  # pragma: no cover
        self._session = session

    async def save(self, stock: BookStock) -> None:  # pragma: no cover
        """Persist a BookStock object – insert or update existing row.

        Args:
            stock: The domain object to persist.
        """
        existing = await self._session.get(BookStockModel, str(stock.isbn))
        if existing:
            existing.available_count = stock.available_count
        else:
            self._session.add(
                BookStockModel(
                    isbn=str(stock.isbn),
                    available_count=stock.available_count,
                )
            )
        await self._session.commit()

    async def find_by_isbn(self, isbn: Isbn) -> BookStock | None:  # pragma: no cover
        """Load a BookStock object by ISBN.

        Args:
            isbn: The ISBN value object.

        Returns:
            The matching BookStock domain object, or None if not found.
        """
        stmt = select(BookStockModel).where(BookStockModel.isbn == str(isbn))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return BookStock(
            isbn=Isbn(model.isbn),
            available_count=model.available_count,
        )
