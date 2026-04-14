"""conftest.py for API tests of the Catalog Service.

Provides shared fixtures for all API tests, in particular
dependency overrides with in-memory fake repositories.
"""
from collections.abc import Generator

import pytest

from catalog.infrastructure.db.fake_repositories import (
    InMemoryBookRepository,
    InMemoryBookStockRepository,
)
from catalog.infrastructure.api.routers.books_router import (
    get_book_repo,
    get_stock_repo,
)
from catalog.main import app


@pytest.fixture(autouse=True)
def override_repositories() -> Generator[None, None, None]:
    """Replace real DB repositories with in-memory fakes for all API tests.

    Yields:
        None – cleans up dependency overrides after each test.
    """
    book_repo = InMemoryBookRepository()
    stock_repo = InMemoryBookStockRepository()
    app.dependency_overrides[get_book_repo] = lambda: book_repo
    app.dependency_overrides[get_stock_repo] = lambda: stock_repo
    yield
    app.dependency_overrides.clear()
