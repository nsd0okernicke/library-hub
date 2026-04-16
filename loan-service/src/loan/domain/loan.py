"""Domain model: Loan entity (Loan Service).

A Loan tracks a single book borrowing transaction and its lifecycle
according to the state machine defined in concept.md.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date

from loan.domain.isbn import Isbn
from loan.domain.loan_status import LoanStatus


@dataclass
class Loan:
    """Domain entity representing a book loan transaction.

    State transitions (see concept.md – LoanStatus):
        PENDING  → ACTIVE    via activate()
        PENDING  → REJECTED  via reject()
        ACTIVE   → RETURNED  via return_book()

    Attributes:
        user_id: UUID of the borrowing user.
        isbn: Validated ISBN value object of the book being borrowed.
        due_date: Date by which the book must be returned.
        id: UUID primary key – auto-generated if not provided.
        status: Current loan state (default: PENDING).
        returned_at: Date the book was returned (None until returned).

    Raises:
        ValueError: On invalid state transitions.
    """

    user_id: uuid.UUID
    isbn: Isbn
    due_date: date
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: LoanStatus = field(default=LoanStatus.PENDING)
    returned_at: date | None = field(default=None)

    def activate(self) -> None:
        """Transition from PENDING to ACTIVE (BookReserved received).

        Raises:
            ValueError: If current status is not PENDING.
        """
        if self.status != LoanStatus.PENDING:
            raise ValueError(f"Invalid status transition: {self.status.value} → ACTIVE")
        self.status = LoanStatus.ACTIVE

    def reject(self) -> None:
        """Transition from PENDING to REJECTED (BookOutOfStock received).

        Raises:
            ValueError: If current status is not PENDING.
        """
        if self.status != LoanStatus.PENDING:
            raise ValueError(
                f"Invalid status transition: {self.status.value} → REJECTED"
            )
        self.status = LoanStatus.REJECTED

    def return_book(self) -> None:
        """Transition from ACTIVE to RETURNED.

        Sets *returned_at* to today's date.

        Raises:
            ValueError: If current status is not ACTIVE.
        """
        if self.status == LoanStatus.RETURNED:
            raise ValueError("Invalid status transition: already returned")
        if self.status != LoanStatus.ACTIVE:
            raise ValueError(
                f"Invalid status transition: {self.status.value} → RETURNED "
                f"(loan is not active)"
            )
        self.status = LoanStatus.RETURNED
        self.returned_at = date.today()

    def is_overdue(self) -> bool:
        """Return True if the loan is ACTIVE and past its due date.

        Returns:
            True when status is ACTIVE and due_date < today.
        """
        return self.status == LoanStatus.ACTIVE and self.due_date < date.today()
