"""Port: BookRepository (Catalog Service).

Defines the abstract interface for persisting and querying Book entities.
Concrete implementations live in the adapters layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from catalog.domain.book import Book
from catalog.domain.isbn import Isbn


class BookRepository(ABC):
    """Abstract repository port for Book entities.

    Any adapter (SQLAlchemy, in-memory fake, etc.) must implement all
    abstract methods defined here.
    """

    @abstractmethod
    async def save(self, book: Book) -> None:
        """Persist a Book (insert or update).

        Args:
            book: The Book entity to persist.
        """

    @abstractmethod
    async def find_by_isbn(self, isbn: Isbn) -> Book | None:
        """Retrieve a single Book by its ISBN.

        Args:
            isbn: The ISBN value object to look up.

        Returns:
            The matching Book, or None if not found.
        """

    @abstractmethod
    async def find_all(
        self,
        *,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Book], int]:
        """Return a paginated, optionally filtered list of Books.

        Args:
            title: Optional case-insensitive substring filter on title.
            author: Optional case-insensitive substring filter on author.
            genre: Optional case-insensitive substring filter on genre.
            page: 1-based page number.
            page_size: Number of items per page.

        Returns:
            A tuple of (items, total_count).
        """

    @abstractmethod
    async def exists(self, isbn: Isbn) -> bool:
        """Check whether a Book with the given ISBN already exists.

        Args:
            isbn: The ISBN value object to check.

        Returns:
            True if the book exists, False otherwise.
        """

