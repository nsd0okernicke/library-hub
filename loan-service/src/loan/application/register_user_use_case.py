"""Application Use Case: RegisterUserUseCase (Loan Service).

Implements LOAN-0 – Neuen Nutzer registrieren.
"""

from __future__ import annotations

from loan.domain.ports.user_repository import UserRepository
from loan.domain.user import User


class RegisterUserUseCase:
    """Register a new library member.

    Raises:
        ValueError: If the e-mail address is already registered (→ HTTP 409).
    """

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def execute(self, *, name: str, email: str) -> User:
        """Create and persist a new User.

        Args:
            name: Full name of the user.
            email: Unique e-mail address.

        Returns:
            The newly created User entity.

        Raises:
            ValueError: If the e-mail is already registered.
        """
        if await self._user_repo.exists_by_email(email):
            raise ValueError(f"A user with email '{email}' already exists")

        user = User(name=name, email=email)
        await self._user_repo.save(user)
        return user
