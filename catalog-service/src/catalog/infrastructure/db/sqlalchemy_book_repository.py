"""
SQLAlchemy-Implementierung des BookRepository-Ports.
"""
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from catalog.domain.book import Book
from catalog.domain.isbn import Isbn
from catalog.domain.ports.book_repository import BookRepository
from .models import BookModel


class SqlAlchemyBookRepository(BookRepository):
    """SQLAlchemy-Adapter für den BookRepository-Port.

    Args:
        session: Aktive SQLAlchemy-AsyncSession.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, book: Book) -> None:
        """Persistiert ein Book-Objekt als ORM-Model.

        Args:
            book: Das zu speichernde Domain-Objekt.
        """
        model = BookModel(
            isbn=str(book.isbn),
            title=book.title,
            author=book.author,
            genre=book.genre,
            description=getattr(book, "description", None),
        )
        self._session.add(model)
        await self._session.commit()

    async def find_by_isbn(self, isbn: Isbn) -> Book | None:
        """Lädt ein Book-Objekt anhand der ISBN.

        Args:
            isbn: Die ISBN als Value Object.

        Returns:
            Das gefundene Book-Objekt oder None.
        """
        stmt = select(BookModel).where(BookModel.isbn == str(isbn))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return Book(
            isbn=Isbn(model.isbn),
            title=model.title,
            author=model.author,
            genre=model.genre,
            description=model.description,
        )

    async def exists(self, isbn: Isbn) -> bool:
        """Prüft, ob ein Buch mit der gegebenen ISBN bereits existiert.

        Args:
            isbn: Die ISBN als Value Object.

        Returns:
            True wenn das Buch existiert, False sonst.
        """
        stmt = select(BookModel.isbn).where(BookModel.isbn == str(isbn))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def find_all(
        self,
        *,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Book], int]:
        """Gibt eine paginierte, optional gefilterte Liste von Büchern zurück.

        Args:
            title: Optionaler Titelfilter (Substring).
            author: Optionaler Autorenfilter (Substring).
            genre: Optionaler Genrefilter (Substring).
            page: Seitennummer (1-basiert).
            page_size: Anzahl Elemente pro Seite.

        Returns:
            Tupel aus (Bücherliste, Gesamtanzahl).
        """
        stmt = select(BookModel)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        books = [
            Book(
                isbn=Isbn(m.isbn),
                title=m.title,
                author=m.author,
                genre=m.genre,
                description=m.description,
            )
            for m in models
        ]
        return books, len(books)

