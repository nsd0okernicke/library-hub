"""Application Use Case: GetLoanUseCase (Loan Service).

Implements LOAN-2 – Einzelne Ausleihe abrufen.
"""

from __future__ import annotations

import uuid

from loan.domain.loan import Loan
from loan.domain.ports.loan_repository import LoanRepository


class GetLoanUseCase:
    """Retrieve a single Loan by its ID.

    Raises:
        ValueError: If the loan does not exist (→ HTTP 404).
    """

    def __init__(self, loan_repo: LoanRepository) -> None:
        self._loan_repo = loan_repo

    async def execute(self, *, loan_id: uuid.UUID) -> Loan:
        """Fetch a Loan by primary key.

        Args:
            loan_id: UUID of the loan.

        Returns:
            The matching Loan entity.

        Raises:
            ValueError: If the loan is not found.
        """
        loan = await self._loan_repo.find_by_id(loan_id)
        if loan is None:
            raise ValueError(f"Loan {loan_id} not found")
        return loan

