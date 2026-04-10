"""Application Use Case: ListLoansUseCase (Loan Service).

Implements LOAN-3 – Alle Ausleihen eines Nutzers anzeigen (paginiert).
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from loan.domain.loan import Loan
from loan.domain.ports.loan_repository import LoanRepository


class ListLoansUseCase:
    """Return a paginated list of Loans for a given user."""

    def __init__(self, loan_repo: LoanRepository) -> None:
        self._loan_repo = loan_repo

    async def execute(
        self,
        *,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Loan], int]:
        """Fetch all loans for the given user.

        Args:
            user_id: UUID of the user.
            page: 1-based page number.
            page_size: Items per page.

        Returns:
            Tuple of (items, total_count).
        """
        return await self._loan_repo.find_by_user_id(
            user_id, page=page, page_size=page_size
        )

