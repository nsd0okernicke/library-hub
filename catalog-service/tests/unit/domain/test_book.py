"""Unit-Tests für das Book-Domain-Modell (Catalog Service).

🔵 REFACTOR: isbn-Felder verwenden jetzt das Isbn Value Object.
Getestete Klasse: catalog.domain.book.Book
"""

import pytest

from catalog.domain.book import Book
from catalog.domain.isbn import Isbn

_ISBN_A = Isbn("978-3-16-148410-0")
_ISBN_B = Isbn("978-0-13-468599-1")


class TestBookCreation:
    """Tests für die Erzeugung eines Book-Domänenobjekts."""

    def test_create_book_with_all_fields(self) -> None:
        """Book kann mit allen Feldern erzeugt werden."""
        book = Book(
            isbn=_ISBN_A,
            title="Clean Architecture",
            author="Robert C. Martin",
            genre="Software Engineering",
            description="A craftsman's guide to software structure and design.",
        )
        assert book.isbn == _ISBN_A
        assert book.title == "Clean Architecture"
        assert book.author == "Robert C. Martin"
        assert book.genre == "Software Engineering"
        assert book.description == "A craftsman's guide to software structure and design."

    def test_create_book_without_description(self) -> None:
        """Description ist optional (Standard: None)."""
        book = Book(isbn=_ISBN_A, title="Clean Architecture", author="Robert C. Martin", genre="Software Engineering")
        assert book.description is None

    def test_book_isbn_is_immutable(self) -> None:
        """ISBN darf nach der Erzeugung nicht verändert werden."""
        book = Book(isbn=_ISBN_A, title="Clean Architecture", author="Robert C. Martin", genre="Software Engineering")
        with pytest.raises((AttributeError, TypeError)):
            book.isbn = _ISBN_B  # type: ignore[misc]

    def test_book_equality_by_isbn(self) -> None:
        """Zwei Books mit gleicher ISBN gelten als gleich."""
        book_a = Book(isbn=_ISBN_A, title="Clean Architecture", author="Robert C. Martin", genre="SE")
        book_b = Book(isbn=_ISBN_A, title="Different Title", author="Different Author", genre="Other")
        assert book_a == book_b

    def test_books_with_different_isbn_are_not_equal(self) -> None:
        """Zwei Books mit unterschiedlicher ISBN gelten nicht als gleich."""
        book_a = Book(isbn=_ISBN_A, title="Clean Architecture", author="Robert C. Martin", genre="SE")
        book_b = Book(isbn=_ISBN_B, title="Clean Architecture", author="Robert C. Martin", genre="SE")
        assert book_a != book_b

    def test_book_repr_contains_isbn_and_title(self) -> None:
        """__repr__ beginnt mit 'Book(' und enthält ISBN und Titel (kein XX-Präfix)."""
        book = Book(isbn=_ISBN_A, title="Clean Architecture", author="Robert C. Martin", genre="SE")
        r = repr(book)
        assert r.startswith("Book(")
        assert "978" in r
        assert "Clean Architecture" in r
        assert not r.startswith("XX")

    def test_book_not_equal_to_non_book(self) -> None:
        """Book verglichen mit einem Nicht-Book gibt NotImplemented zurück."""
        book = Book(isbn=_ISBN_A, title="Clean Architecture", author="Robert C. Martin", genre="SE")
        assert book.__eq__("not-a-book") is NotImplemented

    def test_book_hashable_and_usable_in_set(self) -> None:
        """Book ist hashbar und kann in einem Set verwendet werden."""
        book_a = Book(isbn=_ISBN_A, title="A", author="A", genre="A")
        book_b = Book(isbn=_ISBN_A, title="B", author="B", genre="B")
        book_c = Book(isbn=_ISBN_B, title="C", author="C", genre="C")
        book_set = {book_a, book_b, book_c}
        assert len(book_set) == 2
