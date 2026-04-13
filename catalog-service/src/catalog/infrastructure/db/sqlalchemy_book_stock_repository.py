"""
SQLAlchemy-Implementierung des BookStockRepository-Ports.

Diese Klasse implementiert die Persistenz für BookStock-Objekte mittels SQLAlchemy (async) und übernimmt das Mapping zwischen ORM-Model und Domain-Objekt.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from catalog.domain.book_stock import BookStock
from catalog.domain.isbn import Isbn
from catalog.domain.ports.book_stock_repository import BookStockRepository
from .models import BookStockModel

class SqlAlchemyBookStockRepository(BookStockRepository):
    """Repository für BookStock-Objekte mit SQLAlchemy (async).

    Args:
        session (AsyncSession): Die SQLAlchemy-Session für DB-Zugriffe.
    """
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, stock: BookStock) -> None:
        """Persistiert ein BookStock-Objekt als ORM-Model.

        Args:
            stock (BookStock): Das zu speichernde Domain-Objekt.
        """
        model = BookStockModel(
            isbn=str(stock.isbn),
            available_count=stock.available_count,
        )
        self._session.add(model)
        await self._session.commit()

    async def find_by_isbn(self, isbn: Isbn) -> BookStock | None:
        """Lädt ein BookStock-Objekt anhand der ISBN.

        Args:
            isbn (Isbn): Die ISBN als Value Object.

        Returns:
            BookStock | None: Das gefundene Domain-Objekt oder None.
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
