"""Catalog Service – FastAPI application entry point."""

from fastapi import Depends, FastAPI
from fastapi.openapi.utils import get_openapi
from sqlalchemy.ext.asyncio import AsyncSession

from catalog.infrastructure.api.routers.books_router import (
    get_book_repo,
    get_stock_repo,
    router as books_router,
)
from catalog.infrastructure.db.session import get_session
from catalog.infrastructure.db.sqlalchemy_book_repository import SqlAlchemyBookRepository
from catalog.infrastructure.db.sqlalchemy_book_stock_repository import (
    SqlAlchemyBookStockRepository,
)

# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="LibraryHub – Catalog Service",
    version="0.1.0",
    description=(
        "Manages the book catalogue and stock availability for the LibraryHub system.\n\n"
        "## Features\n"
        "- Add books with metadata and initial stock\n"
        "- Search and retrieve books by ISBN\n"
        "- Check real-time stock availability\n"
        "- Process book returns\n\n"
        "## Event-driven integration\n"
        "Publishes `BookReserved` / `BookOutOfStock` events and consumes "
        "`BookLoanRequested` / `BookReturned` events via RabbitMQ."
    ),
    contact={
        "name": "LibraryHub Team",
        "url": "https://github.com/your-org/library-hub",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "books",
            "description": "Book catalogue operations – search, create, retrieve and return books.",
        },
        {
            "name": "health",
            "description": "Service health check.",
        },
    ],
)


# ── Production dependency overrides ──────────────────────────────────────────

def _prod_book_repo(
    session: AsyncSession = Depends(get_session),
) -> SqlAlchemyBookRepository:
    """Production BookRepository implementation (SQLAlchemy)."""
    return SqlAlchemyBookRepository(session)


def _prod_stock_repo(
    session: AsyncSession = Depends(get_session),
) -> SqlAlchemyBookStockRepository:
    """Production BookStockRepository implementation (SQLAlchemy)."""
    return SqlAlchemyBookStockRepository(session)


app.dependency_overrides[get_book_repo] = _prod_book_repo
app.dependency_overrides[get_stock_repo] = _prod_stock_repo

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(books_router, tags=["books"])


# ── Health ────────────────────────────────────────────────────────────────────

@app.get(
    "/health",
    tags=["health"],
    summary="Health check",
    response_description="Service status and name.",
)
async def health() -> dict[str, str]:
    """Return the current health status of the Catalog Service.

    Returns:
        A dict with ``status`` and ``service`` keys.
    """
    return {"status": "ok", "service": "catalog-service"}

