"""API-Tests für die wichtigsten Endpunkte des Catalog Service.

Verwendet Dependency-Overrides mit In-Memory-Fake-Repositories (via conftest.py),
damit kein echtes Datenbanksetup benötigt wird.
"""
import pytest
from httpx import AsyncClient, ASGITransport

from catalog.main import app


@pytest.mark.asyncio
async def test_get_books_returns_200_and_list() -> None:
    """GET /books gibt 200 OK und eine leere Liste zurück."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/books")
    assert response.status_code == 200
    assert "items" in response.json()
    assert response.json()["items"] == []


@pytest.mark.asyncio
async def test_post_books_creates_book() -> None:
    """POST /books legt ein neues Buch an und gibt 201 zurück."""
    payload = {
        "isbn": "978-3-16-148410-0",
        "title": "Testbuch",
        "author": "Autor",
        "genre": "Roman",
        "initial_stock": 3,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/books", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["isbn"] == payload["isbn"]
    assert data["title"] == payload["title"]
    assert data["author"] == payload["author"]
    assert data["genre"] == payload["genre"]


@pytest.mark.asyncio
async def test_post_books_duplicate_isbn_returns_409() -> None:
    """POST /books mit doppelter ISBN gibt 409 Conflict zurück."""
    payload = {
        "isbn": "978-3-16-148410-0",
        "title": "Testbuch",
        "author": "Autor",
        "genre": "Roman",
        "initial_stock": 1,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post("/books", json=payload)
        response = await ac.post("/books", json=payload)
    assert response.status_code == 409

