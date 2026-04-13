"""Pydantic schemas for User objects (API layer of the Loan Service).

Separates request and response schemas following Clean Architecture.
"""
import uuid

from pydantic import BaseModel


class UserRequest(BaseModel):
    """Schema für eingehende Nutzer-Requests (POST /users).

    Attributes:
        name: Vollständiger Name des Nutzers.
        email: Eindeutige E-Mail-Adresse.
    """

    name: str
    email: str


class UserResponse(BaseModel):
    """Schema für ausgehende Nutzer-Antworten.

    Attributes:
        id: UUID des Nutzers.
        name: Vollständiger Name des Nutzers.
        email: E-Mail-Adresse.
    """

    id: uuid.UUID
    name: str
    email: str

