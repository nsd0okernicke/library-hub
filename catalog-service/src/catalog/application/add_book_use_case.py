"""Application Use Case: AddBookUseCase (Catalog Service).

Implements CAT-3 – Neues Buch mit Metadaten und Anfangsbestand anlegen.
"""

from __future__ import annotations

from catalog.domain.book import Book
from catalog.domain.book_stock import BookStock
from catalog.domain.isbn import Isbn
from catalog.domain.ports.book_repository import BookRepository
from catalog.domain.ports.book_stock_repository import BookStockRepository


class AddBookUseCase:
    """Add a new book to the catalogue together with an initial stock entry.

    Raises:
        ValueError: If a book with the same ISBN already exists (→ HTTP 409).
    """

    def __init__(
        self,
        book_repo: BookRepository,
        stock_repo: BookStockRepository,
    ) -> None:
        """Initialise with required port dependencies.

        Args:
            book_repo: Repository for Book persistence.
            stock_repo: Repository for BookStock persistence.
        """
        self._book_repo = book_repo
        self._stock_repo = stock_repo

    async def execute(
        self,
        *,
        isbn: Isbn,
        title: str,
        author: str,
        genre: str,
        initial_stock: int,
        description: str | None = None,
    ) -> Book:
        """Create and persist a Book and its initial BookStock.

        Args:
            isbn: Validated ISBN value object.
            title: Book title.
            author: Primary author.
            genre: Genre or subject category.
            initial_stock: Number of available copies to start with (≥ 0).
            description: Optional free-text description.

        Returns:
            The newly created Book entity.

        Raises:
            ValueError: If the ISBN is already in the catalogue.
        """
        if await self._book_repo.exists(isbn):
            raise ValueError(
                f"Book with ISBN {isbn} already exists in the catalogue"
            )

        book = Book(
            isbn=isbn,
            title=title,
            author=author,
            genre=genre,
            description=description,
        )
        stock = BookStock(isbn=isbn, available_count=initial_stock)

        await self._book_repo.save(book)
        await self._stock_repo.save(stock)

        return book

