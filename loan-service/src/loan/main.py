"""Loan Service – FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(
    title="LibraryHub – Loan Service",
    version="0.1.0",
    description="Manages loan transactions and users.",
)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        A simple status dict.
    """
    return {"status": "ok", "service": "loan-service"}

