"""Unit tests for ReserveBookUseCase and ReturnBookUseCase (Catalog Service).

🔴 RED phase: Tests must FAIL before any implementation exists.
Tested:
  catalog.application.reserve_book_use_case.ReserveBookUseCase  (CAT-4 incoming)
  catalog.application.return_book_use_case.ReturnBookUseCase     (CAT-6)

ReserveBookUseCase: triggered by an incoming BookLoanRequested event.
  → Reserves stock and publishes BookReserved or BookOutOfStock.
ReturnBookUseCase: triggered by POST /books/{isbn}/return or a BookReturned event.
  → Increases stock by 1.
"""

from __future__ import annotations

from typing import Any

import pytest

from catalog.application.reserve_book_use_case import ReserveBookUseCase
from catalog.application.return_book_use_case import ReturnBookUseCase
from catalog.domain.book_stock import BookStock
from catalog.domain.isbn import Isbn
from catalog.domain.ports.book_stock_repository import BookStockRepository
from catalog.domain.ports.message_publisher import MessagePublisher

_ISBN = Isbn("978-3-16-148410-0")


class FakeBookStockRepository(BookStockRepository):
    def __init__(self, stocks: list[BookStock] | None = None) -> None:
        self._store: dict[str, BookStock] = {
            s.isbn.digits: s for s in (stocks or [])
        }

    async def save(self, stock: BookStock) -> None:
        self._store[stock.isbn.digits] = stock

    async def find_by_isbn(self, isbn: Isbn) -> BookStock | None:
        return self._store.get(isbn.digits)


class FakeMessagePublisher(MessagePublisher):
    def __init__(self) -> None:
        self.published: list[dict[str, Any]] = []

    async def publish(self, routing_key: str, payload: dict[str, Any]) -> None:
        self.published.append({"routing_key": routing_key, "payload": payload})


# ── ReserveBookUseCase ────────────────────────────────────────────────────────

class TestReserveBookUseCase:
    """Reserve a book – triggered by an incoming BookLoanRequested event."""

    def _make_use_case(
        self, available: int
    ) -> tuple[ReserveBookUseCase, FakeMessagePublisher]:
        stock = BookStock(isbn=_ISBN, available_count=available)
        publisher = FakeMessagePublisher()
        use_case = ReserveBookUseCase(
            stock_repo=FakeBookStockRepository(stocks=[stock]),
            publisher=publisher,
        )
        return use_case, publisher

    @pytest.mark.asyncio
    async def test_reserve_available_book_publishes_reserved(self) -> None:
        """Available book → stock -1 and BookReserved published."""
        use_case, publisher = self._make_use_case(available=2)
        await use_case.execute(isbn=_ISBN, loan_id="loan-uuid-1")
        assert len(publisher.published) == 1
        msg = publisher.published[0]
        assert msg["routing_key"] == "book.reserved"
        assert msg["payload"]["event_type"] == "BookReserved"
        assert msg["payload"]["loan_id"] == "loan-uuid-1"
        assert msg["payload"]["version"] == "1.0"

    @pytest.mark.asyncio
    async def test_reserve_decreases_stock(self) -> None:
        """Stock is decreased by 1."""
        use_case, _ = self._make_use_case(available=3)
        await use_case.execute(isbn=_ISBN, loan_id="loan-uuid-1")
        stock = await use_case._stock_repo.find_by_isbn(_ISBN)
        assert stock is not None
        assert stock.available_count == 2

    @pytest.mark.asyncio
    async def test_reserve_out_of_stock_publishes_out_of_stock(self) -> None:
        """No stock available → BookOutOfStock published, stock remains 0."""
        use_case, publisher = self._make_use_case(available=0)
        await use_case.execute(isbn=_ISBN, loan_id="loan-uuid-2")
        assert len(publisher.published) == 1
        msg = publisher.published[0]
        assert msg["routing_key"] == "book.out_of_stock"
        assert msg["payload"]["event_type"] == "BookOutOfStock"
        assert msg["payload"]["loan_id"] == "loan-uuid-2"

    @pytest.mark.asyncio
    async def test_reserve_unknown_isbn_raises(self) -> None:
        """Unknown ISBN raises ValueError."""
        use_case, _ = self._make_use_case(available=1)
        unknown = Isbn("978-0-13-468599-1")
        with pytest.raises(ValueError, match="[Nn]ot found|[Nn]o stock"):
            await use_case.execute(isbn=unknown, loan_id="loan-uuid-3")


# ── ReturnBookUseCase ─────────────────────────────────────────────────────────

class TestReturnBookUseCase:
    """CAT-6: Increase book stock on return."""

    def _make_use_case(
        self, available: int
    ) -> ReturnBookUseCase:
        stock = BookStock(isbn=_ISBN, available_count=available)
        return ReturnBookUseCase(
            stock_repo=FakeBookStockRepository(stocks=[stock]),
        )

    @pytest.mark.asyncio
    async def test_return_increases_stock(self) -> None:
        """return_book() increases stock by 1."""
        use_case = self._make_use_case(available=2)
        stock = await use_case.execute(isbn=_ISBN)
        assert stock.available_count == 3

    @pytest.mark.asyncio
    async def test_return_from_zero_increases_to_one(self) -> None:
        """Stock 0 → 1 after returning the book."""
        use_case = self._make_use_case(available=0)
        stock = await use_case.execute(isbn=_ISBN)
        assert stock.available_count == 1

    @pytest.mark.asyncio
    async def test_return_unknown_isbn_raises(self) -> None:
        """Unbekannte ISBN wirft ValueError (→ HTTP 404)."""
        use_case = self._make_use_case(available=1)
        unknown = Isbn("978-0-13-468599-1")
        with pytest.raises(ValueError, match="[Nn]ot found|[Nn]o stock"):
            await use_case.execute(isbn=unknown)

