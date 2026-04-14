"""Unit tests for the BookStock domain model (Catalog Service).

Tested class: catalog.domain.book_stock.BookStock
"""

import pytest

from catalog.domain.book_stock import BookStock
from catalog.domain.isbn import Isbn

_ISBN = Isbn("978-3-16-148410-0")


class TestBookStockCreation:
    """Tests for creating a BookStock domain object."""

    def test_create_book_stock_with_positive_count(self) -> None:
        """BookStock can be created with a positive stock count."""
        stock = BookStock(isbn=_ISBN, available_count=5)
        assert stock.isbn == _ISBN
        assert stock.available_count == 5

    def test_create_book_stock_with_zero_count(self) -> None:
        """BookStock can be created with a stock count of 0."""
        stock = BookStock(isbn=_ISBN, available_count=0)
        assert stock.available_count == 0

    def test_create_book_stock_with_negative_count_raises(self) -> None:
        """BookStock with a negative count is not allowed – message starts with 'available_count'."""
        with pytest.raises(ValueError) as exc_info:
            BookStock(isbn=_ISBN, available_count=-1)
        msg = str(exc_info.value)
        assert msg.startswith("available_count must be >= 0")
        assert not msg.startswith("XX")


class TestBookStockReserve:
    """Tests for the reserve operation (decrease stock)."""

    def test_reserve_decreases_available_count(self) -> None:
        """reserve() decreases available_count by 1."""
        stock = BookStock(isbn=_ISBN, available_count=3)
        stock.reserve()
        assert stock.available_count == 2

    def test_reserve_on_zero_stock_raises(self) -> None:
        """reserve() with stock 0 raises ValueError containing 'out of stock' (no XX prefix)."""
        stock = BookStock(isbn=_ISBN, available_count=0)
        with pytest.raises(ValueError) as exc_info:
            stock.reserve()
        msg = str(exc_info.value)
        assert "out of stock" in msg
        assert not msg.startswith("XX")

    def test_is_available_returns_true_when_stock_positive(self) -> None:
        """is_available() returns True when stock > 0."""
        stock = BookStock(isbn=_ISBN, available_count=1)
        assert stock.is_available() is True

    def test_is_available_returns_false_when_stock_zero(self) -> None:
        """is_available() returns False when stock == 0."""
        stock = BookStock(isbn=_ISBN, available_count=0)
        assert stock.is_available() is False


class TestBookStockReturn:
    """Tests for the return operation (increase stock)."""

    def test_return_book_increases_available_count(self) -> None:
        """return_book() increases available_count by 1."""
        stock = BookStock(isbn=_ISBN, available_count=2)
        stock.return_book()
        assert stock.available_count == 3

    def test_return_book_from_zero_increases_to_one(self) -> None:
        """return_book() with stock 0 increases it to 1."""
        stock = BookStock(isbn=_ISBN, available_count=0)
        stock.return_book()
        assert stock.available_count == 1
