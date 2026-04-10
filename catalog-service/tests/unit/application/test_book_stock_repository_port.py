"""Contract-Tests für den BookStockRepository-Port (Catalog Service).

🔴 RED-Phase: Diese Tests müssen FEHLSCHLAGEN, bevor die Implementierung beginnt.
Getestete Klasse: catalog.ports.book_stock_repository.BookStockRepository
"""

from __future__ import annotations

import pytest

from catalog.domain.book_stock import BookStock
from catalog.domain.isbn import Isbn
from catalog.domain.ports.book_stock_repository import BookStockRepository

_ISBN = Isbn("978-3-16-148410-0")
_ISBN_B = Isbn("978-0-13-468599-1")


class FakeBookStockRepository(BookStockRepository):
    """In-Memory-Implementierung des BookStockRepository-Ports für Tests."""

    def __init__(self) -> None:
        self._store: dict[str, BookStock] = {}

    async def save(self, stock: BookStock) -> None:
        self._store[stock.isbn.digits] = stock

    async def find_by_isbn(self, isbn: Isbn) -> BookStock | None:
        return self._store.get(isbn.digits)


class TestBookStockRepositoryIsAbstract:
    """Der Port muss ein abstraktes Interface sein."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """BookStockRepository kann nicht direkt instanziiert werden."""
        with pytest.raises(TypeError):
            BookStockRepository()  # type: ignore[abstract]

    def test_fake_can_be_instantiated(self) -> None:
        """Eine konkrete Implementierung kann instanziiert werden."""
        repo = FakeBookStockRepository()
        assert repo is not None


class TestBookStockRepositoryContract:
    """Vertrag: FakeBookStockRepository – alle Port-Methoden korrekt."""

    @pytest.fixture
    def repo(self) -> FakeBookStockRepository:
        return FakeBookStockRepository()

    @pytest.mark.asyncio
    async def test_save_and_find_by_isbn(self, repo: FakeBookStockRepository) -> None:
        """save() + find_by_isbn() – Stock speichern und abrufen."""
        stock = BookStock(isbn=_ISBN, available_count=3)
        await repo.save(stock)
        result = await repo.find_by_isbn(_ISBN)
        assert result is not None
        assert result.available_count == 3

    @pytest.mark.asyncio
    async def test_find_by_isbn_unknown_returns_none(
        self, repo: FakeBookStockRepository
    ) -> None:
        """find_by_isbn() gibt None zurück für unbekannte ISBN."""
        result = await repo.find_by_isbn(_ISBN)
        assert result is None

    @pytest.mark.asyncio
    async def test_save_updates_existing_stock(
        self, repo: FakeBookStockRepository
    ) -> None:
        """save() überschreibt einen vorhandenen Eintrag."""
        stock = BookStock(isbn=_ISBN, available_count=3)
        await repo.save(stock)
        stock.reserve()
        await repo.save(stock)
        result = await repo.find_by_isbn(_ISBN)
        assert result is not None
        assert result.available_count == 2

