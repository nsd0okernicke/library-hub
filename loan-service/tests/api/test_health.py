"""Smoke tests for the Loan Service application setup.

Verifies that the FastAPI app starts correctly and the health endpoint responds.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from loan.main import app


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok() -> None:
    """Health endpoint should return HTTP 200 with status 'ok'."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "loan-service"

