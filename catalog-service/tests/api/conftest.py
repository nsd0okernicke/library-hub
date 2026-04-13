"""conftest.py für API-Tests des Catalog Service.

Stellt gemeinsame Fixtures für alle API-Tests bereit,
insbesondere Dependency-Overrides mit In-Memory-Fake-Repositories.
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
    """Ersetzt echte DB-Repositories durch In-Memory-Fakes für alle API-Tests.

    Yields:
        None – räumt Dependency-Overrides nach dem Test auf.
    """
    book_repo = InMemoryBookRepository()
    stock_repo = InMemoryBookStockRepository()
    app.dependency_overrides[get_book_repo] = lambda: book_repo
    app.dependency_overrides[get_stock_repo] = lambda: stock_repo
    yield
    app.dependency_overrides.clear()

