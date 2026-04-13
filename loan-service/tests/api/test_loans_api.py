"""API-Tests für die wichtigsten Endpunkte des Loan Service."""
import pytest
from httpx import AsyncClient, ASGITransport

from loan.main import app


@pytest.mark.asyncio
async def test_get_loans_returns_200_and_list() -> None:
    """GET /loans gibt 200 OK und eine Liste zurück."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/loans?user_id=1234")
    assert response.status_code == 200
    assert "items" in response.json()


@pytest.mark.asyncio
async def test_post_loans_creates_loan() -> None:
    """POST /loans legt eine neue Ausleih-Anfrage an und gibt 202 zurück."""
    payload = {
        "isbn": "978-3-16-148410-0",
        "user_id": "1234",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/loans", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "loan_id" in data
    assert data["status"] == "PENDING"

