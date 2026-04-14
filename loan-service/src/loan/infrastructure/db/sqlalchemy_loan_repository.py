"""SQLAlchemy implementation of the LoanRepository port (Loan Service)."""
from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from loan.domain.isbn import Isbn
from loan.domain.loan import Loan
from loan.domain.loan_status import LoanStatus
from loan.domain.ports.loan_repository import LoanRepository
from loan.infrastructure.db.models import LoanModel


def _to_domain(model: LoanModel) -> Loan:
    """Convert a LoanModel ORM object to a Loan domain object."""
    return Loan(
        id=uuid.UUID(model.id),
        user_id=uuid.UUID(model.user_id),
        isbn=Isbn(model.isbn),
        due_date=model.due_date,
        status=LoanStatus(model.status),
        returned_at=model.returned_at,
    )


def _to_model(loan: Loan) -> LoanModel:
    """Convert a Loan domain object to a LoanModel ORM object."""
    return LoanModel(
        id=str(loan.id),
        user_id=str(loan.user_id),
        isbn=str(loan.isbn),
        status=loan.status.value,
        due_date=loan.due_date,
        returned_at=loan.returned_at,
    )


class SqlAlchemyLoanRepository(LoanRepository):
    """SQLAlchemy adapter for the LoanRepository port.

    Args:
        session: Active SQLAlchemy AsyncSession.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, loan: Loan) -> None:
        """Persist a Loan domain object (insert or update).

        Args:
            loan: The domain object to persist.
        """
        existing = await self._session.get(LoanModel, str(loan.id))
        if existing:
            existing.status = loan.status.value
            existing.returned_at = loan.returned_at
        else:
            self._session.add(_to_model(loan))
        await self._session.commit()

    async def find_by_id(self, loan_id: uuid.UUID) -> Loan | None:
        """Load a Loan by ID.

        Args:
            loan_id: The loan's UUID.

        Returns:
            The matching Loan domain object, or None if not found.
        """
        model = await self._session.get(LoanModel, str(loan_id))
        if model is None:
            return None
        return _to_domain(model)

    async def find_by_user_id(
        self,
        user_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Loan], int]:
        """Return all loans for a given user (paginated).

        Args:
            user_id: The user's UUID.
            page: Page number (1-based).
            page_size: Number of items per page.

        Returns:
            Tuple of (list of Loan objects, total count).
        """
        stmt = select(LoanModel).where(LoanModel.user_id == str(user_id))
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        total = len(models)
        start = (page - 1) * page_size
        return [_to_domain(m) for m in models[start : start + page_size]], total

    async def find_overdue(self) -> Sequence[Loan]:
        """Return all active loans whose due date has passed.

        Returns:
            Sequence of overdue Loan domain objects.
        """
        today = date.today()
        stmt = select(LoanModel).where(
            LoanModel.status == LoanStatus.ACTIVE.value,
            LoanModel.due_date < today,
        )
        result = await self._session.execute(stmt)
        return [_to_domain(m) for m in result.scalars().all()]

