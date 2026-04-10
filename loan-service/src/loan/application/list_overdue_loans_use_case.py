"""Application Use Case: ListOverdueLoansUseCase (Loan Service).

Implements LOAN-5 – Überfällige Ausleihen einsehen (Admin).
"""

from __future__ import annotations

from collections.abc import Sequence

from loan.domain.loan import Loan
from loan.domain.ports.loan_repository import LoanRepository


class ListOverdueLoansUseCase:
    """Return all ACTIVE loans whose due_date is in the past."""

    def __init__(self, loan_repo: LoanRepository) -> None:
        self._loan_repo = loan_repo

    async def execute(self) -> Sequence[Loan]:
        """Fetch all overdue loans.

        Returns:
            Sequence of Loan entities where status=ACTIVE and due_date < today.
        """
        return await self._loan_repo.find_overdue()

