"""Unit tests for SearchBooksUseCase, GetBookUseCase, CheckAvailabilityUseCase
(Catalog Service).

Tested:
  catalog.application.search_books_use_case.SearchBooksUseCase  (CAT-1)
  catalog.application.get_book_use_case.GetBookUseCase           (CAT-5)
  catalog.application.check_availability_use_case.CheckAvailabilityUseCase (CAT-2)
"""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from catalog.application.check_availability_use_case import CheckAvailabilityUseCase
from catalog.application.get_book_use_case import GetBookUseCase
from catalog.application.search_books_use_case import SearchBooksUseCase
from catalog.domain.book import Book
from catalog.domain.book_stock import BookStock
from catalog.domain.isbn import Isbn
from catalog.domain.ports.book_repository import BookRepository
from catalog.domain.ports.book_stock_repository import BookStockRepository

_ISBN_A = Isbn("978-3-16-148410-0")
_ISBN_B = Isbn("978-0-13-468599-1")
_BOOK_A = Book(
    isbn=_ISBN_A, title="Clean Architecture", author="Robert C. Martin", genre="SE"
)
_BOOK_B = Book(
    isbn=_ISBN_B, title="The Pragmatic Programmer", author="Hunt & Thomas", genre="SE"
)


class FakeBookRepository(BookRepository):
    def __init__(self, books: list[Book] | None = None) -> None:
        self._store: dict[str, Book] = {b.isbn.digits: b for b in (books or [])}

    async def save(self, book: Book) -> None:
        self._store[book.isbn.digits] = book

    async def find_by_isbn(self, isbn: Isbn) -> Book | None:
        return self._store.get(isbn.digits)

    async def find_all(
        self, *, title: str | None = None, author: str | None = None,
        genre: str | None = None, page: int = 1, page_size: int = 20,
    ) -> tuple[Sequence[Book], int]:
        results = list(self._store.values())
        if title:
            results = [b for b in results if title.lower() in b.title.lower()]
        if author:
            results = [b for b in results if author.lower() in b.author.lower()]
        if genre:
            results = [b for b in results if genre.lower() in b.genre.lower()]
        total = len(results)
        start = (page - 1) * page_size
        return results[start : start + page_size], total

    async def exists(self, isbn: Isbn) -> bool:
        return isbn.digits in self._store


class FakeBookStockRepository(BookStockRepository):
    def __init__(self, stocks: list[BookStock] | None = None) -> None:
        self._store: dict[str, BookStock] = {
            s.isbn.digits: s for s in (stocks or [])
        }

    async def save(self, stock: BookStock) -> None:
        self._store[stock.isbn.digits] = stock

    async def find_by_isbn(self, isbn: Isbn) -> BookStock | None:
        return self._store.get(isbn.digits)


# ── SearchBooksUseCase ────────────────────────────────────────────────────────

class TestSearchBooksUseCase:
    """CAT-1: Search, filter and paginate books."""

    @pytest.fixture
    def use_case(self) -> SearchBooksUseCase:
        return SearchBooksUseCase(
            book_repo=FakeBookRepository(books=[_BOOK_A, _BOOK_B])
        )

    @pytest.mark.asyncio
    async def test_search_returns_all_books(
        self, use_case: SearchBooksUseCase
    ) -> None:
        """Without filters all books are returned."""
        books, total = await use_case.execute()
        assert total == 2

    @pytest.mark.asyncio
    async def test_search_filter_by_title(
        self, use_case: SearchBooksUseCase
    ) -> None:
        """Title filter (case-insensitive)."""
        books, total = await use_case.execute(title="clean")
        assert total == 1
        assert list(books)[0] == _BOOK_A

    @pytest.mark.asyncio
    async def test_search_filter_by_author(
        self, use_case: SearchBooksUseCase
    ) -> None:
        """Author filter."""
        books, total = await use_case.execute(author="martin")
        assert total == 1

    @pytest.mark.asyncio
    async def test_search_empty_result(
        self, use_case: SearchBooksUseCase
    ) -> None:
        """No match returns an empty list without raising an error."""
        books, total = await use_case.execute(title="nonexistent")
        assert total == 0
        assert list(books) == []

    @pytest.mark.asyncio
    async def test_search_pagination(
        self, use_case: SearchBooksUseCase
    ) -> None:
        """Pagination: page_size=1 returns 1 item, total=2."""
        books, total = await use_case.execute(page=1, page_size=1)
        assert total == 2
        assert len(list(books)) == 1


# ── GetBookUseCase ────────────────────────────────────────────────────────────

class TestGetBookUseCase:
    """CAT-5: Retrieve a single book by ISBN."""

    @pytest.fixture
    def use_case(self) -> GetBookUseCase:
        return GetBookUseCase(
            book_repo=FakeBookRepository(books=[_BOOK_A])
        )

    @pytest.mark.asyncio
    async def test_get_existing_book(self, use_case: GetBookUseCase) -> None:
        """Known ISBN returns the book."""
        book = await use_case.execute(_ISBN_A)
        assert book == _BOOK_A

    @pytest.mark.asyncio
    async def test_get_unknown_book_raises(
        self, use_case: GetBookUseCase
    ) -> None:
        """Unknown ISBN raises ValueError (→ HTTP 404)."""
        with pytest.raises(ValueError, match="[Nn]ot found|[Nn]o book"):
            await use_case.execute(_ISBN_B)


# ── CheckAvailabilityUseCase ──────────────────────────────────────────────────

class TestCheckAvailabilityUseCase:
    """CAT-2: Check the availability of a book."""

    @pytest.fixture
    def use_case(self) -> CheckAvailabilityUseCase:
        stock = BookStock(isbn=_ISBN_A, available_count=3)
        return CheckAvailabilityUseCase(
            stock_repo=FakeBookStockRepository(stocks=[stock])
        )

    @pytest.mark.asyncio
    async def test_check_known_isbn(
        self, use_case: CheckAvailabilityUseCase
    ) -> None:
        """Known ISBN returns available_count."""
        count = await use_case.execute(_ISBN_A)
        assert count == 3

    @pytest.mark.asyncio
    async def test_check_unknown_isbn_raises(
        self, use_case: CheckAvailabilityUseCase
    ) -> None:
        """Unknown ISBN raises ValueError (→ HTTP 404)."""
        with pytest.raises(ValueError, match="[Nn]ot found|[Nn]o stock"):
            await use_case.execute(_ISBN_B)

