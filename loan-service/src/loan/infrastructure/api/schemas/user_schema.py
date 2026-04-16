"""Pydantic schemas for User objects (API layer of the Loan Service).

Separates request and response schemas following Clean Architecture.
"""

import uuid

from pydantic import BaseModel


class UserRequest(BaseModel):
    """Schema for incoming user requests (POST /users).

    Attributes:
        name: Full name of the user.
        email: Unique e-mail address.
    """

    name: str
    email: str


class UserResponse(BaseModel):
    """Schema for outgoing user responses.

    Attributes:
        id: UUID of the user.
        name: Full name of the user.
        email: E-mail address.
    """

    id: uuid.UUID
    name: str
    email: str
