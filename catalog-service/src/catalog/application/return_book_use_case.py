"""Application Use Case: ReturnBookUseCase (Catalog Service).

Implements CAT-6 – Increase book stock by 1 on return.
Triggered by POST /books/{isbn}/return or a BookReturned event.
"""

from __future__ import annotations

from catalog.domain.book_stock import BookStock
from catalog.domain.isbn import Isbn
from catalog.domain.ports.book_stock_repository import BookStockRepository


class ReturnBookUseCase:
    """Increase the available stock of a book by one.

    Raises:
        ValueError: If no stock entry exists for the ISBN (→ HTTP 404).
    """

    def __init__(self, stock_repo: BookStockRepository) -> None:
        self._stock_repo = stock_repo

    async def execute(self, *, isbn: Isbn) -> BookStock:
        """Increment available_count for the given ISBN.

        Args:
            isbn: ISBN of the returned book.

        Returns:
            The updated BookStock entity.

        Raises:
            ValueError: If the book stock record does not exist.
        """
        stock = await self._stock_repo.find_by_isbn(isbn)
        if stock is None:
            raise ValueError(f"No stock found for ISBN {isbn}")

        stock.return_book()
        await self._stock_repo.save(stock)
        return stock
