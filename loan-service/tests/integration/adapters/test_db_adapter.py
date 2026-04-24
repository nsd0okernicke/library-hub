"""Integration test for the DB adapter of the Loan Service.

Tests the SQLAlchemy repository against a real PostgreSQL instance via Testcontainers.
"""
import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from loan.domain.isbn import Isbn
from loan.domain.loan import Loan
from loan.domain.loan_status import LoanStatus
from loan.infrastructure.db.models import Base
from loan.infrastructure.db.sqlalchemy_loan_repository import SqlAlchemyLoanRepository


@pytest.mark.asyncio
async def test_loan_db_adapter_integration(postgres_url: str) -> None:
    """Loan repository saves and retrieves a loan from real PostgreSQL."""
    engine = create_async_engine(postgres_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    loan_id = uuid.uuid4()
    user_id = uuid.uuid4()

    async with async_session() as session:
        repo = SqlAlchemyLoanRepository(session)
        loan = Loan(
            id=loan_id,
            user_id=user_id,
            isbn=Isbn("978-0-596-51774-8"),
            due_date=date(2026, 12, 31),
            status=LoanStatus.PENDING,
        )
        await repo.save(loan)
        found = await repo.find_by_id(loan_id)

    await engine.dispose()

    assert found is not None
    assert found.id == loan_id
    assert found.status == LoanStatus.PENDING
