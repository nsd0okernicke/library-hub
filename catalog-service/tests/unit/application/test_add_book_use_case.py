"""Unit-Tests für den AddBookUseCase (Catalog Service).

🔴 RED-Phase: Tests müssen FEHLSCHLAGEN, bevor die Implementierung beginnt.
Testet: catalog.application.add_book_use_case.AddBookUseCase

Use Case: CAT-3 – Buch anlegen (requirements.md §5)
"""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from catalog.application.add_book_use_case import AddBookUseCase
from catalog.domain.book import Book
from catalog.domain.book_stock import BookStock
from catalog.domain.isbn import Isbn
from catalog.domain.ports.book_repository import BookRepository
from catalog.domain.ports.book_stock_repository import BookStockRepository

_ISBN = Isbn("978-3-16-148410-0")


# ── Fakes ────────────────────────────────────────────────────────────────────

class FakeBookRepository(BookRepository):
    def __init__(self) -> None:
        self._store: dict[str, Book] = {}

    async def save(self, book: Book) -> None:
        self._store[book.isbn.digits] = book

    async def find_by_isbn(self, isbn: Isbn) -> Book | None:
        return self._store.get(isbn.digits)

    async def find_all(self, *, title: str | None = None, author: str | None = None,
                       genre: str | None = None, page: int = 1,
                       page_size: int = 20) -> tuple[Sequence[Book], int]:
        return [], 0

    async def exists(self, isbn: Isbn) -> bool:
        return isbn.digits in self._store


class FakeBookStockRepository(BookStockRepository):
    def __init__(self) -> None:
        self._store: dict[str, BookStock] = {}

    async def save(self, stock: BookStock) -> None:
        self._store[stock.isbn.digits] = stock

    async def find_by_isbn(self, isbn: Isbn) -> BookStock | None:
        return self._store.get(isbn.digits)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestAddBookUseCase:
    """CAT-3: Neues Buch mit Metadaten und Anfangsbestand anlegen."""

    @pytest.fixture
    def use_case(self) -> AddBookUseCase:
        return AddBookUseCase(
            book_repo=FakeBookRepository(),
            stock_repo=FakeBookStockRepository(),
        )

    @pytest.mark.asyncio
    async def test_add_book_saves_book_and_stock(
        self, use_case: AddBookUseCase
    ) -> None:
        """Buch + Stock werden gespeichert."""
        book = await use_case.execute(
            isbn=_ISBN,
            title="Clean Architecture",
            author="Robert C. Martin",
            genre="Software Engineering",
            initial_stock=3,
        )
        assert book.isbn == _ISBN
        assert book.title == "Clean Architecture"

    @pytest.mark.asyncio
    async def test_add_book_creates_stock_entry(
        self, use_case: AddBookUseCase
    ) -> None:
        """initial_stock wird als BookStock gespeichert."""
        await use_case.execute(
            isbn=_ISBN,
            title="Clean Architecture",
            author="Robert C. Martin",
            genre="Software Engineering",
            initial_stock=5,
        )
        stock = await use_case._stock_repo.find_by_isbn(_ISBN)
        assert stock is not None
        assert stock.available_count == 5

    @pytest.mark.asyncio
    async def test_add_book_with_zero_initial_stock(
        self, use_case: AddBookUseCase
    ) -> None:
        """initial_stock=0 ist erlaubt."""
        await use_case.execute(
            isbn=_ISBN,
            title="Clean Architecture",
            author="Robert C. Martin",
            genre="Software Engineering",
            initial_stock=0,
        )
        stock = await use_case._stock_repo.find_by_isbn(_ISBN)
        assert stock is not None
        assert stock.available_count == 0

    @pytest.mark.asyncio
    async def test_add_book_duplicate_isbn_raises(
        self, use_case: AddBookUseCase
    ) -> None:
        """Doppelte ISBN wirft ValueError – Meldung beginnt mit 'Book with ISBN'."""
        await use_case.execute(
            isbn=_ISBN,
            title="Clean Architecture",
            author="Robert C. Martin",
            genre="SE",
            initial_stock=1,
        )
        with pytest.raises(ValueError) as exc_info:
            await use_case.execute(
                isbn=_ISBN,
                title="Other Title",
                author="Other Author",
                genre="SE",
                initial_stock=1,
            )
        msg = str(exc_info.value)
        assert msg.startswith("Book with ISBN")
        assert "already exists" in msg
        assert not msg.startswith("XX")

    @pytest.mark.asyncio
    async def test_add_book_with_description(
        self, use_case: AddBookUseCase
    ) -> None:
        """Optionale Beschreibung wird gespeichert."""
        book = await use_case.execute(
            isbn=_ISBN,
            title="Clean Architecture",
            author="Robert C. Martin",
            genre="SE",
            initial_stock=1,
            description="A great book.",
        )
        assert book.description == "A great book."


