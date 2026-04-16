"""Domain model: User entity (Loan Service).

A User represents a library member who can borrow books.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class User:
    """Domain entity representing a library member.

    Equality and hashing are based solely on *id*.

    Attributes:
        name: Full name of the user (must not be empty).
        email: Unique e-mail address (must not be empty).
        id: UUID primary key – auto-generated if not provided.

    Raises:
        ValueError: If *name* or *email* is an empty string.
    """

    name: str
    email: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self) -> None:
        """Validate that name and email are non-empty strings."""
        if not self.name:
            raise ValueError("User name must not be empty")
        if not self.email:
            raise ValueError("User email must not be empty")

    def __eq__(self, other: object) -> bool:
        """Compare users by id only."""
        if not isinstance(other, User):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on id only."""
        return hash(self.id)

    def __repr__(self) -> str:
        """Human-readable representation."""
        return f"User(id={self.id!r}, email={self.email!r})"
