"""Port: UserRepository (Loan Service).

Defines the abstract interface for persisting and querying User entities.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from loan.domain.user import User


class UserRepository(ABC):
    """Abstract repository port for User entities."""

    @abstractmethod
    async def save(self, user: User) -> None:
        """Persist a User (insert or update).

        Args:
            user: The User entity to persist.
        """

    @abstractmethod
    async def find_by_id(self, user_id: uuid.UUID) -> User | None:
        """Retrieve a User by primary key.

        Args:
            user_id: UUID of the user.

        Returns:
            The matching User, or None if not found.
        """

    @abstractmethod
    async def find_by_email(self, email: str) -> User | None:
        """Retrieve a User by e-mail address.

        Args:
            email: Unique e-mail address.

        Returns:
            The matching User, or None if not found.
        """

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check whether a User with the given e-mail is already registered.

        Args:
            email: E-mail address to check.

        Returns:
            True if registered, False otherwise.
        """
