"""Application Use Case: ReturnLoanUseCase (Loan Service).

Implements LOAN-4 – Buch zurückgeben: ACTIVE → RETURNED + BookReturned publizieren.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from loan.domain.loan import Loan
from loan.domain.ports.loan_repository import LoanRepository
from loan.domain.ports.message_publisher import MessagePublisher


class ReturnLoanUseCase:
    """Return a borrowed book and publish a BookReturned event.

    Raises:
        ValueError: If the loan is not found (→ HTTP 404) or the
            status transition is invalid (→ HTTP 409).
    """

    def __init__(
        self,
        loan_repo: LoanRepository,
        publisher: MessagePublisher,
    ) -> None:
        self._loan_repo = loan_repo
        self._publisher = publisher

    async def execute(self, *, loan_id: uuid.UUID) -> Loan:
        """Mark the loan as RETURNED and publish BookReturned.

        Args:
            loan_id: UUID of the loan to close.

        Returns:
            The updated Loan entity with status RETURNED.

        Raises:
            ValueError: If the loan is not found or already returned/rejected.
        """
        loan = await self._loan_repo.find_by_id(loan_id)
        if loan is None:
            raise ValueError(f"Loan {loan_id} not found")

        loan.return_book()  # raises ValueError on invalid transition
        await self._loan_repo.save(loan)

        await self._publisher.publish(
            "book.returned",
            {
                "event_type": "BookReturned",
                "version": "1.0",
                "occurred_at": datetime.now(UTC).isoformat(),
                "loan_id": str(loan.id),
                "isbn": str(loan.isbn),
            },
        )

        return loan
