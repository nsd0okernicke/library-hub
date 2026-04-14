"""Contract tests for the BookRepository port (Catalog Service).

Tested class: catalog.domain.ports.book_repository.BookRepository

A port is an abstract interface (ABC). These tests ensure that:
- The port cannot be instantiated directly
- All methods are declared with the correct signature
- A concrete adapter (fake) can fully implement the port
"""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from catalog.domain.book import Book
from catalog.domain.isbn import Isbn
from catalog.domain.ports.book_repository import BookRepository

_ISBN_A = Isbn("978-3-16-148410-0")
_ISBN_B = Isbn("978-0-13-468599-1")

_BOOK_A = Book(
    isbn=_ISBN_A, title="Clean Architecture", author="Robert C. Martin", genre="SE"
)
_BOOK_B = Book(
    isbn=_ISBN_B, title="The Pragmatic Programmer", author="Hunt & Thomas", genre="SE"
)


# ── Fake implementation (in-memory) ─────────────────────────────────────────

class FakeBookRepository(BookRepository):
    """In-memory fake implementation of the BookRepository port for tests."""

    def __init__(self) -> None:
        self._store: dict[str, Book] = {}

    async def save(self, book: Book) -> None:
        self._store[book.isbn.digits] = book

    async def find_by_isbn(self, isbn: Isbn) -> Book | None:
        return self._store.get(isbn.digits)

    async def find_all(
        self,
        *,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        page: int = 1,
        page_size: int = 20,
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


# ── Tests ────────────────────────────────────────────────────────────────────

class TestBookRepositoryIsAbstract:
    """The port must be an abstract interface."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """BookRepository cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BookRepository()  # type: ignore[abstract]

    def test_fake_can_be_instantiated(self) -> None:
        """A concrete implementation can be instantiated."""
        repo = FakeBookRepository()
        assert repo is not None


class TestBookRepositoryContract:
    """Contract: FakeBookRepository must implement all port methods correctly."""

    @pytest.fixture
    def repo(self) -> FakeBookRepository:
        return FakeBookRepository()

    @pytest.mark.asyncio
    async def test_save_and_find_by_isbn(self, repo: FakeBookRepository) -> None:
        """save() + find_by_isbn() – store and retrieve a book."""
        await repo.save(_BOOK_A)
        result = await repo.find_by_isbn(_ISBN_A)
        assert result == _BOOK_A

    @pytest.mark.asyncio
    async def test_find_by_isbn_unknown_returns_none(
        self, repo: FakeBookRepository
    ) -> None:
        """find_by_isbn() returns None for an unknown ISBN."""
        result = await repo.find_by_isbn(_ISBN_A)
        assert result is None

    @pytest.mark.asyncio
    async def test_find_all_returns_all_books(self, repo: FakeBookRepository) -> None:
        """find_all() without filters returns all stored books."""
        await repo.save(_BOOK_A)
        await repo.save(_BOOK_B)
        books, total = await repo.find_all()
        assert total == 2
        assert _BOOK_A in books
        assert _BOOK_B in books

    @pytest.mark.asyncio
    async def test_find_all_filter_by_title(self, repo: FakeBookRepository) -> None:
        """find_all() filters by title (case-insensitive)."""
        await repo.save(_BOOK_A)
        await repo.save(_BOOK_B)
        books, total = await repo.find_all(title="clean")
        assert total == 1
        assert _BOOK_A in books

    @pytest.mark.asyncio
    async def test_find_all_empty_store(self, repo: FakeBookRepository) -> None:
        """find_all() returns an empty list when no books are stored."""
        books, total = await repo.find_all()
        assert total == 0
        assert list(books) == []

    @pytest.mark.asyncio
    async def test_exists_returns_true_for_known_isbn(
        self, repo: FakeBookRepository
    ) -> None:
        """exists() returns True when the ISBN is stored."""
        await repo.save(_BOOK_A)
        assert await repo.exists(_ISBN_A) is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_for_unknown_isbn(
        self, repo: FakeBookRepository
    ) -> None:
        """exists() returns False when the ISBN is not known."""
        assert await repo.exists(_ISBN_A) is False

    @pytest.mark.asyncio
    async def test_pagination(self, repo: FakeBookRepository) -> None:
        """find_all() paginates correctly."""
        await repo.save(_BOOK_A)
        await repo.save(_BOOK_B)
        books, total = await repo.find_all(page=1, page_size=1)
        assert total == 2
        assert len(list(books)) == 1


