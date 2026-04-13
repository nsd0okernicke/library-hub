"""Pydantic-Schemas für Book-Objekte (API-Layer).

Trennt Request- und Response-Schemas gemäß Clean Architecture.
"""
from typing import Optional

from pydantic import BaseModel


class BookRequest(BaseModel):
    """Schema für eingehende Buch-Requests (POST /books).

    Attributes:
        isbn: ISBN-Zeichenkette (10 oder 13 Stellen, Bindestriche erlaubt).
        title: Buchtitel.
        author: Vollständiger Autorenname.
        genre: Genre oder Sachgebiet.
        initial_stock: Anfangsbestand (≥ 0).
        description: Optionale Freitextbeschreibung.
    """

    isbn: str
    title: str
    author: str
    genre: str
    initial_stock: int
    description: Optional[str] = None


class BookResponse(BaseModel):
    """Schema für ausgehende Buch-Antworten.

    Attributes:
        isbn: ISBN-Zeichenkette.
        title: Buchtitel.
        author: Vollständiger Autorenname.
        genre: Genre oder Sachgebiet.
        description: Optionale Freitextbeschreibung.
    """

    model_config = {"from_attributes": True}

    isbn: str
    title: str
    author: str
    genre: str
    description: Optional[str] = None


class BooksListResponse(BaseModel):
    """Schema für eine paginierte Liste von Büchern.

    Attributes:
        items: Liste der Buch-Response-Objekte.
    """

    items: list

