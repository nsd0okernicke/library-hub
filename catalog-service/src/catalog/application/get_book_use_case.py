"""Application Use Case: GetBookUseCase (Catalog Service).

Implements CAT-5 – Einzelnes Buch per ISBN abrufen.
"""

from __future__ import annotations

from catalog.domain.book import Book
from catalog.domain.isbn import Isbn
from catalog.domain.ports.book_repository import BookRepository


class GetBookUseCase:
    """Retrieve a single Book by ISBN.

    Raises:
        ValueError: If no book with the given ISBN exists (→ HTTP 404).
    """

    def __init__(self, book_repo: BookRepository) -> None:
        self._book_repo = book_repo

    async def execute(self, isbn: Isbn) -> Book:
        """Fetch a Book by its ISBN.

        Args:
            isbn: The ISBN value object to look up.

        Returns:
            The matching Book entity.

        Raises:
            ValueError: If the book is not found.
        """
        book = await self._book_repo.find_by_isbn(isbn)
        if book is None:
            raise ValueError(f"No book found for ISBN {isbn}")
        return book

