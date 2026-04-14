"""conftest.py for API tests of the Loan Service.

Provides shared fixtures for all API tests, in particular
dependency overrides with in-memory fake repositories.
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
    """Replace real repositories with in-memory fakes for all API tests.

    Yields:
        None – cleans up dependency overrides after each test.
    """
    loan_repo = InMemoryLoanRepository()
    user_repo = InMemoryUserRepository()
    publisher = InMemoryMessagePublisher()
    app.dependency_overrides[get_loan_repo] = lambda: loan_repo
    app.dependency_overrides[get_publisher] = lambda: publisher
    app.dependency_overrides[get_user_repo] = lambda: user_repo
    yield
    app.dependency_overrides.clear()

