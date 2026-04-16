"""Application Use Case: CheckAvailabilityUseCase (Catalog Service).

Implements CAT-2 – Check the availability of a book by ISBN.
"""

from __future__ import annotations

from catalog.domain.isbn import Isbn
from catalog.domain.ports.book_stock_repository import BookStockRepository


class CheckAvailabilityUseCase:
    """Return the number of available copies for a given ISBN.

    Raises:
        ValueError: If no stock entry exists for the ISBN (→ HTTP 404).
    """

    def __init__(self, stock_repo: BookStockRepository) -> None:
        self._stock_repo = stock_repo

    async def execute(self, isbn: Isbn) -> int:
        """Return available_count for the given ISBN.

        Args:
            isbn: The ISBN value object to check.

        Returns:
            Number of currently available copies.

        Raises:
            ValueError: If no stock record is found.
        """
        stock = await self._stock_repo.find_by_isbn(isbn)
        if stock is None:
            raise ValueError(f"No stock found for ISBN {isbn}")
        return stock.available_count
