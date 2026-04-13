"""Catalog Service – FastAPI application entry point."""

from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from catalog.infrastructure.api.routers.books_router import (
    router as books_router,
    get_book_repo,
    get_stock_repo,
)
from catalog.infrastructure.db.session import get_session
from catalog.infrastructure.db.sqlalchemy_book_repository import SqlAlchemyBookRepository
from catalog.infrastructure.db.sqlalchemy_book_stock_repository import SqlAlchemyBookStockRepository

app = FastAPI(
    title="LibraryHub – Catalog Service",
    version="0.1.0",
    description="Manages book catalog and availability.",
)


# Produktive Repository-Implementierungen: werden bei Tests via
# conftest.py überschrieben; im Produktivbetrieb greifen diese.
def _prod_book_repo(session: AsyncSession = Depends(get_session)) -> SqlAlchemyBookRepository:
    """Produktive BookRepository-Implementierung (SQLAlchemy)."""
    return SqlAlchemyBookRepository(session)


def _prod_stock_repo(session: AsyncSession = Depends(get_session)) -> SqlAlchemyBookStockRepository:
    """Produktive BookStockRepository-Implementierung (SQLAlchemy)."""
    return SqlAlchemyBookStockRepository(session)


app.dependency_overrides[get_book_repo] = _prod_book_repo
app.dependency_overrides[get_stock_repo] = _prod_stock_repo

app.include_router(books_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        A simple status dict.
    """
    return {"status": "ok", "service": "catalog-service"}

