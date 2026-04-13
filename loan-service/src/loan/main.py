"""Loan Service – FastAPI application entry point."""

from fastapi import FastAPI
from loan.infrastructure.api.routers.loans_router import router as loans_router

app = FastAPI(
    title="LibraryHub – Loan Service",
    version="0.1.0",
    description="Manages loan transactions and users.",
)

app.include_router(loans_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        A simple status dict.
    """
    return {"status": "ok", "service": "loan-service"}
