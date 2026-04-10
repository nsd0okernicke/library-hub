"""Unit-Tests für das BookStock-Domain-Modell (Catalog Service).

🔵 REFACTOR: isbn-Felder verwenden jetzt das Isbn Value Object.
Getestete Klasse: catalog.domain.book_stock.BookStock
"""

import pytest

from catalog.domain.book_stock import BookStock
from catalog.domain.isbn import Isbn

_ISBN = Isbn("978-3-16-148410-0")


class TestBookStockCreation:
    """Tests für die Erzeugung eines BookStock-Domänenobjekts."""

    def test_create_book_stock_with_positive_count(self) -> None:
        """BookStock kann mit positivem Bestand erzeugt werden."""
        stock = BookStock(isbn=_ISBN, available_count=5)
        assert stock.isbn == _ISBN
        assert stock.available_count == 5

    def test_create_book_stock_with_zero_count(self) -> None:
        """BookStock kann mit Bestand 0 erzeugt werden."""
        stock = BookStock(isbn=_ISBN, available_count=0)
        assert stock.available_count == 0

    def test_create_book_stock_with_negative_count_raises(self) -> None:
        """BookStock mit negativem Bestand ist nicht erlaubt – Meldung beginnt mit 'available_count'."""
        with pytest.raises(ValueError) as exc_info:
            BookStock(isbn=_ISBN, available_count=-1)
        msg = str(exc_info.value)
        assert msg.startswith("available_count must be >= 0")
        assert not msg.startswith("XX")


class TestBookStockReserve:
    """Tests für den Reserve-Vorgang (Bestand verringern)."""

    def test_reserve_decreases_available_count(self) -> None:
        """reserve() verringert available_count um 1."""
        stock = BookStock(isbn=_ISBN, available_count=3)
        stock.reserve()
        assert stock.available_count == 2

    def test_reserve_on_zero_stock_raises(self) -> None:
        """reserve() bei Bestand 0 wirft ValueError mit 'out of stock' (kein XX-Präfix)."""
        stock = BookStock(isbn=_ISBN, available_count=0)
        with pytest.raises(ValueError) as exc_info:
            stock.reserve()
        msg = str(exc_info.value)
        assert "out of stock" in msg
        assert not msg.startswith("XX")

    def test_is_available_returns_true_when_stock_positive(self) -> None:
        """is_available() gibt True zurück wenn Bestand > 0."""
        stock = BookStock(isbn=_ISBN, available_count=1)
        assert stock.is_available() is True

    def test_is_available_returns_false_when_stock_zero(self) -> None:
        """is_available() gibt False zurück wenn Bestand == 0."""
        stock = BookStock(isbn=_ISBN, available_count=0)
        assert stock.is_available() is False


class TestBookStockReturn:
    """Tests für den Return-Vorgang (Bestand erhöhen)."""

    def test_return_book_increases_available_count(self) -> None:
        """return_book() erhöht available_count um 1."""
        stock = BookStock(isbn=_ISBN, available_count=2)
        stock.return_book()
        assert stock.available_count == 3

    def test_return_book_from_zero_increases_to_one(self) -> None:
        """return_book() bei Bestand 0 erhöht auf 1."""
        stock = BookStock(isbn=_ISBN, available_count=0)
        stock.return_book()
        assert stock.available_count == 1

