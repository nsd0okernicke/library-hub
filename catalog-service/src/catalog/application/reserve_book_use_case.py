"""Application Use Case: ReserveBookUseCase (Catalog Service).

Triggered by an incoming BookLoanRequested event.
Publishes BookReserved (stock available) or BookOutOfStock (no stock).
"""

from __future__ import annotations

from datetime import UTC, datetime

from catalog.domain.isbn import Isbn
from catalog.domain.ports.book_stock_repository import BookStockRepository
from catalog.domain.ports.message_publisher import MessagePublisher


class ReserveBookUseCase:
    """Reserve a book copy and publish the appropriate domain event.

    If stock is available: decrements available_count and publishes
    ``BookReserved``.
    If out of stock: publishes ``BookOutOfStock`` without changing stock.

    Raises:
        ValueError: If no stock entry exists for the ISBN.
    """

    def __init__(
        self,
        stock_repo: BookStockRepository,
        publisher: MessagePublisher,
    ) -> None:
        self._stock_repo = stock_repo
        self._publisher = publisher

    async def execute(self, *, isbn: Isbn, loan_id: str) -> None:
        """Process a loan request for the given ISBN.

        Args:
            isbn: ISBN of the requested book.
            loan_id: UUID string of the originating loan (for correlation).

        Raises:
            ValueError: If the book stock record does not exist.
        """
        stock = await self._stock_repo.find_by_isbn(isbn)
        if stock is None:
            raise ValueError(f"No stock found for ISBN {isbn}")

        occurred_at = datetime.now(UTC).isoformat()

        if stock.is_available():
            stock.reserve()
            await self._stock_repo.save(stock)
            await self._publisher.publish(
                "book.reserved",
                {
                    "event_type": "BookReserved",
                    "version": "1.0",
                    "occurred_at": occurred_at,
                    "loan_id": loan_id,
                    "isbn": str(isbn),
                },
            )
        else:
            await self._publisher.publish(
                "book.out_of_stock",
                {
                    "event_type": "BookOutOfStock",
                    "version": "1.0",
                    "occurred_at": occurred_at,
                    "loan_id": loan_id,
                    "isbn": str(isbn),
                },
            )
