"""Application Use Case: ActivateLoanUseCase (Loan Service).

Triggered by incoming BookReserved event → PENDING → ACTIVE.
"""

from __future__ import annotations

import uuid

from loan.domain.loan import Loan
from loan.domain.ports.loan_repository import LoanRepository


class ActivateLoanUseCase:
    """Transition a Loan from PENDING to ACTIVE.

    Called when a BookReserved event is received from the Catalog Service.

    Raises:
        ValueError: If the loan is not found or not in PENDING state.
    """

    def __init__(self, loan_repo: LoanRepository) -> None:
        self._loan_repo = loan_repo

    async def execute(self, *, loan_id: uuid.UUID) -> Loan:
        """Activate the loan with the given ID.

        Args:
            loan_id: UUID of the loan to activate.

        Returns:
            The updated Loan entity with status ACTIVE.

        Raises:
            ValueError: If the loan is not found or transition is invalid.
        """
        loan = await self._loan_repo.find_by_id(loan_id)
        if loan is None:
            raise ValueError(f"Loan {loan_id} not found")

        loan.activate()
        await self._loan_repo.save(loan)
        return loan
