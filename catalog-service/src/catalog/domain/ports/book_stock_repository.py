"""Port: BookStockRepository (Catalog Service).

Defines the abstract interface for persisting and querying BookStock entities.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from catalog.domain.book_stock import BookStock
from catalog.domain.isbn import Isbn


class BookStockRepository(ABC):
    """Abstract repository port for BookStock entities."""

    @abstractmethod
    async def save(self, stock: BookStock) -> None:
        """Persist a BookStock entry (insert or update).

        Args:
            stock: The BookStock entity to persist.
        """

    @abstractmethod
    async def find_by_isbn(self, isbn: Isbn) -> BookStock | None:
        """Retrieve a single BookStock by its ISBN.

        Args:
            isbn: The ISBN value object to look up.

        Returns:
            The matching BookStock, or None if not found.
        """
