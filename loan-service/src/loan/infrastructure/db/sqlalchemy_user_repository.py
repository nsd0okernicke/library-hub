"""SQLAlchemy implementation of the UserRepository port (Loan Service)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from loan.domain.ports.user_repository import UserRepository
from loan.domain.user import User
from loan.infrastructure.db.models import UserModel


class SqlAlchemyUserRepository(UserRepository):
    """SQLAlchemy adapter for the UserRepository port.

    Args:
        session: Active SQLAlchemy AsyncSession.
    """

    def __init__(self, session: AsyncSession) -> None:  # pragma: no cover
        self._session = session

    async def save(self, user: User) -> None:  # pragma: no cover
        """Persist a User domain object.

        Args:
            user: The domain object to persist.
        """
        existing = await self._session.get(UserModel, str(user.id))
        if existing:
            existing.name = user.name
            existing.email = user.email
        else:
            self._session.add(
                UserModel(id=str(user.id), name=user.name, email=user.email)
            )
        await self._session.commit()

    async def find_by_id(self, user_id: uuid.UUID) -> User | None:  # pragma: no cover
        """Load a User by ID.

        Args:
            user_id: The user's UUID.

        Returns:
            The matching User domain object, or None if not found.
        """
        model = await self._session.get(UserModel, str(user_id))
        if model is None:
            return None
        return User(id=uuid.UUID(model.id), name=model.name, email=model.email)

    async def find_by_email(self, email: str) -> User | None:  # pragma: no cover
        """Load a User by e-mail address.

        Args:
            email: The e-mail address to look up.

        Returns:
            The matching User domain object, or None if not found.
        """
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return User(id=uuid.UUID(model.id), name=model.name, email=model.email)

    async def exists_by_email(self, email: str) -> bool:  # pragma: no cover
        """Return True if a user with the given e-mail address already exists.

        Args:
            email: The e-mail address to check.

        Returns:
            True if found, False otherwise.
        """
        stmt = select(UserModel.id).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
