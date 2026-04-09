"""Domain model: BookStock entity (Catalog Service).

Tracks the number of available copies for a specific book.
"""

from __future__ import annotations

from dataclasses import dataclass

from catalog.domain.isbn import Isbn


@dataclass
class BookStock:
    """Mutable domain entity tracking available copies of a book.

    Attributes:
        isbn: Validated ISBN value object of the corresponding book.
        available_count: Number of currently available copies (must be ≥ 0).

    Raises:
        ValueError: If *available_count* is negative on construction.
    """

    isbn: Isbn
    available_count: int

    def __post_init__(self) -> None:
        """Validate that available_count is not negative."""
        if self.available_count < 0:
            raise ValueError(
                f"available_count must be >= 0, got {self.available_count}"
            )

    def is_available(self) -> bool:
        """Return True if at least one copy is available.

        Returns:
            True when available_count > 0, False otherwise.
        """
        return self.available_count > 0

    def reserve(self) -> None:
        """Decrease available_count by 1 (book is being borrowed).

        Raises:
            ValueError: If the book is out of stock.
        """
        if self.available_count == 0:
            raise ValueError(f"Book {str(self.isbn)!r} is out of stock")
        self.available_count -= 1

    def return_book(self) -> None:
        """Increase available_count by 1 (book has been returned).

        Returns:
            None
        """
        self.available_count += 1

