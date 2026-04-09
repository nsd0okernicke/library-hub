"""Domain model: Book entity (Catalog Service).

A Book represents a library catalogue entry identified by its ISBN.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from catalog.domain.isbn import Isbn


@dataclass(frozen=True)
class Book:
    """Immutable domain entity representing a book in the catalogue.

    Equality and hashing are based solely on *isbn* so that two Book
    instances with the same ISBN are considered identical regardless of
    their other attributes.

    Attributes:
        isbn: Validated ISBN value object (primary identifier).
        title: Book title.
        author: Full name of the primary author.
        genre: Genre or subject category.
        description: Optional free-text description.
    """

    isbn: Isbn
    title: str
    author: str
    genre: str
    description: str | None = field(default=None)

    def __eq__(self, other: object) -> bool:
        """Compare books by ISBN only."""
        if not isinstance(other, Book):
            return NotImplemented
        return self.isbn == other.isbn

    def __hash__(self) -> int:
        """Hash based on ISBN only."""
        return hash(self.isbn)

    def __repr__(self) -> str:
        """Human-readable representation."""
        return f"Book(isbn={self.isbn!r}, title={self.title!r})"

