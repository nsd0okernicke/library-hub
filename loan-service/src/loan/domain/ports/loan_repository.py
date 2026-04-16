"""Port: LoanRepository (Loan Service).

Defines the abstract interface for persisting and querying Loan entities.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from collections.abc import Sequence

from loan.domain.loan import Loan


class LoanRepository(ABC):
    """Abstract repository port for Loan entities."""

    @abstractmethod
    async def save(self, loan: Loan) -> None:
        """Persist a Loan (insert or update).

        Args:
            loan: The Loan entity to persist.
        """

    @abstractmethod
    async def find_by_id(self, loan_id: uuid.UUID) -> Loan | None:
        """Retrieve a single Loan by its primary key.

        Args:
            loan_id: UUID of the loan.

        Returns:
            The matching Loan, or None if not found.
        """

    @abstractmethod
    async def find_by_user_id(
        self,
        user_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Loan], int]:
        """Return a paginated list of Loans belonging to a user.

        Args:
            user_id: UUID of the user.
            page: 1-based page number.
            page_size: Number of items per page.

        Returns:
            A tuple of (items, total_count).
        """

    @abstractmethod
    async def find_overdue(self) -> Sequence[Loan]:
        """Return all ACTIVE loans whose due_date is in the past.

        Returns:
            Sequence of overdue Loan entities.
        """
