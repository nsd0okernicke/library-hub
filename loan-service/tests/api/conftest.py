"""conftest.py für API-Tests des Loan Service.

Stellt gemeinsame Fixtures bereit, insbesondere Dependency-Overrides
mit In-Memory-Fake-Repositories.
"""
from collections.abc import Generator

import pytest

from loan.infrastructure.db.fake_repositories import (
    InMemoryLoanRepository,
    InMemoryMessagePublisher,
    InMemoryUserRepository,
)
from loan.infrastructure.api.routers.loans_router import (
    get_loan_repo,
    get_publisher,
)
from loan.infrastructure.api.routers.users_router import get_user_repo
from loan.main import app


@pytest.fixture(autouse=True)
def override_repositories() -> Generator[None, None, None]:
    """Ersetzt echte Repositories durch In-Memory-Fakes für alle API-Tests.

    Yields:
        None – räumt Dependency-Overrides nach dem Test auf.
    """
    loan_repo = InMemoryLoanRepository()
    user_repo = InMemoryUserRepository()
    publisher = InMemoryMessagePublisher()
    app.dependency_overrides[get_loan_repo] = lambda: loan_repo
    app.dependency_overrides[get_publisher] = lambda: publisher
    app.dependency_overrides[get_user_repo] = lambda: user_repo
    yield
    app.dependency_overrides.clear()

