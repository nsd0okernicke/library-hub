"""In-memory fake repositories for BookRepository and BookStockRepository.

For development and testing only – not for production use.
"""
from collections.abc import Sequence
from typing import Dict
from catalog.domain.book import Book
from catalog.domain.isbn import Isbn
from catalog.domain.book_stock import BookStock
from catalog.domain.ports.book_repository import BookRepository
from catalog.domain.ports.book_stock_repository import BookStockRepository


class InMemoryBookRepository(BookRepository):
    """In-memory fake implementation of the BookRepository port."""

    def __init__(self) -> None:
        self._books: Dict[str, Book] = {}

    async def save(self, book: Book) -> None:
        self._books[str(book.isbn)] = book

    async def find_by_isbn(self, isbn: Isbn) -> Book | None:
        return self._books.get(str(isbn))

    async def exists(self, isbn: Isbn) -> bool:
        return str(isbn) in self._books

    async def find_all(
        self,
        *,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Book], int]:
        items = list(self._books.values())
        return items, len(items)


class InMemoryBookStockRepository(BookStockRepository):
    """In-memory fake implementation of the BookStockRepository port."""

    def __init__(self) -> None:
        self._stocks: Dict[str, BookStock] = {}

    async def save(self, stock: BookStock) -> None:
        self._stocks[str(stock.isbn)] = stock

    async def find_by_isbn(self, isbn: Isbn) -> BookStock | None:
        return self._stocks.get(str(isbn))
