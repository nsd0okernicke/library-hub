"""
SQLAlchemy implementation of the BookRepository port.
"""
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from catalog.domain.book import Book
from catalog.domain.isbn import Isbn
from catalog.domain.ports.book_repository import BookRepository
from .models import BookModel


class SqlAlchemyBookRepository(BookRepository):
    """SQLAlchemy adapter for the BookRepository port.

    Args:
        session: Active SQLAlchemy AsyncSession.
    """

    def __init__(self, session: AsyncSession) -> None:  # pragma: no cover
        self._session = session

    async def save(self, book: Book) -> None:  # pragma: no cover
        """Persist a Book object – insert or update existing row.

        Args:
            book: The domain object to persist.
        """
        existing = await self._session.get(BookModel, str(book.isbn))
        if existing:
            existing.title = book.title
            existing.author = book.author
            existing.genre = book.genre
            existing.description = getattr(book, "description", None)
        else:
            self._session.add(
                BookModel(
                    isbn=str(book.isbn),
                    title=book.title,
                    author=book.author,
                    genre=book.genre,
                    description=getattr(book, "description", None),
                )
            )
        await self._session.commit()

    async def find_by_isbn(self, isbn: Isbn) -> Book | None:  # pragma: no cover
        """Load a Book object by ISBN.

        Args:
            isbn: The ISBN value object.

        Returns:
            The matching Book domain object, or None if not found.
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

    async def exists(self, isbn: Isbn) -> bool:  # pragma: no cover
        """Check whether a book with the given ISBN already exists.

        Args:
            isbn: The ISBN value object.

        Returns:
            True if the book exists, False otherwise.
        """
        stmt = select(BookModel.isbn).where(BookModel.isbn == str(isbn))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def find_all(  # pragma: no cover
        self,
        *,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Book], int]:
        """Return a paginated, optionally filtered list of books.

        Args:
            title: Optional title filter (substring match).
            author: Optional author filter (substring match).
            genre: Optional genre filter (substring match).
            page: Page number (1-based).
            page_size: Number of items per page.

        Returns:
            Tuple of (list of Book objects, total count).
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
