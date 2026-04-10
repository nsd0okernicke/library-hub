"""Application Use Case: RequestLoanUseCase (Loan Service).

Implements LOAN-1 – Buch ausleihen.
Creates a PENDING loan, sets due_date, publishes BookLoanRequested.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

from loan.domain.isbn import Isbn
from loan.domain.loan import Loan
from loan.domain.ports.loan_repository import LoanRepository
from loan.domain.ports.message_publisher import MessagePublisher


class RequestLoanUseCase:
    """Initiate a loan request and publish a BookLoanRequested event.

    The loan is stored with status PENDING immediately.
    The Catalog Service will respond asynchronously with BookReserved
    or BookOutOfStock, which triggers ActivateLoanUseCase / RejectLoanUseCase.
    """

    def __init__(
        self,
        loan_repo: LoanRepository,
        publisher: MessagePublisher,
        loan_duration_days: int = 28,
    ) -> None:
        """Initialise with port dependencies and configuration.

        Args:
            loan_repo: Repository for Loan persistence.
            publisher: Message broker port for publishing events.
            loan_duration_days: Number of days until the loan is due.
        """
        self._loan_repo = loan_repo
        self._publisher = publisher
        self._loan_duration_days = loan_duration_days

    async def execute(self, *, isbn: Isbn, user_id: uuid.UUID) -> Loan:
        """Create a PENDING loan and publish BookLoanRequested.

        Args:
            isbn: ISBN of the book to borrow.
            user_id: UUID of the borrowing user.

        Returns:
            The newly created Loan entity with status PENDING.
        """
        due_date = date.today() + timedelta(days=self._loan_duration_days)
        loan = Loan(user_id=user_id, isbn=isbn, due_date=due_date)

        await self._loan_repo.save(loan)

        await self._publisher.publish(
            "book.loan.requested",
            {
                "event_type": "BookLoanRequested",
                "version": "1.0",
                "occurred_at": datetime.now(UTC).isoformat(),
                "loan_id": str(loan.id),
                "isbn": str(isbn),
                "user_id": str(user_id),
            },
        )

        return loan

