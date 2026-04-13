"""Catalog Service – FastAPI application entry point."""

from fastapi import FastAPI
from catalog.infrastructure.api.routers.books_router import router as books_router

app = FastAPI(
    title="LibraryHub – Catalog Service",
    version="0.1.0",
    description="Manages book catalog and availability.",
)

app.include_router(books_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        A simple status dict.
    """
    return {"status": "ok", "service": "catalog-service"}
