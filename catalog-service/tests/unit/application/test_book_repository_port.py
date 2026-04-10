"""Contract-Tests für den BookRepository-Port (Catalog Service).

🔴 RED-Phase: Diese Tests müssen FEHLSCHLAGEN, bevor die Implementierung beginnt.
Getestete Klasse: catalog.ports.book_repository.BookRepository

Ein Port ist ein abstraktes Interface (ABC). Diese Tests stellen sicher, dass:
- Der Port nicht direkt instanziiert werden kann
- Alle Methoden mit korrekter Signatur deklariert sind
- Ein konkreter Adapter (Fake) den Port vollständig implementieren kann
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


# ── Fake-Implementierung (In-Memory) ────────────────────────────────────────

class FakeBookRepository(BookRepository):
    """In-Memory-Implementierung des BookRepository-Ports für Tests."""

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
    """Der Port muss ein abstraktes Interface sein."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """BookRepository kann nicht direkt instanziiert werden."""
        with pytest.raises(TypeError):
            BookRepository()  # type: ignore[abstract]

    def test_fake_can_be_instantiated(self) -> None:
        """Eine konkrete Implementierung kann instanziiert werden."""
        repo = FakeBookRepository()
        assert repo is not None


class TestBookRepositoryContract:
    """Vertrag: FakeBookRepository muss alle Port-Methoden korrekt implementieren."""

    @pytest.fixture
    def repo(self) -> FakeBookRepository:
        return FakeBookRepository()

    @pytest.mark.asyncio
    async def test_save_and_find_by_isbn(self, repo: FakeBookRepository) -> None:
        """save() + find_by_isbn() – Buch speichern und abrufen."""
        await repo.save(_BOOK_A)
        result = await repo.find_by_isbn(_ISBN_A)
        assert result == _BOOK_A

    @pytest.mark.asyncio
    async def test_find_by_isbn_unknown_returns_none(
        self, repo: FakeBookRepository
    ) -> None:
        """find_by_isbn() gibt None zurück für unbekannte ISBN."""
        result = await repo.find_by_isbn(_ISBN_A)
        assert result is None

    @pytest.mark.asyncio
    async def test_find_all_returns_all_books(self, repo: FakeBookRepository) -> None:
        """find_all() ohne Filter gibt alle gespeicherten Bücher zurück."""
        await repo.save(_BOOK_A)
        await repo.save(_BOOK_B)
        books, total = await repo.find_all()
        assert total == 2
        assert _BOOK_A in books
        assert _BOOK_B in books

    @pytest.mark.asyncio
    async def test_find_all_filter_by_title(self, repo: FakeBookRepository) -> None:
        """find_all() filtert nach Titel (case-insensitive)."""
        await repo.save(_BOOK_A)
        await repo.save(_BOOK_B)
        books, total = await repo.find_all(title="clean")
        assert total == 1
        assert _BOOK_A in books

    @pytest.mark.asyncio
    async def test_find_all_empty_store(self, repo: FakeBookRepository) -> None:
        """find_all() gibt leere Liste zurück wenn kein Buch gespeichert."""
        books, total = await repo.find_all()
        assert total == 0
        assert list(books) == []

    @pytest.mark.asyncio
    async def test_exists_returns_true_for_known_isbn(
        self, repo: FakeBookRepository
    ) -> None:
        """exists() gibt True zurück wenn ISBN gespeichert ist."""
        await repo.save(_BOOK_A)
        assert await repo.exists(_ISBN_A) is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_for_unknown_isbn(
        self, repo: FakeBookRepository
    ) -> None:
        """exists() gibt False zurück wenn ISBN nicht bekannt ist."""
        assert await repo.exists(_ISBN_A) is False

    @pytest.mark.asyncio
    async def test_pagination(self, repo: FakeBookRepository) -> None:
        """find_all() paginiert korrekt."""
        await repo.save(_BOOK_A)
        await repo.save(_BOOK_B)
        books, total = await repo.find_all(page=1, page_size=1)
        assert total == 2
        assert len(list(books)) == 1


